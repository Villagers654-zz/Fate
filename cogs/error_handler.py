from discord.ext import commands
from utils import colors
import traceback
import discord
import asyncio
import sys

class ErrorHandler:
	def __init__(self, bot):
		self.bot = bot

	async def __error(self, ctx, error):
		await ctx.send(error)

	async def on_command_error(self, ctx, error):
		if hasattr(ctx.command, 'on_error'):
			return
		ignored = (commands.CommandNotFound, commands.NoPrivateMessage)
		error = getattr(error, 'original', error)
		if isinstance(error, ignored):
			return
		elif isinstance(error, commands.DisabledCommand):
			return await ctx.send(f'`{ctx.command}` has been disabled.')
		elif isinstance(error, commands.BadArgument):
			if ctx.command.qualified_name == 'tag list':
				return await ctx.send('I could not find that member. Please try again.')
		elif isinstance(error, commands.CommandOnCooldown):
			await ctx.message.add_reaction('⏳')
			return await ctx.send(error)
		elif isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send(error)
		elif isinstance(error, commands.CheckFailure):
			await ctx.message.add_reaction('⚠')
			return await ctx.send(error)
		elif isinstance(error, discord.errors.Forbidden):
			return await ctx.send("I'm missing permissions")
		print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
		e = discord.Embed(color=colors.lime_green())
		e.set_author(name=f"| Fatal Error | {ctx.command}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = "✦ This has been logged and will be resolved shortly!"
		e.add_field(name="◈ Error ◈", value=error, inline=False)
		e.set_footer(text=f"Author: {ctx.author}")
		await self.bot.get_channel(501871950260469790).send(embed=e)
		error_message = await ctx.send(embed=e)
		if "manage_messages" in ', '.join(perm for perm, value in
		ctx.guild.get_member(self.bot.user.id).guild_permissions if value):
			await asyncio.sleep(20)
			await ctx.message.delete()
			await error_message.delete()

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
