
from contextlib import suppress
import asyncio

from discord.ext import commands, tasks
from discord.errors import NotFound, Forbidden
import discord


class GlobalChatRewrite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.msg_cache = []
        self.msg_chunks = []
        self.cache_task = self.bot.loop.create_task(self.cache_channels())
        self.handle_queue.start()
        self._queue = []
        self.last_id = None

    def cog_unload(self):
        self.handle_queue.cancel()
        if not self.cache_task.done():
            self.cache_task.cancel()

    @property
    def queue(self) -> list:
        self._queue = self._queue[-3:]
        return self._queue

    @tasks.loop(seconds=0.21)
    async def handle_queue(self):
        queued_to_send = []
        for entry in list(self.queue):
            if not any(entry[2] in values for values in queued_to_send):
                queued_to_send.append(entry)
        for embed, requires_edit, author_msg in queued_to_send:
            with suppress(ValueError, IndexError):
                self._queue.remove([embed, requires_edit, author_msg])
            if requires_edit:
                for message in self.msg_cache:
                    with suppress(NotFound, Forbidden):
                        await message.edit(embed=embed)
            else:
                self.msg_cache = []
                chunk = {}
                for guild_id, channel in list(self.cache.items()):
                    with suppress(AttributeError):
                        if author_msg.channel.id == channel.id and author_msg.attachments:
                            continue
                    with suppress(NotFound, Forbidden):
                        msg = await channel.send(embed=embed)
                        self.msg_cache.append(msg)
                        chunk[msg.channel.id] = msg.id
                self.msg_chunks.append(chunk)
            with suppress(AttributeError, NotFound, Forbidden):
                if author_msg.attachments:
                    if author_msg.channel.permissions_for(author_msg.guild.me).add_reactions:
                        await author_msg.add_reaction("✅")
                else:
                    await author_msg.delete()

    async def cache_channels(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        while True:
            if not self.bot.pool:
                await asyncio.sleep(1)
                continue
            break
        async with self.bot.cursor() as cur:
            await cur.execute(f"select guild_id, channel_id from global_chat;")
            ids = await cur.fetchall()
        for guild_id, channel_id in ids:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                async with self.bot.cursor() as cur:
                    await cur.execute(
                        f"delete from global_chat "
                        f"where guild_id = {guild_id};"
                    )
            else:
                self.cache[guild_id] = channel

    @commands.group(name="gc", aliases=["global-chat", "globalchat", "global_chat"])
    async def _gc(self, ctx):
        pass

    @_gc.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx):
        msg = await ctx.send("Enabling global chat")
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into global_chat values ("
                f"{ctx.guild.id}, {ctx.channel.id}, {msg.id}"
                f") on duplicate key update "
                f"channel_id = {ctx.channel.id} "
                f"and message_id = {msg.id};"
            )

        self.cache[ctx.guild.id] = ctx.channel
        await ctx.send("Enabled global chat")

    @_gc.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select * from global_chat where guild_id = {ctx.guild.id};")
            if not cur.rowcount:
                return await ctx.send("Global chat isn't enabled")
            if ctx.guild.id in self.cache:
                del self.cache[ctx.guild.id]
            await cur.execute(f"delete from global_chat where guild_id = {ctx.guild.id};")
        await ctx.send("Disabled global chat")

    @commands.Cog.listener()
    async def on_message(self, msg):
        active = [m.id for m in list(self.cache.values())]
        if not msg.author.bot and msg.channel.id in active:
            # Duplicate messages
            if msg.content and any(msg.content == m.content for m in self.msg_cache):
                return

            # Missing permissions to moderate global chat
            if not msg.channel.permissions_for(msg.guild.me).manage_messages:
                async with self.bot.cursor() as cur:
                    await cur.execute(f"delete from global_chat where guild_id = {msg.guild.id};")
                del self.cache[msg.guild.id]
                return await msg.channel.send(
                    "Disabled global chat due to missing manage_message permissions"
                )

            e = discord.Embed()
            e.set_thumbnail(url=msg.author.avatar_url)

            # Edit & combine their last msg
            if msg.author.id == self.last_id:
                em = self.msg_cache[0].embeds[0]
                if not isinstance(e.image.url, str):
                    if msg.attachments:
                        em.set_image(url=msg.attachments[0].url)
                    if em.description:
                        em.description += f"\n{msg.content[:256]}"
                    elif msg.content:
                        em.description = f"{msg.content[:256]}"
                    if len(em.description) >= 1048:
                        return
                    self._queue.append([em, True, msg])
                    return

            # Send a new msg
            if msg.attachments:
                e.set_image(url=msg.attachments[0].url)
            e.set_author(name=str(msg.author), icon_url=msg.author.avatar_url)
            e.set_thumbnail(url=msg.guild.icon_url)
            e.description = msg.content[:512]
            self._queue.append([e, False, msg])
            if msg.attachments:
                self.last_id = None
            else:
                self.last_id = msg.author.id

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if msg.channel.id == 787940379168210944:
            for chunk in list(self.msg_chunks):
                if msg.id in chunk.values():
                    for channel_id, msg_id in chunk.items():
                        channel = self.bot.get_channel(channel_id)
                        with suppress(NotFound, Forbidden):
                            m = await channel.fetch_message(msg_id)
                            await m.delete()
                    return


def setup(bot):
    bot.add_cog(GlobalChatRewrite(bot))
