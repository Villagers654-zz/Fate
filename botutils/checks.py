"""
Check functions for the bot
"""

import asyncio
from contextlib import suppress
from discord.ext import commands
import discord


class Attributes:
    def __init__(self, bot):
        self.bot = bot

    def is_moderator(self, member) -> bool:
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
        :param target: Optional: [Context, Guild]
        :param choice: Allow choice between multiple roles, requires Context
        :param upsert: Create the role if not exists
        :return: Optional: [Role, None]
        """
        ctx = None
        if isinstance(target, commands.Context):
            ctx = target
            guild = ctx.guild
        elif isinstance(target, discord.Guild):
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
            color = discord.Color(self.bot.utils.colors.black())
            mute_role = await guild.create_role(name="Muted", color=color)

            # Set the overwrites for the mute role
            # Set the category channel permissions
            for i, channel in enumerate(guild.categories):
                await asyncio.sleep(0)
                if mute_role in channel.overwrites:
                    continue
                with suppress(discord.errors.Forbidden):
                    await channel.set_permissions(mute_role, send_messages=False)
                if i + 1 >= len(guild.text_channels):  # Prevent sleeping after the last channel in the list
                    await asyncio.sleep(0.5)

            # Set the text channel permissions
            for i, channel in enumerate(guild.text_channels):
                await asyncio.sleep(0)
                if mute_role in channel.overwrites:
                    continue
                with suppress(discord.errors.Forbidden):
                    await channel.set_permissions(mute_role, send_messages=False)
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


def luck(ctx):
    return ctx.message.author.id in [
        264838866480005122,  # Luck
        355026215137968129,  # Tother
    ]


def devs(ctx: commands.Context):
    return (
        ctx.author
        in ctx.bot.get_guild(397415086295089155).get_role(690642373180522606).members
    )


def command_is_enabled(ctx):
    if not isinstance(ctx.guild, discord.Guild):
        return True

    guild_id = str(ctx.guild.id)
    if guild_id not in ctx.bot.disabled_commands:
        return True  # command isn't disabled

    cmd = ctx.command.name
    conf = ctx.bot.disabled_commands[guild_id]  # type: dict
    channel_id = str(ctx.channel.id)

    if cmd in conf["global"]:
        return False
    if channel_id in conf["channels"]:
        if cmd in conf["channels"][channel_id]:
            return False

    if ctx.channel.category:
        channel_id = str(ctx.channel.category.id)
        if channel_id in conf["categories"]:
            if cmd in conf["categories"][channel_id]:
                return False

    return True

def blocked(ctx):
    return ctx.author.id not in ctx.bot.blocked

def restricted(ctx):
    if not ctx.guild or ctx.author.id in ctx.bot.owner_ids:
        return True  # Nothing's restricted
    guild_id = ctx.guild.id
    if guild_id in ctx.bot.restricted:
        if ctx.channel.id in ctx.bot.restricted[guild_id]["channels"]:
            if not ctx.channel.permissions_for(ctx.author).manage_messages:
                return False
    return True
