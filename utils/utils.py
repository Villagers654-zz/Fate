import datetime
import asyncio
import time
from os.path import isfile
import json
from io import BytesIO
import requests
from colormap import rgb2hex

from discord.ext import commands
import discord
from PIL import Image

from utils import colors


def get_prefix(ctx):
	guild_id = str(ctx.guild.id)
	config = ctx.bot.get_config  # type: dict
	p = '.'  # default command prefix
	if guild_id in config['prefix']:
		p = config['prefix'][guild_id]
	return p


def get_prefixes(bot, msg):
	conf = bot.utils.get_config()  # type: dict
	if 'blocked' in conf:
		if msg.author.id in conf['blocked']:
			return 'lsimhbiwfefmtalol'
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

	if emoji is "plus":
		return "<:plus:548465119462424595>"
	if emoji is "edited":
		return "<:edited:550291696861315093>"
	if emoji == 'arrow':
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


def format_dict(data: dict) -> str:
	result = ''
	for k, v in data.items():
		if v:
			result += f"\n{emojis('arrow')} **{k}:** {v}"
		else:
			result += f"\n{emojis('arrow')} {k}"
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
	if not isfile('./data/config.json'):
		with open('./data/config.json', 'w') as f:
			json.dump({}, f, ensure_ascii=False)
	with open('./data/config.json', 'r') as f:
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

def get_user(ctx, user=None):
	if not user:
		return ctx.author
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

def get_time(seconds):
	result = ''
	if seconds < 60:
		return f'{seconds} seconds'
	time = str(datetime.timedelta(seconds=seconds))
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
			if char not in list('1234567890'):
				name = name.replace(str(char), '')
		return ctx.guild.get_member(int(name))
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
				return await embed.delete()
			else:
				try:
					role = int(msg.content)
				except:
					return await ctx.send('Invalid response')
				if role > len(roles):
					return await ctx.send('Invalid response')
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
		return datetime.datetime.utcnow() + datetime.timedelta(seconds=self.seconds)

	def past(self):
		return datetime.datetime.utcnow() - datetime.timedelta(seconds=self.seconds)

class Time:
	def __init__(self, seconds):
		self.seconds = seconds

	def future(self):
		return time.time() + self.seconds

	def past(self):
		return time.time() - self.seconds
