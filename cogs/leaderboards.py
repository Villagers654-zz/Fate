from datetime import datetime, timedelta
from utils.utils import bytes2human
from discord.ext import commands
from utils import checks, colors
from time import time, monotonic
from os.path import isfile
from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
import discord
import asyncio
import random
import psutil
import json
import os

config = {'channel_id': 510410941809033216, 'message': None}

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
		self.toggle = []
		self.role_rewards = {}
		if isfile('./data/userdata/rolerewards.json'):
			with open('./data/userdata/rolerewards.json', 'r') as f:
				dat = json.load(f)
				if 'role_rewards' in dat:
					self.role_rewards = dat['role_rewards']
				if 'toggle' in dat:
					self.toggle = dat['toggle']

	def save_data(self):
		with open('./data/userdata/rolerewards.json', 'w') as f:
			json.dump({'toggle': self.toggle, 'role_rewards': self.role_rewards}, f, ensure_ascii=False)

	def get_user(self, ctx, user):
		if user.startswith("<@"):
			for char in list(user):
				if char not in list('1234567890'):
					user = user.replace(str(char), '')
			return ctx.guild.get_member(int(user))
		else:
			user = user.lower()
			for member in ctx.guild.members:
				if user == member.name.lower():
					return member
			for member in ctx.guild.members:
				if user == member.display_name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.display_name.lower():
					return member
		return None

	async def get_role(self, ctx, name):
		if name.startswith("<@"):
			for char in list(name):
				if char not in list('1234567890'):
					name = name.replace(str(char), '')
			return ctx.guild.get_member(int(name))
		else:
			roles = []
			for role in ctx.guild.roles:
				if name == role.name.lower():
					roles.append(role)
			if not roles:
				for role in ctx.guild.roles:
					if name in role.name.lower():
						roles.append(role)
			if roles:
				if len(roles) == 1:
					return roles[0]
				index = 1
				role_list = ''
				for role in roles:
					role_list += f'{index} : {role.mention}\n'
					index += 1
				e = discord.Embed(color=colors.fate(), description=role_list)
				e.set_author(name='Multiple Roles Found')
				e.set_footer(text='Reply with the correct role number')
				embed = await ctx.send(embed=e)
				def pred(m):
					return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
				try:
					msg = await self.bot.wait_for('message', check=pred, timeout=60)
				except asyncio.TimeoutError:
					await ctx.send('Timeout error', delete_after=5)
					return await embed.delete()
				else:
					try: role = int(msg.content)
					except: return await ctx.send('Invalid response')
					if role > len(roles):
						return await ctx.send('Invalid response')
					await embed.delete()
					await msg.delete()
					return roles[role - 1]

	def get_level_info(self, total_xp):
		level = 0; level_xp = 0
		level_end_xp = round(250 * (level + 1) * 1.21)
		for xp in range(total_xp):
			if xp > 250 * (level + 1) * 1.21:
				level_xp = round(250 * (level + 1) * 1.21)
				level += 1
				level_end_xp = round(250 * (level + 1) * 1.21)
		return {'level': level, 'base_xp': level_xp, 'max_xp': level_end_xp}

	async def xp_dump_task(self):
		while True:
			try:
				with open("./data/userdata/xp.json", "w") as outfile:
					json.dump({"global": self.global_data, "guilded": self.guilds_data, "monthly_global": self.monthly_global_data,
				               "monthly_guilded": self.monthly_guilds_data, "vclb": self.vclb, "gvclb": self.gvclb},
					          outfile, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
			except Exception as e:
				try: await self.bot.get_channel(501871950260469790).send(f'Error saving xp: {e}')
				except: pass
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
				return 'Discord Outage'
		msg_list = list(self.global_data.keys())
		vc_list = list(self.gvclb.keys())
		for user_id in list(set(msg_list) | set(vc_list)):
			user = self.bot.get_user(int(user_id))
			if not isinstance(user, discord.User):
				if user_id in self.global_data:
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

	@commands.command(name='rank', aliases=['xp'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def rank(self, ctx, *, user=None):
		results = await self.run_xp_cleanup()
		if user:
			user = self.get_user(ctx, user)
			if not isinstance(user, discord.Member):
				return await ctx.send('User not found')
		else:
			user = ctx.author
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		guild_rank = 0
		for id, xp in (sorted(self.guilds_data[guild_id].items(), key=lambda kv: kv[1], reverse=True)):
			guild_rank += 1
			if user_id == id:
				break
		xp = self.guilds_data[guild_id][user_id]
		dat = self.get_level_info(xp)
		level = dat['level']
		base_xp = dat['base_xp']
		max_xp = dat['max_xp']
		e = discord.Embed(color=0x4A0E50)
		icon_url = self.bot.user.avatar_url
		if user.avatar_url:
			icon_url = user.avatar_url
		else:
			if ctx.guild.icon_url:
				icon_url = ctx.guild.icon_url
		e.set_author(name=user.display_name, icon_url=icon_url)
		e.description = f'__**Rank:**__ [`{guild_rank}`] __**Level:**__ [`{level}`] __**XP:**__ [`{xp - base_xp}/{max_xp - base_xp}`]\n' \
			f'__**Total XP:**__ [`{xp}`] __**Required:**__ [`{max_xp - xp}`]\n'
		e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {results}'))
		await ctx.send(embed=e)

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
			level = self.get_level_info(xp)['level']
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

	@commands.command(name='rolerewards', aliases=['rolereward'])
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(embed_links=True, manage_messages=True, manage_roles=True)
	async def rolerewards(self, ctx, *args):
		if not args:
			e = discord.Embed(color=colors.fate())
			u = '.rolerewards enable\n' \
			    '.rolerewards disable\n' \
			    '.rolerewards level rolename\n' \
			    '.rolerewards remove rolename\n' \
			    '.rolerewards config'
			e.description = u
			return await ctx.send(embed=e)
		guild_id = str(ctx.guild.id)
		if guild_id not in self.role_rewards:
			self.role_rewards[guild_id] = {}
		if args[0] == 'enable':
			if guild_id in self.toggle:
				return await ctx.send('Role rewards are already enabled')
			self.toggle.append(guild_id)
			if guild_id not in self.role_rewards:
				self.role_rewards[guild_id] = {}
			await ctx.send('Enabled role rewards')
			return self.save_data()
		if args[0] == 'disable':
			if guild_id not in self.toggle:
				return await ctx.send('Role rewards isn\'t enabled')
			index = self.toggle.index(guild_id)
			self.toggle.pop(index)
			await ctx.send('Disabled role rewards')
			return self.save_data()
		if args[0].isdigit():
			if not len(args) > 1:
				return await ctx.send('Role name is a required argument that is missing')
			role = await self.get_role(ctx, args[1].replace('`', ''))
			if not isinstance(role, discord.Role):
				return await ctx.send('Role not found')
			await ctx.send('Should this role be allowed to stack?\nReply with "yes", "no", or anything else to cancel')
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				return await ctx.send('Timeout error')
			else:
				msg.content = msg.content.lower()
				if 'yes' not in msg.content and 'no' not in msg.content:
					return await ctx.send('Canceled')
				if 'yes' in msg.content.lower():
					stacking = True
				else:
					stacking = False
				self.role_rewards[guild_id][args[0]] = {'role': role.id, 'stacking': str(stacking)}
				await ctx.send(f'Added {role.name}.')
				return self.save_data()
		if args[0] == 'remove':
			if guild_id not in self.role_rewards:
				return await ctx.send('This server currently doesn\'t have any roles added')
			if not len(args) > 1:
				return await ctx.send('Role name is a required argument that is missing')
			role = await self.get_role(ctx, args[1].replace('`', ''))
			if not isinstance(role, discord.Role):
				return await ctx.send('Role not found')
			for level, dat in list(self.role_rewards[guild_id].items()):
				if dat['role'] == role.id:
					del self.role_rewards[guild_id][level]
					await ctx.send(f'Removed {role.name}')
					return self.save_data()
			return await ctx.send('Role not in dat')
		if args[0] == 'config':
			if guild_id not in self.role_rewards:
				return await ctx.send('This server currently doesn\'t have any roles added')
			role_rewards = ''
			for level, dat in list(self.role_rewards[guild_id].items()):
				role = ctx.guild.get_role(dat['role'])
				if not role:
					del self.role_rewards[guild_id][level]
					self.save_data()
					continue
				role_rewards += f'{role.mention} - level {level}\n'
			if not role_rewards:
				return await ctx.send('No configured roles')
			e = discord.Embed(color=colors.fate())
			e.description = role_rewards
			return await ctx.send(embed=e)
		await ctx.send('Unknown option passed')

	@commands.command(name='giv')
	@commands.check(checks.luck)
	async def giv(self, ctx, user: discord.Member, xp: int):
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		self.guilds_data[guild_id][user_id] += xp
		await ctx.send('👍')

	@commands.command(name='take')
	@commands.check(checks.luck)
	async def take(self, ctx, user: discord.Member, xp: int):
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		self.guilds_data[guild_id][user_id] -= xp
		await ctx.send('👍')

	@commands.Cog.listener()
	async def on_ready(self):
		await asyncio.sleep(1)
		self.bot.loop.create_task(self.xp_dump_task())
		results = await self.run_xp_cleanup()
		print(f'XP Cleanup: {results}')

	@commands.Cog.listener()
	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):

			if m.channel.id == config['channel_id']:
				if m.author.id != self.bot.user.id:
					await asyncio.sleep(60)
					await m.delete()

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

					previous_level = str(self.get_level_info(self.guilds_data[guild_id][user_id])['level'])

					self.global_data[author_id] += 1
					self.guilds_data[guild_id][author_id] += 1
					self.monthly_global_data[author_id][msg_id] = time()
					self.monthly_guilds_data[guild_id][author_id][msg_id] = time()
					self.cd[author_id] = time() + 10

					new_level = str(self.get_level_info(self.guilds_data[guild_id][user_id])['level'])

					if previous_level != new_level:
						if guild_id in self.toggle:
							for level, dat in list(self.role_rewards[guild_id].items()):
								if int(level) < int(new_level):
									if bool(dat['stacking']):
										role = m.guild.get_role(dat['role'])
										if role not in m.author.roles:
											try: await m.author.add_roles(role)
											except: return await m.channel.send('Failed to give you your role rewards')
							if new_level in self.role_rewards[guild_id]:
								stacking = bool(self.role_rewards[guild_id][new_level]['stacking'])
								if not stacking:
									for level, dat in list(self.role_rewards[guild_id].items()):
										if not bool(dat['stacking']):
											role = m.guild.get_role(dat['role'])
											if not isinstance(role, discord.Role):
												del self.role_rewards[guild_id][level]
												self.save_data()
												continue
											if role in m.author.roles:
												try: await m.author.remove_roles(role)
												except: return await m.channel.send('Failed to give you your role reward')
								role_id = self.role_rewards[guild_id][new_level]['role']
								role = m.guild.get_role(role_id)
								if not isinstance(role, discord.Role):
									del self.role_rewards[guild_id][new_level]
									return self.save_data()
								try: await m.author.add_roles(role)
								except: return await m.channel.send('Failed to give you your role reward')
								e = discord.Embed(color=colors.fate())
								e.description = f'Congratulations {m.author.mention}, you unlocked {role.mention}'
								try: await m.channel.send(embed=e)
								except: await m.channel.send(f'Congratulations {m.author.mention}, you unlocked {role.name}')

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
