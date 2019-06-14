from discord.ext import commands
import discord

class Embeds(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def embed(self, ctx, *, arg):
		try:
			e = discord.Embed()
			e.description = arg
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)

	@commands.command()
	async def embeda(self, ctx, *, arg):
		try:
			e = discord.Embed()
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = arg
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)

	@commands.command()
	async def embedb(self, ctx, arg1, *, arg2):
		try:
			e = discord.Embed(color=f'0x{arg1}')
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = arg2
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)

	@commands.command()
	async def embedc(self, ctx, arg1, arg2, *, arg3):
		try:
			e = discord.Embed(title=arg2, color=f'0x{arg1}')
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = arg3
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)

	@commands.command()
	async def embedu(self, ctx, arg1, arg2, arg3, arg4, *, arg5):
		try:
			e = discord.Embed(title=arg2, url=arg3, color='0x{}'.format(arg4))
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = arg5
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)

	@commands.command()
	async def embedx(self, ctx, arg1, arg2, arg3, arg4, arg5, *, arg6):
		try:
			e = discord.Embed(title=arg2, url=arg3, color='0x{}'.format(arg4))
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.add_field(name=arg5, value=arg6, inline=False)
			await ctx.send(embed=e)
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

def setup(bot):
	bot.add_cog(Embeds(bot))
