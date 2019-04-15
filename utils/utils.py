from discord.ext import commands
import datetime
import discord
import time

class Bot:

	async def can_dm(self, user: discord.User):
		dm_channel = user.dm_channel
		if not dm_channel:
			dm_channel = await user.create_dm()
		return dm_channel.permissions_for(self).send_messages

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
