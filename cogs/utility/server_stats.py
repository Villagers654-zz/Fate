"""
cogs.utility.server_stats
~~~~~~~~~~~~~~~~~~~~~~~~~~

A cog for showing server stats in voice channel names

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import asyncio
from discord.ext import commands
import discord
from fate import Fate


class ServerStatistics(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.defaults = {
            "members": "👥 | {count} Members",
            "bots": "🤖 | {count} Bots",
            "boosts": "💎 | {count} Boosts"
        }
        self.config = bot.utils.cache("server_stats")

    @commands.group(
        name="server-stats",
        aliases=["serverstats", "server_stats", "ss"],
        description="Shows how to use the module"
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def server_statistics(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Server Stat Channels", icon_url=self.bot.user.display_avatar.url)
            e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
            e.description = "• Use voice channels to automatically update and show server statistics\n" \
                            "• Display things like the member count, bot count, and boost count"
            p: str = ctx.prefix
            e.add_field(
                name="◈ Usage",
                value=f"{p}server-stats enable\n"
                      f"`helps you setup the module`\n"
                      f"{p}server-stats disable\n"
                      f"`completely disables the module`\n"
                      f"{p}server-stats config\n"
                      f"`send your current setup`",
                inline=False
            )
            e.add_field(
                name="◈ Formatting",
                value="You can alter the channel name format just by editing the actual channels name. "
                      "Just put `{count}` where you want it to put the count",
                inline=False
            )
            await ctx.send(embed=e)

    @server_statistics.command(name="enable", description="Starts the setup process")
    async def _enable(self, ctx):
        converter = commands.VoiceChannelConverter()
        types = ["members", "bots", "boosts"]
        results = {}

        for channel_type in types:
            await ctx.send(
                f"Should I show the count of {channel_type}? "
                f"Name the voice channel if you do, otherwise say `skip`"
            )
            reply = await self.bot.utils.get_message(ctx)
            if "skip" in reply.content.lower():
                continue
            if not any(reply.content == c.name for c in ctx.guild.voice_channels):
                return await ctx.send("That voice channel doesn't exist")
            channel = await converter.convert(ctx, reply.content)
            results[channel_type] = channel

        if not any(value for value in results.values()):
            return await ctx.send("You didn't choose to use any of the channel types")

        self.config[ctx.guild.id] = {
            ctype: {
                "channel_id": channel.id,
                "format": channel.name if "{count}" in channel.name else self.defaults[ctype]
            } for ctype, channel in results.items()
        }
        await self.update_channels(ctx.guild)

        await ctx.send("Enabled server stats")
        await self.config.flush()

    @server_statistics.command(name="disable", description="Disables the module")
    async def _disable(self, ctx):
        if ctx.guild.id not in self.config:
            return await ctx.send("Server stats aren't enabled")
        await self.config.remove(ctx.guild.id)
        await ctx.send("Disabled server stats")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before and after and before.guild.id in self.config and "{count}" in after.name:
            guild_id = before.guild.id
            for ctype, data in list(self.config[guild_id].items()):
                if before.id == data["channel_id"]:
                    self.config[guild_id][ctype]["format"] = after.name
                    await self.config.flush()
                    return await self.update_channels(after.guild)

    async def update_channels(self, guild):
        """ Refreshes all the channels names if changed """
        fmts = {
            "members": 0,
            "bots": 0,
            "boosts": guild.premium_subscription_count
        }
        for member in list(guild.members):
            await asyncio.sleep(0)
            if member.bot:
                fmts["bots"] += 1
            else:
                fmts["members"] += 1
        for ctype, data in list(self.config[guild.id].items()):
            if channel := self.bot.get_channel(data["channel_id"]):
                fmt = data["format"].replace("{count}", str(fmts[ctype]))
                if fmt != channel.name:
                    try:
                        await channel.edit(name=fmt)  # type: ignore
                    except discord.Forbidden:
                        return await self.config.remove(guild.id)
            else:
                await self.config.remove_sub(guild.id, ctype)

    @commands.Cog.listener("on_member_join")
    @commands.Cog.listener("on_member_remove")
    async def on_member_join(self, member):
        if member.guild and member.guild.id in self.config:
            await self.update_channels(member.guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before and after and before.id in self.config:
            await self.update_channels(after)


def setup(bot):
    bot.add_cog(ServerStatistics(bot), override=True)
