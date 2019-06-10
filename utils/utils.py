import datetime
import discord
import asyncio
import time

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

class Text:

	def cleanup(text):
		chars = list('abcdefghijklmnopqrstuvwxyz')
		clean = ''
		for char in list(text):
			if char in chars:
				clean += char
		return clean
