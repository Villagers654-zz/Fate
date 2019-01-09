from discord.ext import commands
import discord
import random
import os

class Reactions:
	def __init__(self, bot):
		self.bot = bot



def setup(bot):
	bot.add_cog(Reactions(bot))
