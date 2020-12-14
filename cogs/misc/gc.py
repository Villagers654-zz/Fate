
from contextlib import suppress
import asyncio

from discord.ext import commands, tasks
from discord.errors import NotFound, Forbidden
import discord


class GlobalChatRewrite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.message_cache = []
        self.cache_task = self.bot.loop.create_task(self.cache_channels())
        self.handle_queue.start()
        self.queue = None

    def cog_unload(self):
        self.handle_queue.cancel()
        if not self.cache_task.done():
            self.cache_task.cancel()

    @property
    def messages(self):
        self.message_cache = self.message_cache[-16:]
        return self.message_cache

    @tasks.loop(seconds=3)
    async def handle_queue(self):
        if self.queue:
            messages, e = self.queue
            self.queue = None
            for guild_id, message in list(self.cache.items()):
                with suppress(NotFound, Forbidden):
                    await message.edit(content=messages, embed=e)

    async def cache_channels(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        while True:
            if not self.bot.pool:
                await asyncio.sleep(1)
                continue
            break
        async with self.bot.cursor() as cur:
            await cur.execute(f"select guild_id, channel_id, message_id from global_chat;")
            ids = await cur.fetchall()
        for guild_id, channel_id, message_id in ids:
            channel = self.bot.get_channel(channel_id)
            try:
                msg = await channel.fetch_message(message_id)
                self.cache[guild_id] = msg
            except (AttributeError, Forbidden, NotFound):
                async with self.bot.cursor() as cur:
                    await cur.execute(
                        f"delete from global_chat "
                        f"where guild_id = {guild_id};"
                    )
                if channel:
                    with suppress(Forbidden):
                        await channel.send("Disabled global chat due to missing permissions")

    @commands.group(name="gcr")
    async def _gc(self, ctx):
        pass

    @_gc.command(name="enable")
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

        self.cache[ctx.guild.id] = msg
        await ctx.send("Enabled global chat")

    @commands.Cog.listener()
    async def on_message(self, msg):
        active = [m.channel.id for m in list(self.cache.values())]
        if not msg.author.bot and msg.channel.id in active:
            if any(msg.content == m.content for m in self.messages):
                return
            self.message_cache.append(msg)
            messages = ""
            last = None
            e = discord.Embed()
            e.set_thumbnail(url=msg.author.avatar_url)
            for i, message in enumerate(self.messages):
                if message.author.id == last:
                    messages += f"\n{message.content[:100]}"
                    e.set_field_at(
                        index=len(e.fields) - 1,
                        name=str(message.author),
                        value=e.fields[len(e.fields) - 1].value + f"\n{message.content[:100]}", inline=False
                    )
                else:
                    messages += f"\n\n<:{message.author.display_name}:> {message.content[:100]}"
                    e.add_field(name=(str(message.author)), value=f"{message.content[:100]}", inline=False)
                last = message.author.id
            messages = f"```css{messages.replace('`', '')}```"
            self.queue = messages, e
            await asyncio.sleep(1)
            with suppress(NotFound, Forbidden):
                await msg.delete()


def setup(bot):
    bot.add_cog(GlobalChatRewrite(bot))
