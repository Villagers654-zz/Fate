import re
import asyncio
from contextlib import suppress

import discord
import lavalink
from discord.ext import commands
from discord.errors import NotFound, Forbidden

from botutils import auth


url_rx = re.compile(r'https?://(?:www\.)?.+')
creds = auth.Lavalink()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create the lavalink client if not exists
        if not hasattr(bot, 'lavalink') or not bot.lavalink:
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        # Create a new node
        bot.lavalink.add_node(creds.host, creds.port, creds.password, 'eu', 'default-node')
        lavalink.add_event_hook(self.track_hook)

        # Assets
        self.color = self.bot.utils.colors.green()
        self._playlist = "https://cdn.discordapp.com/attachments/632084935506788385/797738904483528765/playlist.png"
        self._player = "https://cdn.discordapp.com/attachments/498333830395199488/507170864614342676/75c21df998c0d0c97631853ea5619ea1.gif"
        self._playing = "https://media.discordapp.net/attachments/498333830395199488/507136609897021455/Z23N.gif"
        self._note = "https://cdn.discordapp.com/attachments/632084935506788385/797744681672507402/note.png"
        self._notes = "https://cdn.discordapp.com/attachments/632084935506788385/797740072262303744/note.gif"
        self._repeat = "https://cdn.discordapp.com/attachments/632084935506788385/797743421770432542/repeat.gif"
        self._volume = "https://cdn.discordapp.com/attachments/632084935506788385/797782826484498432/volume.png"
        self._skip = "https://cdn.discordapp.com/attachments/632084935506788385/797783872581795840/skip.png"
        self._seek = "https://cdn.discordapp.com/attachments/632084935506788385/797793989947293767/seek.png"


    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()
        for node in self.bot.lavalink.node_manager.nodes:
            self.bot.lavalink.node_manager.remove_node(node)

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        async def ensure_playing():
            if not ctx.player or not ctx.player.is_connected:
                await ctx.send("I'm not connected to any voice channel")
            elif not ctx.author.voice or (
                    ctx.player.is_connected and ctx.author.voice.channel.id != int(ctx.player.channel_id)):
                await ctx.send("We don't currently share a voice channel")
            else:
                return None
            raise self.bot.ignored_exit

        async def delete_after():
            await asyncio.sleep(25)
            if ctx.message is not None:
                with suppress(NotFound, Forbidden):
                    await ctx.message.delete()

        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            self.bot.loop.create_task(delete_after())

        # Ensure music commands are ran in a guild
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
            ctx.player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            ctx.ensure_player_is_playing = ensure_playing

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    async def ensure_voice(self, ctx):
        """Ensures the bot and author are in the same voice channel"""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError("Join a voice channel first")

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError("I'm not connected to any voice channel")

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError("I need `connect` and `speak` permissions")

            player.store('channel', ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError("You need to be in my voice channel")

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id):
        """ Connects to the given voice channel ID. A channel_id of `None` means disconnect. """
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    def get_player(self, ctx):
        self.bot.lavalink.player_manager.get(ctx.guild.id)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = ctx.player
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        e = discord.Embed(color=self.color)

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            e.set_author(name="Playlist Queued", icon_url=self._playlist)
            e.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        else:
            options = [
                f"[{track['info']['title']}]({track['info']['uri']})"
                for track in results["tracks"]
            ][:5]
            choice = await self.bot.utils.get_choice(ctx, *options, user=ctx.author)
            if not choice:
                return
            track = results['tracks'][options.index(choice)]

            e.set_author(name="Song Queued", icon_url=self._note)
            e.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=e, delete_after=25)

        if not player.is_playing:
            await player.play()

    @commands.command(name="queue")
    async def queue(self, ctx):
        await ctx.ensure_player_is_playing()

        # Index the pages for the queue
        def create_embed():
            e = discord.Embed(color=self.color)
            e.set_author(name="Music Queue", icon_url=self._playing)
            e.set_thumbnail(url=self._player)
            e.description = "\n".join(_page)
            e.set_footer(text=f"Page 1/{len(pages)}")
            pages.append(e)

        pages = []
        _page = []
        for i, track in enumerate(ctx.player.queue):
            requester = self.bot.get_user(track.requester)
            song = f"**#{i + 1}.** [{track.title}]({track.uri})\n﹂`From {requester}`"
            _page.append(song)
            if len(_page) == 9:
                create_embed()
                _page = []
        if _page:
            create_embed()
        if not pages:
            return await ctx.send("The queue is currently empty", delete_after=25)

        async def add_emojis_task():
            """ So the bot can read reactions before all are added """
            for emoji in emojis:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.5)
            return

        index = 0
        emojis = ["🏡", "⏪", "⏩"]
        pages[0].set_footer(
            text=f"Page {index + 1}/{len(pages)}"
        )
        msg = await ctx.send(embed=pages[0])
        if len(pages) == 1:
            await asyncio.sleep(25)
            return await msg.delete()

        self.bot.loop.create_task(add_emojis_task())
        while True:
            try:
                reaction, user = await self.bot.utils.get_reaction(ctx, timeout=25, ignore_timeout=False)
            except asyncio.TimeoutError:
                return await msg.delete()
            emoji = reaction.emoji

            if emoji == emojis[0]:  # home
                index = 0

            if emoji == emojis[1]:
                index -= 1

            if emoji == emojis[2]:
                index += 1

            if index > len(pages) - 1:
                index = len(pages) - 1

            if index < 0:
                index = 0

            pages[index].set_footer(
                text=f"Page {index + 1}/{len(pages)}"
            )
            await msg.edit(embed=pages[index])
            await msg.remove_reaction(reaction, ctx.author)

    @commands.command(name="disconnect", aliases=['dc'])
    async def disconnect(self, ctx):
        """Disconnects the player from the voice channel and clears its queue"""
        await ctx.ensure_player_is_playing()
        ctx.player.queue.clear()
        await ctx.player.stop()
        await self.connect_to(ctx.guild.id, None)
        await ctx.send("*⃣ | Disconnected.", delete_after=25)

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops the player from playing without leaving the channel"""
        await ctx.ensure_player_is_playing()
        ctx.player.queue.clear()
        await ctx.player.stop()
        await ctx.send("Stopped playing", delete_after=25)

    @commands.command(name="repeat")
    async def repeat(self, ctx):
        """Sets the player to repeat the currently playing track"""
        await ctx.ensure_player_is_playing()
        ctx.player.repeat = not ctx.player.repeat
        e = discord.Embed(color=self.color)
        new_toggle = "Enabled" if ctx.player.repeat else "Disabled"
        e.set_author(name=f"{new_toggle} repeat", icon_url=self.repeat)
        await ctx.send(embed=e, delete_after=25)

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip to the next track in queue"""
        await ctx.ensure_player_is_playing()
        await ctx.player.skip()
        e = discord.Embed(color=self.color)
        e.set_author(name="Skipped to the next song", icon_url=self._skip)
        await ctx.send(embed=e, delete_after=25)

    @commands.command(name="seek", aliases=["s"])
    async def seek(self, ctx, amount: int):
        await ctx.ensure_player_is_playing()
        position = amount * 1000 + ctx.player.current.duration
        await ctx.player.seek(position)
        e = discord.Embed(color=self.color)
        e.set_author(name=f"Skipped {amount} seconds", icon_url=self._notes)
        await ctx.send(embed=e, delete_after=25)

    @commands.command(name="playat")
    async def play_at(self, ctx, position):
        """Skip forward in a song, or play at a specific time"""
        await ctx.ensure_player_is_playing()

        usage = "Invalid usage. Either specify in seconds, or in the format of 5:27 to " \
                "play at 5 minutes and 27 seconds into the track"

        if position.isdigit():
            _position = int(position)

        elif ":" in position:
            nums = position.split(":")
            if not any(num.isdigit() for num in nums):
                return await ctx.send(usage, delete_after=25)
            for num in nums:
                if not num:
                    return await ctx.send(usage, delete_after=25)

            nums = [int(num) for num in nums]
            if len(nums) == 2:
                minutes, seconds = nums
                _position = 60 * minutes + seconds

            elif len(nums) == 3:
                hours, minutes, seconds = nums
                _position = ((60 * 60) * hours) + 60 * minutes + seconds

            else:
                return await ctx.send("Nope. I'm not allowed to read that far", delete_after=25)

        else:
            return await ctx.send(usage, delete_after=25)
        _position *= 1000

        if _position > ctx.player.current.duration:
            return await ctx.send("The current track isn't that long", delete_after=25)
        await ctx.player.seek(_position)

        e = discord.Embed(color=self.color)
        e.set_author(name=f"Now playing at {position}", icon_url=self._seek)
        await ctx.send(embed=e, delete_after=25)

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, volume: int):
        """Alter the players volume to raise or lower it"""
        await ctx.ensure_player_is_playing()
        if volume > 1000:
            await ctx.send("biTcH nO, those heels are too high", delete_after=25)
        if volume < 0:
            await ctx.send("That's deeper than corpses voice.. no", delete_after=25)
        await ctx.player.set_volume(volume)
        e = discord.Embed(color=self.color)
        e.set_author(name=f"Set the volume to {volume}", icon_url=self._volume)
        await ctx.send(embed=e, delete_after=25)

    @commands.command(name="now", aliases=["np", "playing", "current", "cur"])
    async def now_playing(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="pause")
    async def pause(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="resume")
    async def resume(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="remove")
    async def remove(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="previous")
    async def resume(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")

    @commands.command(name="find")
    async def find(self, ctx):
        await ctx.ensure_player_is_playing()
        await ctx.send("This command isn't implemented yet")


def setup(bot):
    bot.add_cog(Music(bot))
