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

from botutils import colors, Cooldown, Configure
from botutils.cache_rewrite import Cache


class AntiRaid(commands.Cog):
    default = {
        "mass_join": True,
        "mass_ban": True,
        "self_bot": False,
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Cache(bot, "anti_raid")
        self.join_cd = Cooldown(15, 25)
        self.ban_cd = Cooldown(10, 15)
        self.counter = {}
        self.locked = []
        self.last = {}

    async def is_enabled(self, guild_id: int):
        return await self.config.contains(guild_id)

    async def ensure_permissions(self, guild):
        bot = guild.get_member(self.bot.user.id)
        perms = [perm for perm, value in bot.guild_permissions if value]
        required = ["view_audit_log", "ban_members"]
        for perm in required:
            if perm not in perms:
                await self.config.remove(guild.id)
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
            p = ctx.prefix
            e.add_field(
                name="Usage",
                value=f"{p}antiraid configure\n"
                      f"{p}antiraid disable",
                inline=False,
            )
            e.set_footer(text=f"Current Status: {toggle}")
            await ctx.send(embed=e)

    @_anti_raid.command(name="configure", aliases=["config", "enable"], description="AntiRaid Toggles")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True, manage_roles=True)
    async def _configure(self, ctx):
        config = await self.config.fetch(ctx.guild.id)
        if not config:
            config.update(**self.default)
        config = await Configure(ctx, config)
        if not any(v for v in config.values()):
            del self.config[ctx.guild.id]
        else:
            await config.save()
        await ctx.send("Updated your config")

    @_anti_raid.command(name="disable", description="Disables AntiRaid")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        if not await self.config[ctx.guild.id]:
            return await ctx.send("Anti raid is not enabled")
        await self.config.remove(ctx.guild.id)
        await ctx.send("Disabled anti raid")

    @commands.Cog.listener()
    async def on_typing(self, _channel, user, _when):
        if user.id in self.counter:
            self.counter[user.id] = None
            await asyncio.sleep(10)
            self.counter.pop(user.id, None)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.is_system() or msg.author.bot or not msg.guild:
            return
        guild_id = msg.guild.id
        if conf := await self.config[guild_id]:
            if conf["self_bot"]:
                triggered = False
                user_id = msg.author.id
                if user_id not in self.counter:
                    self.counter[user_id] = 0
                if self.counter[user_id] is not None:
                    self.counter[user_id] += 1
                    if self.counter[user_id] > 5:
                        triggered = True
                if msg.embeds and "." not in msg.content:
                    triggered = True
                if triggered:
                    with suppress(Exception):
                        await msg.author.ban(reason="AntiRaid: using a self-bot")
                        await msg.channel.send(f"Banned **{msg.author}** for using a self-bot or client modification")

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
        if member.top_role.position >= guild.me.top_role.position:
            return
        config = await self.config[guild.id]
        if not config or not config["mass_ban"]:
            return
        try:
            entry, = await guild.audit_logs(limit=1).flatten()
        except (ValueError, discord.Forbidden):
            return
        if entry.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=3):
            if entry.action in [discord.AuditLogAction.kick, discord.AuditLogAction.ban]:
                user = guild.get_member(entry.user.id)
                if user and self.ban_cd.check(user.id):
                    if user.top_role.position >= guild.me.top_role.position:
                        return
                    if await self.ensure_permissions(guild):
                        await guild.ban(
                            user=user,
                            reason="Attempted Purge",
                            delete_message_days=0,
                        )


def setup(bot):
    bot.add_cog(AntiRaid(bot), override=True)
