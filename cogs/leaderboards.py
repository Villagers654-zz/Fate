from datetime import datetime, timedelta
from discord.ext import commands
from utils import checks
from os.path import isfile
from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
from time import time, monotonic
import discord
import asyncio
import random
import json
import os

class Leaderboards(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.cd = {}
		self.cleaning = False
		self.spam_cd = {}
		self.macro_cd = {}
		self.global_data = {}
		self.guilds_data = {}
		self.monthly_global_data = {}
		self.monthly_guilds_data = {}
		self.gvclb = {}
		self.vclb = {}
		self.cache = {}
		if isfile("./data/userdata/xp.json"):
			with open("./data/userdata/xp.json", "r") as infile:
				dat = json.load(infile)
				if "global" in dat and "guilded" in dat:
					self.global_data = dat["global"]
					self.guilds_data = dat["guilded"]
					self.monthly_global_data = dat["monthly_global"]
					self.monthly_guilds_data = dat["monthly_guilded"]
					self.vclb = dat["vclb"]
					self.gvclb = dat["gvclb"]

	async def xp_dump_task(self):
		while True:
			try:
				with open("./data/userdata/xp.json", "w") as outfile:
					json.dump({"global": self.global_data, "guilded": self.guilds_data, "monthly_global": self.monthly_global_data,
				               "monthly_guilded": self.monthly_guilds_data, "vclb": self.vclb, "gvclb": self.gvclb},
					          outfile, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
				await asyncio.sleep(60)
			except Exception as e:
				try:
					log = self.bot.get_channel(501871950260469790)
					await log.send(f'Error saving xp: {e}')
				except:
					pass
				await asyncio.sleep(60)

	def msg_footer(self):
		return random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready",
		    "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme",
		                      "Powered by doritos", "Cooldown: 10 seconds", '[result]'])

	def vc_footer(self):
		return random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready",
		    "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by tostitos"])

	async def subtract_spam_from_monthly(self, guild_id, user_id):
		deleted = 0
		for msg_id, msg_time in (sorted(self.monthly_global_data[user_id].items(), key=lambda kv: kv[1], reverse=True)):
			if float(msg_time) > time() - 60:
				del self.monthly_global_data[user_id][str(msg_id)]
				deleted += 1
		for msg_id, msg_time in (sorted(self.monthly_guilds_data[guild_id][user_id].items(), key=lambda kv: kv[1], reverse=True)):
			if float(msg_time) > time() - 60:
				del self.monthly_guilds_data[guild_id][user_id][str(msg_id)]
		return deleted

	async def run_xp_cleanup(self):
		before = monotonic()
		for user_id in self.monthly_global_data.keys():
			for msg_id, msg_time in (sorted(self.monthly_global_data[user_id].items(), key=lambda kv: kv[1], reverse=True)):
				if float(msg_time) < time() - 2592000:
					del self.monthly_global_data[user_id][str(msg_id)]
		for guild_id in self.monthly_guilds_data.keys():
			for user_id in self.monthly_guilds_data[guild_id].keys():
				for msg_id, msg_time in (sorted(self.monthly_guilds_data[guild_id][user_id].items(), key=lambda kv: kv[1], reverse=True)):
					if float(msg_time) < time() - 2592000:
						del self.monthly_guilds_data[guild_id][user_id][str(msg_id)]
		for guild in self.bot.guilds:
			if guild.unavailable:
				return
		for user_id in list(self.global_data.keys()):
			user = self.bot.get_user(int(user_id))
			if not isinstance(user, discord.User):
				del self.global_data[user_id]
				for guild_id in list(self.guilds_data.keys()):
					if user_id in self.guilds_data[guild_id]:
						del self.guilds_data[guild_id][user_id]
				if user_id in self.monthly_global_data:
					del self.monthly_global_data[user_id]
				for guild_id in list(self.monthly_guilds_data.keys()):
					if user_id in self.monthly_guilds_data[guild_id]:
						del self.monthly_guilds_data[guild_id][user_id]
				if user_id in self.gvclb:
					del self.gvclb[user_id]
				for guild_id in list(self.vclb.keys()):
					if user_id in self.vclb[guild_id]:
						del self.vclb[guild_id][user_id]
		return str(round((monotonic() - before) * 1000)) + 'ms'

	@commands.command(name="leaderboard", aliases=["lb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def leaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.title = "Leaderboard"
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		if ctx.guild.icon_url:
			e.set_thumbnail(url=ctx.guild.icon_url)
		else:
			e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="gleaderboard", aliases=["glb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def gleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.title = 'Global Leaderboard'
		e.description = ''
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = 'INVALID-USER'
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="ggleaderboard", aliases=["gglb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def ggleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.title = 'Guild Leaderboard'
		e.description = ""
		rank = 1
		for guild_id, xp in (sorted({i:sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
			name = "INVALID-GUILD"
			guild = self.bot.get_guild(int(guild_id))
			if isinstance(guild, discord.Guild):
				name = guild.name
			else:
				del self.guilds_data[guild_id]
			e.description += f'**#{rank}.** `{name}`: {xp}\n'
			rank += 1
		if ctx.guild.icon_url:
			e.set_thumbnail(url=ctx.guild.icon_url)
		else:
			e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="mleaderboard", aliases=["mlb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _mleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		guild_id = str(ctx.guild.id)
		xp = {}
		for user in list(self.monthly_guilds_data[guild_id]):
			xp[user] = len(self.monthly_guilds_data[guild_id][user])
		e = discord.Embed(title="Monthly Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		if ctx.guild.icon_url:
			e.set_thumbnail(url=ctx.guild.icon_url)
		else:
			e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="gmleaderboard", aliases=["gmlb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _gmleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		xp = {}
		for user in list(self.monthly_global_data):
			xp[user] = len(self.monthly_global_data[user])
		e = discord.Embed(color=0x4A0E50)
		e.title = 'Global Monthly Leaderboard'
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = 'INVALID-USER'
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name='vcleaderboard', aliases=['vclb'])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def vcleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.title = 'VC Leaderboard'
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.vclb[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			e.description += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
			rank += 1
		if ctx.guild.icon_url:
			e.set_thumbnail(url=ctx.guild.icon_url)
		else:
			e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="gvcleaderboard", aliases=["gvclb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def gvcleaderboard(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.title = 'Global VC Leaderboard'
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.gvclb.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			e.description += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
			rank += 1
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name='leaderboards', aliases=['lbs'])
	async def leaderboards(self, ctx):
		result = await self.run_xp_cleanup()
		e = discord.Embed(color=0x4A0E50)
		e.set_author(name='Leaderboard')
		e.set_thumbnail(url=self.bot.user.avatar_url)
		leaderboard = ''
		rank = 1
		for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			leaderboard += f'**#{rank}.** `{name}`: {level} | {xp}\n'
		e.description = leaderboard
		gleaderboard = ''
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = 'INVALID-USER'
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			gleaderboard += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		e.add_field(name='Global Leaderboard', value=gleaderboard, inline=False)
		ggleaderboard = ''
		rank = 1
		for guild_id, xp in (sorted({i: sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
			name = "INVALID-GUILD"
			guild = self.bot.get_guild(int(guild_id))
			if isinstance(guild, discord.Guild):
				name = guild.name
			else:
				del self.guilds_data[guild_id]
			ggleaderboard += f'**#{rank}.** `{name}`: {xp}\n'
			rank += 1
		e.add_field(name='Guild Leaderboard', value=ggleaderboard, inline=False)
		mleaderboard = ''
		guild_id = str(ctx.guild.id)
		xp = {}
		for user in list(self.monthly_guilds_data[guild_id]):
			xp[user] = len(self.monthly_guilds_data[guild_id][user])
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			mleaderboard += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		e.add_field(name='Monthly Leaderboard', value=mleaderboard, inline=False)
		gmleaderboard = ''
		xp = {}
		for user in list(self.monthly_global_data):
			xp[user] = len(self.monthly_global_data[user])
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = 'INVALID-USER'
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			gmleaderboard += f'**#{rank}.** `{name}`: {level} | {xp}\n'
			rank += 1
		e.add_field(name='Global Monthly Leaderboard', value=gmleaderboard, inline=False)
		vcleaderboard = ''
		rank = 1
		for user_id, xp in (sorted(self.vclb[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			vcleaderboard += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
			rank += 1
		e.add_field(name='VC Leaderboard', value=vcleaderboard, inline=False)
		gvcleaderboard = ''
		rank = 1
		for user_id, xp in (sorted(self.gvclb.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			gvcleaderboard += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
			rank += 1
		e.add_field(name='Global VC Leaderboard', value=gvcleaderboard, inline=False)
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
		await ctx.send(embed=e)

	@commands.command(name="card")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _card(self, ctx):
		leaderboard = ""
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				filter = list('abcdefghijklmnopqrstuvwxyz1234567890 ')
				name = ""
				for char in list(user.name):
					if char.lower() in filter:
						name += char
				check = True
				for char in list(name):
					if char != " ":
						check = False
				if check:
					name = "Unknown"
			level = str(xp / 750)
			level = level[:level.find(".")]
			leaderboard += "‎#‎{}. ‎{}‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
		card = Image.new("RGBA", (1024, 1024), (255, 255, 255))
		img = Image.open('./data/images/backgrounds/galaxy.jpg').convert("RGBA")
		img = img.resize((1024, 1024), Image.BICUBIC)
		card.paste(img, (0, 0, 1024, 1024), img)
		card.save("./data/images/backgrounds/galaxy.png", format="png")
		img = Image.open('./data/images/backgrounds/galaxy.png')
		draw = ImageDraw.Draw(img)
		font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 60)
		def large(size):
			return ImageFont.truetype("./utils/fonts/Fitamint Script.ttf", size)
		draw.text((25, 25), "Global Leaderboard", (255, 255, 255), font=large(150))
		draw.text((5, 220), leaderboard, (255, 255, 255), font=font)
		img = img.convert("RGB")
		img.save('./data/images/backgrounds/results/galaxy.png')
		e = discord.Embed(color=0x4A0E50)
		e.set_image(url="attachment://" + os.path.basename('/data/images/backgrounds/results/galaxy.png'))
		await ctx.send(file=discord.File('./data/images/backgrounds/results/galaxy.png',
		    filename=os.path.basename('/data/images/backgrounds/results/galaxy.png')), embed=e)

	@commands.command(name='giv')
	@commands.check(checks.luck)
	async def giv(self, ctx, user: discord.Member, seconds: int):
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		self.vclb[guild_id][user_id] += seconds
		self.gvclb[user_id] += seconds
		await ctx.send('👍')

	@commands.command(name='take')
	@commands.check(checks.luck)
	async def take(self, ctx, user: discord.Member, seconds: int):
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		self.vclb[guild_id][user_id] -= seconds
		self.gvclb[user_id] -= seconds
		await ctx.send('👍')

	@commands.Cog.listener()
	async def on_ready(self):
		await asyncio.sleep(1)
		await self.bot.loop.create_task(self.xp_dump_task())
		await self.run_xp_cleanup()

	@commands.Cog.listener()
	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):
			if not m.author.bot:

				author_id = str(m.author.id)
				user_id = str(m.author.id)
				guild_id = str(m.guild.id)
				msg_id = str(m.id)

				# anti spam
				now = int(time() / 5)
				if guild_id not in self.spam_cd:
					self.spam_cd[guild_id] = {}
				if author_id not in self.spam_cd[guild_id]:
					self.spam_cd[guild_id][user_id] = [now, 0]
				if self.spam_cd[guild_id][user_id][0] == now:
					self.spam_cd[guild_id][user_id][1] += 1
				else:
					self.spam_cd[guild_id][user_id] = [now, 0]
				if self.spam_cd[guild_id][user_id][1] > 2:
					if m.author.id != 264838866480005122:
						self.cd[user_id] = time() + 600
						count = await self.subtract_spam_from_monthly(guild_id, user_id)
						self.global_data[user_id] -= count
						self.guilds_data[guild_id][user_id] -= count
						print(f"{m.author} is spamming")

				# anti macro
				if user_id not in self.macro_cd:
					self.macro_cd[user_id] = {}
					self.macro_cd[user_id]['intervals'] = []
				if 'last' not in self.macro_cd[user_id]:
					self.macro_cd[user_id]['last'] = datetime.now()
				else:
					last = self.macro_cd[user_id]['last']
					self.macro_cd[user_id]['intervals'].append((datetime.now() - last).seconds)
					intervals = self.macro_cd[user_id]['intervals']
					self.macro_cd[user_id]['intervals'] = intervals[-3:]
					if len(intervals) > 2:
						if all(interval == intervals[0] for interval in intervals):
							if m.author.id != 264838866480005122:
								self.cd[user_id] = time() + 600
								count = await self.subtract_spam_from_monthly(guild_id, user_id)
								self.global_data[user_id] -= count
								self.guilds_data[guild_id][user_id] -= count
								print(f"{m.author} is using a macro")

				if user_id not in self.cd:
					self.cd[user_id] = 0
				if self.cd[user_id] < time():
					if guild_id not in self.guilds_data:
						self.guilds_data[guild_id] = {}
					if user_id not in self.guilds_data[guild_id]:
						self.guilds_data[guild_id][user_id] = 0
					if author_id not in self.global_data:
						self.global_data[author_id] = 0
					if author_id not in self.monthly_global_data:
						self.monthly_global_data[author_id] = {}
					if guild_id not in self.monthly_guilds_data:
						self.monthly_guilds_data[guild_id] = {}
					if author_id not in self.monthly_guilds_data[guild_id]:
						self.monthly_guilds_data[guild_id][author_id] = {}

					self.global_data[author_id] += 1
					self.guilds_data[guild_id][author_id] += 1
					self.monthly_global_data[author_id][msg_id] = time()
					self.monthly_guilds_data[guild_id][author_id][msg_id] = time()
					self.cd[author_id] = time() + 10

	@commands.Cog.listener()
	async def on_voice_state_update(self, user, before, after):
		if isinstance(user.guild, discord.Guild):
			guild_id = str(user.guild.id)
			channel_id = None  # type: discord.TextChannel
			if before.channel:
				channel_id = str(before.channel.id)
			if after.channel:
				channel_id = str(after.channel.id)
			user_id = str(user.id)
			if guild_id not in self.vclb:
				self.vclb[guild_id] = {}
			if user_id not in self.vclb[guild_id]:
				self.vclb[guild_id][user_id] = 0
			if user_id not in self.gvclb:
				self.gvclb[user_id] = 0
			if channel_id not in self.cache:
				self.cache[channel_id] = {}
				self.cache[channel_id]['members'] = {}
			def get_active_members(channel):
				members = []
				total = 0
				for member in channel.members:
					if not member.bot:
						total += 1
						state = member.voice
						if not state.mute and not state.self_mute:
							if not state.deaf and not state.self_deaf:
								members.append(member)
				return (members, total)
			async def wrap(channel):
				cid = str(channel.id)
				for member_id in list(self.cache[cid]['members'].keys()):
					seconds = (datetime.now() - self.cache[cid]['members'][member_id]).seconds
					self.vclb[guild_id][member_id] += seconds
					self.gvclb[member_id] += seconds
					del self.cache[cid]['members'][member_id]
					print(f'Removed {self.bot.get_user(int(member_id)).name} 1')
			async def run(channel):
				channel_id = str(channel.id)
				members, total = get_active_members(channel)
				if len(members) == 0 or len(members) == 1 and len(members) == total:
					return await wrap(channel)
				for member in channel.members:
					if member not in self.cache[channel_id]['members']:
						if not member.bot:
							member_id = str(member.id)
							if member_id not in self.cache[channel_id]['members']:
								self.cache[channel_id]['members'][member_id] = datetime.now()
								print(f'Added {self.bot.get_user(int(member_id)).name}')
			if before.channel and after.channel:
				if before.channel.id != after.channel.id:
					channel_id = str(before.channel.id)
					if user_id in self.cache[channel_id]['members']:
						seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
						self.vclb[guild_id][user_id] += seconds
						self.gvclb[user_id] += seconds
						del self.cache[channel_id]['members'][user_id]
						print(f'Removed {self.bot.get_user(int(user_id)).name} 2')
					await run(before.channel)
					await run(after.channel)
			if not after.channel:
				channel_id = str(before.channel.id)
				if user_id in self.cache[channel_id]['members']:
					seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
					self.vclb[guild_id][user_id] += seconds
					self.gvclb[user_id] += seconds
					del self.cache[channel_id]['members'][user_id]
					print(f'Removed {self.bot.get_user(int(user_id)).name} 3')
					await run(before.channel)
			if before.channel is not None:
				await run(before.channel)
			if after.channel is not None:
				await run(after.channel)

def setup(bot: commands.Bot):
	bot.add_cog(Leaderboards(bot))
