import discord
import asyncio

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	async def on_message(self, msg: discord.Message):
		if isinstance(msg.guild, discord.Guild):
			if msg.guild.name == "Polis":
				if msg.author.id == self.bot.user.id:
					pass
				else:
					ar = self.bot.get_guild(530973099886379008)
					for channel in ar.channels:
						if channel.name == msg.channel.name:
							async for m in channel.history(limit=1):
								if msg.content.lower() in m.content.lower():
									pass
								else:
									await channel.send(f"{msg.content}")
									await asyncio.sleep(0.5)
									await msg.delete()
			if msg.guild.name == "[Avapzian Regime]":
				polis = self.bot.get_guild(534949405824909323)
				for channel in polis.channels:
					if channel.name == msg.channel.name:
						await channel.send(f"**{msg.author.name}:** {msg.content}")

def setup(bot):
	bot.add_cog(Owner(bot))
