from discord.ext import commands
import random
import discord

class textartclass:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_textart(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	@commands.command()
	async def tshrug(self, ctx):
		try:
			await ctx.send('¯\_(ツ)_/¯')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def chill(self, ctx):
		try:
			await ctx.send('(~˘▾˘)~')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def cross(self, ctx, *, arg):
		try:
			await ctx.send('{} (╬ Ò ‸ Ó)'.format(arg))
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def yes(self, ctx):
		try:
			await ctx.send("░░░░░░▄▄\n░░░░░█░░█\n▄▄▄▄▄█░░█▄▄▄\n▓▓▓▓█░░░░░░░█\n▓▓▓▓█░░░░░░░░█\n▓▓▓▓█░░░░░░░░█\n▓▓▓▓█░░░░░░░░█\n███▀▀▀███████")
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def angry(self, ctx):
		try:
			await ctx.send('(ノಠ益ಠ)ノ彡┻━┻')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def fuckit(self, ctx):
		try:
			await ctx.send("Fuck it ヽ(*ﾟｰﾟ*)ﾉ")
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

def setup(bot):
    bot.add_cog(textartclass(bot))
