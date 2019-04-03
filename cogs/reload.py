from discord.ext import commands
from utils import checks, colors
import discord
import asyncio
import random

class Reload(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def __error(self, ctx, error):
		await ctx.send(error)

	@commands.command(name="reload", aliases=["relaod"], hidden=True)
	@commands.check(checks.luck)
	async def _reload(self, ctx, *, module=""):
		if not module:
			for module in self.bot.extensions:
				self.bot.unload_extension(module)
				self.bot.load_extension(module)
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f'| {ctx.author.name} | 🍪', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png")
			e.description = f"reloaded {len(self.bot.extensions)} modules"
			await ctx.send(embed=e, delete_after=5)
			await asyncio.sleep(0.5)
			return await ctx.message.delete()
		try:
			self.bot.unload_extension(f'cogs.{module}')
			self.bot.load_extension(f'cogs.{module}')
		except Exception as e:
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f'| {ctx.author.name} | {module} | ⚠', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(
				url="https://cdn.discordapp.com/attachments/501871950260469790/513637807680389121/lzbecdmvffggwmxconlk.png")
			e.description = f'{random.choice(["So sorry", "Apologies", "Sucks to be you", "Sorry"])} {random.choice(["dad", "master", "mike", "luck"])}'
			await ctx.send(embed=e, delete_after=5)
			await asyncio.sleep(0.5)
			await ctx.message.delete()
		else:
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f'| {ctx.author.name} | 🍪', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png")
			e.description = f'Reloaded {module}'
			await ctx.send(embed=e, delete_after=5)
			await asyncio.sleep(0.5)
			await ctx.message.delete()

	@commands.command(name="disable")
	@commands.check(checks.luck)
	async def _disable(self, ctx, *, module : str):
		self.bot.unload_extension("cogs." + module)
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f'| {ctx.author.name} | 🍪', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png")
		e.description = f'Disabled {module}'
		await ctx.send(embed=e, delete_after=5)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

def setup(bot):
	bot.add_cog(Reload(bot))
