from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json

class Mute:
	def __init__(self, bot):
		self.bot = bot



def setup(bot):
	bot.add_cog(Mute(bot))
