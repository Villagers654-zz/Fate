from discord.ext import commands
from utils import checks
import discord
import asyncio
import random

class System(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.output_log = ''
		self.error_log = ''

	async def console_task(self):
		while True:
			try:
				channel = self.bot.get_channel(577661412432805888)
				output_msg = await channel.fetch_message(577662410010263564)
				with open('/home/luck/.pm2/logs/fate-out.log', 'r') as f:
					new_log = f'```{f.read()[-1994:]}```'
					if new_log != self.output_log:
						self.output_log = new_log
						await output_msg.edit(content=new_log)
						await channel.send('updated clean console', delete_after=5)
				output_msg = await channel.fetch_message(577662416687595535)
				with open('/home/luck/.pm2/logs/fate-error.log', 'r') as f:
					new_log = f'```{discord.utils.escape_markdown(f.read())[-1994:]}```'
					if new_log != self.error_log:
						self.error_log = new_log
						await output_msg.edit(content=new_log)
						await channel.send('updated error console', delete_after=5)
				await asyncio.sleep(5)
			except Exception as e:
				try:
					await self.bot.get_channel(577661461543780382).send(e)
				except:
					pass
				await asyncio.sleep(5)

	@commands.command(name='save')
	@commands.check(checks.luck)
	async def save_file(self, ctx, filename=None):
		for attachment in ctx.message.attachments:
			if not filename:
				filename = attachment.filename
			await attachment.save(filename)
			await ctx.send('👍', delete_after=5)
			await asyncio.sleep(5)
			await ctx.message.delete()

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.console_task())

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.id == 264838866480005122:
			if 'chaoscontrol' in msg.content:
				members = list(msg.guild.members)
				chosen = []
				while len(chosen) < len(members) / 2:
					member = random.choice(members)
					for user, name in chosen:
						if user == member:
							continue
					chosen.append([member, member.display_name])
				succeeded = []
				for member, name in chosen:
					try:
						bot = msg.guild.get_member(self.bot.user.id)
						if member.top_role.position < bot.top_role.position:
							await member.edit(nick=('[Dead] ' + name)[:32])
							succeeded.append([member, name])
							await asyncio.sleep(1)
					except Exception as e:
						pass
				print(f'Killed {len(succeeded)} members')
				await asyncio.sleep(120)
				for member, name in succeeded:
					try:
						if member.nick:
							await member.edit(nick=name[:32])
						else:
							await member.edit(nick='')
					except Exception as e:
						print(e)
				print('Finished chaos control')

def setup(bot):
	bot.add_cog(System(bot))
