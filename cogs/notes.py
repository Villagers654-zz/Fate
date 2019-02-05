from discord.ext import commands
from os.path import isfile
import datetime
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
        if isfile("./data/userdata/notes.json"):
            with open("./data/userdata/notes.json", "r") as infile:
                dat = json.load(infile)
                if "notes" in dat and "timestamp" in dat:
                    self.notes = dat["notes"]
                    self.timestamp = dat["timestamp"]

    def save(self):
        with open("./data/userdata/notes.json", "w") as outfile:
            return json.dump({"notes": self.notes, "timestamp": self.timestamp}, outfile, ensure_ascii=False)

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def note(self, ctx, *, arg: commands.clean_content = ""):
        author_id = str(ctx.author.id)
        if len(arg) > 400:
            return await ctx.send("Each note cannot be larger than 400 characters")
        if len(arg) > 0:
            async with ctx.typing():
                if author_id not in self.notes:
                    self.notes[author_id] = []
                self.notes[author_id].append(arg)
                if len(self.notes[author_id]) > 5:
                    del self.notes[author_id][0]
                if author_id not in self.timestamp:
                    self.timestamp[author_id] = []
                self.timestamp[author_id].append(datetime.datetime.now().strftime("%m-%d-%Y %I:%M%p"))
                if len(self.timestamp[author_id]) > 5:
                    del self.timestamp[author_id][0]
                self.save()
                path = os.getcwd() + "/data/images/reactions/notes/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/notes/"))
                e = discord.Embed(color=0xFFC923)
                e.set_author(name='Noted..', icon_url=ctx.author.avatar_url)
                e.set_image(url="attachment://" + os.path.basename(path))
                await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e, delete_after=10)
            await asyncio.sleep(10)
            await ctx.message.delete()
        else:
            if str(ctx.author.id) in self.notes:
                async with ctx.typing():
                    e = discord.Embed(color=0xFFC923)
                    e.title = "~~===🥂🍸🍷Note🍷🍸🥂===~~"
                    e.set_thumbnail(url=ctx.author.avatar_url)
                    e.description = self.notes[author_id][-1]
                    e.set_footer(text=self.timestamp[author_id][-1])
                    await ctx.send(embed=e)
            else:
                await ctx.send("no data")

    @commands.command(name="notes")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def _notes(self, ctx):
        author_id = str(ctx.author.id)
        if author_id in self.notes:
            e = discord.Embed(color=0xFFC923)
            e.title = "~~===🥂🍸🍷Notes🍷🍸🥂===~~"
            e.set_thumbnail(url=ctx.author.avatar_url)
            e.description = f"**You're last {len(self.notes[author_id])} note(s):**"
            note = len(self.notes[author_id]) - 1
            position = 1
            for i in self.notes[author_id]:
                e.description += f"\n{position}. {self.notes[author_id][note].replace('`', '')}\n`{self.timestamp[author_id][note]}`\n"
                note -= 1
                position += 1
            await ctx.send(embed=e)
        else:
          await ctx.send("no data")

def setup(bot: commands.Bot):
    bot.add_cog(Notepad(bot))
