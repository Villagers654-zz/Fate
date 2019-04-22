from discord.ext import commands
from utils import colors, utils
import lavalink
import discord
import asyncio
import math
import re

time_rx = re.compile('[0-9]+')
url_rx = re.compile('https?:\/\/(?:www\.)?.+')  # noqa: W605

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'lavalink'):
            lavalink.Client(bot=bot, password='youshallnotpass', loop=bot.loop, ws_port=2333, rest_port=2333)
            self.bot.lavalink.register_hook(self._track_hook)

    def cog_unload(self):
        for guild_id, player in self.bot.lavalink.players:
            self.bot.loop.create_task(player.disconnect())
            player.cleanup()
        # Clear the players from Lavalink's internal cache
        self.bot.lavalink.players.clear()
        self.bot.lavalink.unregister_hook(self._track_hook)

    async def _track_hook(self, event):
        if isinstance(event, lavalink.Events.StatsUpdateEvent):
            return
        channel = self.bot.get_channel(event.player.fetch('channel'))
        if not channel:
            return
        if isinstance(event, lavalink.Events.TrackStartEvent):
            await channel.send(embed=discord.Embed(title='Now playing:',
                description=event.track.title, color=colors.green()), delete_after=20)
        elif isinstance(event, lavalink.Events.QueueEndEvent):
            await channel.send('Queue ended', delete_after=5)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not after.channel:
            def get_humans(channel):
                humans = 0
                for member in channel.members:
                    if not member.bot:
                        humans += 1
                return humans
            bot = member.guild.get_member(self.bot.user.id)
            channel = self.bot.get_channel(before.channel.id)
            if bot in channel.members:
                player = self.bot.lavalink.players.get(member.guild.id)
                if get_humans(channel) < 1:
                    await asyncio.sleep(25)
                    channel = self.bot.get_channel(before.channel.id)
                    if get_humans(channel) < 1:
                        player.queue.clear()
                        if player.is_connected:
                            await player.disconnect()

    @commands.command(name="play")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def _play(self, ctx, *, query):
        """ Lists the first 10 search results from a given query. """
        if not query.startswith('ytsearch:') and not query.startswith('scsearch:'):
            query = 'ytsearch:' + query
        if 'youtu.be' in query or 'http' in query:
            player = self.bot.lavalink.players.get(ctx.guild.id)
            query = query.strip('<>')
            if not url_rx.match(query):
                query = f'ytsearch:{query}'
            results = await self.bot.lavalink.get_tracks(query)
            if not results or not results['tracks']:
                await ctx.send('Nothing found', delete_after=20)
                await asyncio.sleep(20)
                return await ctx.message.delete()
            e = discord.Embed(color=colors.green())
            if results['loadType'] == 'PLAYLIST_LOADED':
                tracks = results['tracks']
                for track in tracks:
                    player.add(requester=ctx.author.id, track=track)
                e.set_author(name="Playlist Enqueued!", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
                e.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
                await ctx.send(embed=e, delete_after=20)
            else:
                track = results['tracks'][0]
                e.set_author(name="Track Enqueued", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
                e.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
                await ctx.send(embed=e, delete_after=20)
                player.add(requester=ctx.author.id, track=track)
            if not player.is_playing:
                await player.play()
            return await ctx.message.delete()
        results = await self.bot.lavalink.get_tracks(query)
        if not results or not results['tracks']:
            await ctx.send('Nothing found', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        tracks = results['tracks'][:10]  # First 10 results
        e = discord.Embed(color=colors.green())
        e.title = 'Which track number?'
        e.description = ''
        local = []
        for index, track in enumerate(tracks, start=1):
            track_title = track["info"]["title"]
            track_uri = track["info"]["uri"]
            e.description += f'`{index}.` [{track_title}]({track_uri})\n'
            local.append((f"{track_title}", track_uri))
        e.set_footer(text='Reply with "cancel" to stop')
        message = await ctx.send(embed=e)
        completed = False
        while completed is False:
            async def clean_chat(ctx, message, msg=None):
                await ctx.message.delete()
                await message.delete()
                if msg:
                    await msg.delete()
            def pred(m):
                return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
            try:
                msg = await self.bot.wait_for('message', check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send('You took a min to respond so ima just go.. ;-;', delete_after=5)
                await clean_chat(ctx, message)
            else:
                if 'cancel' in msg.content.lower():
                    return await clean_chat(ctx, message, msg)
                invalid_chars = False
                for x in list(msg.content):
                    if x not in '1234567890':
                        await ctx.send('Invalid character, try again', delete_after=3)
                        await msg.delete()
                        invalid_chars = True
                        break
                if invalid_chars:
                    continue
                query = local[int(msg.content) - 1][1]  # type: str
                player = self.bot.lavalink.players.get(ctx.guild.id)
                query = query.strip('<>')
                if not url_rx.match(query):
                    query = f'ytsearch:{query}'
                results = await self.bot.lavalink.get_tracks(query)
                if not results or not results['tracks']:
                    await ctx.send('Nothing found', delete_after=20)
                    await asyncio.sleep(20)
                    return await clean_chat(ctx, message, msg)
                embed = discord.Embed(color=colors.green())
                if results['loadType'] == 'PLAYLIST_LOADED':
                    tracks = results['tracks']
                    for track in tracks:
                        player.add(requester=ctx.author.id, track=track)
                    embed.set_author(name="Playlist Enqueued!", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
                    embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
                    await ctx.send(embed=embed, delete_after=20)
                else:
                    track = results['tracks'][0]
                    embed.set_author(name="Track Enqueued", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
                    embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
                    await ctx.send(embed=embed, delete_after=20)
                    player.add(requester=ctx.author.id, track=track)
                if not player.is_playing:
                    await player.play()
                await clean_chat(ctx, message, msg)
                completed = True

    @commands.command(name='old_play', aliases=['p'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def _old_play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        results = await self.bot.lavalink.get_tracks(query)
        if not results or not results['tracks']:
            await ctx.send('Nothing found', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        embed = discord.Embed(color=colors.green())
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            embed.set_author(name="Playlist Enqueued!", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            await ctx.send(embed=embed, delete_after=20)
        else:
            track = results['tracks'][0]
            embed.set_author(name="Track Enqueued", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            await ctx.send(embed=embed, delete_after=20)
            player.add(requester=ctx.author.id, track=track)
        if not player.is_playing:
            await player.play()
        await ctx.message.delete()

    @commands.command(name='previous', aliases=['pv'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _previous(self, ctx):
        """ Plays the previous song. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        try:
            await player.play_previous()
            await ctx.message.add_reaction("👍")
            await asyncio.sleep(20)
            await ctx.message.delete()
        except lavalink.NoPreviousTrack:
            await ctx.send('There is no previous song to play.', delete_after=20)
            await asyncio.sleep(20)
            await ctx.message.delete()

    @commands.command(name='playnow', aliases=['pn'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def _playnow(self, ctx, *, query: str):
        """ Plays immediately a song. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.queue and not player.is_playing:
            await ctx.invoke(self._play, query=query, delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        results = await self.bot.lavalink.get_tracks(query)
        if not results or not results['tracks']:
            await ctx.send('Nothing found', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        tracks = results['tracks']
        track = tracks.pop(0)
        if results['loadType'] == 'PLAYLIST_LOADED':
            for _track in tracks:
                player.add(requester=ctx.author.id, track=_track)
        await player.play_now(requester=ctx.author.id, track=track)
        await asyncio.sleep(20)
        await ctx.messagae.delete()

    @commands.command(name='playat', aliases=['pa'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def _playat(self, ctx, index: int):
        """ Plays the queue from a specific point. Disregards tracks before the index. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if index < 1:
            await ctx.send('Invalid specified index.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if len(player.queue) < index:
            await ctx.send('This index exceeds the queue\'s length.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await player.play_at(index-1)
        await ctx.message.add_reaction("👍")
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name="forward", aliases=["seek"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _forward(self, ctx, *, time: str):
        """ Seeks to a given position in a track. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Not playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        seconds = time_rx.search(time)
        if not seconds:
            await ctx.send('You need to specify the amount of seconds to skip!', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        seconds = int(seconds.group()) * 1000
        if time.startswith('-'):
            seconds *= -1
        track_time = player.position + seconds
        await player.seek(track_time)
        await ctx.send(f'Moved track to **{lavalink.Utils.format_time(track_time)}**', delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='skip', aliases=['forceskip', 'fs'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _skip(self, ctx):
        """ Skips the current track. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Not playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await player.skip()
        await ctx.send('⏭ | Skipped.', delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='stop')
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _stop(self, ctx):
        """ Stops the player and clears its queue. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Not playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Stopped.', delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='now', aliases=['np', 'n', 'playing'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def _now(self, ctx):
        """ Shows some stats about the currently playing song. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        song = 'Nothing'
        if player.current:
            position = lavalink.Utils.format_time(player.position)
            if player.current.stream:
                duration = '🔴 LIVE'
            else:
                duration = lavalink.Utils.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({position}/{duration})'
        embed = discord.Embed(color=colors.green(), title='Now Playing', description=song)
        await ctx.send(embed=embed, delete_after=20)
        await asyncio.sleep(20)
        return await ctx.message.delete()

    @commands.command(name='queue', aliases=['q'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def _queue(self, ctx, page: int = 1):
        """ Shows the player's queue. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.queue:
            await ctx.send('There\'s nothing in the queue! Why not queue something?', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue_list = ''
        for index, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'
        embed = discord.Embed(colour=colors.green(), description=queue_list)
        embed.set_author(name=f"Queue: {len(player.queue)}", icon_url="https://cdn.discordapp.com/attachments/498333830395199488/507136609897021455/Z23N.gif")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/498333830395199488/507170864614342676/75c21df998c0d0c97631853ea5619ea1.gif")
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed, delete_after=60)
        await asyncio.sleep(60)
        await ctx.message.delete()

    @commands.command(name='pause', aliases=['resume'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _pause(self, ctx):
        """ Pauses/Resumes the current track. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Not playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if player.paused:
            await player.set_pause(False)
            await ctx.send('⏯ | Resumed', delete_after=20)
            await asyncio.sleep(20)
            await ctx.message.delete()
        else:
            await player.set_pause(True)
            await ctx.send('⏯ | Paused', delete_after=20)
            await asyncio.sleep(20)
            await ctx.message.delete()

    @commands.command(name='volume', aliases=['vol'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _volume(self, ctx, volume: int = None):
        """ Changes the player's volume. Must be between 0 and 1000. Error Handling for that is done by Lavalink. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not volume:
            await ctx.send(f'🔈 | {player.volume}%', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        await player.set_volume(volume)
        await ctx.send(f'🔈 | Set to {player.volume}%', delete_after=20)
        await asyncio.sleep(20)
        return await ctx.message.delete()

    @commands.command(name='shuffle')
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _shuffle(self, ctx):
        """ Shuffles the player's queue. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Nothing playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        player.shuffle = not player.shuffle
        await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'), delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='repeat', aliases=['loop'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _repeat(self, ctx):
        """ Repeats the current song until the command is invoked again. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send('Nothing playing.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        player.repeat = not player.repeat
        await ctx.send('🔁 | Repeat ' + ('enabled' if player.repeat else 'disabled'), delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='remove')
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _remove(self, ctx, index: int):
        """ Removes an item from the player's queue with the given index. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.queue:
            await ctx.send('Nothing queued.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if index > len(player.queue) or index < 1:
            await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        index -= 1
        removed = player.queue.pop(index)
        await ctx.send(f'Removed **{removed.title}** from the queue.', delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='find')
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def _find(self, ctx, *, query):
        """ Lists the first 10 search results from a given query. """
        if not query.startswith('ytsearch:') and not query.startswith('scsearch:'):
            query = 'ytsearch:' + query
        results = await self.bot.lavalink.get_tracks(query)
        if not results or not results['tracks']:
            await ctx.send('Nothing found', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        tracks = results['tracks'][:10]  # First 10 results
        o = ''
        for index, track in enumerate(tracks, start=1):
            track_title = track["info"]["title"]
            track_uri = track["info"]["uri"]
            o += f'`{index}.` [{track_title}]({track_uri})\n'
        embed = discord.Embed(color=colors.green(), description=o)
        await ctx.send(embed=embed, delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @commands.command(name='disconnect', aliases=['dc'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_connected:
            await ctx.send('Not connected.', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            await ctx.send('You\'re not in my voicechannel!', delete_after=20)
            await asyncio.sleep(20)
            return await ctx.message.delete()
        player.queue.clear()
        await player.disconnect()
        await ctx.send('*⃣ | Disconnected.', delete_after=20)
        await asyncio.sleep(20)
        await ctx.message.delete()

    @_playnow.before_invoke
    @_previous.before_invoke
    @_play.before_invoke
    @_old_play.before_invoke
    async def ensure_voice(self, ctx):
        """ A few checks to make sure the bot can join a voice channel. """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send('You aren\'t connected to any voice channel.', delete_after=20)
                await asyncio.sleep(20)
                return await ctx.message.delete()
            permissions = ctx.author.voice.channel.permissions_for(ctx.me)
            if not permissions.connect or not permissions.speak:
                await ctx.send('Missing permissions `CONNECT` and/or `SPEAK`.', delete_after=20)
                await asyncio.sleep(20)
                return await ctx.message.delete()
            player.store('channel', ctx.channel.id)
            await player.connect(ctx.author.voice.channel.id)
        else:
            if player.connected_channel.id != ctx.author.voice.channel.id:
                await ctx.send('Join my voice channel!', delete_after=20)
                await asyncio.sleep(20)
                await ctx.message.delete()

def setup(bot):
    bot.add_cog(Music(bot))
