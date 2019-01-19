from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json

class Legit:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def tm(ctx):
		return ctx.author.id in [264838866480005122, 355026215137968129]

# ~== Test ==~

#	async def on_message(self, m: discord.Message):
#		if m.channel.id == 529705827716825098:
#			if m.author.id == 529287770233896961:
#				if len(m.embeds) >= 1:
#					await asyncio.sleep(15)
#					try:
#						await m.delete()
#					except commands.MissingPermissions:
#						c = self.bot.get_channel(514213558549217330)
#						await c.send("I'm missing permissions in the livechat")
#					except discord.errors.NotFound:
#						pass
#					except Exception as e:
#						c = self.bot.get_channel(514213558549217330)
#						await c.send(f"Livechat error: {e}")

	@commands.command()
	@commands.check(luck)
	async def clearembeds(self, ctx):
		async for msg in ctx.channel.history():
			if len(msg.embeds) >= 1:
				await msg.delete()

def setup(bot):
	bot.add_cog(Legit(bot))
