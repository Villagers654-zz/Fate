"""
cogs.utility.autorole
~~~~~~~~~~~~~~~~~~~~~~

A module for granting users role(s) when they join

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *

import discord
from discord import NotFound, Forbidden
from discord.ext import commands

from botutils import colors, GetChoice
from botutils import cache_rewrite


class AutoRole(commands.Cog):
    default_config = {
        "wait_for_verify": False,
        "roles": [],
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = cache_rewrite.Cache(bot, "autorole")

    async def is_enabled(self, guild_id: int):
        return await self.config.contains(guild_id)

    @commands.group(
        name="auto-role",
        aliases=["autorole", "auto_role"],
        description="Shows how to use the module"
    )
    @commands.bot_has_permissions(embed_links=True)
    async def auto_role(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Auto Role", icon_url=self.bot.user.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Gives role(s) to new members when they join"
            p = ctx.prefix
            e.add_field(
                name="◈ Commands",
                value=f"{p}auto-role add @role"
                      f"\n{p}auto-role remove",
                inline=False,
            )
            roles = ""
            config = await self.config[ctx.guild.id]
            if config:
                for role_id in config["roles"]:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        roles += f"\n- {role.mention}"
            if not roles:
                roles = "None set"
            e.add_field(
                name="◈ Roles",
                value=roles,
                inline=False
            )
            await ctx.send(embed=e)

    @auto_role.command(name="add", description="Adds a new role to give on join")
    @commands.has_permissions(manage_roles=True)
    async def _add(self, ctx, *, role: Union[discord.Role, str]):
        guild_id = ctx.guild.id
        config = await self.config[guild_id]
        if not config:
            config.update(**self.default_config)

        # Convert the args into a Role
        if not isinstance(role, discord.Role):
            role = await self.bot.utils.get_role(ctx, role)
            if not role:
                return await ctx.send("Role not found")

        # Check the author, and roles position
        if ctx.author.id != ctx.guild.owner.id:
            if role.position >= ctx.author.top_role.position:
                return await ctx.send("That role's above your paygrade, take a seat")
            if role.id in config["roles"]:
                return await ctx.send("That role's already in use")
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's higher than I can manage")

        config["roles"].append(role.id)
        await ctx.send(f"Added `{role.name}` to the list of auto roles")
        await config.save()

    @auto_role.command(name="remove", description="Removes one or more roles")
    @commands.has_permissions(manage_roles=True)
    async def _remove(self, ctx):
        config = await self.config[ctx.guild.id]
        if not config:
            return await ctx.send("Auto role isn't active")
        roles = {
            role.name: role for role_id in config["roles"]
            if (role := ctx.guild.get_role(role_id))
        }
        if len(roles) == 1:
            config["roles"].clear()
        else:
            to_remove = await GetChoice(ctx, roles.keys(), limit=None)
            for role in to_remove:
                config["roles"].remove(roles[role].id)
        if config == self.default_config:
            await config.delete()
        else:
            await config.save()
        await ctx.send("Updated the list of auto-roles")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = await self.config[member.guild.id]
        if self.bot.is_ready() and config:
            guild = member.guild
            bot = guild.me
            if not bot.guild_permissions.manage_roles:
                try:
                    dm = guild.owner.dm_channel
                    if not dm:
                        dm = await guild.owner.create_dm()
                    history = await dm.history(limit=1).flatten()
                    if history and "AutoRole" in history[0].content:
                        return
                    await guild.owner.send(
                        f"**[AutoRole - {guild}] I'm missing manage_roles permissions "
                        f"in order to add roles to new users"
                    )
                except (Forbidden, NotFound, AttributeError):
                    return
                return
            for role_id in config["roles"]:
                role = guild.get_role(int(role_id))
                if not role:
                    continue
                if role.position >= bot.top_role.position:
                    try:
                        await guild.owner.send(
                            f"**[AutoRole - {bot.guild.name}] can't add {role.name} to user. "
                            f"Its position is higher than mine. You'll need to re-add it"
                        )
                    except discord.Forbidden:
                        pass
                    config["roles"].remove(role_id)
                    await self.config.flush()
                else:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass
                    except (discord.NotFound, discord.HTTPException):
                        pass

    @commands.Cog.listener()
    async def on_role_delete(self, role):
        config = await self.conifg[role.guild.id]
        if config and role.id in config["roles"]:
            config["roles"].remove(role.id)
            await config.save()


def setup(bot):
    bot.add_cog(AutoRole(bot), override=True)
