from time import monotonic
import asyncio

from discord.ext import commands, tasks
import discord
import aiomysql

from utils import colors


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {}
        self.is_ready = False
        self.bot.loop.create_task(self._load_from_sql())
        self.ensure_subscriptions_task.start()

    async def _load_from_sql(self):
        """Cache configs from mysql server"""
        while not self.bot.pool and not self.bot.is_ready():
            await asyncio.sleep(0.21)
        async with self.bot.pool.acquire() as conn:
            before = monotonic()
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "select guild_id, channel_id, subreddit, new_posts, images, text, rate from reddit;"
                )
            results = await cur.fetchall()
            for entry in results:
                await asyncio.sleep(0)
                guild_id = entry.pop("guild_id")
                self.config[guild_id] = entry
            self.is_ready = True
            ping = str(round((monotonic() - before) * 1000)) + "ms"
            self.bot.log.info(f"Cached reddit config. Operation took {ping}")

    @tasks.loop(minutes=1)
    async def ensure_subscriptions_task(self):
        if not self.is_ready:
            return None
        if "reddit" not in self.bot.tasks:
            self.bot.tasks["reddit"] = {}
        for guild_id, data in list(self.config.items()):
            if guild_id not in self.bot.tasks["reddit"] or self.bot.tasks["reddit"][guild_id].done():
                self.bot.tasks["reddit"][guild_id] = self.bot.loop.create_task(
                    self.handle_subscription(guild_id)
                )

    async def handle_subscription(self, guild_id):
        pass

    @commands.group(name="reddit-api")
    async def _reddit(self, ctx):
        if not ctx.invoked_subcommand:
            pass
        elif not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Reddit", icon_url=ctx.author.avatar_url)
            e.description = "Pulls from a subreddits posts and can subscribe to a " \
                            "designated TextChannel. Can be sorted by top or new and can collect " \
                            "images only, text only, or title only depending on preference"

    @_reddit.command(name="subscribe")
    @commands.has_permissions(administrator=True)
    async def _subscribe(self, ctx, *, subreddit):
        await ctx.send("Do you want the bot to send Hot, or New posts")
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            if "hot" not in msg.content.lower() and "new" not in msg.content.lower():
                return await ctx.send("That wasn't a valid response")
            if "hot" in msg.content.lower():
                new = False
            else:
                new = True

        await ctx.send("Should I send Images, Text, or Both")
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            content = msg.content.lower()
            if "images" not in content and "text" not in content and "both" not in content:
                return await ctx.send("Invalid response")
            images = text = False
            if "images" in msg.content.lower():
                images = True
            elif "text" in msg.content.lower():
                text = True
            elif "both" in msg.content.lower():
                images = text = True

        await ctx.send(
            "At what rate (in seconds) should I send a reddit post. "
            "You can pick between 5 minutes to 24 hours"
        )
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            if not msg.content.isdigit():
                return await ctx.send("Bruh.. a number please\nRedo the command")
            rate = int(msg.content)
        if rate < 60 * 5:
            return await ctx.send("That rates too fast\nRedo the command")
        if rate > 60 * 60 * 24:
            return await ctx.send("That rates too...... long.......for............me.....owo blushes")
            # i looked away for literally 20 seconds. and you do this
            # without regerts

        guild_id = ctx.guild.id
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into reddit "
                f"values ({guild_id}, {ctx.channel.id}, '{subreddit}', {new}, {text}, {images}, {rate}) "
                
                f"on duplicate key "
                f"update "
                f"guild_id = {guild_id}, "
                f"channel_id = {ctx.channel.id}, "
                f"subreddit = '{subreddit}', "
                f"new_posts = {new}, "
                f"text = {text}, "
                f"images = {images}, "
                f"rate = {rate};"
            )

        # Cache the current config
        self.config[guild_id] = {
            "channel_id": ctx.channel.id,
            "subreddit": subreddit,
            "new_posts": new,
            "text": text,
            "images": images,
            "rate": rate
        }

        await ctx.send(
            f"Set up the subreddit subscription. You'll now receive "
            f"a new post every {self.bot.utils.get_time(rate)}"
        )


def setup(bot):
    bot.add_cog(Reddit(bot))
