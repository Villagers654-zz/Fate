from os.path import isfile
import json
import asyncio
import random
import requests
from time import time, monotonic
from datetime import datetime, timedelta
import os
from math import sqrt

from discord.ext import commands
import discord
from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
from io import BytesIO
from sympy import Symbol, solve, log

from utils import checks, colors, utils

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
					if 'monthly_global' in dat:
						self.monthly_global_data = dat["monthly_global"]
					if 'monthly_guilded' in dat:
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

	def calc_lvl(self, total_xp):
		def x(level):
			x = 1; y = 0.125; lmt = 3
			for i in range(level):
				if x >= lmt:
					y = y / 2
					lmt += 3
				x += y
			return x

		level = 0; levels = [[0, 250]]
		lvl_up = 1; sub = 0; progress = 0
		for xp in range(total_xp):
			requirement = 0
			for lvl, xp_req in levels:
				requirement += xp_req
			if xp > requirement:
				level += 1
				levels.append([level, 250 * x(level)])
				lvl_up = 250 * x(level)
				sub = requirement
			progress = xp - sub

		return {
			'level': round(level),
			'level_up': round(lvl_up),
			'xp': round(progress)
		}

	async def xp_dump_task(self):
		while True:
			try:
				before = monotonic()
				with open("./data/userdata/xp.json", "w") as outfile:
					json.dump({"global": self.global_data, "guilded": self.guilds_data, "monthly_global": self.monthly_global_data,
				               "monthly_guilded": self.monthly_guilds_data, "vclb": self.vclb, "gvclb": self.gvclb},
					          outfile, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
				print(f'Saved xp: {round((monotonic() - before) * 1000)}ms')
			except Exception as e:
				try: await self.bot.get_channel(501871950260469790).send(f'Error saving xp: {e}')
				except: pass
			await asyncio.sleep(3600)

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

	async def wait_for_dismissal(self, ctx, msg):
		def pred(m):
			return m.channel.id == ctx.channel.id and m.content.lower().startswith('k')
		try:
			reply = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			await asyncio.sleep(0.21)
			await ctx.message.delete()
			await asyncio.sleep(0.21)
			await msg.delete()
			await asyncio.sleep(0.21)
			await reply.delete()

	@commands.command(name='rank', aliases=['level', 'xp'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(attach_files=True)
	async def rank_card(self, ctx, user: discord.Member=None):
		if not user:
			user = ctx.author
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		guild_rank = 0
		for id, xp in (sorted(self.guilds_data[guild_id].items(), key=lambda kv: kv[1], reverse=True)):
			guild_rank += 1
			if user_id == id:
				break
		if user_id not in self.guilds_data[guild_id]:
			total_xp = 0
		else:
			total_xp = self.guilds_data[guild_id][user_id]
		dat = self.calc_lvl(total_xp)
		level = dat['level']; xp = dat['xp']
		max_xp = 250 if level == 0 else dat['level_up']
		length = ((100 * (xp / max_xp)) * 1024) / 100
		ranking = f'Rank: [{guild_rank}] Level: [{level}] XP: [{xp}/{max_xp}]\n\n' \
			f'Total XP: [{xp}] Required: [{max_xp - xp}]\n'
		def font(size):
			return ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", size)
		def add_corners(im, rad):
			circle = Image.new('L', (rad * 2, rad * 2), 0)
			draw = ImageDraw.Draw(circle)
			draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
			alpha = Image.new('L', im.size, 255)
			w, h = im.size
			alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
			alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
			alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
			alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
			im.putalpha(alpha)
			return im
		color = tuple(int(str(user.color).lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
		card = Image.new('RGBA', (1024, 256), color)
		gradient = Image.new('L', (1, 255))
		for y in range(255):
			gradient.putpixel((0, 254 - y), y)
		alpha = gradient.resize(card.size)
		card.putalpha(alpha)
		avatar = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert('RGBA')
		avatar = add_corners(avatar.resize((175, 175), Image.BICUBIC), 87)
		card.paste(avatar, (42, 42), avatar)
		draw = ImageDraw.Draw(card)
		draw.text((250, 65), ranking, (255, 255, 255), font=font(50))
		draw.line((0, 250, length, 250), fill=(255, 255, 255), width=10)
		draw.ellipse((42, 42, 218, 218), outline='black', width=6)
		card.save('rank.png', 'png')
		await ctx.send(file=discord.File('rank.png'))
		os.remove('rank.png')

	@commands.command(
		name='leaderboard',
		aliases=[
			'lb', 'mlb', 'vclb', 'glb', 'gmlb', 'gvclb', 'gglb', 'ggvclb',
			'mleaderboard', 'vcleaderboard', 'gleaderboard', 'gvcleaderboard',
			'ggleaderboard', 'ggvcleaderboard'
		]
	)
	@commands.cooldown(1, 60, commands.BucketType.user)
	@commands.cooldown(1, 3, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True, manage_messages=True, add_reactions=True)
	async def leaderboard(self, ctx):
		guild_id = str(ctx.guild.id)
		default = discord.Embed()
		default.description = 'Collecting Leaderboard Data..'
		result = await self.run_xp_cleanup()
		async def wait_for_reaction()->list:
			def check(reaction, user):
				return user == ctx.author
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except asyncio.TimeoutError:
				return [None, None]
			else:
				return [reaction, str(reaction.emoji)]
		def lb():
			e = discord.Embed(color=0x4A0E50)
			e.title = "Leaderboard"
			e.description = ""
			rank = 1
			for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
				name = "INVALID-USER"
				user = self.bot.get_user(int(user_id))
				if isinstance(user, discord.User):
					name = user.name
				level = self.calc_lvl(xp)['level']
				e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
				rank += 1
			if ctx.guild.icon_url:
				e.set_thumbnail(url=ctx.guild.icon_url)
			else:
				e.set_thumbnail(url=self.bot.user.avatar_url)
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e
		def glb():
			e = discord.Embed(color=0x4A0E50)
			e.title = 'Global Leaderboard'
			e.description = ''
			rank = 1
			for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
				name = 'INVALID-USER'
				user = self.bot.get_user(int(user_id))
				if isinstance(user, discord.User):
					name = user.name
				level = self.calc_lvl(xp)['level']
				e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
				rank += 1
			e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e
		def mlb():
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
				level = self.calc_lvl(xp)['level']
				e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
				rank += 1
			if ctx.guild.icon_url:
				e.set_thumbnail(url=ctx.guild.icon_url)
			else:
				e.set_thumbnail(url=self.bot.user.avatar_url)
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e
		def gmlb():
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
				level = self.calc_lvl(xp)['level']
				e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
				rank += 1
			e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e
		def gglb():
			e = discord.Embed(color=0x4A0E50)
			e.title = 'Guild Leaderboard'
			e.description = ""
			rank = 1
			for guild_id, xp in (sorted({i: sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
				guild = self.bot.get_guild(int(guild_id))
				if not isinstance(guild, discord.Guild):
					del self.guilds_data[guild_id]
					continue
				name = guild.name
				e.description += f'**#{rank}.** `{name}`: {xp}\n'
				rank += 1
			if ctx.guild.icon_url:
				e.set_thumbnail(url=ctx.guild.icon_url)
			else:
				e.set_thumbnail(url=self.bot.user.avatar_url)
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e
		def vclb():
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
			return e
		def gvclb():
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
			return e
		def ggvclb():
			e = discord.Embed(color=0x4A0E50)
			e.title = 'Guilded VC Leaderboard'
			e.description = ""
			dat = {}
			for guild_id in self.vclb.keys():
				dat[guild_id] = 0
				for xp in self.vclb[guild_id].values():
					dat[guild_id] += xp
			rank = 1
			index = 1
			for guild_id, xp in (sorted(dat.items(), key=lambda kv: kv[1], reverse=True)):
				name = "INVALID-GUILD"
				guild = self.bot.get_guild(int(guild_id))
				if isinstance(guild, discord.Guild):
					name = guild.name
				else:
					continue
				score = timedelta(seconds=xp)
				e.description += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
				rank += 1
				if index == 15:
					break
				index += 1
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
			return e

		with open('./data/config.json', 'r') as f:
			config = json.load(f)  # type: dict
		prefix = '.'  # default prefix
		if guild_id in config['prefix']:
			prefix = config['prefix'][guild_id]
		target = ctx.message.content.split()[0]
		aliases = [
			('lb', 'leaderboard'),
			('mlb', 'mleaderboard'),
			('vclb', 'vcleaderboard'),
			('glb', 'gleaderboard'),
			('gmlb', 'gmleaderboard'),
			('gvclb', 'gvcleaderboard'),
			('gglb', 'ggleaderboard'),
			('ggvclb', 'ggvcleaderboard')
		]
		for cmd, alias in aliases:
			if target == alias:
				target = cmd
		cut_length = len(target) - len(prefix)
		embed = eval(f'{target[-cut_length:]}()')
		msg = await ctx.send(embed=embed)
		await msg.add_reaction('🚀')
		reaction, emoji = await wait_for_reaction()
		await msg.clear_reactions()
		if not reaction:
			return
		if emoji != '🚀':
			return
		await msg.edit(embed=default)
		emojis = ['🏡', '⏮', '⏪', '⏩', '⏭']
		index = 0; sub_index = None
		embeds = [lb(), vclb(), glb(), gvclb(), mlb(), gmlb(), gglb(), ggvclb()]
		await msg.edit(embed=embeds[0])
		def index_check(index):
			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0
			return index

		for emoji in emojis:
			await msg.add_reaction(emoji)
			await asyncio.sleep(0.5)
		while True:
			reaction, emoji = await wait_for_reaction()
			if not reaction:
				return await msg.clear_reactions()
			if emoji == emojis[0]:  # home
				index = 0; sub_index = None
			if emoji == emojis[1]:
				index -= 2; sub_index = None
				if isinstance(embeds[index], list):
					sub_index = 0
			if emoji == emojis[2]:
				if isinstance(embeds[index], list):
					if not isinstance(sub_index, int):
						sub_index = len(embeds[index]) - 1
					else:
						if sub_index == 0:
							index -= 1; sub_index = None
							index = index_check(index)
							if isinstance(embeds[index], list):
								sub_index = len(embeds[index]) - 1
						else:
							sub_index -= 1
				else:
					index -= 1
					if isinstance(embeds[index], list):
						sub_index = len(embeds[index]) - 1
			if emoji == emojis[3]:
				if isinstance(embeds[index], list):
					if not isinstance(sub_index, int):
						sub_index = 0
					else:
						if sub_index == len(embeds[index]) - 1:
							index += 1; sub_index = None
							index = index_check(index)
							if isinstance(embeds[index], list):
								sub_index = 0
						else:
							sub_index += 1
				else:
					index += 1
					index = index_check(index)
					if isinstance(embeds[index], list):
						sub_index = 0
			if emoji == emojis[4]:
				index += 2; sub_index = None
				index = index_check(index)
				if isinstance(embeds[index], list):
					sub_index = 0
			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0
			if isinstance(embeds[index], list):
				if index == len(embeds) - 1:
					embeds[index][sub_index].set_footer(text='Last Page! You\'ve reached the end')
				await msg.edit(embed=embeds[index][sub_index])
			else:
				if index == len(embeds) - 1:
					embeds[index].set_footer(text='Last Page! You\'ve reached the end')
				await msg.edit(embed=embeds[index])
			await msg.remove_reaction(reaction, ctx.author)

	#@commands.command(name="oleaderboard", aliases=["olb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def oleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = "Leaderboard"
	#	e.description = ""
	#	rank = 1
	#	for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = "INVALID-USER"
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		level = self.calc_lvl(xp)['level']
	#		e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
	#		rank += 1
	#	if ctx.guild.icon_url:
	#		e.set_thumbnail(url=ctx.guild.icon_url)
	#	else:
	#		e.set_thumbnail(url=self.bot.user.avatar_url)
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name="gleaderboard", aliases=["glb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def gleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = 'Global Leaderboard'
	#	e.description = ''
	#	rank = 1
	#	for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = 'INVALID-USER'
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		level = self.calc_lvl(xp)['level']
	#		e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
	#		rank += 1
	#	e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name="ggleaderboard", aliases=["gglb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def ggleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = 'Guild Leaderboard'
	#	e.description = ""
	#	rank = 1
	#	for guild_id, xp in (sorted({i:sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
	#		guild = self.bot.get_guild(int(guild_id))
	#		if not isinstance(guild, discord.Guild):
	#			del self.guilds_data[guild_id]
	#			continue
	#		name = guild.name
	#		e.description += f'**#{rank}.** `{name}`: {xp}\n'
	#		rank += 1
	#	if ctx.guild.icon_url:
	#		e.set_thumbnail(url=ctx.guild.icon_url)
	#	else:
	#		e.set_thumbnail(url=self.bot.user.avatar_url)
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name="mleaderboard", aliases=["mlb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def _mleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	guild_id = str(ctx.guild.id)
	#	xp = {}
	#	for user in list(self.monthly_guilds_data[guild_id]):
	#		xp[user] = len(self.monthly_guilds_data[guild_id][user])
	#	e = discord.Embed(title="Monthly Leaderboard", color=0x4A0E50)
	#	e.description = ""
	#	rank = 1
	#	for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = "INVALID-USER"
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		level = self.calc_lvl(xp)['level']
	#		e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
	#		rank += 1
	#	if ctx.guild.icon_url:
	#		e.set_thumbnail(url=ctx.guild.icon_url)
	#	else:
	#		e.set_thumbnail(url=self.bot.user.avatar_url)
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name="gmleaderboard", aliases=["gmlb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def _gmleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	xp = {}
	#	for user in list(self.monthly_global_data):
	#		xp[user] = len(self.monthly_global_data[user])
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = 'Global Monthly Leaderboard'
	#	e.description = ""
	#	rank = 1
	#	for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = 'INVALID-USER'
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		level = self.calc_lvl(xp)['level']
	#		e.description += f'**#{rank}.** `{name}`: {level} | {xp}\n'
	#		rank += 1
	#	e.set_thumbnail(url='https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png')
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name='vcleaderboard', aliases=['vclb'])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def vcleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = 'VC Leaderboard'
	#	e.description = ""
	#	rank = 1
	#	for user_id, xp in (sorted(self.vclb[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = "INVALID-USER"
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		score = timedelta(seconds=xp)
	#		e.description += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
	#		rank += 1
	#	if ctx.guild.icon_url:
	#		e.set_thumbnail(url=ctx.guild.icon_url)
	#	else:
	#		e.set_thumbnail(url=self.bot.user.avatar_url)
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)
	#
	#@commands.command(name="gvcleaderboard", aliases=["gvclb"])
	#@commands.cooldown(1, 10, commands.BucketType.channel)
	#@commands.bot_has_permissions(embed_links=True)
	#async def gvcleaderboard(self, ctx):
	#	result = await self.run_xp_cleanup()
	#	e = discord.Embed(color=0x4A0E50)
	#	e.title = 'Global VC Leaderboard'
	#	e.description = ""
	#	rank = 1
	#	for user_id, xp in (sorted(self.gvclb.items(), key=lambda kv: kv[1], reverse=True))[:15]:
	#		name = "INVALID-USER"
	#		user = self.bot.get_user(int(user_id))
	#		if isinstance(user, discord.User):
	#			name = user.name
	#		score = timedelta(seconds=xp)
	#		e.description += f'‎**‎#{rank}.** ‎`‎{name}`: ‎{score}\n'
	#		rank += 1
	#	e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
	#	e.set_footer(text=self.msg_footer().replace('[result]', f'XP Cleanup: {result}'))
	#	msg = await ctx.send(embed=e)
	#	await self.wait_for_dismissal(ctx, msg)

	@commands.command(name='leaderboards', aliases=['lbs'])
	async def leaderboards(self, ctx):
		return await ctx.send('This command is currently disabled, xp is still being collected')
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
			level = self.calc_lvl(xp)['level']
			leaderboard += f'**#{rank}.** `{name}`: {level} | {xp}\n'
		e.description = leaderboard
		gleaderboard = ''
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = 'INVALID-USER'
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = self.calc_lvl(xp)['level']
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
			level = self.calc_lvl(xp)['level']
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
			level = self.calc_lvl(xp)['level']
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
		msg = await ctx.send(embed=e)
		await self.wait_for_dismissal(ctx, msg)

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
				return await ctx.send('Role rewards aren\'t enabled')
			index = self.toggle.index(guild_id)
			self.toggle.pop(index)
			await ctx.send('Disabled role rewards')
			return self.save_data()
		if args[0].isdigit():
			if not len(args) > 1:
				return await ctx.send('Role name is a required argument that is missing')
			role = await utils.get_role(ctx, args[1].replace('`', ''))
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
			role = await utils.get_role(ctx, args[1].replace('`', ''))
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
						self.cd[user_id] = time() + 60

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
								self.cd[user_id] = time() + 60

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

					previous_level = str(self.calc_lvl(self.guilds_data[guild_id][user_id])['level'])

					self.global_data[author_id] += 1
					self.guilds_data[guild_id][author_id] += 1
					self.monthly_global_data[author_id][msg_id] = time()
					self.monthly_guilds_data[guild_id][author_id][msg_id] = time()
					self.cd[author_id] = time() + 10

					new_level = str(self.calc_lvl(self.guilds_data[guild_id][user_id])['level'])

					if previous_level != new_level:
						if guild_id in self.toggle:
							for level, dat in list(self.role_rewards[guild_id].items()):
								if int(level) < int(new_level):
									if bool(dat['stacking']):
										role = m.guild.get_role(dat['role'])
										if role not in m.author.roles:
											try: await m.author.add_roles(role)
											except: return await m.channel.send('Failed to give you your role rewards')
											e = discord.Embed(color=colors.fate())
											e.description = f'Congratulations {m.author.mention}, you already unlocked {role.mention}, but here you go anyways'
											try: await m.channel.send(embed=e)
											except: await m.channel.send(f'Congratulations {m.author.mention}, you already unlocked {role.name}, but here you go anyways')
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
			if before.channel and after.channel:
				if before.channel.id != after.channel.id:
					channel_id = str(before.channel.id)
					if user_id in self.cache[channel_id]['members']:
						seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
						self.vclb[guild_id][user_id] += seconds
						self.gvclb[user_id] += seconds
						del self.cache[channel_id]['members'][user_id]
					await run(before.channel)
					await run(after.channel)
			if not after.channel:
				channel_id = str(before.channel.id)
				if user_id in self.cache[channel_id]['members']:
					seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
					self.vclb[guild_id][user_id] += seconds
					self.gvclb[user_id] += seconds
					del self.cache[channel_id]['members'][user_id]
					await run(before.channel)
			if before.channel is not None:
				await run(before.channel)
			if after.channel is not None:
				await run(after.channel)

def setup(bot: commands.Bot):
	bot.add_cog(Leaderboards(bot))
