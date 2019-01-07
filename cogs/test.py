from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json
import os

class Test:
	def __init__(self, bot):
		self.bot = bot


	async def __error(self, ctx, error):
		await ctx.send(error)

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_test(self, ctx):
		await ctx.send('working')

# ~== Main ==~



def setup(bot):
	bot.add_cog(Test(bot))
