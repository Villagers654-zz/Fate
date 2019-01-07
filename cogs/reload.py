from discord.ext import commands
import discord
import random

class Reload:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(name='reload', aliases=['relaod'], hidden=True)
	@commands.check(luck)
	async def _reload(self, ctx, *, module=" "):
		if module == " ":
			for module in self.bot.extensions:
				self.bot.unload_extension(module)
				self.bot.load_extension(module)
			e = discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| {ctx.author.name} | 🍪', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png")
			e.description = f"reloaded {len(self.bot.extensions)} modules"
			await ctx.send(embed=e, delete_after=5)
			await ctx.message.delete()
		else:
			try:
				self.bot.unload_extension(f'cogs.{module}')
				self.bot.load_extension(f'cogs.{module}')
			except Exception as e:
				e=discord.Embed(color=0x80b0ff)
				e.set_author(name=f'| {ctx.author.name} | {module} | ⚠', icon_url=ctx.author.avatar_url)
				e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637807680389121/lzbecdmvffggwmxconlk.png")
				e.description = f'{random.choice(["So sorry", "Apologies", "Sucks to be you", "Sorry"])} {random.choice(["dad", "master", "mike", "luck"])}'
				await ctx.send(embed=e, delete_after=5)
				await ctx.message.delete()
			else:
				e=discord.Embed(color=0x80b0ff)
				e.set_author(name=f'| {ctx.author.name} | 🍪', icon_url=ctx.author.avatar_url)
				e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png")
				e.description = f'Reloaded {module}'
				await ctx.send(embed=e, delete_after=5)
				await ctx.message.delete()

	@commands.command(name='unload', aliases=['disable'])
	@commands.check(luck)
	async def unload(self, ctx, *, module : str):
		self.bot.unload_extension(module)
		await ctx.send(f'disabled {module}')

def setup(bot):
	bot.add_cog(Reload(bot))
