# Customizable xp ranking system

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

		self.msg = self._global('msg')
		self.monthly_msg = self._global('monthly')
		self.vc = self._global('vc')
		self.monthly_vc = self._global('monthly_vc')

		self.guilds = {}
		for directory in os.listdir('xp'):
			if directory.isdigit():
				for filename in os.listdir(path.join('xp', directory)):
					with open(path.join('xp', directory, filename), 'r') as f:
						self.guilds[filename.replace('.json', '')] = json.load(f)

		self.msg_cooldown = 10
		self.cd = {}
		self.macro_cd = {}
		self.counter = 0
		self.config = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)

	def _global(self, Global) -> dict:
		""" Returns data for each global leaderboard """
		with open(path.join('xp', Global) + '.json', 'r') as f:
			return json.load(f)

	def save_config(self):
		with open(self.path, 'w') as f:
			json.dump(self.config, f)

	def static_config(self):
		return {
			"min_xp_per_msg": 1,
			"max_xp_per_msg": 1,
			"base_level_xp_req": 100,
			"timeframe": 10,
			"msgs_within_timeframe": 1
		}

	def init(self, guild_id: str):
		self.config[guild_id] = self.static_config()
		self.save_config()

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.guild and not msg.author.bot:
			guild_id = str(msg.guild.id)
			user_id = str(msg.author.id)
			guild_path = path.join('xp', guild_id)

			conf = self.static_config()  # type: dict
			if guild_id in self.config:
				conf = self.config[guild_id]

			now = int(time() / conf['timeframe'])
			if guild_id not in self.cd:
				self.cd[guild_id] = {}
			if user_id not in self.cd[guild_id]:
				self.cd[guild_id][user_id] = [now, 0]
			if self.cd[guild_id][user_id][0] == now:
				self.cd[guild_id][user_id][1] += 1
			else:
				self.cd[guild_id][user_id] = [now, 0]
			if self.cd[guild_id][user_id][1] > conf['msgs_within_timeframe']:

				if user_id not in self.msg:
					self.msg[user_id] = 0
				if user_id not in self.monthly_msg:
					self.monthly_msg[user_id] = {}
				if not path.isdir(guild_path):
					os.mkdir(guild_path)
					for filename in self.globals:
						with open(path.join(guild_path, filename) + '.json', 'w') as f:
							json.dump({}, f, ensure_ascii=False)
					self.guilds[guild_id] = {
						Global: {} for Global in self.globals
					}
				if user_id not in self.guilds[guild_id]['msg']:
					self.guilds[guild_id]['msg'][user_id] = 0
				if user_id not in self.guilds[guild_id]['monthly_msg']:
					self.guilds[guild_id]['monthly_msg'][user_id] = {}

				xp = randint(conf['min_xp_per_msg'], conf['max_xp_per_msg'])
				self.msg[user_id] += xp
				self.monthly_msg[user_id][str(time())] = xp
				self.guilds[guild_id]['msg'] += xp
				self.guilds[guild_id]['monthly_msg'][str(time)] = xp

				with open(path.join(guild_path, 'msg.json'), 'w') as f:
					json.dump(self.guilds[guild_id]['msg'], f, ensure_ascii=False)
				with open(path.join(guild_path, 'monthly_msg.json', 'w')) as f:
					json.dump(self.guilds[guild_id]['monthly_msg'], f, ensure_ascii=False)

				self.counter += 1
				if self.counter >= 10:
					with open(path.join('xp', 'msg.json'), 'w') as f:
						json.dump(self.msg, f, ensure_ascii=False)
					with open(path.join('xp', 'msg.json'), 'w') as f:
						json.dump(self.monthly_msg, f, ensure_ascii=True)

def setup(bot):
	bot.add_cog(Ranking(bot))
