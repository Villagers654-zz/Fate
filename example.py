from discord.ext import commands

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122



def setup(bot):
	bot.add_cog(Owner(bot))
