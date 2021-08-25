"""
cogs.fun.cookies
~~~~~~~~~~~~~~~~~

A wholesome cog to give, receive, and eat virtual cookies

:copyright: (C) 2018-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import random
import os
from discord.ext import commands
import discord
from botutils import colors


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dat = bot.utils.cache("cookies")

    def setup(self, user_id):
        self.dat[user_id] = {
            "cookies": 0,
            "sent": 0,
            "received": 0,
            "eaten": 0
        }

    @commands.command(name="cookie")
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def cookie(self, ctx, user: discord.Member = None):
        e = discord.Embed(color=colors.fate)
        e.set_footer(text=f"Powered by Cookie Mix")
        author_id = ctx.author.id
        if author_id not in self.dat:
            self.setup(author_id)

        # Giving a cookie
        if user:
            user_id = user.id
            if user.bot:
                return await ctx.send("You cannot give cookies to bots")
            if user_id not in self.dat:
                self.setup(user_id)
            self.dat[author_id]["sent"] += 1
            self.dat[user_id]["received"] += 1
            self.dat[user_id]["cookies"] += 1
            dat = self.dat[user_id]  # type: dict
            e.set_author(
                name=f"| 📤 {dat['sent']} | 📥 {dat['received']} | 🍪 {dat['cookies']}",
                icon_url=ctx.author.display_avatar.url,
            )
            e.description = f"**{ctx.author.display_name}** has given **{user.display_name}** a cookie"
            await ctx.send(embed=e)
            return await self.dat.flush()

        # Eating a cookie
        if self.dat[author_id]["cookies"] == 0:
            return await ctx.send("You have no cookies to eat :(")
        self.dat[author_id]["cookies"] -= 1
        self.dat[author_id]["eaten"] += 1
        dat = self.dat[author_id]  # type: dict
        e.set_author(
            name=f"| 📤 {dat['sent']} | 📥 {dat['received']} | 🍪 {dat['cookies']}",
            icon_url=ctx.author.display_avatar.url,
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
        await self.dat.flush()

    @commands.command(name="cookies")
    async def _cookies(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        user_id = user.id
        if user_id not in self.dat:
            return await ctx.send("You have no cookie data")
        e = discord.Embed(color=colors.fate)
        dat = self.dat[user_id]  # type: dict
        e.set_author(
            name=f"| 📤 {dat['sent']} | 📥 {dat['received']} | 🍪 {dat['cookies']}",
            icon_url=ctx.author.display_avatar.url,
        )
        e.set_footer(text="Powered by Cookie Mix")
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Cookies(bot), override=True)
