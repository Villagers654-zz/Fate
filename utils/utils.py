from datetime import datetime, timedelta
import asyncio
import time
from os.path import isfile
import json
from io import BytesIO
import requests
import subprocess
import os
from ast import literal_eval
from time import monotonic
from typing import *
import re
import aiofiles

from discord.ext import commands
import discord
from PIL import Image
from colormap import rgb2hex

from utils import colors


class SqlCursor:
	def __init__(self, bot):
		self.bot = bot
		self.connection = None
		self.cursor = None

	async def __aenter__(self):
		self.connection = await self.bot.pool.acquire()
		self.cursor = await self.connection.cursor()
		return self.cursor

	async def __aexit__(self, _type, _value, _traceback):
		self.connection.close()
		await self.connection.ensure_closed()


class AsyncFileManager:
	def __init__(self, file: str, mode: str = "r", lock: asyncio.Lock = None):
		self.file = file
		self.mode = mode
		self.fp_manager = None
		self.lock = lock

	async def __aenter__(self):
		if self.lock and "r" not in self.mode:
			await self.lock.acquire()
		self.fp_manager = await aiofiles.open(file=self.file, mode=self.mode)
		return self.fp_manager

	async def __aexit__(self, _exc_type, _exc_value, _exc_traceback):
		await self.fp_manager.close()
		if self.lock and "r" not in self.mode:
			self.lock.release()


class Result:
	def __init__(self, result, errored=False, traceback=None):
		self.result = result
		self.errored = errored
		self.traceback = traceback


async def update_msg(msg, new) -> discord.Message:
	if len(msg.content) + len(new) + 2 >= 2000:
		msg = await msg.channel.send("Uploading emoji(s)")
	await msg.edit(content=f"{msg.content}\n{new}")
	return msg


def split(text, amount=2000) -> list:
	return [text[i:i + amount] for i in range(0, len(text), amount)]


def get_prefix(ctx):
	guild_id = str(ctx.guild.id)
	config = ctx.bot.utils.get_config()  # type: dict
	p = '.'  # default command prefix
	if guild_id in config['prefix']:
		p = config['prefix'][guild_id]
	return p


def get_prefixes(bot, msg):
	conf = bot.utils.get_config()  # type: dict
	with open("./data/config.json", "r") as f:
		config = json.load(f)  # type: dict
	if msg.author.id == config['bot_owner_id']:
		return commands.when_mentioned_or(".")(bot, msg)
	if 'blocked' in conf:
		if msg.author.id in conf['blocked']:
			return 'lsimhbiwfefmtalol'
	else:
		bot.log("Blocked key was non existant")
	if not msg.guild:
		return commands.when_mentioned_or(".")(bot, msg)
	guild_id = str(msg.guild.id)
	if 'restricted' not in conf:
		conf['restricted'] = {}
	if guild_id in conf['restricted']:
		if msg.channel.id in conf['restricted'][guild_id]['channels'] and (
				not msg.author.guild_permissions.administrator):
			return 'lsimhbiwfefmtalol'
	if 'personal_prefix' not in conf:
		conf['personal_prefix'] = {}
	user_id = str(msg.author.id)
	if user_id in conf['personal_prefix']:
		return commands.when_mentioned_or(conf['personal_prefix'][user_id])(bot, msg)
	if 'prefix' not in conf:
		conf['prefix'] = {}
	prefixes = conf['prefix']
	if guild_id not in prefixes:
		return commands.when_mentioned_or('.')(bot, msg)
	return commands.when_mentioned_or(prefixes[guild_id])(bot, msg)


def emojis(emoji):
	if emoji is None:
		return '‎'
	if emoji == "plus":
		return "<:plus:548465119462424595>"
	if emoji == "edited":
		return "<:edited:550291696861315093>"
	if emoji == 'arrow':
		date = datetime.utcnow()
		if date.month == 1 and date.day == 26:  # Chinese New Year
			return '🐉'
		if date.month == 2 and date.day == 14:  # Valentines Day
			return '❤'
		if date.month == 6:  # Pride Month
			return '<a:arrow:679213991721173012>'
		if date.month == 7 and date.day == 4:  # July 4th
			return '🎆'
		if date.month == 10 and date.day == 31:  # Halloween
			return '🎃'
		if date.month == 11 and date.day == 26:  # Thanksgiving
			return '🦃'
		if datetime.month == 12 and date.day == 25:  # Christmas
			return '🎄'
		return '<:enter:673955417994559539>'

	if emoji == 'text_channel':
		return '<:textchannel:679179620867899412>'
	if emoji == 'voice_channel':
		return '<:voicechannel:679179727994617881>'

	if emoji == 'invisible' or emoji is discord.Status.offline:
		return '<:status_offline:659976011651219462>'
	if emoji == 'dnd' or emoji is discord.Status.dnd:
		return '<:status_dnd:659976008627388438>'
	if emoji == 'idle' or emoji is discord.Status.idle:
		return '<:status_idle:659976006030983206>'
	if emoji == 'online' or emoji is discord.Status.online:
		return '<:status_online:659976003334045727>'


def format_dict(data: dict, emoji=None) -> str:
	if emoji is None:
		emoji = emojis('arrow') + ' '
	elif emoji is False:
		emoji = ''
	result = ''
	for k, v in data.items():
		if v:
			result += f"\n{emoji}**{k}:** {v}"
		else:
			result += f"\n{emoji}{k}"
	return result


def add_field(embed, name: str, value: dict, inline=True):
	embed.add_field(
		name=f'◈ {name}', value=format_dict(value), inline=inline
	)


def avg_color(url):
	"""Gets an image and returns the average color"""
	if not url:
		return colors.fate()
	im = Image.open(BytesIO(requests.get(url).content)).convert('RGBA')
	pixels = list(im.getdata())
	r = g = b = c = 0
	for pixel in pixels:
		# brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
		if pixel[3] > 64:
			r += pixel[0]
			g += pixel[1]
			b += pixel[2]
			c += 1
	r = r / c
	g = g / c
	b = b / c
	return eval('0x' + rgb2hex(round(r), round(g), round(b)).replace('#', ''))


def total_seconds(now, before):
	secs = str((now - before).total_seconds())
	return secs[:secs.find('.') + 2]

def get_stats():
	if not isfile('./data/stats.json'):
		with open('./data/stats.json', 'w') as f:
			json.dump({'commands': []}, f, ensure_ascii=False)
	with open('./data/stats.json', 'r') as stats:
		return json.load(stats)

def get_config():
	if not isfile('./data/userdata/config.json'):
		with open('./data/userdata/config.json', 'w') as f:
			json.dump({}, f, ensure_ascii=False)
	with open('./data/userdata/config.json', 'r') as f:
		return json.load(f)

def default_cooldown():
	return [2, 5, commands.BucketType.user]

def bytes2human(n):
	symbols = ('KB', 'MB', 'GB', 'TB', 'PB', 'E', 'Z', 'Y')
	prefix = {}
	for i, s in enumerate(symbols):
		prefix[s] = 1 << (i + 1) * 10
	for s in reversed(symbols):
		if n >= prefix[s]:
			value = float(n) / prefix[s]
			return '%.1f%s' % (value, s)
	return "%sB" % n

def cleanup_msg(msg, content=None):
	if not content:
		content = msg
	if isinstance(msg, discord.Message):
		content = content if content else msg.content
		for mention in msg.role_mentions:
			content = content.replace(str(mention), mention.name)
	content = str(content).replace('@', '@ ')
	extensions = ['.' + x for x in [c for c in list(content) if c != ' ']]
	if len(content.split(' ')) > 1:
		content = content.split(' ')
	else:
		content = [content]
	if isinstance(content, list):
		targets = [c for c in content if any(x in c for x in extensions)]
		for target in targets:
			content[content.index(target)] = '**forbidden-link**'
	content = ' '.join(content) if len(content) > 1 else content[0]
	return content

def get_user(ctx, user: str =None):
	if not user:
		return ctx.author
	if str(user).isdigit():
		user = str(user)
		usr = None
		if ctx.guild:
			usr = ctx.guild.get_member(int(user))
		return usr if usr else ctx.bot.get_user(int(user))
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

async def get_user_rewrite(ctx, target: str = None) -> Union[discord.User, discord.Member]:
	""" Grab a user by id, name, or username, and convert to Member if possible """
	if not target:
		user = ctx.author
	elif target.isdigit() or re.findall("<.@[0-9]*>", target):
		user_id = int("".join(c for c in target if c.isdigit()))
		user = await ctx.bot.fetch_user(user_id)
	elif ctx.guild is None:
		user = ctx.author
	else:
		for usr in ctx.bot.users:
			if str(usr) == target:
				user = usr
				break
		else:
			target = re.sub("#[0-9]{4}", "", target.lower())
			results = [
				member for member in ctx.guild.members
				if (target in member.display_name.lower() if not member.nick
				    else target in member.name.lower())
			]
			if len(results) == 1:
				user = results[0]  # type: discord.Member
			elif len(results) > 1:
				user = await ctx.bot.get_choice(ctx, *results, user=ctx.author)
			else:
				user = ctx.author
	if ctx.guild is not None and not isinstance(user, discord.Member):
		if user.id in [m.id for m in ctx.guild.members]:
			user = ctx.guild.get_member(user.id)
	return user

def get_time(seconds):
	result = ''
	if seconds < 60:
		return f'{seconds} seconds'
	time = str(timedelta(seconds=seconds))
	if ',' in time:
		days = str(time).replace(' days,', '').split(' ')[0]
		time = time.replace(f'{days} day{"s" if int(days) > 1 else ""}, ', '')
		result += f'{days} days'
	hours, minutes, seconds = time.split(':')
	hours = int(hours); minutes = int(minutes)
	if hours > 0:
		result += f'{", " if result else ""}{hours} hour{"s" if hours > 1 else ""}'
	if minutes > 0:
		result += f'{", and " if result else ""}{minutes} minute{"s" if minutes > 1 else ""}'
	return result

async def get_role(ctx, name):
	if name.startswith("<@"):
		for char in list(name):
			if not char.isdigit():
				name = name.replace(str(char), '')
		return ctx.guild.get_role(int(name))
	else:
		roles = []
		for role in ctx.guild.roles:
			if name.lower() == role.name.lower():
				roles.append(role)
		if not roles:
			for role in ctx.guild.roles:
				if name.lower() in role.name.lower():
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
				msg = await ctx.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send('Timeout error', delete_after=5)
				await embed.delete()
				return None
			else:
				try:
					role = int(msg.content)
				except:
					await ctx.send('Invalid response')
					return None
				if role > len(roles):
					await ctx.send('Invalid response')
					return None
				await embed.delete()
				await msg.delete()
				return roles[role - 1]


async def wait_for_msg(self, ctx, user=None):
	if not user:
		user = ctx.author
	def pred(m):
		return m.channel.id == ctx.channel.id and m.author.id == user.id
	try:
		msg = await self.bot.wait_for('message', check=pred, timeout=60)
	except asyncio.TimeoutError:
		await ctx.send("Timeout error")
		return False
	else:
		return msg


def get_seconds(minutes=None, hours=None, days=None):
	if minutes:
		return minutes * 60
	if hours:
		return hours * 60 * 60
	if days:
		return days * 60 * 60 * 24
	return 0


async def get_images(ctx) -> list:
	""" Gets the latest image(s) in the channel """
	def scrape(msg: discord.Message) -> list:
		""" Thoroughly checks a msg for images """
		image_links = []
		if msg.attachments:
			for attachment in msg.attachments:
				image_links.append(attachment.url)
		for embed in msg.embeds:
			if 'image' in embed.to_dict():
				image_links.append(embed.to_dict()['image']['url'])
		args = msg.content.split()
		if not args:
			args = [msg.content]
		for arg in args:
			if 'https://cdn.discordapp.com/attachments/' in arg:
				image_links.append(arg)
		return image_links

	image_links = scrape(ctx.message)
	if image_links:
		return image_links
	async for msg in ctx.channel.history(limit=10):
		image_links = scrape(msg)
		if image_links:
			return image_links
	await ctx.send('No images found in the last 10 msgs')
	return image_links

async def configure(self, ctx, options: dict) -> Union[dict, None]:
	""" Reaction based configuration """

	async def wait_for_reaction():
		def pred(r, u):
			return u.id == ctx.author.id and r.message.id == message.id

		try:
			reaction, user = await self.bot.wait_for('reaction_add', check=pred, timeout=60)
		except asyncio.TimeoutError:
			await message.edit(content="Menu Inactive")
			return None
		else:
			return reaction, user

	async def wait_for_msg() -> Optional[discord.Message]:
		def pred(m):
			return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

		now = time.time()
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=30)
		except asyncio.TimeoutError:
			await message.edit(content="Menu Inactive")
			return None
		else:
			async def remove_msg(msg):
				await asyncio.sleep(round(time.time() - now))
				await msg.delete()

			self.bot.loop.create_task(remove_msg(msg))
			return msg

	async def clear_user_reactions(message) -> None:
		before = monotonic()
		message = await ctx.channel.fetch_message(message.id)
		for reaction in message.reactions:
			if reaction.count > 1:
				async for user in reaction.users():
					if user.id == ctx.author.id:
						await message.remove_reaction(reaction.emoji, user)
						break
		after = round((monotonic() - before) * 1000)
		print(f"{after}ms to clear reactions")

	async def init_reactions_task() -> None:
		if len(options) > 9:
			other = ["🏡", "◀", "▶"]
			for i, emoji in enumerate(other):
				if i > 0:
					await asyncio.sleep(1)
				await message.add_reaction(emoji)
		for emoji in emojis[:len(options)]:
			await message.add_reaction(emoji)

	emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"]
	pages = []
	tmp_page = {}
	for i, (key, value) in enumerate(options.items()):
		value = options[key]
		if i == len(emojis):
			pages.append(tmp_page)
			tmp_page = {}
			continue
		tmp_page[key] = value
	pages.append(tmp_page)
	page = 0

	def overview():
		e = discord.Embed(color=0x992d22)
		e.description = ""
		for i, (key, value) in enumerate(pages[page].items()):
			if isinstance(value, list):
				value = ' '.join([str(v) for v in value])
			e.description += f"\n{emojis[i]} | {key} - {value}"
		return e

	message = await ctx.send(embed=overview())
	self.bot.loop.create_task(init_reactions_task())
	while True:
		await clear_user_reactions(message)
		payload = await wait_for_reaction()
		if not payload:
			return None
		reaction, user = payload
		emoji = str(reaction.emoji)
		if emoji == "🏡":
			await message.edit(embed=overview())
			continue
		elif emoji == "▶":
			page += 1
			await message.edit(embed=overview())
			continue
		elif emoji == "◀":
			page -= 1
			await message.edit(embed=overview())
			continue
		elif emoji == "✅":
			full = {}
			for page in pages:
				for key, value in page.items():
					full[key] = value
			await message.edit(content="Menu Inactive")
			await message.clear_reactions()
			return full
		else:
			while True:
				await clear_user_reactions(message)
				index = emojis.index(str(reaction.emoji))
				value = pages[page][list(pages[page].keys())[index]]
				if isinstance(value, bool):
					pages[page][list(pages[page].keys())[index]] = False if value else True
					await message.edit(embed=overview())
					break
				await ctx.send(f"Send the new value for {list(pages[page].keys())[index]} in the same format as it's listed", delete_after=30)
				msg = await wait_for_msg()
				if not msg:
					return None
				msg = await ctx.channel.fetch_message(msg.id)
				if isinstance(value, list) and '[' not in msg.content:
					if ',' in msg.content:
						msg.content = msg.content.split(', ')
					else:
						msg.content = msg.content.split()
					new_value = [literal_eval(x) for x in msg.content]
				else:
					new_value = literal_eval(msg.content)
				if type(value) != type(new_value):
					await ctx.send("Invalid format\nPlease retry", delete_after=5)
					await msg.delete()
					continue
				elif isinstance(value, list):
					invalid = False
					for i, v in enumerate(value):
						if type(v) != type(new_value[i]):
							await ctx.send(f"Invalid format at `{discord.utils.escape_markdown(new_value[i])}`\nPlease retry", delete_after=5)
							await msg.delete()
							invalid = True
							break
					if invalid:
						continue
				pages[page][list(pages[page].keys())[index]] = new_value
				await message.edit(embed=overview())
				await msg.delete()
				break
			if "✅" not in [str(r.emoji) for r in message.reactions]:
				await message.add_reaction("✅")


class MemoryInfo:
	@staticmethod
	async def __coro_fetch(interval=0):
		p = subprocess.Popen(f'python3 memory_info.py {os.getpid()} {interval}', stdout=subprocess.PIPE, shell=True)
		await asyncio.sleep(1)
		(output, err) = p.communicate()
		output = output.decode()
		return json.loads(output)

	@staticmethod
	def __fetch(interval=1):
		p = subprocess.Popen(f'python3 memory_info.py {os.getpid()} {interval}', stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = output.decode()
		return json.loads(output)

	@staticmethod
	async def full(interval=1):
		return await MemoryInfo.__coro_fetch(interval)

	@staticmethod
	async def cpu(interval=1):
		mem = await MemoryInfo.__coro_fetch(interval)
		return mem['PID']['CPU']

	@staticmethod
	def ram(interval=0):
		return MemoryInfo.__fetch(interval)['PID']['RAM']['RSS']

	@staticmethod
	async def cpu_info(interval=1):
		mem = await MemoryInfo.__coro_fetch(interval)
		return {'global': mem['GLOBAL']['CPU'], 'bot': mem['PID']['CPU']}

	@staticmethod
	def global_cpu(interval=1):
		return MemoryInfo.__fetch(interval)['GLOBAL']['CPU']

	@staticmethod
	def global_ram(interval=0):
		return MemoryInfo.__fetch()['GLOBAL']['RAM']['USED']


class Bot:
	def __init__(self, bot):
		self.bot = bot
		self.dir = './data/stats.json'

	async def wait_for_msg(self, ctx):
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=60)
		except asyncio.TimeoutError:
			await ctx.send("Timeout error")
			return False
		else:
			return msg


class User:
	def __init__(self, user: discord.User):
		self.user = user

	async def init(self):
		dm_channel = self.user.dm_channel
		if not dm_channel:
			await self.user.create_dm()

	def can_dm(self):
		return self.user.dm_channel.permissions_for(self).send_messages


class Datetime:
	def __init__(self, seconds):
		self.seconds = seconds

	def future(self):
		return datetime.utcnow() + timedelta(seconds=self.seconds)

	def past(self):
		return datetime.utcnow() - timedelta(seconds=self.seconds)


class Time:
	def __init__(self, seconds):
		self.seconds = seconds

	def future(self):
		return time.time() + self.seconds

	def past(self):
		return time.time() - self.seconds
