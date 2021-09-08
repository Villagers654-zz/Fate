"""
cogs.utility.restore_roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A cog for restoring a members roles when they rejoin the server

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from os.path import isfile
import json
from contextlib import suppress
from discord.ext import commands
import discord
from botutils import colors


class RestoreRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds = []
        self.allow_perms = []
        self.cache = {}
        self.path = "./data/userdata/restore_roles.json"
        if isfile(self.path):
            with open(self.path, "r") as f:
                dat = json.load(f)
                if "guilds" in dat:
                    self.guilds = dat["guilds"]
                if "allow_perms" in dat:
                    self.allow_perms = dat["allow_perms"]

    async def save_data(self):
        """ Saves any changes made """
        data = {"guilds": self.guilds, "allow_perms": self.allow_perms}
        async with self.bot.utils.open(self.path, "w") as f:
            await f.write(await self.bot.dump(data))

    def is_enabled(self, guild_id):
        return str(guild_id) in self.guilds

    async def disable_module(self, guild_id: str):
        """ Disables the module and resets guild data """
        self.guilds.pop(self.guilds.index(guild_id))
        if guild_id in self.allow_perms:
            self.allow_perms.pop(self.allow_perms.index(guild_id))
        await self.save_data()

    @commands.group(
        name="restore-roles",
        aliases=["restore_roles", "restoreroles"],
        description="Shows how to use the module"
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def restore_roles(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Restore Roles", icon_url=ctx.author.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Adds a users roles back if they leave and rejoin"
            usage = (
                ".Restore-Roles enable\n• Enables the module\n"
                ".Restore-Roles disable\n• Disables the module\n"
                ".Restore-Roles allow-perms\n• Restores roles with mod perms"
            )
            e.add_field(name="◈ Usage ◈", value=usage)
            await ctx.send(embed=e)

    @restore_roles.command(name="enable", description="Enables restoring roles on rejoin")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.guilds:
            return await ctx.send("Restore-Roles is already enabled")
        self.guilds.append(guild_id)
        await ctx.send("Enabled Restore-Roles")
        await self.save_data()

    @restore_roles.command(name="disable", description="Disables restoring roles on rejoin")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.guilds:
            return await ctx.send("Restore-Roles is not enabled")
        await self.disable_module(guild_id)
        await ctx.send("Disabled Restore-Roles")

    @restore_roles.command(name="allow-perms", description="Toggles restoring mod/admin roles")
    @commands.bot_has_permissions(manage_roles=True)
    async def _allow_perms(self, ctx):
        if ctx.author.id != ctx.guild.owner.id:
            return await ctx.send("Only the server owner can toggle this")
        guild_id = str(ctx.guild.id)
        if guild_id in self.allow_perms:
            self.allow_perms.pop(self.allow_perms.index(guild_id))
            await ctx.send("Unallowed perms")
        else:
            self.allow_perms.append(guild_id)
            await ctx.send("Allowed perms")
        await self.save_data()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """ Restore roles on rejoin """
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        if guild_id in self.cache and guild_id in self.guilds:
            if user_id in self.cache[guild_id]:
                roles = []
                with suppress(discord.errors.NotFound, discord.errors.Forbidden, AttributeError):
                    for role_id in self.cache[guild_id][user_id]:
                        role = member.guild.get_role(role_id)
                        if isinstance(role, discord.Role):
                            if role.position < member.guild.me.top_role.position:
                                roles.append(role)
                    await member.add_roles(*roles, reason=".Restore-Roles")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """ Saves role id's when a member leaves """
        if member.id == self.bot.user.id:
            return
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        if guild_id in self.guilds:
            if guild_id not in self.cache:
                self.cache[guild_id] = {}
            self.cache[guild_id][user_id] = []

            def is_modifiable(role):
                return (
                    not role.is_default()
                    and role.position < member.guild.me.top_role.position
                    and not role.managed
                )

            for role in [role for role in member.roles if role and is_modifiable(role)]:
                notable = [
                    "view_audit_log",
                    "manage_roles",
                    "manage_channels",
                    "manage_emojis",
                    "kick_members",
                    "ban_members",
                    "manage_messages",
                    "mention_everyone",
                ]
                if (
                    not any(perm in notable for perm in role.permissions)
                    or guild_id in self.allow_perms
                ):
                    self.cache[guild_id][user_id].append(role.id)


def setup(bot):
    bot.add_cog(RestoreRoles(bot), override=True)
