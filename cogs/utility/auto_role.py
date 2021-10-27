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

    @commands.group(
        name="autorole",
        aliases=["auto-role", "auto_role"],
        description="Shows how to use the module"
    )
    @commands.bot_has_permissions(embed_links=True)
    async def auto_role(self, ctx):
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Auto Role", icon_url=self.bot.user.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.description = "Gives role(s) to new members when they join"
        p = ctx.prefix
        e.add_field(
            name="◈ Commands",
            value=f"{p}auto-role add @role"
                  f"\n{p}auto-role clear"
                  f"\n{p}auto-role list",
            inline=False,
        )
        await ctx.send(embed=e)

    @auto_role.command(name="add", description="Adds a new role to give on join")
    @commands.has_permissions(manage_roles=True)
    async def _add(self, ctx, *, role: Union[discord.Role, str]):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = self.default_config

        # Convert the args into a Role
        if not isinstance(role, discord.Role):
            role = await self.bot.utils.get_role(ctx, role)
            if not role:
                return await ctx.send("Role not found")

        # Check the author, and roles position
        if ctx.author.id != ctx.guild.owner.id:
            if role.position >= ctx.author.top_role.position:
                return await ctx.send("That role's above your paygrade, take a seat")
            if role.id in self.config[guild_id]["roles"]:
                return await ctx.send("That role's already in use")
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's higher than I can manage")

        self.config[guild_id]["roles"].append(role.id)
        await ctx.send(f"Added `{role.name}` to the list of auto roles")
        await self.config.flush()

    @auto_role.command(name="clear", description="Removes all the auto roles")
    @commands.has_permissions(manage_roles=True)
    async def _clear(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Auto role is not active")
        self.config[guild_id]["roles"] = []
        if self.config[guild_id] == self.default_config:
            await self.config.remove(guild_id)
        else:
            await self.config.flush()
        await ctx.send("Cleared list of auto roles")

    @auto_role.command(name="list", description="Lists all the auto roles")
    @commands.bot_has_permissions(embed_links=True)
    async def _list(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Auto role isn't active")
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Auto Roles", icon_url=self.bot.user.display_avatar.url)
        e.description = ""
        for role_id in self.config[guild_id]["roles"]:
            if role := ctx.guild.get_role(role_id):
                e.description += f"• {role.name}\n"
            else:
                self.config[guild_id]["roles"].remove(role_id)
                await self.config.flush()
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        if self.bot.is_ready() and guild_id in self.config:
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
                if not isinstance(role_id, int):
                    self.bot.log.critical(f"A role_id in auto-role is str")
                role = guild.get_role(int(role_id))
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
