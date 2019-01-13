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
				msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
			except asyncio.TimeoutError:
				async for i in m.channel.history(limit=5):
					await i.delete()
			else:
				await asyncio.sleep(0.5)
				await msg.delete()
				await m.channel.send("next time i ban you")

def setup(bot):
	bot.add_cog(Owner(bot))
