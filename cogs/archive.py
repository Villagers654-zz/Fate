from discord.ext import commands
from utils import checks
import discord
import os

class customclass:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='archive')
	@commands.has_permissions(manage_messages=True)
	@commands.cooldown(1, 120, commands.BucketType.channel)
	async def archive(self, ctx, amount:int):
		if amount > 1000:
			await ctx.send('You cannot go over 1000')
		else:
			async with ctx.typing():
				log = ""
				async for msg in ctx.channel.history(limit=amount):
					log += f"""{msg.author.name}: {msg.content}\n"""
				ctx.channel.name = ctx.channel.name.replace(" ", "-")
				f = open(f'/home/luck/FateZero/data/{ctx.channel.name}.txt', 'w')
				f.write(log)
				f.close()
				path = os.getcwd() + f"/data/{ctx.channel.name}.txt"
				await ctx.send(file=discord.File(path))
				os.system(f'rm data/{ctx.channel.name}.txt')

	@commands.command()
	@commands.check(checks.luck)
	@commands.cooldown(1, 120, commands.BucketType.channel)
	async def sss(self, ctx, amount:int):
		c = 0
		if c == 0:
			async with ctx.typing():
				log = ""
				async for msg in ctx.channel.history(limit=amount):
					log += f"""{msg.author.name}: {msg.content}\n"""
				ctx.channel.name = ctx.channel.name.replace(" ", "-")
				f = open(f'/home/luck/FateZero/data/{ctx.channel.name}.txt', 'w')
				f.write(log)
				f.close()
				path = os.getcwd() + f"/data/{ctx.channel.name}.txt"
				await ctx.send(file=discord.File(path))
				os.system(f'rm data/{ctx.channel.name}.txt')

def setup(bot):
	bot.add_cog(customclass(bot))
