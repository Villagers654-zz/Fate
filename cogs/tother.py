from discord.ext import commands
from os.path import isfile
import random
import json

class Tothy:
	def __init__(self, bot):
		self.bot = bot
		self.tothy = []
		if isfile("./data/userdata/tother.json"):
			with open("./data/userdata/tother.json", "r") as infile:
				dat = json.load(infile)
				if "tothy" in dat:
					self.tothy = dat["tothy"]

	def tother(ctx):
		return ctx.message.author.id == 355026215137968129

	@commands.group(name="tother")
	@commands.check(tother)
	async def _tother(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send(random.choice(self.tothy))

	@_tother.command(name="add")
	@commands.check(tother)
	async def _add(self, ctx, *, content=None):
		if content is None:
			await ctx.message.delete()
		else:
			self.tothy.append(content)

def setup(bot):
	bot.add_cog(Tothy(bot))
