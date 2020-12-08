import asyncio

from discord.ext import commands, tasks
import discord
import praw
import prawcore

from utils import colors, auth


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = []
        self.ensure_subscriptions_task.start()

    def cog_unload(self):
        self.ensure_subscriptions_task.cancel()

    @tasks.loop(minutes=1)
    async def ensure_subscriptions_task(self):
        await asyncio.sleep(0.21)
        if not self.bot.is_ready() or not self.bot.pool:
            return
        if "reddit" not in self.bot.tasks:
            self.bot.tasks["reddit"] = {}
        if not self.enabled:
            async with self.bot.cursor() as cur:
                await cur.execute("select guild_id from reddit;")
                results = await cur.fetchall()
            self.enabled = [result[0] for result in results]
        for guild_id in self.enabled:
            if guild_id not in self.bot.tasks["reddit"] or self.bot.tasks["reddit"][guild_id].done():
                self.bot.tasks["reddit"][guild_id] = self.bot.loop.create_task(
                    self.handle_subscription(guild_id)
                )
        for guild_id, task in self.bot.tasks["reddit"].items():
            if guild_id not in self.enabled:
                task.cancel()
        await asyncio.sleep(60)

    async def handle_subscription(self, guild_id):
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select channel_id, subreddit, new_posts, text, images, rate "
                f"from reddit "
                f"where guild_id = {guild_id} "
                f"limit 1;"
            )
            results = await cur.fetchall()
        if not results:
            return

        channel_id, subreddit, new_posts, text, images, rate = results[0]

        def collect() -> list:
            creds = auth.Reddit()
            client = praw.Reddit(
                client_id=creds.client_id,
                client_secret=creds.client_secret,
                user_agent=creds.user_agent,
            )
            reddit = client.subreddit(subreddit)
            if new_posts:
                posts = reddit.new(limit=50)
            else:
                posts = reddit.hot(limit=50)
            exts = ["png", "jpg", "jpeg", "gif"]
            passing_posts = []
            if images:
                for post in posts:
                    if any(ext in post.url for ext in exts):
                        passing_posts.append(post)
            if text:
                for post in posts:
                    if not any(ext in post.url for ext in exts):
                        passing_posts.append(post)
            return list(set(passing_posts))

        channel = self.bot.get_channel(channel_id)

        while True:
            try:
                for post in await self.bot.loop.run_in_executor(None, collect):
                    await asyncio.sleep(rate)
                    e = discord.Embed(color=colors.red())
                    e.title = post.title
                    e.set_footer(text=f"{subreddit}")
                    e.set_image(url=post.url)
                    await channel.send(embed=e)
            except prawcore.exceptions.BadRequest:
                await asyncio.sleep(1.21)
                continue

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

        await ctx.send(
            f"Set up the subreddit subscription. You'll now receive "
            f"a new post every {self.bot.utils.get_time(rate)}"
        )

    @_reddit.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        if ctx.guild.id not in self.enabled:
            return await ctx.send("This server currently isn't subscribed to a subreddit")
        async with self.bot.cursor() as cur:
            await cur.execute(f"delete from reddit where guild_id = {ctx.guild.id};")
        self.enabled.remove(ctx.guild.id)
        await ctx.send("Disabled the reddit subscription")


def setup(bot):
    bot.add_cog(Reddit(bot))
