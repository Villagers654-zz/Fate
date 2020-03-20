from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import random
import json
import time
import os


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookies = {}
        self.sent = {}
        self.received = {}
        self.eaten = {}
        self.cd = {}
        if isfile("./data/userdata/cookies.json"):
            with open("./data/userdata/cookies.json", "r") as infile:
                dat = json.load(infile)
                if (
                    "cookies" in dat
                    and "sent" in dat
                    and "received" in dat
                    and "eaten" in dat
                ):
                    self.cookies = dat["cookies"]
                    self.sent = dat["sent"]
                    self.received = dat["received"]
                    self.eaten = dat["eaten"]
                    self.cd = dat["cd"]

    def save(self):
        with open("./data/userdata/cookies.json", "w") as outfile:
            json.dump(
                {
                    "cookies": self.cookies,
                    "sent": self.sent,
                    "received": self.received,
                    "eaten": self.eaten,
                    "cd": self.cd,
                },
                outfile,
                ensure_ascii=False,
            )

    def setup(self, id):
        self.cookies[id] = 0
        self.sent[id] = 0
        self.received[id] = 0
        self.eaten[id] = 0
        self.cd[id] = 0
        self.save()

    @commands.command(name="cookie")
    async def _cookie(self, ctx, user: discord.Member = None):
        e = discord.Embed(color=colors.fate())
        e.set_footer(text=f"Powered by Cookie Mix")
        author_id = str(ctx.author.id)
        if author_id not in self.cookies:
            self.setup(author_id)
        if user:
            user_id = str(user.id)
            if user.bot is True:
                return await ctx.send("You cannot give cookies to bots")
            if user_id not in self.cookies:
                self.setup(user_id)
            self.sent[author_id] += 1
            self.received[user_id] += 1
            self.cookies[user_id] += 1
            e.set_author(
                name=f"| 📤 {self.sent[author_id]} | 📥 {self.received[author_id]} | 🍪 {self.cookies[author_id]}",
                icon_url=ctx.author.avatar_url,
            )
            e.description = (
                f"{ctx.author.display_name} has given {user.display_name} a cookie"
            )
            self.cd[author_id] = time.time() + 3600
            await ctx.send(embed=e)
            return self.save()
        if self.cookies[author_id] == 0:
            return await ctx.send("You have no cookies to eat :(")
        self.cookies[author_id] = self.cookies[author_id] - 1
        self.eaten[author_id] += 1
        e.set_author(
            name=f"| 📤 {self.sent[author_id]} | 📥 {self.received[author_id]} | 🍪 {self.cookies[author_id]}",
            icon_url=ctx.author.avatar_url,
        )
        actions = [
            "chews on one of his/her cookies",
            "nibbles on one of his/her cookies",
            "eats a cookie whole",
        ]
        e.description = f"{ctx.author.name} {random.choice(actions)}"
        path = (
            os.getcwd()
            + "/data/images/reactions/cookie/"
            + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/cookie/"))
        )
        e.set_image(url="attachment://" + os.path.basename(path))
        await ctx.send(
            file=discord.File(path, filename=os.path.basename(path)), embed=e
        )
        self.save()

    @commands.command(name="cookies")
    async def _cookies(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        user_id = str(user.id)
        if user_id not in self.cookies:
            self.setup(user_id)
        e = discord.Embed(color=colors.fate())
        e.set_author(
            name=f"| 📤 {self.sent[user_id]} | 📥 {self.received[user_id]} | 🍪 {self.cookies[user_id]}",
            icon_url=user.avatar_url,
        )
        e.set_footer(text="Powered by Cookie Mix")
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Cookies(bot))
