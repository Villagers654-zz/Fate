import discord
from discord.ext import commands
import json
from os.path import isfile
import datetime
import time
import random
import asyncio
import os
import psutil

class Leaderboards:
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.guilds_data = {}
		self.global_data = {}
		self.cd = {}
		if isfile("./data/leaderboards.json"):
			with open("./data/leaderboards.json", "r") as infile:
				dat = json.load(infile)
				if "guilded" in dat and "global" in dat:
					self.guilds_data = dat["guilded"]
					self.global_data = dat["global"]
		self.statschannel = {}
		self.statsmessage = {}
		if isfile("./data/config/stats.json"):
			with open("./data/config/stats.json", "r") as infile:
				dat = json.load(infile)
				if "statschannel" in dat and "statsmessage" in dat:
					self.statschannel = dat["statschannel"]
					self.statsmessage = dat["statsmessage"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	async def on_message(self, message: discord.Message):
		if not message.author.bot:
			author_id = str(message.author.id)
			if isinstance(message.guild, discord.Guild):
				if author_id not in self.cd:
					self.cd[author_id] = 0
				if self.cd[author_id] < time.time():
							guild_id = str(message.guild.id)
							if guild_id not in self.guilds_data:
									self.guilds_data[guild_id] = {}
							if author_id not in self.guilds_data[guild_id]:
									self.guilds_data[guild_id][author_id] = 0
							if author_id not in self.global_data:
									self.global_data[author_id] = 0

							self.guilds_data[guild_id][author_id] += 1
							self.global_data[author_id] += 1
							self.cd[author_id] = time.time() + 10
			
			with open("./data/leaderboards.json", "w") as outfile:
				json.dump({"guilded": self.guilds_data, "global": self.global_data}, outfile, ensure_ascii=False)

def setup(bot: commands.Bot):
	bot.add_cog(Leaderboards(bot))
