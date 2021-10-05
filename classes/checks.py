"""
Command Checks
~~~~~~~~~~~~~~~

A collection of functions for checking if a command should run

:copyright: (C) 2019-present FrequencyX4
:license: Proprietary and Confidential, see LICENSE for details
"""

import discord


def command_is_enabled(ctx):
    if not isinstance(ctx.guild, discord.Guild):
        return True

    guild_id = ctx.guild.id
    cog = ctx.bot.get_cog("Core")
    if not cog:
        return True
    if guild_id not in cog.config:
        return True  # command isn't disabled

    cmd = ctx.command.name
    conf = cog.config[guild_id]  # type: dict
    channel_id = str(ctx.channel.id)

    if channel_id in conf and cmd in conf[channel_id]:
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
            if ctx.channel.permissions_for(ctx.author).manage_messages:
                if "effect_mods" in ctx.bot.restricted[guild_id]:
                    return False
            else:
                return False
    return True
