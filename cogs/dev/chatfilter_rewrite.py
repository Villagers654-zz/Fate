import json
import re
from os import path

import discord
from discord.ext import commands


class ChatFilter(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dat = {}
		self.path = './data/userdata/chatfilter.json'
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.dat = json.load(f)  # type: dict

	def save_data(self):
		with open(self.path, 'w+') as f:
			json.dump(self.dat, f)

	def init(self, guild_id: str):
		self.dat[guild_id] = {
			'toggle': True,
			'modules': {
				'advertising': False
			},
			'phrases': []
		}

	@commands.Cog.listener()
	async def on_message(self, msg):
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			if guild_id in self.dat:
				if self.dat[guild_id]['toggle']:
					abcs = 'abcdefghijklmopqrstuvwxyz'
					for phrase in self.dat[guild_id]['phrases']:
						if any(str(c).lower() not in abcs for c in list(phrase)):
							msg.content = ''.join([c for c in list(msg.content) if c.lower() in abcs])
						if phrase.lower() in msg.content.lower():
							try:
								await msg.author.send(f"The phrase \"{phrase}\" is blacklisted :[")
							except discord.errors.Forbidden:
								pass
							return await msg.delete()
					if self.dat[guild_id]['modules']['advertising']:
						match = re.search('d{0,2}i{0,2}s{0,2}c{0,2}o{0,2}r{0,2}d.g{0,2}g', msg.content.lower().replace(' ', ''))

def setup(bot):
	bot.add_cog(ChatFilter(bot))
