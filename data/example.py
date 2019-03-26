from discord.ext import commands
import discord

class Example:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def kill(self, ctx, user):
		await ctx.send(f"{ctx.author.mention} has killed {user}")

def setup(bot):
	bot.add_cog(Example(bot))
