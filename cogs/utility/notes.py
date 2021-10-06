"""
cogs.utility.notes
~~~~~~~~~~~~~~~~~~~

A cog for jutting down notes for later

:copyright: (C) 2019-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

from os.path import isfile
from datetime import datetime, timezone
import asyncio
import random
import json
import os

from discord.ext import commands
import discord


class Notepad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notes = {}
        self.timestamp = {}
        if isfile("./data/userdata/notes.json"):
            with open("./data/userdata/notes.json", "r") as infile:
                dat = json.load(infile)
                if "notes" in dat and "timestamp" in dat:
                    self.notes = dat["notes"]
                    self.timestamp = dat["timestamp"]

    async def save(self):
        data = {"notes": self.notes, "timestamp": self.timestamp}
        await self.bot.utils.save_json("./data/userdata/notes.json", data)

    @commands.command(name="note", description="Saves a note for later")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def _note(self, ctx, *, arg: commands.clean_content = ""):
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
                self.timestamp[author_id].append(
                    datetime.now(tz=timezone.utc).strftime("%m-%d-%Y %I:%M%p")
                )
                if len(self.timestamp[author_id]) > 5:
                    del self.timestamp[author_id][0]
                await self.save()
                path = (
                    os.getcwd()
                    + "/data/images/reactions/notes/"
                    + random.choice(
                        os.listdir(os.getcwd() + "/data/images/reactions/notes/")
                    )
                )
                e = discord.Embed(color=0xFFC923)
                e.set_author(name="Noted..", icon_url=ctx.author.display_avatar.url)
                e.set_image(url="attachment://" + os.path.basename(path))
                await ctx.send(
                    file=discord.File(path, filename=os.path.basename(path)),
                    embed=e,
                    delete_after=10,
                )
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await asyncio.sleep(10)
                await ctx.message.delete()
        else:
            if str(ctx.author.id) in self.notes:
                async with ctx.typing():
                    e = discord.Embed(color=0xFFC923)
                    e.title = "~~===🥂🍸🍷Note🍷🍸🥂===~~"
                    e.set_thumbnail(url=ctx.author.display_avatar.url)
                    e.description = self.notes[author_id][-1]
                    e.set_footer(text=self.timestamp[author_id][-1])
                    await ctx.send(embed=e)
            else:
                await ctx.send("no data")

    @commands.command(name="quicknote", description="Saves a note without sending an embed")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def _quicknote(self, ctx, *, note):
        author_id = str(ctx.author.id)
        if len(note) > 400:
            return await ctx.send("Each note cannot be larger than 400 characters")
        if author_id not in self.notes:
            self.notes[author_id] = []
        self.notes[author_id].append(note)
        if len(self.notes[author_id]) > 5:
            del self.notes[author_id][0]
        if author_id not in self.timestamp:
            self.timestamp[author_id] = []
        self.timestamp[author_id].append(
            datetime.now(tz=timezone.utc).strftime("%m-%d-%Y %I:%M%p")
        )
        if len(self.timestamp[author_id]) > 5:
            del self.timestamp[author_id][0]
        await self.save()
        await ctx.send("Noted..", delete_after=1)
        await asyncio.sleep(1)
        await ctx.message.delete()

    @commands.command(name="notes", description="Shows your last 5 notes")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def _notes(self, ctx):
        author_id = str(ctx.author.id)
        if author_id in self.notes:
            e = discord.Embed(color=0xFFC923)
            e.title = "~~===🥂🍸🍷Notes🍷🍸🥂===~~"
            e.set_thumbnail(url=ctx.author.display_avatar.url)
            e.description = f"**Your last {len(self.notes[author_id])} note(s):**"
            note = len(self.notes[author_id]) - 1
            position = 1
            for _i in self.notes[author_id]:
                e.description += f"\n**{position}.** {self.notes[author_id][note].replace('`', '')}\n`{self.timestamp[author_id][note]}`\n"
                note -= 1
                position += 1
            await ctx.send(embed=e)
        else:
            await ctx.send("no data")


def setup(bot: commands.Bot):
    bot.add_cog(Notepad(bot), override=True)
