from discord.ext import commands
from utils import checks
import discord
import json

class User(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dir = './data/config.json'

	def get_config(self):
		with open(self.dir, 'r') as config:
			return json.load(config)

	def update_config(self, config):
		with open(self.dir, 'w') as f:
			json.dump(config, f, ensure_ascii=False)

	@commands.command(name='changepresence', aliases=['cp'])
	@commands.check(checks.luck)
	async def change_presence(self, ctx, *, presence):
		config = self.get_config()  # type: dict
		config['presence'] = presence
		self.update_config(config)
		await ctx.message.add_reaction('👍')

	@commands.command(name='block')
	@commands.check(checks.luck)
	async def block(self, ctx, user: discord.Member):
		config = self.get_config()  # type: dict
		if 'blocked' not in config:
			config['blocked'] = []
		config['blocked'].append(user.id)
		self.update_config(config)
		await ctx.send(f'Blocked {user}')

	@commands.command(name='unblock')
	@commands.check(checks.luck)
	async def unblock(self, ctx, user: discord.Member):
		config = self.get_config()  # type: dict
		index = config['blocked'].index(user.id)
		config['blocked'].pop(index)
		self.update_config(config)
		await ctx.send(f'Unblocked {user}')

def setup(bot):
	bot.add_cog(User(bot))
