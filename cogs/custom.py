from discord.ext import commands
import discord
import random

class customclass:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def tm(ctx):
		return ctx.author.id in [264838866480005122, 355026215137968129]

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_custom(self, ctx):
		await ctx.send('working')

# ~== Fun ==~

	@commands.command()
	async def tostitos(self, ctx):
		await ctx.send("reeeeee")

	@commands.command()
	async def nigward(self, ctx):
		e=discord.Embed(color=0xFF0000)
		e.set_image(url="https://cdn.discordapp.com/attachments/501492059765735426/505687664805281802/Nigward.jpg")
		await ctx.send(embed=e)

	@commands.command()
	async def agent(self, ctx):
		await ctx.send(random.choice(["big gay", "kys", "get off me property", "now that's alotta damage"]))
		await ctx.message.delete()

# ~== Pings ==~

def setup(bot):
	bot.add_cog(customclass(bot))
