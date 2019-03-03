from discord.ext import commands
from utils import colors, config
import subprocess
import traceback
import discord
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
			return await ctx.send(str(error).replace("command.", f"`{ctx.command}`"))
		elif isinstance(error, discord.errors.Forbidden):
			return await ctx.send("I'm missing permissions")
		print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
		p = subprocess.Popen("cat  /root/.pm2/logs/bot-error.log", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").replace("`", "").replace("\\", "").split("\\n")
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
		await ctx.send(embed=e)
		message = await self.bot.get_channel(549192817097048080).send(embed=e)
		await message.add_reaction("✔")

	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			if data.guild_id == config.server("id"):
				if str(data.emoji) == "✔":
					channel = self.bot.get_channel(data.channel_id)
					msg = await channel.get_message(data.message_id)
					for embed in msg.embeds:
						await self.bot.get_channel(config.server("log")).send("Error Dismissed", embed=embed)
					await msg.delete()

def setup(bot):
	bot.add_cog(ErrorHandler(bot))
