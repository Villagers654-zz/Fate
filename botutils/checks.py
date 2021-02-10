"""
Check functions for the bot
"""

from discord.ext import commands
import discord


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
    guild_id = str(ctx.guild.id)
    if guild_id in ctx.bot.restricted:
        if ctx.channel.id in ctx.bot.restricted[guild_id]["channels"]:
            if not ctx.channel.permissions_for(ctx.author).manage_messages:
                return False
    return True
