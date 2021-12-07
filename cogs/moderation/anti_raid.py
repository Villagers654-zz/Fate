"""
cogs.utility.anti_raid
~~~~~~~~~~~~~~~~~~~~~~~

A cog for preventing mass join and kick/ban raids

:copyright: (C) 2020-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import asyncio
from datetime import datetime, timezone, timedelta
from contextlib import suppress
from time import time
import discord
from discord.ext import commands

from botutils import colors, Cooldown
from botutils.cache_rewrite import Cache


class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Cache(bot, "anti_raid")
        self.join_cd = Cooldown(15, 25)
        self.ban_cd = Cooldown(10, 15)
        self.locked = []
        self.last = {}

    async def is_enabled(self, guild_id: int):
        if await self.config[guild_id]:
            return True
        return False

    async def ensure_permissions(self, guild):
        bot = guild.get_member(self.bot.user.id)
        perms = [perm for perm, value in bot.guild_permissions if value]
        required = ["view_audit_log", "ban_members"]
        for perm in required:
            if perm not in perms:
                del self.config[guild.id]
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        await channel.send(
                            f"Disabled anti raid, missing {perm} permissions"
                        )
                        break
                return False
        return True

    @commands.group(name="antiraid", aliases=["anti_raid"], description="Prevents mass-join and mass-kick/ban raids")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(embed_links=True)
    async def _anti_raid(self, ctx):
        if not ctx.invoked_subcommand:
            toggle = "disabled"
            if await self.config[ctx.guild.id]:
                toggle = "enabled"
            e = discord.Embed(color=colors.red)
            e.set_author(name="Anti Raid", icon_url=ctx.author.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = self._anti_raid.description
            e.add_field(
                name="Usage",
                value=".antiraid enable\n" ".antiraid disable",
                inline=False,
            )
            e.set_footer(text=f"Current Status: {toggle}")
            await ctx.send(embed=e)

    @_anti_raid.command(name="enable", description="Enables AntiRaid")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True, manage_roles=True)
    async def _enable(self, ctx):
        if await self.config[ctx.guild.id]:
            return await ctx.send("Anti raid is already enabled")
        self.config[ctx.guild.id] = {
            "mass_join": True,
            "mass_ban": True
        }
        await ctx.send("Enabled anti raid")

    @_anti_raid.command(name="disable", description="Disables AntiRaid")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        if not await self.config[ctx.guild.id]:
            return await ctx.send("Anti raid is not enabled")
        del self.config[ctx.guild.id]
        await ctx.send("Disabled anti raid")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """ Prevents mass-join raids """
        guild = member.guild
        config = await self.config[guild.id]
        if config and config["mass_join"] and not member.bot:
            if not await self.ensure_permissions(member.guild):
                return

            # Server's already locked
            if guild.id in self.locked:
                with suppress(Exception):
                    await member.send(
                        f"**{member.guild.name}** is currently locked due to an "
                        f"attempted raid, you can try rejoining in an hour"
                    )
                with suppress(Exception):
                    await guild.ban(
                        user=member,
                        reason="Server locked due to raid",
                        delete_message_days=0
                    )
                    await asyncio.sleep(600)
                    try:
                        await member.guild.unban(member, reason="Server unlocked")
                    except (discord.Forbidden, discord.NotFound):
                        pass
                return

            if guild.id not in self.last:
                self.last[guild.id] = {}
            self.last[guild.id][member.id] = time()
            if self.join_cd.check(guild.id):
                self.locked.append(guild.id)
                for user_id, joined_at in self.last[guild.id].items():
                    user = guild.get_member(user_id)
                    if user and joined_at > time() - 15:
                        with suppress(Exception):
                            await user.send(
                                f"**{member.guild.name}** is currently locked due to "
                                f"an attempted raid, you can try rejoining in an hour"
                            )
                        with suppress(discord.NotFound):
                            await member.guild.ban(
                            user=user,
                            reason="AntiRaid",
                            delete_message_days=0,
                        )
                del self.last[guild.id]
                await asyncio.sleep(600)
                if guild.id in self.locked:
                    self.locked.remove(guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id == self.bot.user.id or not member.guild:
            return
        guild = member.guild  # type: discord.Guild
        if not guild.me.guild_permissions.view_audit_log:
            return
        config = await self.config[guild.id]
        if not config or not config["mass_ban"]:
            return
        try:
            entry, = await guild.audit_logs(limit=1).flatten()
        except discord.Forbidden:
            return
        if entry.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=3):
            if entry.action in [discord.AuditLogAction.kick, discord.AuditLogAction.ban]:
                user = entry.user
                if self.ban_cd.check(user.id):
                    if await self.ensure_permissions(guild):
                        await guild.ban(
                            user=user,
                            reason="Attempted Purge",
                            delete_message_days=0,
                        )


def setup(bot):
    bot.add_cog(AntiRaid(bot), override=True)
