import asyncio
import traceback
from time import time
from datetime import datetime

from discord.ext import commands, tasks
import discord
import asyncpraw

from utils import colors, auth


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = []
        if "reddit" not in self.bot.tasks:
            self.bot.tasks["reddit"] = {}
        for guild_id, task in list(self.bot.tasks["reddit"].items()):
            task.cancel()
            del self.bot.tasks["reddit"][guild_id]

        creds = auth.Reddit()
        self.client = asyncpraw.Reddit(
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            user_agent=creds.user_agent,
        )

        self.ensure_subscriptions_task.start()

    def cog_unload(self):
        self.ensure_subscriptions_task.cancel()
        for guild_id, task in list(self.bot.tasks["reddit"].items()):
            task.cancel()

    @tasks.loop(minutes=1)
    async def ensure_subscriptions_task(self):
        await asyncio.sleep(0.21)
        if not self.bot.is_ready() or not self.bot.pool:
            return
        async with self.bot.cursor() as cur:
            if "reddit" not in self.bot.tasks:
                self.bot.tasks["reddit"] = {}
            if not self.enabled:
                async with self.bot.cursor() as cur:
                    await cur.execute("select guild_id from reddit;")
                    results = await cur.fetchall()
                self.enabled = [result[0] for result in results]
            lmt = time() - 60 * 60 * 24 * 14
            await cur.execute(f"delete from reddit_cache where sent_at < {lmt};")
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

        channel_id, subreddit_name, new_posts, text, images, rate = results[0]
        exts = ["png", "jpg", "jpeg", "gif"]

        cache = []
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select post_id from reddit_cache "
                f"where guild_id = {guild_id};"
            )
            results = await cur.fetchall()
        for result in results:
            cache.append(result[0])

        channel = self.bot.get_channel(channel_id)
        get_description = lambda post: post.selftext if post.selftext else post.title

        subreddit_name = subreddit_name.replace(" ", "")
        reddit = await self.client.subreddit(subreddit_name.replace(",", "+"))
        subreddit = reddit.new if new_posts else reddit.hot
        search_limit = 25
        if new_posts:
            search_limit = 5

        reduced_time = None
        history = await channel.history(limit=1).flatten()
        if history and history[0].author.id == self.bot.user.id:
            time_since = (datetime.utcnow() - history[0].created_at).total_seconds()
            if rate > time_since:
                reduced_time = round(rate - time_since)

        while True:
            await asyncio.sleep(0.21)
            posts = []
            try:
                async for post in subreddit(limit=search_limit):
                    if post.stickied or post.id in cache:
                        continue
                    has_images = any(post.url.endswith(ext) for ext in exts)
                    if images and any(post.url.endswith(ext) for ext in exts):
                        posts.append(post)
                    elif text and not images and not has_images:
                        posts.append(post)
                    elif text and (post.title or post.selftext):
                        posts.append(post)
                    if len(posts) == 50:
                        break

                if not posts:
                    if search_limit == 250:
                        await channel.send(f"No results after searching r/{subreddit_name}")
                        await asyncio.sleep(rate)
                        continue
                    if new_posts:
                        await asyncio.sleep(300)  # Wait 5 minutes for new posts
                        continue
                    search_limit += 25
                    continue

                for post in posts:
                    url = f"https://reddit.com{post.permalink}"
                    sleep_time = rate
                    if reduced_time:
                        sleep_time = reduced_time
                        await channel.send(f"Resuming a timer and sleeping for {sleep_time}")
                        reduced_time = None
                    await asyncio.sleep(sleep_time)
                    await post.author.load()
                    await post.subreddit.load()

                    e = discord.Embed(color=colors.red())
                    icon_img = self.bot.user.avatar_url
                    if hasattr(post.author, "icon_img"):
                        icon_img = post.author.icon_img
                    e.set_author(name=f"u/{post.author.name}", icon_url=icon_img, url=post.url)

                    # Set to use text
                    if text and (post.title or post.selftext):
                        enum = enumerate(self.bot.utils.split(get_description(post), 914))
                        for i, chunk in enum:
                            if i == 0:
                                e.description = chunk
                            elif i == 1:
                                e.description += chunk
                            elif i == 5:
                                e.add_field(
                                    name="Reached the character limit",
                                    value=f"Click the [hyperlink]({url}) to view more",
                                    inline=False
                                )
                                break
                            else:
                                e.add_field(
                                    name="Additional Text",
                                    value=chunk,
                                    inline=False
                                )

                    # Set to use images
                    if images and "." in post.url.split("/")[post.url.count("/")]:
                        if any(post.url.endswith(ext) for ext in exts):
                            e.set_image(url=post.url)
                        else:
                            e.description += f"\n[click to view attachment]({post.url})"

                    e.set_footer(
                        text=f"r/{post.subreddit.display_name} | "
                             f"⬆ {post.score} | "
                             f"👍 {str(post.upvote_ratio).lstrip('0.')}% | "
                             f"💬 {post.num_comments}"
                    )
                    await channel.send(embed=e)
                    async with self.bot.cursor() as cur:
                        await cur.execute(
                            f"insert into reddit_cache values ({guild_id}, '{post.id}', {time()});"
                        )
                    cache.append(post.id)
            except asyncio.CancelledError:
                return
            except:
                await channel.send(traceback.format_exc())
                await asyncio.sleep(1.21)
                continue

    @commands.group(name="reddit", aliases=["reddit-api"])
    async def _reddit(self, ctx):
        if not ctx.invoked_subcommand:
            args = ctx.message.content.split()
            if len(args) > 1:
                subreddit = args[1:][0].lstrip("r/")
                reddit = await self.client.subreddit(subreddit)
                post = await reddit.random()
                await post.author.load()

                e = discord.Embed(color=colors.red())
                icon_img = self.bot.user.avatar_url
                if hasattr(post.author, "icon_img"):
                    icon_img = post.author.icon_img
                e.set_author(name=f"u/{post.author.name}", icon_url=icon_img, url=post.url)

                # Set to use text
                if post.title or post.selftext:
                    enum = enumerate(self.bot.utils.split(
                        post.selftext if post.selftext else post.title, 914
                    ))
                    for i, chunk in enum:
                        if i == 0:
                            e.description = chunk
                        elif i == 1:
                            e.description += chunk
                        elif i == 5:
                            e.add_field(
                                name="Reached the character limit",
                                value=f"Click the [hyperlink]({post.url}) to view more",
                                inline=False
                            )
                            break
                        else:
                            e.add_field(
                                name="Additional Text",
                                value=chunk,
                                inline=False
                            )

                # Set to use images
                if "." in post.url.split("/")[post.url.count("/")]:
                    if any(post.url.endswith(ext) for ext in ["png", "jpg", "gif", "jpeg"]):
                        e.set_image(url=post.url)
                    else:
                        e.description += f"\n[click to view attachment]({post.url})"

                e.set_footer(
                    text=f"r/{post.subreddit.display_name} | "
                         f"⬆ {post.score} | "
                         f"👍 {str(post.upvote_ratio).lstrip('0.')}% | "
                         f"💬 {post.num_comments}"
                )
                return await ctx.send(embed=e)

            e = discord.Embed(color=colors.red())
            e.set_author(name="Reddit", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(
                url="https://cdn3.iconfinder.com/data/icons/2018-social-media-logotypes/1000/2018_social_media_popular_app_logo_reddit-512.png"
            )
            e.description = "Get a random post from a subreddit, or subscribe to a " \
                            "designated TextChannel at a set interval"
            p = self.bot.utils.get_prefix(ctx)  # type: str
            e.add_field(
                name="◈ Usage",
                value=f"**{p}reddit r/example**\n"
                      f"`get a random post`\n"
                      f"**{p}reddit subscribe r/example**\n"
                      f"`begin setup`\n"
                      f"**{p}reddit unsubscribe**\n"
                      f"`disables the subscription`"
            )
            await ctx.send(embed=e)

    @_reddit.command(name="subscribe")
    @commands.has_permissions(administrator=True)
    async def _subscribe(self, ctx, *, subreddit):
        subreddit = subreddit.lstrip("r/")
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
        if rate < 60 * 5 and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send("That rates too fast\nRedo the command")
        if rate > 60 * 60 * 24:
            return await ctx.send("That rates too... long.....for.........me.....OwO blushes")
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
        self.enabled.append(guild_id)
        if ctx.guild.id in self.bot.tasks["reddit"]:
            self.bot.tasks["reddit"][ctx.guild.id].cancel()
        self.bot.tasks["reddit"][ctx.guild.id] = self.bot.loop.create_task(
            self.handle_subscription(guild_id)
        )

        msg = f"Set up the subreddit subscription. You'll now receive " \
              f"a new post every {self.bot.utils.get_time(rate)}"
        if new:
            msg += ". Allow the bot a bit of time to catch up on the most recent posts"
        await ctx.send(msg)

    @_reddit.command(name="unsubscribe", aliases=["disable"])
    @commands.has_permissions(administrator=True)
    async def unsubscribe(self, ctx):
        if ctx.guild.id not in self.enabled:
            return await ctx.send("This server currently isn't subscribed to a subreddit")
        async with self.bot.cursor() as cur:
            await cur.execute(f"delete from reddit where guild_id = {ctx.guild.id};")
        self.enabled.remove(ctx.guild.id)
        if ctx.guild.id in self.bot.tasks["reddit"]:
            self.bot.tasks["reddit"][ctx.guild.id].cancel()
            del self.bot.tasks["reddit"][ctx.guild.id]
        await ctx.send("Disabled the reddit subscription")


def setup(bot):
    bot.add_cog(Reddit(bot))
