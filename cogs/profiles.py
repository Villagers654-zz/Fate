from discord.ext import commands
from os.path import isfile
import discord
import json
import time

class Profiles:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = {}
        self.info = {}
        self.created = {}
        if isfile("./data/profiles.json"):
            with open("./data/profiles.json", "r") as infile:
                dat = json.load(infile)
                if "name" in dat and "info" in dat and "created" in dat:
                    self.name = dat["name"]
                    self.info = dat["info"]
                    self.created = dat["created"]

    @commands.command()
    async def set(self, ctx, item, *, arg):
        if item == "name":
            self.name[str(ctx.author.id)] = arg
            await ctx.send('success')
            with open("./data/profiles.json", "w") as outfile:
                json.dump({"info": self.info, "name": self.name, "created": self.created}, outfile, ensure_ascii=False)
        if item == "info":
            self.info[str(ctx.author.id)] = arg
            await ctx.send('success')
            with open("./data/profiles.json", "w") as outfile:
                json.dump({"info": self.info, "name": self.name, "created": self.created}, outfile, ensure_ascii=False)

    @commands.command()
    async def profile(self, ctx):
        fmt = "%m/%d/%Y"
        created = time
        e = discord.Embed(color=0x9eafe3)
        e.set_thumbnail(url=ctx.author.avatar_url)
        if str(ctx.author.id) not in self.name:
            self.name[str(ctx.author.id)] = ctx.author.name
            with open("./data/profiles.json", "w") as outfile:
                json.dump({"info": self.info, "name": self.name, "created": self.created}, outfile, ensure_ascii=False)
        e.set_author(name=self.name[str(ctx.author.id)], icon_url=ctx.author.avatar_url)
        if str(ctx.author.id) not in self.info:
            self.info[str(ctx.author.id)] = 'nothing to see here, try using .set info'
            with open("./data/profiles.json", "w") as outfile:
                json.dump({"info": self.info, "name": self.name, "created": self.created}, outfile, ensure_ascii=False)
        e.description = self.info[str(ctx.author.id)]
        if str(ctx.author.id) not in self.created:
            self.created[str(ctx.author.id)] = created.strftime(fmt)
            with open("./data/profiles.json", "w") as outfile:
                json.dump({"info": self.info, "name": self.name, "created": self.created}, outfile, ensure_ascii=False)
        e.set_footer(text=f'Profile Created: {self.created[str(ctx.author.id)]}')
        await ctx.send(embed=e)

def setup(bot: commands.Bot):
    bot.add_cog(Profiles(bot))
