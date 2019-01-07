from discord.ext import commands
import discord
import random

class Math:
	def __init__(self, bot):
		self.bot = bot

# ~== Test ==~

	@commands.command()
	async def cogs_math(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	@commands.command()
	async def add(self, ctx, left: int, right: int):
		try:
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| {ctx.author.name} | 🖥', icon_url=ctx.author.avatar_url)
			e.description = f'Q: {left} + {right}\nA: {left + right}'
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```{e}```**')

	@commands.command()
	async def subtract(self, ctx, left: int, right: int):
		try:
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| {ctx.author.name} | 🖥', icon_url=ctx.author.avatar_url)
			e.description = f'Q: {left} - {right}\nA: {left - right}'
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```{e}```**')

	@commands.command()
	async def multiply(self, ctx, left: int, right: int):
		try:
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| {ctx.author.name} | 🖥', icon_url=ctx.author.avatar_url)
			e.description = f'Q: {left} * {right}\nA: {left * right}'
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```{e}```**')

	@commands.command()
	async def divide(self, ctx, left: int, right: int):
		try:
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| {ctx.author.name} | 🖥', icon_url=ctx.author.avatar_url)
			e.description = f'Q: {left} % {right}\nA: {left / right}'
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```{e}```**')

def setup(bot):
    bot.add_cog(Math(bot))
