from discord.ext import commands
from utils import colors, config
from time import time
import subprocess
import traceback
import discord
import sys

class ErrorHandler(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cd = {}

	async def __error(self, ctx, error):
		await ctx.send(error)

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if hasattr(ctx.command, 'on_error'):
			return
		ignored = (commands.CommandNotFound, commands.NoPrivateMessage, discord.errors.NotFound)
		error = getattr(error, 'original', error)
		if isinstance(error, ignored):
			return
		elif isinstance(error, commands.DisabledCommand):
			return await ctx.send(f'`{ctx.command}` has been disabled.')
		elif isinstance(error, commands.BadArgument):
			if ctx.command.qualified_name == 'tag list':
				return await ctx.send('I could not find that member. Please try again.')
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
			await ctx.message.add_reaction('⚠')
			return await ctx.send(f"You don't have permission to use `{ctx.command}`")
		elif isinstance(error, discord.errors.Forbidden):
			try:
				await ctx.send(error)
			except:
				try:
					await ctx.message.add_reaction("⚠")
				except:
					pass
			finally:
				return
		print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
		e = discord.Embed(color=colors.red())
		e.set_author(name=f"| Fatal Error | {ctx.command}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = "This has been logged and will be resolved shortly"
		e.add_field(name="◈ Error ◈", value=str(error)[:2000], inline=False)
		await ctx.send(error)
		p = subprocess.Popen("cat  /home/luck/.pm2/logs/bot-error.log", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").replace("`", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		msg = msg[::-1]
		msg = msg[:msg.find("Ignoring"[::-1])]
		r = f"```Ignoring{msg[::-1]}```"
		e = discord.Embed(color=colors.red())
		e.set_author(name=f"| Fatal Error | {ctx.command}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Error ◈", value=r, inline=False)
		message = await self.bot.get_channel(549192817097048080).send(embed=e)
		await message.add_reaction("✔")

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			if data.guild_id == config.server("id"):
				if str(data.emoji) == "✔":
					channel = self.bot.get_channel(data.channel_id)
					msg = await channel.fetch_message(data.message_id)
					for embed in msg.embeds:
						await self.bot.get_channel(config.server("log")).send("Error Dismissed", embed=embed)
					await msg.delete()

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
