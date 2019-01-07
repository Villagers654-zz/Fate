import discord
from discord.ext import commands
import json
from os.path import isfile
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

	@commands.command(name="leaderboard", aliases=["lb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def leaderboard(self, ctx):
		embed = discord.Embed(title="Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for user_id, count in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			embed.description += "‎**‎#{}.** ‎`‎{}`: ‎{}\n".format(rank, name, count)
			rank += 1
			embed.set_thumbnail(url=ctx.guild.icon_url)
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 5 seconds"]))
		await ctx.send(embed=embed)

	@commands.command(name="gleaderboard", aliases=["glb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def gleaderboard(self, ctx):
		embed = discord.Embed(title="Global Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for user_id, count in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			embed.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{}\n".format(rank, name, count)
			rank += 1
			embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 10 seconds"]))
		await ctx.send(embed=embed)

	@commands.command(name="ggleaderboard", aliases=["gglb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def ggleaderboard(self, ctx):
		embed = discord.Embed(title="Guild Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for guild_id, count in (sorted({i:sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
			name = "INVALID-GUILD"
			guild = self.bot.get_guild(int(guild_id))
			if isinstance(guild, discord.Guild):
				name = guild.name
			embed.description += "**#{}.** `{}`: {}\n".format(rank, name, count)
			rank += 1
			embed.set_thumbnail(url=ctx.guild.icon_url)
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 10 seconds"]))
		await ctx.send(embed=embed)

	@commands.command()
	async def topguilds(self, ctx):
		e = discord.Embed(color=0x80b0ff)
		e.title = "Top Guildies"
		e.description = ""
		rank = 1
		for guild in sorted([[g.name, g.member_count] for g in self.bot.guilds], key=lambda k: k[1], reverse=True)[:8]:
			e.description += "**{}.** {}: `{}`\n".format(rank, guild[0], guild[1])
			rank += 1
		await ctx.send(embed=e)

	@commands.group(name='stats')
	@commands.check(luck)
	async def _stats(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	@_stats.command(name='setchannel')
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		if channel is None:
			self.statschannel = ctx.channel.id
		else:
			self.statschannel = channel
		with open("./data/config/stats.json", "w") as outfile:
			json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
		await ctx.message.delete()

	@_stats.command(name='start', aliases=['fix'])
	async def _start(self, ctx):
		self.bot.loop.create_task(self.stats())
		await ctx.message.delete()

	async def stats(self):
		while True:
			def bytes2human(n):
				symbols = ('GHz', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
				prefix = {}
				for i, s in enumerate(symbols):
					prefix[s] = 1 << (i + 1) * 10
				for s in reversed(symbols):
					if n >= prefix[s]:
						value = float(n) / prefix[s]
						return '%.1f%s' % (value, s)
				return "%sB" % n
			p = psutil.Process(os.getpid())
			botram = p.memory_full_info().rss
			ramused = psutil.virtual_memory().used
			storageused = psutil.disk_usage('/').used
			storagetotal = psutil.disk_usage('/').total
			cpufreqcurrent = psutil.cpu_freq().current
			cpufreqmax = psutil.cpu_freq().max
			channel = self.bot.get_channel(self.statschannel)
			e = discord.Embed(title="", color=0x4A0E50)
			e.description = "💎 Official 4B4T Server 💎"
			leaderboard = ""
			rank = 1
			for user_id, count in (sorted(self.guilds_data[str(channel.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:8]:
				name = "INVALID-USER"
				user = self.bot.get_user(int(user_id))
				if isinstance(user, discord.User):
					name = user.name
				leaderboard += f'‎**#‎{rank}.** `‎{name}`: ‎{count}\n'
				rank += 1
			e.set_thumbnail(url=channel.guild.icon_url)
			e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
			e.add_field(name="◈ Discord ◈", value=f'__**Founder**__: FrequencyX4\n__**Members**__: {channel.guild.member_count}', inline=False)
			e.add_field(name="Leaderboard", value=leaderboard, inline=False)
			e.add_field(
				name="◈ Memory ◈",
				value=f"__**Storage**__: [{bytes2human(storageused)}/{bytes2human(storagetotal)}]\n"
				f"__**RAM**__: **Global**: {bytes2human(ramused)} **Bot**: {bytes2human(botram)}\n"
				f"__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%\n"
				f"__**CPU Per Core**__: {[round(i) for i in psutil.cpu_percent(interval=1, percpu=True)]}\n"
				f"__**CPU Frequency**__: [{bytes2human(cpufreqcurrent)}/null]")
			date = os.popen('date')
			timestamp = date.read()
			e.set_footer(text=f'Updated: {timestamp}')
			statschannel = self.bot.get_channel(self.statschannel)
			try:
				message = await statschannel.get_message(self.statsmessage)
				await message.edit(embed=e)
			except Exception as e:
				preparing = discord.Embed()
				preparing.description = 'preparing stats..'
				msg = await statschannel.send(embed=preparing)
				self.statsmessage = msg.id
				with open("./data/config/stats.json", "w") as outfile:
					json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
			async for msg in statschannel.history(limit=5):
				greenid = "{}".format(self.statsmessage)
				redid = "{}".format(msg.id)
				if redid not in greenid:
					await msg.delete()
			await asyncio.sleep(25)

	@commands.command()
	async def ltr(self, ctx):
		await ctx.send(u"\u200E")

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.stats())

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
