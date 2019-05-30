from discord.ext import commands
from utils import checks, colors
import discord
import asyncio
import random

class System(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dir = './data/stats.json'
		self.output_log = ''
		self.error_log = ''
		self.last_voice_state = ''

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

	async def activity_task(self):
		while True:
			e = discord.Embed(color=colors.fate())
			voice_state = ''
			for guild_id in self.bot.voice_calls:
				guild = self.bot.get_guild(int(guild_id))
				voice_state += f'• **[`{guild.name}`]**\n'
			if not voice_state:
				voice_state = 'None'
			e.add_field(name='Voice State', value=voice_state, inline=False)
			channel = self.bot.get_channel(577661440442236931)
			msg = await channel.fetch_message(581773493738274826)
			if voice_state != self.last_voice_state:
				await msg.edit(embed=e)
				self.last_voice_state = voice_state
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

	@commands.command(name='removenick')
	@commands.check(checks.luck)
	async def remove_nick(self, ctx):
		bot = ctx.guild.get_member(self.bot.user.id)
		await bot.edit(nick='')
		await ctx.message.delete()

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.console_task())
		self.bot.loop.create_task(self.activity_task())

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.id == 264838866480005122:
			if 'chaoscontrol' in msg.content:
				chosen = []
				indexed = []
				bot = msg.guild.get_member(self.bot.user.id)
				async for m in msg.channel.history(limit=20):
					if m.author.top_role.position < bot.top_role.position:
						if m.author.id not in indexed:
							if random.randint(1, 2) == 1:
								chosen.append([m.author, m.author.display_name])
							indexed.append(m.author.id)
				succeeded = []
				for member, name in chosen:
					try:
						await member.edit(nick=('[Snapped] ' + name)[:32])
						succeeded.append([member, name])
						await asyncio.sleep(1)
					except:
						pass
				kill_count = len(succeeded)
				await msg.channel.send(f'Killed {kill_count} {"user" if kill_count == 1 else "users"}')
				await asyncio.sleep(120)
				for member, name in succeeded:
					try:
						if member.nick:
							await member.edit(nick=name[:32])
						else:
							await member.edit(nick='')
					except:
						pass

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if before.id == self.bot.user.id:
			if before.name == after.name:
				if before.display_name != after.display_name:
					bot = before.guild.get_member(self.bot.user.id)
					await bot.edit(nick='')

def setup(bot):
	bot.add_cog(System(bot))
