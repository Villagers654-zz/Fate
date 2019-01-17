import discord
import asyncio

class Owner:
	def __init__(self, bot):
		self.bot = bot

	async def on_message(self, m:discord.Message):
		if m.channel.id == 533817312634208257:
			if m.id is not 534039043483369482:
				await asyncio.sleep(3600)
				try:
					await m.delete()
				except:
					pass

def setup(bot):
	bot.add_cog(Owner(bot))
