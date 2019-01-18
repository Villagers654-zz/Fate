import discord
import asyncio

class AR:
	def __init__(self, bot):
		self.bot = bot

	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):
			if m.channel.id == 533817312634208257:
				if m.id is not 534039043483369482:
					await asyncio.sleep(3600)
					try:
						await m.delete()
					except:
						pass

	async def on_ready(self):
		async for msg in self.bot.get_channel(533817312634208257).history(limit=100):
			if msg.content.startswith("```Hello there!"):
				pass
			else:
				await asyncio.sleep(1)
				await msg.delete()

def setup(bot):
	bot.add_cog(AR(bot))
