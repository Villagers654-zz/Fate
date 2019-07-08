from discord.ext import commands
import discord

class Example:
	def __init__(self, bot):
		self.bot = bot
		self.last = {}

	@commands.command(name='snipe')
	async def snipe(self, ctx):
		if ctx.channel.id not in self.last:
			return await ctx.send('nothing to snipe')
		msg = self.last[ctx.channel.id]  # type: discord.Message
		await ctx.send(msg.content)

	@commands.Cog.listener()
	async def on_message_delete(self, msg):
		self.last[msg.channel.id] = msg

def setup(bot):
	bot.add_cog(Example(bot))
