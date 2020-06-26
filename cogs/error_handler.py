from time import time
import subprocess
import traceback
import sys

from discord.ext import commands
import discord

from utils import colors, config, checks


class ErrorHandler(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cd = {}

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if hasattr(ctx.command, 'on_error'):
			return
		perms = None if not ctx.guild else ctx.channel.permissions_for(ctx.guild.me)
		if not ctx.guild or (not perms.send_messages or not perms.add_reactions):
			return

		error = getattr(error, 'original', error)
		error_str = str(error)
		self.bot.last_traceback = str(sys.exc_info())

		try:
			ignored = (commands.CommandNotFound, commands.NoPrivateMessage, discord.errors.NotFound)
			if isinstance(error, ignored):
				return
			elif isinstance(error, commands.DisabledCommand):
				return await ctx.send(f'`{ctx.command}` is disabled.')
			elif isinstance(error, commands.BadArgument):
				return await ctx.send(f"Bad Argument: {error}")
			elif isinstance(error, commands.CommandOnCooldown):
				user_id = str(ctx.author.id)
				await ctx.message.add_reaction('⏳')
				if user_id not in self.cd:
					self.cd[user_id] = 0
				if self.cd[user_id] < time() - 10:
					await ctx.send(error)
				self.cd[user_id] = time() + 10
				return
			elif isinstance(error, commands.MissingRequiredArgument):
				return await ctx.send(error)
			elif isinstance(error, commands.CheckFailure):
				if not checks.command_is_enabled(ctx):
					return await ctx.send(f"{ctx.command} is disabled")
				elif "check functions" in str(error):
					return await ctx.message.add_reaction('🚫')
				else:
					return await ctx.send(error)
			elif isinstance(error, discord.errors.Forbidden):
				if not ctx.guild:
					return
				if ctx.channel.permissions_for(ctx.guild.me).send_messages:
					return await ctx.send(error)
				if ctx.channel.permissions_for(ctx.guild.me).add_reactions:
					return await ctx.message.add_reaction("⚠")
				try:
					await ctx.author.send(f"I don't have permission to reply to you in {ctx.guid.name}")
				except discord.errors.Forbidden:
					pass
				return
			elif isinstance(error, discord.errors.HTTPException):
				if "internal" in error_str or "service unavailable" in error_str:
					return await ctx.send("Oop-\nDiscord shit in the bed\nIt's not my fault, it's theirs")
			elif isinstance(error, KeyError):
				error_str = f'No Data: {error}'
			print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			e = discord.Embed(color=colors.red())
			e.description = f'[{error_str}](https://www.youtube.com/watch?v=t3otBjVZzT0)'
			e.set_footer(text='This error has been logged, and will be fixed soon')
			await ctx.send(embed=e)
		except (discord.errors.Forbidden, discord.errors.NotFound):
			return

		channel = self.bot.get_channel(self.bot.config["error_channel"])
		e = discord.Embed(color=colors.red())
		e.description = ctx.message.content
		e.set_author(name=f"| Fatal Error | in {ctx.command}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Error ◈", value=self.bot.last_traceback, inline=False)

		# Check to make sure the error isn't already logged
		async for msg in channel.history(limit=16):
			for embed in msg.embeds:
				if not embed.fields:
					continue
				if embed.fields[0].value == e.fields[0].value:
					return

		message = await channel.send(embed=e)
		await message.add_reaction("✔")
		if ctx.author.id == config.owner_id():
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f"Here's the full traceback:", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = self.bot.last_traceback
			await ctx.send(embed=e)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			if data.channel_id == self.bot.config["error_channel"]:
				if str(data.emoji) == "✔":
					channel = self.bot.get_channel(data.channel_id)
					msg = await channel.fetch_message(data.message_id)
					for embed in msg.embeds:
						channel = self.bot.get_channel(self.bot.config["dump_channel"])
						await channel.send("Error Dismissed", embed=embed)
					await msg.delete()

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
