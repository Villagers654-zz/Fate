from discord.ext import commands
import discord

class Embeds(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_embeds(self, ctx):
		await ctx.send('working')

# ~== Main ==~



def setup(bot):
	bot.add_cog(Embeds(bot))
