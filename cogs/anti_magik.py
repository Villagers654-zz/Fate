from discord.ext import commands
import discord
import asyncio

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	async def on_message(self, m: discord.Message):
		if m.content.lower().startswith("pls magik <@264838866480005122>"):
			def pred(m):
				return m.author.id == 270904126974590976 and m.channel == m.channel
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=120.0)
			except asyncio.TimeoutError:
				async for i in m.channel.history(limit=5):
					await i.delete()
			else:
				await asyncio.sleep(0.5)
				await msg.delete()
				await m.channel.send("next time i ban you")
		commands = ["t!avatar <@264838866480005122>", ".avatar <@264838866480005122>", "./avatar <@264838866480005122>"]
		bots = [506735111543193601, 418412306981191680, 172002275412279296]
		if m.content.lower() in commands:
			def pred(m):
				return m.author.id in bots and m.channel == m.channel
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=60.0)
			except asyncio.TimeoutError:
				async for i in m.channel.history(limit=5):
					await i.delete()
			else:
				await asyncio.sleep(0.5)
				await msg.delete()
				await m.channel.send("next time i ban you")

def setup(bot):
	bot.add_cog(Owner(bot))
