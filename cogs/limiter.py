from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json
from PIL import Image
from io import BytesIO
import requests


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.images = {}
        self.boosters = {}
        self.dupe = {}
        if isfile("./data/userdata/limiter.json"):
            with open("./data/userdata/limiter.json", "r") as infile:
                dat = json.load(infile)
                if "images" in dat:
                    self.images = dat["images"]
                if "boosters" in dat:
                    self.boosters = dat["boosters"]
                if "duplicate_images" in dat:
                    self.dupe = dat["duplicate_images"]

    def save_data(self):
        with open("./data/userdata/limiter.json", "w") as outfile:
            json.dump(
                {
                    "images": self.images,
                    "boosters": self.boosters,
                    "duplicate_images": self.dupe,
                },
                outfile,
                ensure_ascii=False,
            )

    @commands.group(name="limit", aliases=["limiter"])
    @commands.has_permissions(manage_guild=True)
    async def _limit(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Channel Limiter Instructions:**\n"
                ".limit images ~ `toggles image limiter (per-channel)`\n"
                "only allows messages with files attached\n"
                ".limit boosters"
                "only allows nitro boosters to send"
            )

    @_limit.command(name="images")
    @commands.has_permissions(manage_channels=True)
    async def _images(self, ctx):
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        if guild_id not in self.images:
            self.images[guild_id] = {}
        if channel_id not in self.images[guild_id]:
            self.images[guild_id][channel_id] = "enabled"
            await ctx.message.add_reaction("👍")
            await ctx.send(f"Limited **{ctx.channel.name}** to only allow images")
        else:
            del self.images[guild_id][channel_id]
            await ctx.message.add_reaction("👍")
            await ctx.send("Disabled channel limiter")
        self.save_data()

    @_limit.command(name="boosters")
    @commands.has_permissions(manage_channels=True)
    async def _boosters(self, ctx):
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        if guild_id not in self.boosters:
            self.boosters[guild_id] = {}
        if channel_id not in self.boosters[guild_id]:
            self.boosters[guild_id][channel_id] = "enabled"
            await ctx.message.add_reaction("👍")
            await ctx.send(f"Limited **{ctx.channel.name}** to only allow boosters")
        else:
            del self.boosters[guild_id][channel_id]
            await ctx.message.add_reaction("👍")
            await ctx.send("Disabled channel limiter")
        self.save_data()

    @_limit.command(name="duplicateimages")
    @commands.has_permissions(manage_channels=True)
    async def _duplicate_images(self, ctx):
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        if guild_id not in self.dupe:
            self.dupe[guild_id] = {}
        if channel_id not in self.dupe[guild_id]:
            self.dupe[guild_id][channel_id] = "enabled"
            await ctx.message.add_reaction("👍")
            await ctx.send(f"Limited **{ctx.channel.name}** to only allow boosters")
        else:
            del self.dupe[guild_id][channel_id]
            await ctx.message.add_reaction("👍")
            await ctx.send("Disabled channel limiter")
        self.save_data()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if isinstance(m.guild, discord.Guild):
            guild_id = str(m.guild.id)
            channel_id = str(m.channel.id)
            for i in [".limit", "limited **", "disabled channel"]:
                if m.content.lower().startswith(i):
                    return
            await asyncio.sleep(0.5)

            # image limiter
            if guild_id in self.images:
                if channel_id in self.images[guild_id]:
                    if len(m.attachments) < 1:
                        await m.delete()

            # booster limiter
            if guild_id in self.boosters:
                if channel_id in self.boosters[guild_id]:
                    if not m.author.premium_since:
                        await m.delete()

            # duplicate image limiter
            if guild_id in self.dupe:
                if channel_id in self.dupe[guild_id]:
                    if m.attachments:
                        image_data = []
                        for attachment in m.attachments:
                            dat = ""
                            im = Image.open(
                                BytesIO(requests.get(attachment.url).content)
                            ).convert("RGBA")
                            pixels = list(im.getdata())
                            for pixel in pixels:
                                dat += str(pixel)
                            image_data.append(dat)
                        async for msg in m.channel.history(limit=10):
                            if msg.id != m.id:
                                for attachment in msg.attachments:
                                    dat = ""
                                    im = Image.open(
                                        BytesIO(requests.get(attachment.url).content)
                                    ).convert("RGBA")
                                    pixels = list(im.getdata())
                                    for pixel in pixels:
                                        dat += str(pixel)
                                    if dat in image_data:
                                        print("Msg didnt pass")
                                        return await m.delete()
                                    await asyncio.sleep(1)
                                print("msg passed")
                        print("ran through all images")


def setup(bot):
    bot.add_cog(Utility(bot))
