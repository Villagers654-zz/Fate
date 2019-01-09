from discord.ext import commands
import traceback
import discord

class ErrorHandler:
	def __init__(self, bot):
		self.bot = bot

	async def __error(self, ctx, error):
		await ctx.send(error)

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_error(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	async def on_command_error(self, ctx, error):
		if hasattr(ctx.command, 'on_error'):
			return
		ignored = (commands.CommandNotFound)
		error = getattr(error, 'original', error)
		if isinstance(error, ignored):
			return
		elif isinstance(error, commands.DisabledCommand):
			return await ctx.send(f'`{ctx.command}` has been disabled.')
		elif isinstance(error, commands.NoPrivateMessage):
			try:
				return await ctx.author.send(f'`{ctx.command}` can not be used in Private Messages.')
			except:
				pass
		elif isinstance(error, commands.BadArgument):
			if ctx.command.qualified_name == 'tag list':
				return await ctx.send('I could not find that member. Please try again.')
		elif isinstance(error, commands.CommandOnCooldown):
			return await ctx.message.add_reaction('⏳')
		elif isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send(error)
		elif isinstance(error, commands.CheckFailure):
			await ctx.message.add_reaction('⚠')
		elif isinstance(error, discord.errors.Forbidden):
			await ctx.send("I'm missing permissions")
		if "NoneType: None" in traceback.format_exc():
			await ctx.send(error)
		else:
			await ctx.send(traceback.format_exc())

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
