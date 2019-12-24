"""
Check functions for the bot
"""

import json
from os import path

from discord.ext import commands
import discord


def luck(ctx):
	return ctx.message.author.id in [264838866480005122, 355026215137968129]

def command_is_enabled():  # decorator check
	async def predicate(ctx):
		if not isinstance(ctx.guild, discord.Guild):
			return True

		guild_id = str(ctx.guild.id)
		file_path = './data/userdata/disabled_commands.json'

		if not path.isfile(file_path):
			with open(file_path, 'w') as f:
				json.dump({}, f, ensure_ascii=False)

		with open(file_path, 'r') as f:
			config = json.load(f)  # type: dict

		if guild_id not in config:
			return True  # command isn't disabled
		if ctx.command.name in config[guild_id]:
			await ctx.send("That command is disabled")
			return False

	return commands.check(predicate)
