"""
cogs.misc.nsfw
~~~~~~~~~~~~~~~

A cog for basic nsfw commands

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from random import randint, choice

import aiohttp
import discord
from discord.ext import commands

from botutils import colors


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get(self, filename):
        async with self.bot.utils.open(f"./data/images/urls/{filename}", "r") as f:
            return choice([c for c in await f.readlines() if len(c) > 5])

    @commands.command(name="gel")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def _gel(self, ctx, *, tag):
        blacklist = ["loli", "shota"]
        send_all = False
        if "all " in tag:
            if ctx.author.name == "Luck":
                send_all = True
                tag = tag.replace("all ", "")
        tag = tag.replace(" ", "_")
        for x in blacklist:
            if x in tag:
                return await ctx.send("that tag is blacklisted")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={tag}&json=1&limit=100&pid={randint(1, 3)}"
                async with session.get(url) as resp:
                    dat = await resp.json()
            if send_all:
                try:
                    for i in range(len(dat)):
                        e = discord.Embed(color=colors.random())
                        e.set_image(url=dat[i]["file_url"])
                        await ctx.send(embed=e)
                except Exception as e:
                    await ctx.send(e)
                return
            e = discord.Embed(color=colors.random())
            e.set_image(url=dat[randint(1, len(dat))]["file_url"])
            await ctx.send(embed=e)
        except:
            await ctx.send("error")

    @commands.command(name="trap")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def trap(self, ctx):
        e = discord.Embed(color=colors.purple)
        e.set_image(url=await self.get("traps.txt"))
        await ctx.send(embed=e)

    @commands.command(name="neko")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def neko(self, ctx):
        e = discord.Embed(color=colors.purple)
        e.set_image(url=await self.get("nekos.txt"))
        await ctx.send(embed=e)

    @commands.command(name="yaoi")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def _yaoi(self, ctx):
        e = discord.Embed(color=colors.purple)
        e.set_image(url=await self.get("yaoi.txt"))
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(NSFW(bot))
