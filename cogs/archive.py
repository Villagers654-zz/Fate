from discord.ext import commands
from utils import config
import discord
import os

class Archive(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.saving = {}

	@commands.command(name='archive', description="saves x messages from channel history into a txt")
	@commands.has_permissions(manage_messages=True)
	@commands.cooldown(1, 25, commands.BucketType.channel)
	async def _archive(self, ctx, amount:int):
		if amount > 1000:
			if not config.owner(ctx):
				return await ctx.send('You cannot go over 1000')
		self.saving[str(ctx.channel.id)] = "saving"
		async with ctx.typing():
			log = ""
			async for msg in ctx.channel.history(limit=amount):
				log = f"{msg.created_at.strftime('%I:%M%p')} | {msg.author.display_name}: {msg.content}\n{log}"
			with open(f'./data/{ctx.channel.name}.txt', 'w') as f:
				f.write(log)
			path = os.getcwd() + f"/data/{ctx.channel.name}.txt"
			await ctx.send(file=discord.File(path))
			os.remove(f'./data/{ctx.channel.name}.txt')
			del self.saving[str(ctx.channel.id)]

def setup(bot):
	bot.add_cog(Archive(bot))
