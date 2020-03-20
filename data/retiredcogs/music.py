import discord
from discord.ext import commands
import asyncio
import random
import functools
import itertools
import math
import youtube_dl

if not discord.opus.is_loaded():
    """
    The opus library here is opus.dll on Windows.
    Or libopus.so on Linux in the current directory.
    Replace this with the location where opus is installed and its proper filename.
    On Windows this DLL is automatically provided for you.
    """
    discord.opus.load_opus("opus")


class YTDLError(Exception):
    pass


class MusicError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_opts = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }

    ffmpeg_opts = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(ytdl_opts)

    def __init__(self, message, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.requester = message.author
        self.channel = message.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        self.upload_date = f'{data.get("upload_date")[6:8]}.{data.get("upload_date")[4:6]}.{data.get("upload_date")[0:4]}'
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}** *[Duration: {self.duration}]*"

    @classmethod
    async def create_source(cls, message, search: str, *, loop=None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=False
        )
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(
                f"Couldn't find anything that matches the search query `{search}`"
            )

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry is not None:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(
                    f"Couldn't retrieve any data for the search query `{search}`"
                )

        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(
                f"Error while trying to fetch the data for the url `{webpage_url}`"
            )

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(
                        f"Couldn't retrieve any matches for the url `{webpage_url}`"
                    )

        return cls(
            message, discord.FFmpegPCMAudio(info["url"], **cls.ffmpeg_opts), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        # Create an actual string
        duration = []
        if days > 0:
            duration.append(f"{days} days")
        if hours > 0:
            duration.append(f"{hours} hours")
        if minutes > 0:
            duration.append(f"{minutes} minutes")
        if seconds > 0:
            duration.append(f"{seconds} seconds")

        return ", ".join(duration)


class Song:
    def __init__(self, state, source):
        self.state = state
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = discord.Embed(
            title="Now playing:", description=f"{self.source.title}", color=0x39FF14
        )
        embed.add_field(name="Duration:", value=self.source.duration)
        embed.add_field(name="Requested by:", value=self.requester.mention)
        embed.add_field(
            name="Channel:",
            value=f"[{self.source.uploader}]({self.source.uploader_url})",
        )
        embed.add_field(name="Song URL:", value=f"[Click here]({self.source.url})")
        embed.set_thumbnail(url=self.source.thumbnail)

        return embed

    def thumbnail(self):
        img = self.source.thumbnail
        return img


class SongQueue(asyncio.Queue):
    def __iter__(self):
        return self._queue.__iter__()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, value: int):
        self._queue.rotate(-value)
        self._queue.pop()
        self._queue.rotate(value - 1)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return list(
                itertools.islice(self._queue, index.start, index.stop, index.step)
            )
        else:
            return self._queue[index]

    def __len__(self):
        return len(self._queue)


class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self._volume = 0.5
        self.bot = bot
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    async def audio_player_task(self):
        while True:
            self.next.clear()

            self.current = await self.songs.get()

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(
                embed=self.current.create_embed(), delete_after=20
            )

            await self.next.wait()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value

        if self.voice:
            self.voice.source.volume = value

    def is_done(self):
        if self.voice is None or self.current is None:
            return True

        return not self.voice.is_playing() and not self.voice.is_paused()

    def play_next_song(self, error=None):
        fut = asyncio.run_coroutine_threadsafe(self.next.set(), self.bot.loop)

        try:
            fut.result()
        except:
            raise MusicError(error)

    def skip(self):
        self.skip_votes.clear()

        if not self.is_done():
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music:
    def luck(ctx):
        return ctx.message.author.id == 264838866480005122

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, guild):
        state = self.voice_states.get(str(guild.id))

        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[str(guild.id)] = state

        return state

    def __unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def __local_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in a DM channel."
            )

        return True

    async def __before_invoke(self, ctx):
        ctx.state = self.get_voice_state(ctx.guild)

    async def on_voice_state_update(self, member, before, after):
        if before.channel:
            if not after.channel:
                c = 0
                for member in before.channel.members:
                    if not member.bot:
                        c += 1
                if c < 1:
                    for channel in member.guild.channels:
                        if isinstance(channel, discord.VoiceChannel):
                            for member in before.channel.members:
                                if self.bot.user.id == member.id:
                                    await VoiceState.stop(
                                        self.get_voice_state(member.guild)
                                    )
                                    del self.voice_states[str(member.guild.id)]

    @commands.command(name="join", invoke_without_command=True)
    async def _join(self, ctx):
        destination = ctx.author.voice.channel
        if ctx.state.voice is not None:
            return await ctx.state.voice.move_to(destination)
        ctx.state.voice = await destination.connect()

    @commands.command(name="summon")
    async def _summon(self, ctx, *, channel: discord.VoiceChannel = None):
        if channel is None and not ctx.author.voice:
            await ctx.send(
                "You are not connected to a voice channel nor specified a channel to join.",
                delete_after=20,
            )
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        else:
            destination = channel or ctx.author.voice.channel
            if ctx.state.voice is not None:
                return await ctx.state.voice.move_to(destination)
            ctx.state.voice = await destination.connect()
            await ctx.message.add_reaction("👍")
            await asyncio.sleep(20)
            await ctx.messagge.delete()

    @commands.command(name="play", aliases=["p"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(manage_messages=True)
    async def _play(self, ctx, *, search: str):
        if ctx.state.voice is None:
            await ctx.invoke(self._join)
        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(
                    ctx.message, search, loop=self.bot.loop
                )
            except Exception as e:
                await ctx.send(
                    f"An error occurred while processing this request: {e}",
                    delete_after=20,
                )
                await ctx.message.add_reaction("⚠")
                await asyncio.sleep(20)
                return await ctx.message.delete()
            song = Song(ctx.state.voice, source)
            await ctx.state.songs.put(song)
            e = discord.Embed(description=f"{str(source)}", color=0x39FF14)
            e.set_author(
                name="{} added to the queue".format(ctx.author.name),
                icon_url=ctx.author.avatar_url,
            )
            await ctx.send(embed=e, delete_after=20)
            await ctx.message.delete()

    @commands.command(name="volume", aliases=["vol", "v"])
    async def _volume(self, ctx, *, volume: int):
        if ctx.state.is_done():
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if 0 > volume > 100:
            await ctx.send("Volume must be between 0 and 100", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        ctx.state.volume = volume / 100
        e = discord.Embed(color=0x39FF14)
        e.set_author(
            name=f"set the volume to {volume}%", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=e)
        await ctx.message.delete()

    @commands.command(name="now", aliases=["playing", "current", "nowplaying", "np"])
    async def _now(self, ctx):
        if ctx.state.is_done():
            await ctx.message.add_reaction("⚠")
            await ctx.send("Theres nothing playing right now", delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await ctx.send(embed=ctx.state.current.create_embed(), delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name="pause")
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx):
        if not ctx.state.is_done():
            ctx.state.voice.pause()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="resume")
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx):
        if not ctx.state.is_done():
            ctx.state.voice.resume()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="stop")
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx):
        ctx.state.songs.clear()
        if not ctx.state.is_done():
            ctx.state.voice.stop()
            await ctx.message.add_reaction("⏹")

    @commands.command(name="skip")
    async def _skip(self, ctx):
        if ctx.state.is_done():
            await ctx.send("I'm not playing any music right now", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        voter = ctx.message.author
        if voter == ctx.state.current.requester:
            await ctx.message.add_reaction("⏭")
            ctx.state.skip()
            await asyncio.sleep(20)
            await ctx.message.delete()
        elif voter.id not in ctx.state.skip_votes:
            ctx.state.skip_votes.add(voter.id)
            total_votes = len(ctx.state.skip_votes)
            if total_votes >= 2:
                await ctx.message.add_reaction("⏭")
                ctx.state.skip()
                await asyncio.sleep(20)
                await ctx.message.delete()
            else:
                await ctx.send(
                    f"Vote added, currently at **{total_votes}/3**", delete_after=20
                )
                await asyncio.sleep(20)
                await ctx.message.delete()
        else:
            await ctx.send("You have already voted to skip", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            await ctx.message.delete()

    @commands.command(name="queue")
    async def _queue(self, ctx, *, page: int = 1):
        if len(ctx.state.songs) == 0:
            queue = "Theres nothing in the queue"
            page = 0
            pages = 0
        else:
            items_per_page = 9
            pages = math.ceil(len(ctx.state.songs) / items_per_page)
            start = (page - 1) * items_per_page
            end = start + items_per_page
            queue = ""
            for index, song in enumerate(ctx.state.songs[start:end], start=start):
                queue += f"**#{index + 1}.** [{song.source.title}]({song.source.url})\n"
        e = discord.Embed(
            description=f"Tracks: [{len(ctx.state.songs) + 1}]", color=0x39FF14
        )
        e.set_author(
            name="{} Queue".format(ctx.guild.name),
            icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif",
        )
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/498333830395199488/507170864614342676/75c21df998c0d0c97631853ea5619ea1.gif"
        )
        e.add_field(name="◈ Upcoming ◈", value=f"{queue}")
        e.set_footer(text=f"Viewing page {page}/{pages}")
        await ctx.send(embed=e, delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name="thumbnail")
    async def _thumbnail(self, ctx):
        e = discord.Embed(color=0x39FF14)
        e.set_image(url=ctx.state.current.thumbnail())
        await ctx.send(embed=e)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx):
        if len(ctx.state.songs) == 0:
            await ctx.send("There is nothing in the queue", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        ctx.state.songs.shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="remove")
    async def _remove(self, ctx, index: int):
        if len(ctx.state.songs) == 0:
            await ctx.send("Nothing in the queue.", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        ctx.state.songs.remove(index)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name="disconnect", aliases=["dc"])
    @commands.has_permissions(manage_guild=True)
    async def _disconnect(self, ctx):
        if ctx.state.voice is None:
            await ctx.send("Not connected to any voice channel.", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await ctx.state.stop()
        del self.voice_states[str(ctx.guild.id)]
        await ctx.send("Disconnected", delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name="luckydisconnect")
    @commands.check(luck)
    async def _luckydisconnect(self, ctx):
        if ctx.state.voice is None:
            await ctx.send("Not connected to any voice channel.", delete_after=20)
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await ctx.state.stop()
        del self.voice_states[str(ctx.guild.id)]

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(
                "You are not connected to any voice channel.", delete_after=20
            )
            await ctx.message.add_reaction("⚠")
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if ctx.voice_client is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send("Bot already in a voice channel.", delete_after=20)
                await ctx.message.add_reaction("⚠")
                await asyncio.sleep(20)
                return await ctx.message.delete()


def setup(bot):
    bot.add_cog(Music(bot))
