from time import time
import subprocess
import traceback
import sys

from discord.ext import commands
import discord

from utils import colors, config


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
		err = str(error)
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
				if "check functions" in str(error):
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
				error_str = str(error).lower()
				if "internal" in error_str or "service unavailable" in error_str:
					return await ctx.send("Oop-\nDiscord shit in the bed\nIt's not my fault, it's theirs")
			elif isinstance(error, KeyError):
				err = f'No Data: {error}'
			print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			e = discord.Embed(color=colors.red())
			e.description = f'[{err}](https://www.youtube.com/watch?v=t3otBjVZzT0)'
			e.set_footer(text='This error has been logged, and will be fixed soon')
			await ctx.send(embed=e)
		except discord.errors.Forbidden:
			return
		p = subprocess.Popen("cat  /home/luck/.pm2/logs/fate-error.log", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").replace("`", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		msg = msg[::-1]
		msg = msg[:msg.find("Ignoring"[::-1])]
		r = f"```Ignoring{msg[::-1][-1980:]}```"
		e = discord.Embed(color=colors.red())
		e.description = ctx.message.content
		e.set_author(name=f"| Fatal Error | {ctx.command}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Error ◈", value=r, inline=False)
		channel = self.bot.get_channel(577661392098820106)
		async for msg in channel.history(limit=1):
			for embed in msg.embeds:
				if embed.fields[0].value == e.fields[0].value:
					return
		message = await channel.send(embed=e)
		await message.add_reaction("✔")
		if ctx.author.id == config.owner_id():
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f"Here's the full traceback:", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = r
			await ctx.send(embed=e)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			if data.channel_id == 577661392098820106:
				if str(data.emoji) == "✔":
					channel = self.bot.get_channel(data.channel_id)
					msg = await channel.fetch_message(data.message_id)
					for embed in msg.embeds:
						await self.bot.get_channel(577661461543780382).send("Error Dismissed", embed=embed)
					await msg.delete()

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
