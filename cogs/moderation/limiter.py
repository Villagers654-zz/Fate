"""
cogs.moderation.limiter
~~~~~~~~~~~~~~~~~~~~~~~~

A cog for limiting channels to specific things like images or youtube links

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio

import discord
from discord.ext import commands
from discord.errors import HTTPException, NotFound, Forbidden

from fate import Fate
from botutils import colors


class Limiter(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.config = bot.utils.cache("limiter")

    @commands.group(name="limit", aliases=["limiter"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def limit(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Channel Limiter", icon_url=self.bot.user.avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Limits channels to specific things. To unlimit use `.unlimit`"
            e.add_field(
                name="◈ Usage",
                value="> **.limit images**\n"
                      "only allows messages with files attached\n"
                      "> **.limit yt-links**\n"
                      "only allows YouTube links to be sent\n"
                      "> **.unlimit**\n"
                      "unlimits the channel you use it in",
                inline=False
            )
            await ctx.send(embed=e)

    @commands.command(name="unlimit")
    @commands.has_permissions(manage_messages=True)
    async def unlimit(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        guild_id = ctx.guild.id
        channel_id = str(channel.id)
        if guild_id not in self.config:
            return await ctx.send("There's no channels in this server with a limiter enabled")
        if channel_id not in self.config[guild_id]:
            return await ctx.send(f"{channel.mention} doesn't have a limiter enabled")
        await self.config.remove_sub(guild_id, channel_id)
        await ctx.send(f"Removed the limiter in {channel.mention}")

    @limit.command(name="images")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _images(self, ctx):
        guild_id = ctx.guild.id
        channel_id = str(ctx.channel.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if channel_id in self.config[guild_id]:
            return await ctx.send("This channel already has a limiter enabled")
        self.config[guild_id][channel_id] = "images"
        await ctx.send(f"Limited {ctx.channel.mention} to only allow images")
        await self.config.flush()

    @limit.command(name="yt-links")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _youtube(self, ctx):
        guild_id = ctx.guild.id
        channel_id = str(ctx.channel.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if channel_id in self.config[guild_id]:
            return await ctx.send("This channel already has a limiter enabled")
        self.config[guild_id][channel_id] = "youtube"
        await ctx.send(f"Limited {ctx.channel.mention} to only allow YouTube links")
        await self.config.flush()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if isinstance(m.author, discord.Member) and m.guild and m.guild.owner:
            if not m.author.guild_permissions.administrator:
                guild_id = m.guild.id
                if guild_id in self.config:
                    channel_id = str(m.channel.id)
                    if channel_id in self.config[guild_id]:
                        try:
                            # Limit the channel to only allow images
                            if self.config[guild_id][channel_id] == "images":
                                if len(m.attachments) == 0:
                                    await asyncio.sleep(0)
                                    await m.delete()

                            # Limit the channel to only allow YouTube links
                            elif self.config[guild_id][channel_id] == "youtube":
                                if "youtu.be" not in m.content and "youtube.com" not in m.content:
                                    await asyncio.sleep(0)
                                    await m.delete()
                        except Forbidden:
                            self.config.remove_sub(guild_id, channel_id)
                        except (HTTPException, NotFound):
                            pass


def setup(bot):
    bot.add_cog(Limiter(bot), override=True)
