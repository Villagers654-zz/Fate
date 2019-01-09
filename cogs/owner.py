from discord.ext import commands
import subprocess
import discord
import asyncio
import os

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(name="changepresence", aliases=["cp"])
	@commands.check(luck)
	async def changepresence(self, ctx, *, arg):
		async with ctx.typing():
			await self.bot.change_presence(activity=discord.Game(name=arg))
			await ctx.send('done', delete_after=5)
			await asyncio.sleep(5)
			await ctx.message.delete()

	@commands.command()
	@commands.check(luck)
	async def sendfile(self, ctx, directory):
		path = os.getcwd() + f"{directory}"
		await ctx.send(file=discord.File(path))

	@commands.command(name='console', aliases=['c'])
	@commands.check(luck)
	async def console(self, ctx, *, command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output)
		await ctx.send(output[:2000])

	@commands.command()
	@commands.check(luck)
	async def logout(self, ctx):
		await ctx.send('logging out')
		await self.bot.logout()

def setup(bot):
	bot.add_cog(Owner(bot))
