"""
Attributes Helper
~~~~~~~~~~~~~~~~~

Helper class for easily checking if a users a mod, and getting the mute role

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from contextlib import suppress

from discord.ext import commands
from discord.ext.commands import Context
import discord
from discord import Guild, Role, Member

from . import colors


class Attributes:
    def __init__(self, bot):
        self.bot = bot

    def is_moderator(self, member: Member) -> bool:
        if not isinstance(member, Member):
            return False
        if member.guild_permissions.administrator:
            return True
        guild_id = str(member.guild.id)
        mod = self.bot.cogs["Moderation"]
        if guild_id in mod.config:
            if member.id in mod.config[guild_id]["usermod"]:
                return True
            if any(r.id in mod.config[guild_id]["rolemod"] for r in member.roles):
                return True
        return False

    def is_restricted(self, channel, member):
        guild_id = channel.guild.id
        if guild_id in self.bot.restricted:
            if channel.id in self.bot.restricted[guild_id]["channels"]:
                if not channel.permissions_for(member).manage_messages:
                    return True
        return False

    async def get_mute_role(self, target, upsert=False):
        """
        :param Context or Guild target: Optional: [Context, Guild]
        :param bool choice: Allow choice between multiple roles, requires Context
        :param bool upsert: Create the role if not exists
        :return Role or None:
        """
        ctx = None
        if isinstance(target, Context):
            ctx = target
            guild = ctx.guild
        elif isinstance(target, Guild):
            guild = target
        else:
            raise TypeError(f"Parameter 'target' must be either Context or Guild")

        # Check the Moderation cog for a configured mute role
        guild_id = str(guild.id)
        mod = self.bot.cogs["Moderation"]
        if guild_id in mod.config and mod.config[guild_id]["mute_role"]:
            role = guild.get_role(mod.config[guild_id]["mute_role"])
            if role:
                return role
            else:
                mod.config[guild_id]["mute_role"] = None

        # Get all the related roles
        roles = []
        for role in reversed(guild.roles):
            await asyncio.sleep(0)
            if "muted" in role.name.lower():
                if not ctx:
                    return role
                roles.append(role)

        if len(roles) == 1:
            return roles[0]
        elif len(roles) > 1:
            if not ctx:
                return roles[0]
            mentions = [r.mention for r in roles]
            mention = await self.bot.utils.get_choice(ctx, mentions, name="Select Which Mute Role")
            role = roles[mentions.index(mention)]
            if guild_id in mod.config:
                mod.config[guild_id]["mute_role"] = role.id
                await mod.save_data()
            return role

        if upsert:
            color = discord.Color(colors.black)
            try:
                mute_role = await guild.create_role(name="Muted", color=color)
            except discord.errors.HTTPException:
                return None

            # Set the overwrites for the mute role
            # Set the category channel permissions
            for i, channel in enumerate(guild.categories):
                await asyncio.sleep(0)
                if mute_role in channel.overwrites:
                    continue
                with suppress(discord.errors.Forbidden):
                    await channel.set_permissions(mute_role, send_messages=False, use_threads=False)
                if i + 1 >= len(guild.text_channels):  # Prevent sleeping after the last channel in the list
                    await asyncio.sleep(0.5)

            # Set the text channel permissions
            for i, channel in enumerate(guild.text_channels):
                await asyncio.sleep(0)
                if mute_role in channel.overwrites:
                    continue
                with suppress(discord.errors.Forbidden):
                    await channel.set_permissions(mute_role, send_messages=False, use_threads=False)
                if i + 1 >= len(guild.text_channels):  # Prevent sleeping after the last channel in the list
                    await asyncio.sleep(0.5)

            # Set the voice channel permissions
            for i, channel in enumerate(guild.voice_channels):
                await asyncio.sleep(0)
                if mute_role in channel.overwrites:
                    continue
                with suppress(discord.errors.Forbidden):
                    await channel.set_permissions(mute_role, speak=False)
                if i + 1 >= len(guild.voice_channels):  # Prevent sleeping after the last
                    await asyncio.sleep(0.5)

            return mute_role

        return None
