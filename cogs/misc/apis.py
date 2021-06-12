import requests
import random
import json
import aiohttp
from discord.ext import commands
import discord
from botutils import colors


class APIS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tenor")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(
        embed_links=True, attach_files=True, manage_messages=True
    )
    async def tenor(self, ctx, *, search):
        apikey = "LIWIXISVM3A7"
        lmt = 50
        r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
        if r.status_code == 200:
            anon_id = json.loads(r.content)["anon_id"]
        else:
            anon_id = ""
        r = requests.get(
            "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s"
            % (search, apikey, lmt, anon_id)
        )
        if r.status_code == 200:
            try:
                dat = json.loads(r.content)
                e = discord.Embed(color=colors.random())
                e.set_image(
                    url=dat["results"][random.randint(0, len(dat["results"]) - 1)][
                        "media"
                    ][0]["gif"]["url"]
                )
                e.set_footer(text="Powered by Tenor")
                await ctx.send(embed=e)
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(e)
        else:
            await ctx.send("error")

    @commands.command(name="tenor-beta")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(
        embed_links=True, attach_files=True, manage_messages=True
    )
    async def _tenor(self, ctx, *, search):
        apikey = "LIWIXISVM3A7"
        lmt = 50
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.tenor.com/v1/anonid?key=%s" % apikey
            ) as r:
                if r.status == 200:
                    anon_id = json.loads(await r.content.read())["anon_id"]
                else:
                    anon_id = ""
                async with aiohttp.ClientSession() as session_2:
                    async with session_2.get(
                        "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s"
                        % (search, apikey, lmt, anon_id)
                    ) as rr:
                        if rr.status == 200:
                            try:
                                dat = json.loads(await rr.content.read())
                                e = discord.Embed(color=colors.random())
                                e.set_image(
                                    url=dat["results"][
                                        random.randint(0, len(dat["results"]) - 1)
                                    ]["media"][0]["gif"]["url"]
                                )
                                e.set_footer(text="Powered by Tenor")
                                await ctx.send(embed=e)
                                await ctx.message.delete()
                            except Exception as e:
                                await ctx.send(e)
                        else:
                            await ctx.send("error")

    # @commands.command(name="reddit")
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # @commands.bot_has_permissions(embed_links=True, attach_files=True)
    # async def reddit(self, ctx, search):
    #     try:
    #         dat = auth.Reddit()
    #         reddit = Reddit(
    #             client_id=dat.client_id,
    #             client_secret=dat.client_secret,
    #             user_agent=dat.user_agent,
    #         )
    #     except Exception as e:
    #         return await ctx.send(f"Error With Reddit Credentials\n{e}")
#
    #     reddit_posts = []  # type: Reddit.submission
    #     try:
    #         subreddit = reddit.subreddit(search)
    #         if subreddit.over18 and not ctx.channel.is_nsfw():
    #             return await ctx.send(
    #                 f"Channel '{ctx.channel.name}' needs to be NSFW to view this subreddit"
    #             )
    #         for submission in subreddit.hot(limit=100):
    #             exts = [".png", ".jpg", ".jpeg", ".gif"]
    #             if submission.title and all(ext not in submission.url for ext in exts):
    #                 reddit_posts.append(submission)
    #     except discord.DiscordException:
    #         return await ctx.send(
    #             f"Error Searching r/{search}\nMake sure it's public and exists"
    #         )
#
    #     post = random.choice(reddit_posts)
    #     e = discord.Embed(color=colors.red())
    #     e.set_author(name=post.title, icon_url=post.author.icon_img)
    #     e.set_image(url=post.url)
    #     e.set_footer(
    #         text=f"{post.author.name} | 👍 {post.score} | 💬 {post.num_comments}"
    #     )
    #     await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(APIS(bot))
