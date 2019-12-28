"""

"""

from os import path
import os
import json
from time import time, monotonic
from random import *
import asyncio

from discord.ext import commands
import discord


class Ranking(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './static/xp.json'
		self.globals = [
			'msg', 'monthly_msg', 'vc', 'monthly_vc'
		]

		if not path.isdir('xp'):
			os.mkdir('xp')
			for filename in self.globals:
				with open(path.join('xp', filename) + '.json', 'w') as f:
					json.dump({}, f, ensure_ascii=False)

		self.msg_cooldown = 10
		self.cd = {}
		self.macro_cd = {}
		self.config = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)

	def _global(self) -> dict:
		""" Returns data for each global leaderboard """
		dicts = {}
		for filename in self.globals:
			with open(path.join('xp', filename) + '.json', 'r') as f:
				dicts[filename] = json.load(f)
		return dicts

	def save_config(self):
		with open(self.path, 'w') as f:
			json.dump(self.config, f)

	def init(self, guild_id: str):
		self.config[guild_id] = {
			"min_xp_per_msg": 1,
			"max_xp_per_msg": 1,
			"base_level_xp_req": 100,
			"cooldown": {
				"msgs": 1,
				"timeframe": 10
			}
		}
		self.save_config()

def setup(bot):
	bot.add_cog(Ranking(bot))
