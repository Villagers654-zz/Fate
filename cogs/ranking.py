# Customizable xp ranking system

from os import path
import os
import json
from time import time, monotonic
from random import *
import asyncio

from discord.ext import commands
import discord

from utils import colors


class Ranking(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './static/xp.json'
		self.globals = [
			'msg', 'monthly_msg', 'vc', 'monthly_vc'
		]

		if not path.exists('xp'):
			os.mkdir('xp')
			os.mkdir(path.join('xp', 'global'))
			os.mkdir(path.join('xp', 'guilds'))
			for filename in self.globals:
				with open(path.join('xp', 'global', filename) + '.json', 'w') as f:
					json.dump({}, f, ensure_ascii=False)

		self.msg = self._global('msg')
		self.monthly_msg = self._global('monthly_msg')
		self.vc = self._global('vc')
		self.monthly_vc = self._global('monthly_vc')

		self.guilds = {}
		for directory in os.listdir(path.join('xp', 'guilds')):
			if directory.isdigit():
				self.guilds[directory] = {}
				for filename in os.listdir(path.join('xp', 'guilds', directory)):
					if '.json' in filename:
						with open(path.join('xp', 'guilds', directory, filename), 'r') as f:
							self.guilds[directory][filename.replace('.json', '')] = json.load(f)

		self.msg_cooldown = 10
		self.cd = {}
		self.global_cd = {}
		self.macro_cd = {}
		self.counter = 0
		self.backup_counter = 0
		self.config = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)

	def _global(self, Global) -> dict:
		""" Returns data for each global leaderboard """
		with open(path.join('xp','global', Global) + '.json', 'r') as f:
			return json.load(f)

	def save_config(self):
		""" Saves per-server configuration """
		with open(self.path, 'w') as f:
			json.dump(self.config, f)

	def static_config(self):
		""" Default config """
		return {
			"min_xp_per_msg": 1,
			"max_xp_per_msg": 1,
			"base_level_xp_req": 100,
			"timeframe": 10,
			"msgs_within_timeframe": 1
		}

	def init(self, guild_id: str):
		""" Saves static config as the guilds initial config """
		self.config[guild_id] = self.static_config()
		self.save_config()

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.guild and not msg.author.bot:
			guild_id = str(msg.guild.id)
			user_id = str(msg.author.id)
			guild_path = path.join('xp', 'guilds', guild_id)

			before = monotonic()

			conf = self.static_config()  # type: dict
			if guild_id in self.config:
				conf = self.config[guild_id]
			xp = randint(conf['min_xp_per_msg'], conf['max_xp_per_msg'])

			# global leveling
			if user_id not in self.global_cd:
				self.global_cd[user_id] = 0
			if self.global_cd[user_id] < time() - 10:
				if user_id not in self.msg:
					self.msg[user_id] = 0
				if user_id not in self.monthly_msg:
					self.monthly_msg[user_id] = {}

				self.msg[user_id] += xp
				self.monthly_msg[user_id][str(time())] = xp

				self.counter += 1
				if self.counter >= 10:
					with open(path.join('xp', 'global', 'msg.json'), 'w') as f:
						json.dump(self.msg, f, ensure_ascii=False)
					with open(path.join('xp', 'global', 'monthly_msg.json'), 'w') as f:
						json.dump(self.monthly_msg, f, ensure_ascii=True)
					self.counter = 0

			# per-server leveling
			if guild_id not in self.cd:
				self.cd[guild_id] = {}
			if user_id not in self.cd[guild_id]:
				self.cd[guild_id][user_id] = []
			msgs = [x for x in self.cd[guild_id][user_id] if x > time() - conf['timeframe']]
			if len(msgs) < conf['msgs_within_timeframe']:
				self.cd[guild_id][user_id].append(time())
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

				self.guilds[guild_id]['msg'][user_id] += xp
				self.guilds[guild_id]['monthly_msg'][user_id][str(time())] = xp

				with open(path.join(guild_path, 'msg.json'), 'w') as f:
					json.dump(self.guilds[guild_id]['msg'], f, ensure_ascii=False)
				with open(path.join(guild_path, 'monthly_msg.json'), 'w') as f:
					json.dump(self.guilds[guild_id]['monthly_msg'], f, ensure_ascii=False)

				self.backup_counter += 1
				if self.backup_counter > 25:
					if not path.exists(path.join(guild_path, 'backup')):
						os.mkdir(path.join(guild_path, 'backup'))
					for filename in os.listdir(guild_path):
						if '.' in filename:
							with open(path.join(guild_path, filename), 'r') as rf:
								with open(path.join(guild_path, 'backup', filename), 'w') as wf:
									wf.write(rf.read())
					self.backup_counter = 0

			ping = (monotonic() - before) * 1000
			print(f'Took {round(ping)}ms')

	@commands.command(name='test-lb')
	async def test_leaderboard(self, ctx):
		e = discord.Embed(color=colors.purple())
		e.set_author(name='Test Leaderboard', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.description = ''
		rank = 1
		for user_id, xp in sorted(self.msg.items(), key=lambda kv: kv[1], reverse=True)[:15]:
			user = await self.bot.fetch_user(int(user_id))
			e.description += f"**#{rank}.** `{user.name}` - {xp}\n"
			rank += 1
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Ranking(bot))
