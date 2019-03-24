from utils import bytes2human as p
from discord.ext import commands
from datetime import datetime
from os.path import isfile
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO
from PIL import Image
import traceback
import requests
import discord
import asyncio
import psutil
import json
import os

class Owner:
	def __init__(self, bot):
		self.bot = bot
		self.statschannel = {}
		self.statsmessage = {}
		if isfile("./data/userdata/config/stats.json"):
			with open("./data/userdata/config/stats.json", "r") as infile:
				dat = json.load(infile)
				if "statschannel" in dat and "statsmessage" in dat:
					self.statschannel = dat["statschannel"]
					self.statsmessage = dat["statsmessage"]

	def get(self):
		with open("./data/userdata/xp.json", "r") as f:
			return json.load(f)

	def global_data(self):
		return self.get()["global"]

	def guilds_data(self):
		return self.get()["guilded"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.group(name='stats')
	@commands.check(luck)
	async def _stats(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	@_stats.command(name="fix")
	@commands.check(luck)
	async def _fix(self, ctx):
		self.channel = ctx.channel.id
		msg = await ctx.send(embed=discord.Embed(description="Preparing stats.."))
		self.message = msg.id
		with open("./data/config/stats.json", "w") as outfile:
			json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
		self.bot.loop.create_task(self.stats())
		await ctx.message.delete()

	@_stats.command(name='setchannel')
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		if channel is None:
			self.statschannel = ctx.channel.id
		else:
			self.statschannel = channel
		with open("./data/config/stats.json", "w") as outfile:
			json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
		await ctx.message.delete()

	@_stats.command(name='start')
	async def _start(self, ctx):
		self.bot.loop.create_task(self.stats())
		await ctx.message.delete()

	async def stats(self):
		while True:
			try:
				channel = self.bot.get_channel(self.statschannel)
				e = discord.Embed(title="", color=0x4A0E50)
				e.description = "💎 Official 4B4T Server 💎"
				leaderboard = ""
				rank = 1
				for user_id, xp in (sorted(self.guilds_data()[str(channel.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:8]:
					name = "INVALID-USER"
					user = self.bot.get_user(int(user_id))
					if isinstance(user, discord.User):
						name = user.name
					level = str(xp / 750)
					level = level[:level.find(".")]
					leaderboard += "‎**‎#{}.** ‎`‎{}`: ‎{} | {}\n".format(rank, name, level, xp)
					rank += 1
				f = psutil.Process(os.getpid())
				try:
					cpufreqcurrent = p.bytes2human(psutil.cpu_freq().current)
				except:
					cpufreqcurrent = "unavailable"
				try:
					cpufreqmax = p.bytes2human(psutil.cpu_freq().max)
				except:
					cpufreqmax = "unavailable"
				e.set_thumbnail(url=channel.guild.icon_url)
				e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
				e.add_field(name="◈ Discord ◈", value=f'__**Founder**__: FrequencyX4\n__**Members**__: {channel.guild.member_count}', inline=False)
				e.add_field(name="Leaderboard", value=leaderboard, inline=False)
				e.add_field(name="◈ Memory ◈",
					value=f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
					f"__**RAM**__: **Global**: {p.bytes2human(psutil.virtual_memory().used)} **Bot**: {p.bytes2human(f.memory_full_info().rss)}\n"
					f"__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {f.cpu_percent(interval=1)}%\n"
					f"__**CPU Per Core**__: {[round(i) for i in psutil.cpu_percent(interval=1, percpu=True)]}\n"
					f"__**CPU Frequency**__: [{cpufreqcurrent}/{cpufreqmax}]")
				fmt = "%m-%d-%Y %I:%M%p"
				time = datetime.now()
				time = time.strftime(fmt)
				e.set_footer(text=f'Updated: {time}')
				statschannel = self.bot.get_channel(self.statschannel)
				try:
					message = await statschannel.get_message(self.statsmessage)
					await message.edit(embed=e)
				except Exception as e:
					preparing = discord.Embed()
					preparing.description = 'preparing stats..'
					msg = await statschannel.send(embed=preparing)
					self.statsmessage = msg.id
					with open("./data/userdata/config/stats.json", "w") as outfile:
						json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
				async for msg in statschannel.history(limit=3):
					stats_id = "{}".format(self.statsmessage)
					msg_id = "{}".format(msg.id)
					if stats_id not in msg_id:
						await msg.delete()
				await asyncio.sleep(60)
			except Exception as e:
				await self.bot.get_channel(534608853300412416).send(f"```{traceback.format_exc()}```{e}")

	async def arkadia_stats(self):
		while True:
			try:
				channel = self.bot.get_channel(540086847842549770)
				channels = 0
				for server in self.bot.guilds:
					for c in server.channels:
						channels += 1
				e = discord.Embed(title="", color=0x4A0E50)
				e.description = f"💎 {self.bot.user.name} 💎\n" \
				f"**Commands:** {len(self.bot.commands)}\n" \
				f"**Modules:** {len(self.bot.extensions)}\n" \
				f"**Servers:** {len(list(self.bot.guilds))}\n" \
				f"**Users:** {len(list(self.bot.users))}\n"
				leaderboard = ""
				rank = 1
				for user_id, xp in (sorted(self.guilds_data()[str(channel.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:8]:
					name = "INVALID-USER"
					user = self.bot.get_user(int(user_id))
					if isinstance(user, discord.User):
						name = user.name
					level = str(xp / 750)
					level = level[:level.find(".")]
					leaderboard += "‎**‎#{}.** ‎`‎{}`: ‎{} | {}\n".format(rank, name, level, xp)
					rank += 1
				e.set_thumbnail(url=channel.guild.icon_url)
				e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
				e.add_field(name="◈ Discord ◈", value=f'__**Owner**__: Luck\n__**Members**__: {channel.guild.member_count}', inline=False)
				fmt = "%m-%d-%Y %I:%M%p"
				time = datetime.now()
				time = time.strftime(fmt)
				e.set_footer(text=f'Updated: {time}')
				message = await channel.get_message(540096913995726848)
				await message.edit(embed=e)
				await asyncio.sleep(1500)
			except Exception as e:
				await self.bot.get_channel(534608853300412416).send(f"```{traceback.format_exc()}```{e}")

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.stats())
		self.bot.loop.create_task(self.arkadia_stats())

def setup(bot):
	bot.add_cog(Owner(bot))
