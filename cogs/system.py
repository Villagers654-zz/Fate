from discord.ext import commands
from utils import checks
import discord
import asyncio

class System(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.output_log = ''
		self.error_log = ''

	async def console_task(self):
		while True:
			try:
				channel = self.bot.get_channel(571476425757163540)
				output_msg = await channel.fetch_message(571476486847070208)
				with open('/home/luck/.pm2/logs/fate-out.log', 'r') as f:
					new_log = f'```{f.read()[-1994:]}```'
					if new_log != self.output_log:
						self.output_log = new_log
						await output_msg.edit(content=new_log)
						await channel.send('updated clean console', delete_after=5)
				output_msg = await channel.fetch_message(571527005435330571)
				with open('/home/luck/.pm2/logs/fate-error.log', 'r') as f:
					new_log = f'```{discord.utils.escape_markdown(f.read())[-1994:]}```'
					if new_log != self.error_log:
						self.error_log = new_log
						await output_msg.edit(content=new_log)
						await channel.send('updated error console', delete_after=5)
				await asyncio.sleep(2.5)
			except Exception as e:
				complete = False
				while not complete:
					try:
						await self.bot.get_channel(571171616214614028).send(e)
					except:
						pass
					else:
						break
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

def setup(bot):
	bot.add_cog(System(bot))
