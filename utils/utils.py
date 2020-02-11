from utils import colors
import datetime
import discord
import asyncio
import time

from discord.ext import commands


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


def get_prefix(ctx):
	return ctx.bot.utils.get_prefix(ctx.bot, ctx.message)


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
