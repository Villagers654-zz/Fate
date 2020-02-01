# Customizable xp ranking system

from os import path
import os
import json
from time import time, monotonic
from random import *
import asyncio
from datetime import datetime, timedelta
import requests
from io import BytesIO
import aiosqlite

from discord.ext import commands
import discord
from PIL import Image, ImageFont, ImageDraw, ImageSequence

from utils import colors, utils


def profile_help():
	e = discord.Embed(color=colors.purple())
	e.add_field(
		name='.set title your_new_title',
		value='Changes the title field in your profile card',
		inline=False
	)
	e.add_field(
		name='.set background [optional-url]',
		value="You can attach a file while using the cmd, or put a link where it says optional-url. "
		      "If you don't do either, i'll reset your background to default (transparent)"
	)
	return e

class Ranking(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.db_path = './data/userdata/xp.db'
		self.path = './data/userdata/xp.json'
		self.profile_path = './data/userdata/profiles.json'

		self.msg_cooldown = 10
		self.cd = {}
		self.global_cd = {}
		self.macro_cd = {}
		self.counter = 0
		self.vc_counter = 0
		self.backup_counter = 0
		self.cache = {}
		# xp config
		self.config = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)
		# save storage
		for guild_id, config in list(self.config.items()):
			if config == self.static_config():
				del self.config[guild_id]
		# profile config
		self.profile = {}
		if path.isfile(self.profile_path):
			with open(self.profile_path, 'r') as f:
				self.profile = json.load(f)
		# vc caching
		self.vclb = {}
		self.vc_counter = 0
		self.write = {'global': False, 'guilded': False}

	# def _global(self, Global) -> dict:
	# 	""" Returns data for each global leaderboard """
	# 	try:
	# 		with open(path.join('xp', 'global', Global) + '.json', 'r') as f:
	# 			return json.load(f)
	# 	except json.JSONDecodeError:
	# 		with open(path.join('xp', 'global', 'backup', Global + '.json'), 'r') as f:
	# 			return json.load(f)

	def save_config(self):
		""" Saves per-server configuration """
		with open(self.path, 'w') as f:
			json.dump(self.config, f)

	def static_config(self):
		""" Default config """
		return {
			"min_xp_per_msg": 1,
			"max_xp_per_msg": 1,
			"first_lvl_xp_req": 250,
			"timeframe": 10,
			"msgs_within_timeframe": 1
		}

	def init(self, guild_id: str):
		""" Saves static config as the guilds initial config """
		self.config[guild_id] = self.static_config()
		self.save_config()

	def calc_lvl(self, total_xp, config):
		def x(level):
			x = 1; y = 0.125; lmt = 3
			for i in range(level):
				if x >= lmt:
					y = y / 2
					lmt += 3
				x += y
			return x

		lvl_req = config['first_lvl_xp_req']
		level = 0; levels = [[0, lvl_req]]
		lvl_up = 1; sub = 0; progress = 0
		for xp in range(total_xp):
			requirement = 0
			for lvl, xp_req in levels:
				requirement += xp_req
			if xp > requirement:
				level += 1
				levels.append([level, lvl_req * x(level)])
				lvl_up = lvl_req * x(level)
				sub = requirement
			progress = xp - sub

		return {
			'level': round(level),
			'level_up': round(lvl_up),
			'xp': round(progress)
		}

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.guild and not msg.author.bot:
			guild_id = str(msg.guild.id)
			user_id = msg.author.id

			conf = self.static_config()  # type: dict
			if guild_id in self.config:
				conf = self.config[guild_id]
			new_xp = randint(conf['min_xp_per_msg'], conf['max_xp_per_msg'])

			# global leveling
			if user_id not in self.global_cd:
				self.global_cd[user_id] = 0
			if self.global_cd[user_id] < time() - 10:
				while self.write['global']:
					await asyncio.sleep(0.21)
				self.write['global'] = True
				async with aiosqlite.connect('./data/userdata/global-xp.db') as db:
					await db.execute(f"PRAGMA journal_mode=WAL;")
					cursor = await db.execute(f"SELECT xp FROM msg WHERE user_id = {user_id} LIMIT 1;")
					dat = await cursor.fetchone()
					if not dat:
						await db.execute(f"INSERT INTO msg VALUES ({user_id}, 0);")
						dat = (0,)
					msg_xp = dat[0]  # type: int
					cursor = await db.execute(f"SELECT * FROM monthly_msg WHERE user_id = {user_id};")
					dat = await cursor.fetchall()
					monthly_xp = 0
					for user_id, msg_time, xp in dat:
						if msg_time > time() - 60*60*24*30:
							monthly_xp += msg_xp
						else:
							await db.execute(
								f"DELETE FROM monthly_msg WHERE msg_time = '{msg_time}' and user_id = {user_id};"
							)
					await db.execute(f"UPDATE msg SET xp = {msg_xp+new_xp} WHERE user_id = {user_id};")
					await db.execute(f"INSERT INTO monthly_msg VALUES ({user_id}, {time()}, {new_xp});")
					await db.commit()
				self.write['global'] = False

			# per-server leveling
			if guild_id not in self.cd:
				self.cd[guild_id] = {}
			if user_id not in self.cd[guild_id]:
				self.cd[guild_id][user_id] = []
			msgs = [x for x in self.cd[guild_id][user_id] if x > time() - conf['timeframe']]
			if len(msgs) < conf['msgs_within_timeframe']:
				while self.write['guilded']:
					await asyncio.sleep(0.21)
				self.write['guilded'] = True
				self.cd[guild_id][user_id].append(time())
				async with aiosqlite.connect('./data/userdata/msg-xp.db') as db:
					await db.execute("PRAGMA journal_mode=WAL;")
					await db.execute(f"CREATE TABLE IF NOT EXISTS '{guild_id}' (user_id int, xp int);")
					cursor = await db.execute(f"SELECT xp FROM '{guild_id}' WHERE user_id = {user_id};")
					dat = await cursor.fetchone()
					if not dat:
						await db.execute(f"INSERT INTO '{guild_id}' VALUES ({user_id}, 0);")
						dat = (0,)
					await db.execute(f"UPDATE '{guild_id}' SET xp = {new_xp+dat[0]} WHERE user_id = {user_id};")
					await db.commit()
				async with aiosqlite.connect('./data/userdata/monthly-xp.db') as db:
					await db.execute(f"PRAGMA journal_mode=WAL;")
					await db.execute(f"CREATE TABLE IF NOT EXISTS '{guild_id}' (user_id int, msg_time float, xp int);")
					await db.execute(f"INSERT INTO '{guild_id}' VALUES ({user_id}, {time()}, {new_xp});")
					await db.commit()
				self.write['guilded'] = False

	@commands.Cog.listener()
	async def on_voice_state_update(self, user, before, after):
		if isinstance(user.guild, discord.Guild):
			guild_id = str(user.guild.id)
			channel_id = None
			if before.channel:
				channel_id = str(before.channel.id)
			if after.channel:
				channel_id = str(after.channel.id)
			user_id = user.id
			if user_id not in self.vclb:
				self.vclb[user_id] = 0
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
					self.vclb[guild_id]['vc'][member_id] += seconds
					del self.cache[cid]['members'][member_id]
					await save()
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
			async def save():
				async with aiosqlite.connect('./data/userdata/global-xp.db') as db:
					await db.execute("PRAGMA journal_mode=WAL;")
					cursor = await db.execute(f"SELECT xp FROM vc WHERE user_id = {user_id} LIMIT 1;")
					dat = await cursor.fetchone()
					if not dat:
						await db.execute(f"INSERT INTO vc VALUES ({user_id}, 0);")
						dat = (0,)
					new_xp = self.vclb[user_id] + dat[0]
					await db.execute(f"UPDATE vc SET xp = {new_xp} WHERE user_id = {user_id};")
					await db.commit()
				async with aiosqlite.connect('./data/userdata/vc-xp.db') as db:
					await db.execute("PRAGMA journal_mode=WAL;")
					await db.execute(f"CREATE TABLE IF NOT EXISTS '{guild_id}' (user_id int, xp int);")
					cursor = await db.execute(f"SELECT xp FROM '{guild_id}' WHERE user_id = {user_id} LIMIT 1;")
					dat = await cursor.fetchone()
					if not dat:
						await db.execute(f"INSERT INTO '{guild_id}' VALUES ({user_id}, 0);")
						dat = (0,)
					new_xp = self.vclb[user_id] + dat[0]
					await db.execute(f"UPDATE '{guild_id}' SET xp = {new_xp} WHERE user_id = {user_id};")
					await db.commit()
			if before.channel and after.channel:
				if before.channel.id != after.channel.id:
					channel_id = str(before.channel.id)
					if user_id in self.cache[channel_id]['members']:
						seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
						self.vclb[user_id] += seconds
						del self.cache[channel_id]['members'][user_id]
						await save()
					await run(before.channel)
					await run(after.channel)
			if not after.channel:
				channel_id = str(before.channel.id)
				if user_id in self.cache[channel_id]['members']:
					seconds = (datetime.now() - self.cache[channel_id]['members'][user_id]).seconds
					self.vclb[user_id] += seconds
					del self.cache[channel_id]['members'][user_id]
					await save()
					await run(before.channel)
			if before.channel is not None:
				await run(before.channel)
			if after.channel is not None:
				await run(after.channel)

	@commands.command(name='xp-config')
	@commands.cooldown(*utils.default_cooldown())
	@commands.bot_has_permissions(embed_links=True)
	async def xp_config(self, ctx):
		""" Sends an overview for the current config """
		e = discord.Embed(color=0x4A0E50)
		e.set_author(name='XP Configuration', icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)
		conf = self.config[str(ctx.guild.id)]
		e.description = f"• Min XP Per Msg: {conf['min_xp_per_msg']}" \
		                f"\n• Max XP Per Msg: {conf['max_xp_per_msg']}" \
		                f"\n• Timeframe: {conf['timeframe']}" \
		                f"\n• Msgs Within Timeframe: {conf['msgs_within_timeframe']}" \
		                f"\n• First Lvl XP Req: {conf['first_lvl_xp_req']}"
		p = utils.get_prefix(ctx)
		e.set_footer(text=f"Use {p}set to adjust these settings")
		await ctx.send(embed=e)

	@commands.group(name='set')
	@commands.cooldown(*utils.default_cooldown())
	@commands.guild_only()
	async def set(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Set Usage', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			p = utils.get_prefix(ctx)  # type: str
			e.description = "`[]` = your arguments / setting"
			e.add_field(
				name='◈ Profile Stuff',
				value=f"{p}set title [new title]"
				      f"\n• `sets the title in your profile`"
				      f"\n{p}set background [optional_url]"
				      f"\n• `sets your profiles background img`",
				inline=False
			)
			e.add_field(
				name='◈ XP Stuff',
				value=f"{p}set min-xp-per-msg [amount]"
				      f"\n• `sets the minimum gained xp per msg`"
				      f"\n{p}set max-xp-per-msg [amount]"
				      f"\n• `sets the maximum gained xp per msg`"
				      f"\n{p}set timeframe [amount]"
				      f"\n• `sets the timeframe to allow x messages`"
				      f"\n{p}set msgs-within-timeframe [amount]"
				      f"\n• `sets the limit of msgs within the timeframe`"
				      f"\n{p}set first-lvl-xp-req [amount]"
				      f"\n• `required xp to level up your first time`",
				inline=False
			)
			e.set_footer(text=f"Use {p}xp-config to see xp settings")
			await ctx.send(embed=e)

	@set.command(name='title')
	async def _set_title(self, ctx, *, title):
		if len(title) > 32:
			return await ctx.send("There's a character limit is 22!")
		user_id = str(ctx.author.id)
		if user_id not in self.profile:
			self.profile[user_id] = {}
		self.profile[user_id]['title'] = title
		with open(self.profile_path, 'w+') as f:
			json.dump(self.profile, f)
		await ctx.send('Set your title')

	@set.command(name='background')
	async def _set_background(self, ctx, url=None):
		user_id = str(ctx.author.id)
		if user_id not in self.profile:
			self.profile[user_id] = {}
		if not url and not ctx.message.attachments:
			if 'background' not in self.profile[user_id]:
				return await ctx.send("You don't have a custom background")
			del self.profile[user_id]['background']
			with open(self.profile_path, 'w+') as f:
				json.dump(self.profile, f)
			return await ctx.send('Reset your background')
		if not url:
			url = ctx.message.attachments[0].url
		self.profile[user_id]['background'] = url
		with open(self.profile_path, 'w+') as f:
			json.dump(self.profile, f)
		await ctx.send('Set your background image')

	@set.command(name='min-xp-per-msg')
	@commands.has_permissions(administrator=True)
	async def _min_xp_per_msg(self, ctx, amount: int):
		""" sets the minimum gained xp per msg """
		guild_id = str(ctx.guild.id)
		self.config[guild_id]['min_xp_per_msg'] = amount
		await ctx.send(f"Set the minimum xp gained per msg to {amount}")
		if amount > self.config[guild_id]['max_xp_per_msg']:
			self.config[guild_id]['max_xp_per_msg'] = amount
			await ctx.send(f"I also upped the maximum xp per msg to {amount}")
		self.save_config()

	@set.command(name='max-xp-per-msg')
	@commands.has_permissions(administrator=True)
	async def _max_xp_per_msg(self, ctx, amount: int):
		""" sets the minimum gained xp per msg """
		guild_id = str(ctx.guild.id)
		self.config[guild_id]['max_xp_per_msg'] = amount
		await ctx.send(f"Set the maximum xp gained per msg to {amount}")
		if amount < self.config[guild_id]['max_xp_per_msg']:
			self.config[guild_id]['max_xp_per_msg'] = amount
			await ctx.send(f"I also lowered the minimum xp per msg to {amount}")
		self.save_config()

	@set.command(name='timeframe')
	@commands.has_permissions(administrator=True)
	async def _timeframe(self, ctx, amount: int):
		""" sets the timeframe to allow x messages """
		guild_id = str(ctx.guild.id)
		self.config[guild_id]['timeframe'] = amount
		await ctx.send(f"Set the timeframe that allows x messages to {amount}")
		self.save_config()

	@set.command(name='msgs-within-timeframe')
	@commands.has_permissions(administrator=True)
	async def _msgs_within_timeframe(self, ctx, amount: int):
		""" sets the limit of msgs within the timeframe """
		guild_id = str(ctx.guild.id)
		self.config[guild_id]['msgs_within_timeframe'] = amount
		await ctx.send(f"Set msgs within timeframe limit to {amount}")
		self.save_config()

	@set.command(name='first-lvl-xp-req')
	@commands.has_permissions(administrator=True)
	async def _first_level_xp_req(self, ctx, amount: int):
		""" sets the required xp to level up your first time """
		guild_id = str(ctx.guild.id)
		self.config[guild_id]['first_lvl_xp_req'] = amount
		await ctx.send(f"Set the required xp to level up your first time to {amount}")
		self.save_config()

	@commands.command(name='profile', aliases=['rank'], usage=profile_help())
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(attach_files=True)
	async def profile(self, ctx):
		""" Profile / Rank Image Card """
		def add_corners(im, rad):
			""" Adds transparent corners to an img """
			circle = Image.new('L', (rad * 2, rad * 2), 0)
			d = ImageDraw.Draw(circle)
			d.ellipse((0, 0, rad * 2, rad * 2), fill=255)
			alpha = Image.new('L', im.size, 255)
			w, h = im.size
			alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
			alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
			alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
			alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
			im.putalpha(alpha)
			return im

		def font(size):
			return ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", size)

		# core
		path = './static/card.png'
		user = ctx.author
		if ctx.message.mentions:
			user = ctx.message.mentions[0]
		user_id = str(user.id)
		guild_id = str(ctx.guild.id)

		# config
		title = 'Use .help profile'
		backgrounds = [
			'https://cdn.discordapp.com/attachments/632084935506788385/670258618750337024/unknown.png',  # gold
			'https://media.giphy.com/media/26n6FdRZBIjOCHpJK/giphy.gif'  # spinning blade effect
		]
		background_url = choice(backgrounds)
		if ctx.guild.splash:
			background_url = ctx.guild.splash_url
		if ctx.guild.banner:
			background_url = ctx.guild.banner_url
		if user_id in self.profile:
			if 'title' in self.profile[user_id]:
				title = self.profile[user_id]['title']
			if 'background' in self.profile[user_id]:
				background_url = self.profile[user_id]['background']

		# xp variables
		async with aiosqlite.connect('./data/userdata/msg-xp.db') as db:
			await db.execute("PRAGMA journal_mode=WAL;")
			cursor = await db.execute(f"SELECT * FROM '{guild_id}' ORDER BY xp DESC;")
			guild_xp = await cursor.fetchall()
			guild_rank = 0
			for i, (id, xp) in enumerate(guild_xp):
				if id == user.id:
					guild_rank = i + 1
					break
			cursor = await db.execute(f"SELECT xp FROM '{guild_id}' WHERE user_id = '{user.id}';")
			guild_xp = await cursor.fetchone()
		conf = self.config[guild_id]
		if 'global' in ctx.message.content:
			async with aiosqlite.connect('./data/userdata/global-xp.db') as db:
				await db.execute("PRAGMA journal_mode=WAL;")
				cursor = await db.execute(f"SELECT * FROM msg ORDER BY xp DESC;")
				global_xp = await cursor.fetchall()
				guild_rank = 0
				for i, (id, xp) in enumerate(global_xp):
					if id == user.id:
						guild_rank = i + 1
						break
				cursor = await db.execute(f"SELECT xp FROM msg WHERE user_id = '{user.id}';")
				guild_xp = await cursor.fetchone()
			if not guild_xp:
				return await ctx.send('somehow I have no xp for you .-.')
			dat = self.calc_lvl(guild_xp[0], self.static_config())
		else:
			if not guild_xp:
				return await ctx.send('somehow I have no xp for this server .-.')
			dat = self.calc_lvl(guild_xp[0], conf)
		base_req = self.config[guild_id]['first_lvl_xp_req']
		level = dat['level']
		xp = dat['xp']
		max_xp = base_req if level == 0 else dat['level_up']
		length = ((100 * (xp / max_xp)) * 1000) / 100
		total = f'Total: {guild_xp[0]}'
		required = f'Required: {max_xp - xp}'
		progress = f'{xp} / {max_xp} xp'
		misc = f'{progress} | {total} | {required}'

		# pick status icon
		statuses = {
			discord.Status.online: 'https://cdn.discordapp.com/emojis/659976003334045727.png?v=1',
			discord.Status.idle: 'https://cdn.discordapp.com/emojis/659976006030983206.png?v=1',
			discord.Status.dnd: 'https://cdn.discordapp.com/emojis/659976008627388438.png?v=1',
			discord.Status.offline: 'https://cdn.discordapp.com/emojis/659976011651219462.png?v=1'
		}
		status = statuses[user.status]
		if user.is_on_mobile():
			status = 'https://cdn.discordapp.com/attachments/541520201926311986/666182794665263124/1578900748602.png'

		# Prepare the profile card
		url = 'https://cdn.discordapp.com/attachments/632084935506788385/666158201867075585/rank-card.png'
		card = Image.open(BytesIO(requests.get(url).content))
		draw = ImageDraw.Draw(card)
		data = []
		for r, g, b, c in card.getdata():
			if c == 0:
				data.append((r, g, b, c))
			elif r == 0 and g == 174 and b == 239:  # blue
				data.append((r, g, b, 100))
			elif r == 48 and g == 48 and b == 48:  # dark gray
				data.append((r, g, b, 225))
			elif r == 218 and g == 218 and b == 218:  # light gray
				data.append((r, g, b, 150))
			else:
				data.append((r, g, b, c))
		card.putdata(data)

		# user vanity
		avatar = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert('RGBA')
		avatar = add_corners(avatar.resize((175, 175), Image.BICUBIC), 87)
		card.paste(avatar, (75, 85), avatar)
		draw.ellipse((75, 85, 251, 261), outline='black', width=6)
		status = Image.open(BytesIO(requests.get(status).content)).convert('RGBA')
		status = status.resize((75, 75), Image.BICUBIC)
		card.paste(status, (190, 190), status)

		# leveling / ranking
		rank_pos = [865, 85]
		rank_font = 30
		for i in range(len(str(guild_rank))):
			if i > 1:
				rank_pos[1] += 1
				rank_font -= 5
		draw.text(tuple(rank_pos), f'Rank #{guild_rank}', (255, 255, 255), font=font(rank_font))

		level_pos = [640, 145]
		text = f'Level {level}'
		for i in range(len(str(level))):
			if i == 1:
				text = f'Lvl. {level}'
				level_pos[0] += 15
			if i == 2:
				level_pos[0] -= 5
			if i == 3:
				level_pos[0] -= 5
		draw.text(tuple(level_pos), text, (0, 0, 0), font=font(100))

		draw.text((10, 320), title, (0, 0, 0), font=font(50))
		draw.text((25, 415), misc, (255, 255, 255), font=font(50))
		draw.line((0, 500, length, 500), fill=user.color.to_rgb(), width=10)

		# backgrounds and saving
		if background_url:
			background = Image.open(BytesIO(requests.get(background_url).content))
			if 'gif' in str(background_url):
				dur = background.info['duration']
				count = len(list(ImageSequence.Iterator(background)))
				skip = False
				skip_two = False
				skipped = 0
				frames = []
				index = 0
				for frame in ImageSequence.Iterator(background):
					if count > 40 and count < 100:
						if skip:
							skip = False
							continue
						elif skip_two:
							skip_two = False
							continue
						else:
							skip = True
							skip_two = True
					elif count > 100:
						skip = int(str(count)[:1]) + 2
						if skipped <= skip:
							skipped += 1
							continue
						else:
							skipped = 0

					frame = frame.convert('RGBA')
					frame = frame.resize((1000, 500), Image.BICUBIC)
					frame.paste(card, (0, 0), card)
					b = BytesIO()
					frame.save(b, format="GIF")
					frame = Image.open(b)
					frames.append(frame)
					index += 1
					if index == 50:
						break
				path = path.replace('png', 'gif')
				frames[0].save(path, save_all=True, append_images=frames[1:], loop=0, duration=dur, optimize=False)
			else:
				background = background.convert('RGBA')
				background = background.resize((1000, 500), Image.BICUBIC)
				background.paste(card, (0, 0), card)
				background.save(path, format='PNG')
		else:
			card.save(path, format='PNG')
		await ctx.send(f"> **Profile card for {user}**", file=discord.File(path))

	@commands.command(
		name='leaderboard',
		aliases = [
			'lb', 'mlb', 'vclb', 'glb', 'gmlb', 'gvclb', 'gglb', 'ggvclb', 'mleaderboard', 'vcleaderboard',
			'gleaderboard', 'gvcleaderboard', 'ggleaderboard', 'ggvcleaderboard'
		]
	)
	@commands.cooldown(*utils.default_cooldown())
	@commands.cooldown(1, 2, commands.BucketType.channel)
	@commands.cooldown(6, 60, commands.BucketType.guild)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True, manage_messages=True)
	async def leaderboard(self, ctx):
		""" Refined leaderboard command """
		async def wait_for_reaction():
			try:
				reaction, user = await self.bot.wait_for(
					'reaction_add', timeout=60.0, check=lambda r, u: u == ctx.author
				)
			except asyncio.TimeoutError:
				return [None, None]
			else:
				return [reaction, str(reaction.emoji)]

		def index_check(index):
			""" Ensures the index isn't too high or too low """
			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0
			return index

		async def add_emojis_task():
			""" So the bot can read reactions before all are added """
			for emoji in emojis:
				await msg.add_reaction(emoji)
				await asyncio.sleep(0.5)
			return

		async def create_embed(name: str, rankings: list, lmt, top_user=None):
			""" Gen a list of embed leaderboards """
			icon_url = None
			thumbnail_url = 'https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png'
			if top_user:
				user = self.bot.get_user(int(top_user))
				if isinstance(user, discord.User):
					icon_url = user.avatar_url
				else:
					guild = self.bot.get_guild(int(top_user))
					if isinstance(guild, discord.Guild):
						icon_url = guild.icon_url
			embeds = []
			e = discord.Embed(color=0x4A0E50)
			e.set_author(name=name, icon_url=icon_url)
			e.set_thumbnail(url=thumbnail_url)
			e.description = ''
			rank = 1; index = 0
			for user_id, xp in rankings:
				if index == lmt:
					embeds.append(e)
					e = discord.Embed(color=0x4A0E50)
					e.set_author(name=name, icon_url=icon_url)
					e.set_thumbnail(url=thumbnail_url)
					e.description = ''
					index = 0
				user = self.bot.get_user(int(user_id))
				if isinstance(user, discord.User):
					username = str(user)
				else:
					guild = self.bot.get_guild(int(user_id))
					if isinstance(guild, discord.Guild):
						username = guild.name
					else:
						username = 'INVALID'
				e.description += f"#{rank}. `{username}` - {xp}\n"
				rank += 1
				index += 1
			embeds.append(e)

			return embeds

		with open('./data/config.json', 'r') as f:
			config = json.load(f)  # type: dict
		prefix = '.'  # default prefix
		guild_id = str(ctx.guild.id)
		if guild_id in config['prefix']:
			prefix = config['prefix'][guild_id]
		target = ctx.message.content.split()[0]
		cut_length = len(target) - len(prefix)
		aliases = [
			('lb', 'leaderboard'),
			('vclb', 'vcleaderboard'),
			('glb', 'gleaderboard'),
			('gvclb', 'gvcleaderboard'),
			('mlb', 'mleaderboard'),
			('gmlb', 'gmleaderboard'),
			('gglb', 'ggleaderboard'),
			('ggvclb', 'ggvcleaderboard')
		]
		index = 0  # default
		for i, (cmd, alias) in enumerate(aliases):
			if target[-cut_length:] in [cmd, alias]:
				index = i
				break

		default = discord.Embed()
		default.description = 'Collecting Leaderboard Data..'
		msg = await ctx.send(embed=default)
		emojis = ['🏡', '⏮', '⏪', '⏩', '⏭']
		self.bot.loop.create_task(add_emojis_task())

		embeds = []
		guild_id = str(ctx.guild.id)
		leaderboards = {}
		async with aiosqlite.connect('./data/userdata/msg-xp.db') as db:
			await db.execute("PRAGMA journal_mode=WAL;")
			cursor = await db.execute("SELECT * FROM sqlite_master WHERE TYPE = 'table';")
			tables = await cursor.fetchall()
			tables = [i[1] for i in tables]
			msg_xp = {}
			for g_id in tables:
				cursor = await db.execute(f"SELECT * FROM '{g_id}' ORDER BY xp DESC;")
				dat = await cursor.fetchall()
				msg_xp[g_id] = {
					user_id: xp for user_id, xp in dat
				}
		leaderboards['Msg Leaderboard'] = {
			user_id: xp for user_id, xp in msg_xp[guild_id].items()
		}
		async with aiosqlite.connect('./data/userdata/vc-xp.db') as db:
			await db.execute("PRAGMA journal_mode=WAL;")
			cursor = await db.execute("SELECT * FROM sqlite_master WHERE TYPE = 'table';")
			tables = await cursor.fetchall()
			tables = [i[1] for i in tables]
			vc_xp = {}
			for g_id in tables:
				cursor = await db.execute(f"SELECT * FROM '{g_id}' ORDER BY xp DESC;")
				dat = await cursor.fetchall()
				vc_xp[g_id] = {
					user_id: xp for user_id, xp in dat
				}
		leaderboards['Vc Leaderboard'] = {
			user_id: timedelta(seconds=xp) for user_id, xp in vc_xp[guild_id].items()
		}
		async with aiosqlite.connect('./data/userdata/global-xp.db') as db:
			await db.execute("PRAGMA journal_mode=WAL;")
			cursor = await db.execute("SELECT * FROM msg ORDER BY xp DESC;")
			global_msg_xp = await cursor.fetchall()
			leaderboards['Global Msg Leaderboard'] = {
				user_id: xp for user_id, xp in global_msg_xp
			}
			cursor = await db.execute("SELECT * FROM vc ORDER BY xp DESC")
			global_vc_xp = await cursor.fetchall()
			leaderboards['Global Vc Leaderboard'] = {
				user_id: timedelta(seconds=xp) for user_id, xp in global_vc_xp
			}
			cursor = await db.execute("SELECT * FROM monthly_msg;")
			dat = await cursor.fetchall()
			global_monthly = {}
			for user_id, msg_time, xp in dat:
				if user_id not in global_monthly:
					global_monthly[user_id] = 0
				if msg_time > time() - 60*60*24*30:
					global_monthly[user_id] += 1
		async with aiosqlite.connect('./data/userdata/monthly-xp.db') as db:
			await db.execute("PRAGMA journal_mode=WAL;")
			cursor = await db.execute(f"SELECT * FROM '{guild_id}';")
			dat = await cursor.fetchall()
			monthly_msg = {}
			for user_id, msg_time, xp in dat:
				if user_id not in monthly_msg:
					monthly_msg[user_id] = 0
				monthly_msg[user_id] += xp
		leaderboards['Monthly Msg Leaderboard'] = {
			user_id: xp for user_id, xp in monthly_msg.items()
		}
		leaderboards['Global Monthly Msg Leaderboard'] = {
			user_id: xp for user_id, xp in global_monthly.items()
		}
		leaderboards['Server Msg Leaderboard'] = {
			guild_id: sum(xp for xp in dat.values()) for guild_id, dat in msg_xp.items()
		}
		leaderboards['Server Vc Leaderboard'] = {
				guild_id: timedelta(
					seconds=sum([xp for xp in dat.values()])
				) for guild_id, dat in vc_xp.items()
			}

		for name, data in leaderboards.items():
			sorted_data = [
				(user_id, xp) for user_id, xp in sorted(
					data.items(), key=lambda kv: kv[1], reverse=True
				)
			]
			ems = await create_embed(
				name=name,
				rankings=sorted_data,
				lmt=15,
				top_user=sorted_data[0][0]  # user_id
			)
			embeds.append(ems)

		sub_index = 0
		embeds[index][0].set_footer(text=f'Leaderboard {index + 1}/{len(embeds)} Page {sub_index + 1}/{len(embeds[index])}')
		await msg.edit(embed=embeds[index][0])

		while True:
			reaction, emoji = await wait_for_reaction()
			if not reaction:
				return await msg.clear_reactions()

			if emoji == emojis[0]:  # home
				index = 0; sub_index = 0

			if emoji == emojis[1]:
				index -= 1; sub_index = 0

			if emoji == emojis[2]:
				if isinstance(embeds[index], list):
					if not isinstance(sub_index, int):
						sub_index = len(embeds[index]) - 1
					else:
						if sub_index == 0:
							index -= 1; sub_index = 0
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
							index += 1; sub_index = 0
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
				index += 1; sub_index = 0
				index = index_check(index)

			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0

			embeds[index][sub_index].set_footer(text=f'Leaderboard {index + 1}/{len(embeds)} Page {sub_index+1}/{len(embeds[index])}')
			await msg.edit(embed=embeds[index][sub_index])
			await msg.remove_reaction(reaction, ctx.author)

	@commands.command(name='gen-lb')
	@commands.is_owner()
	async def generate_leaderboard(self, ctx):
		async def update_embed(m, data):
			""" gen and update the leaderboard embed """
			e = discord.Embed(color=0x4A0E50)
			e.title = 'Msg Leaderboard'
			e.description = ''
			rank = 1
			for user_id, xp in sorted(data.items(), reverse=True, key=lambda kv: kv[1]):
				user = self.bot.get_user(int(user_id))
				if not isinstance(user, discord.User):
					continue
				e.description += f'#{rank}. `{user}` - {xp}\n'
				rank += 1
				if rank == 10:
					break
			e.set_footer(text=footer)
			await m.edit(embed=e)

		e = discord.Embed()
		e.description = 'Starting..'
		m = await ctx.send(embed=e)

		xp = {}
		last_update = time() + 5

		for i, channel in enumerate(ctx.guild.text_channels):
			footer = f"Reading #{channel.name} ({i + 1}/{len(ctx.guild.text_channels)})"
			await update_embed(m, xp)
			last_gain = {}
			bot_counter = 0

			async for msg in channel.history(oldest_first=True, limit=None):
				# skip channels where every msg is a bot
				if msg.author.bot:
					bot_counter += 1
					if bot_counter == 1024:
						break
					continue
				else:
					bot_counter = 0

				# init
				user_id = str(msg.author.id)
				if user_id not in xp:
					xp[user_id] = 0
				if user_id not in last_gain:
					last_gain[user_id] = None
				if last_gain[user_id]:
					if (msg.created_at - last_gain[user_id]).total_seconds() < 10:
						continue

				# update stuff
				last_gain[user_id] = msg.created_at
				xp[user_id] += 1
				if last_update < time():
					await update_embed(m, xp)
					last_update = time() + 5

		footer = f'Gen Complete ({len(ctx.guild.text_channels)}/{len(ctx.guild.text_channels)})'
		await update_embed(m, xp)

	@_min_xp_per_msg.before_invoke
	@_max_xp_per_msg.before_invoke
	@_first_level_xp_req.before_invoke
	@_timeframe.before_invoke
	@_msgs_within_timeframe.before_invoke
	@xp_config.before_invoke
	@profile.before_invoke
	async def initiate_config(self, ctx):
		""" Make sure the guild has a config """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.config:
			self.init(guild_id)

def setup(bot):
	bot.add_cog(Ranking(bot))
