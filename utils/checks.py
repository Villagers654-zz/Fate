"""
Check functions for the bot
"""

import json
from os import path

from discord.ext import commands
import discord


def luck(ctx):
	return ctx.message.author.id in [264838866480005122, 355026215137968129]

def command_is_enabled(ctx):
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

	cmd = ctx.command.name
	conf = config[guild_id]  # type: dict

	if cmd in conf['global']:
		return False
	channel_id = str(ctx.channel.id)
	if channel_id in conf['channels']:
		if cmd in conf['channels'][channel_id]:
			return False
	if ctx.channel.category:
		channel_id = str(ctx.channel.category.id)
		if channel_id in conf['categories']:
			if cmd in conf['categories'][channel_id]:
				return False
	return True
