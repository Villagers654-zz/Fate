from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json
import os

class Notepad:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.notes = {}
        self.timestamp = {}
        if isfile("./data/notes.json"):
            with open("./data/notes.json", "r") as infile:
                dat = json.load(infile)
                if "notes" in dat and "timestamp" in dat:
                    self.notes = dat["notes"]
                    self.timestamp = dat["timestamp"]

    @commands.command()
    async def note(self, ctx, *, arg = ""):
        async with ctx.typing():
            if len(arg) > 0:
                self.notes[str(ctx.author.id)] = arg
                date = os.popen('date')
                timestamp = date.read()
                self.timestamp[str(ctx.author.id)] = timestamp
                path = os.getcwd() + "/data/images/reactions/notes/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/notes/"))
                e = discord.Embed(color=0xFFC923)
                e.set_author(name='Noted..', icon_url=ctx.author.avatar_url)
                e.set_image(url="attachment://" + os.path.basename(path))
                await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e, delete_after=10)
                await asyncio.sleep(10)
                await ctx.message.delete()
                with open("./data/notes.json", "w") as outfile:
                    json.dump({"notes": self.notes, "timestamp": self.timestamp}, outfile, ensure_ascii=False)
            else:
                if str(ctx.author.id) in self.notes:
                    e = discord.Embed(color=0xFFC923)
                    e.title = "~~===🥂🍸🍷Note🍷🍸🥂===~~"
                    e.set_thumbnail(url=ctx.author.avatar_url)
                    e.description = self.notes[str(ctx.author.id)]
                    e.set_footer(text=self.timestamp[str(ctx.author.id)])
                    await ctx.send(embed=e)
                else:
                    await ctx.send("no data")

def setup(bot: commands.Bot):
    bot.add_cog(Notepad(bot))
