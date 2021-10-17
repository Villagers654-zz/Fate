"""
cogs.utility.autorole
~~~~~~~~~~~~~~~~~~~~~~

A module for granting users role(s) when they join

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from discord.ext import commands
from typing import *
from botutils import colors
import discord
from discord.errors import NotFound, Forbidden


class AutoRole(commands.Cog):
    default_config = {
        "wait_for_verify": False,
        "roles": [],
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.utils.cache("autorole")

    def is_enabled(self, guild_id):
        return guild_id in self.config

    @commands.command(
        name="autorole", description="Adds a role to users when they join"
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def _autorole(self, ctx, *, args: Union[discord.Role, str] = None):
        guild_id = ctx.guild.id
        e = discord.Embed(color=colors.fate)
        if not args:
            e.set_author(name="Auto-Role Help", icon_url=self.bot.user.display_avatar.url)
            e.set_thumbnail(url=ctx.author.display_avatar.url)
            e.add_field(
                name="◈ Usage ◈",
                value=".autorole {role}\n" ".autorole list\n" ".autorole clear",
                inline=False,
            )
            return await ctx.send(embed=e)

        if args == "clear":
            if guild_id not in self.config:
                return await ctx.send("Auto role is not active")
            self.config[guild_id]["roles"] = []
            if self.config[guild_id] == self.default_config:
                await self.config.remove(guild_id)
            else:
                await self.config.flush()
            return await ctx.send("Cleared list of roles")

        if args == "list":
            if guild_id not in self.config:
                return await ctx.send("Auto role is not active")
            e.set_author(name="Auto Roles", icon_url=self.bot.user.display_avatar.url)
            e.description = ""
            for role_id in self.config[guild_id]["roles"]:
                role = ctx.guild.get_role(role_id)
                if not role:
                    self.config[guild_id]["roles"].remove(role_id)
                    await self.config.flush()
                    continue
                e.description += f"• {role.name}\n"
            return await ctx.send(embed=e)

        if guild_id not in self.config:
            self.config[guild_id] = self.default_config

        # Convert the args into a Role
        if isinstance(args, discord.Role):
            role = args
        else:
            role = await self.bot.utils.get_role(ctx, args)
            if not role:
                return await ctx.send("Role not found")

        # Check the author, and roles position
        if ctx.author.id != ctx.guild.owner.id:
            if role.position >= ctx.author.top_role.position:
                return await ctx.send("That role's above your paygrade, take a seat")
            if role.id in self.config[guild_id]["roles"]:
                return await ctx.send("That role's already in use")

        self.config[guild_id]["roles"].append(role.id)
        await self.config.flush()
        await ctx.send(f"Added `{role.name}` to the list of auto roles")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        if guild_id in self.config:
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
            for role_id in self.config[guild_id]["roles"]:
                role = guild.get_role(role_id)
                if not role:
                    self.config[guild_id]["roles"].remove(role_id)
                    await self.config.flush()
                    continue
                if role.position >= bot.top_role.position:
                    try:
                        await guild.owner.send(
                            f"**[AutoRole - {bot.guild.name}] can't add {role.name} to user. "
                            f"Its position is higher than mine. You'll need to re-add it"
                        )
                    except discord.errors.Forbidden:
                        pass
                    self.config[guild_id]["roles"].remove(role_id)
                    await self.config.flush()
                else:
                    try:
                        await member.add_roles(role)
                    except discord.errors.Forbidden:
                        self.config[guild_id]["roles"].remove(role_id)
                        await self.config.flush()
                    except (discord.errors.NotFound, discord.errors.HTTPException):
                        pass

    @commands.Cog.listener()
    async def on_role_delete(self, role):
        guild_id = role.guild.id
        if guild_id in self.config and role.id in self.config[guild_id]["roles"]:
            self.config[guild_id]["roles"].remove(role.id)
            await self.config.flush()


def setup(bot):
    bot.add_cog(AutoRole(bot), override=True)
