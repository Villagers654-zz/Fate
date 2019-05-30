from discord.ext import commands
from os.path import isfile
import discord
import json

class Toggles(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='enable')
	async def enable(self, ctx):
		pass

def setup(bot):
	bot.add_cog(Toggles(bot))
