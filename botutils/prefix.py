import discord
from discord.ext import commands
from .packages import resources


async def get_prefixes_async(bot, msg):
    default_prefix = commands.when_mentioned_or(".")(bot, msg)
    prefixes = []
    override = False

    guild_id = msg.guild.id if msg.guild else None
    user_id = msg.author.id

    if guild_id and guild_id in bot.guild_prefixes:
        prefixes.append(bot.guild_prefixes[guild_id]["prefix"])
        if bot.guild_prefixes[guild_id]["override"]:
            override = True

    if not override and user_id in bot.user_prefixes:
        prefixes.append(bot.user_prefixes[user_id]["prefix"])

    if not isinstance(msg.guild, discord.Guild):
        return prefixes if prefixes else default_prefix

    # Parse the wanted prefixes
    if not prefixes:
        return commands.when_mentioned_or(".")(bot, msg)
    return [
        *commands.when_mentioned(bot, msg),
        *prefixes
    ]


def get_prefixes(bot, msg):
    conf = resources.get_config()
    config = bot.config
    if msg.author.id == config["bot_owner_id"]:
        return commands.when_mentioned_or(".")(bot, msg)
    if "blocked" in conf:
        if msg.author.id in conf["blocked"]:
            return "lsimhbiwfefmtalol"
    else:
        bot.log("Blocked key was non existant")
    if not msg.guild:
        return commands.when_mentioned_or(".")(bot, msg)
    guild_id = str(msg.guild.id)
    if "restricted" not in conf:
        conf["restricted"] = {}
    if guild_id in conf["restricted"]:
        if msg.channel.id in conf["restricted"][guild_id]["channels"] and (
                not msg.channel.permissions_for(msg.author).manage_messages
        ):
            return "lsimhbiwfefmtalol"
    if "personal_prefix" not in conf:
        conf["personal_prefix"] = {}
    user_id = str(msg.author.id)
    if user_id in conf["personal_prefix"]:
        return commands.when_mentioned_or(conf["personal_prefix"][user_id])(
            bot, msg
        )
    if "prefix" not in conf:
        conf["prefix"] = {}
    prefixes = conf["prefix"]
    if guild_id not in prefixes:
        return commands.when_mentioned_or(".")(bot, msg)
    return commands.when_mentioned_or(prefixes[guild_id])(bot, msg)

