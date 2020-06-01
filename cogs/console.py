import traceback
from discord.ext import commands
import discord
import os; os.system("echo yee")
# ~

class Console(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, msg):
		console_id = 541520201926311986
		if msg.channel.id == console_id:
			if not msg.content.startswith('.') and not msg.author.bot:
				msg = await msg.channel.fetch_message(msg.id)
				msg.content = msg.content.replace('ctx.send', 'msg.channel.send').replace('ctx', 'msg')
				try:
					if msg.content == 'reload':
						self.bot.reload_extension('cogs.console')
						return await msg.channel.send('👍')
					if msg.content.startswith('import') or msg.content.startswith('from'):
						with open('./cogs/console.py', 'r') as f:
							imports, *code = f.read().split('# ~')
							imports += f'{msg.content}\n'
							file = '# ~'.join([imports, *code])
							with open('./cogs/console.py', 'w') as wf:
								wf.write(file)
						self.bot.reload_extension('cogs.console')
						return await msg.channel.send('👍')
					if 'await' in msg.content:
						msg.content = msg.content.replace('await ', '')
						await eval(msg.content)
						if not 'msg.channel.send' in msg.content:
							await msg.channel.send('👍')
						return
					if 'send' in msg.content:
						msg.content = msg.content.replace('send ', '')
						return await msg.channel.send(eval(msg.content))
					eval(msg.content)
					await msg.channel.send('👍')
				except:
					error = str(traceback.format_exc()).replace('\\', '')
					if 'EOL' not in error and 'not defined' not in error and '.' in msg.content:
						await msg.channel.send(f'```css\n{discord.utils.escape_markdown(error)}```')

def setup(bot):
	bot.add_cog(Console(bot))
