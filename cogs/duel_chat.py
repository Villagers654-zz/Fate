import discord
import asyncio
import requests

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	async def on_message(self, msg: discord.Message):
		if isinstance(msg.guild, discord.Guild):
			try:
				if msg.guild.name == "Polis":
					if msg.author.id == self.bot.user.id:
						pass
					else:
						ar = self.bot.get_guild(470961230362837002)
						for channel in ar.channels:
							if channel.name == msg.channel.name:
								if msg.attachments:
									for attachment in msg.attachments:
										await channel.send(f"**{msg.author.name}:** {msg.content}",
										                   file=discord.File(requests.get(attachment).content))
									return
								await channel.send(f"{msg.content}")
								await asyncio.sleep(0.5)
								await msg.delete()
				if msg.guild.name.startswith("4B4T"):
					polis = self.bot.get_guild(534949405824909323)
					for channel in polis.channels:
						if channel.name == msg.channel.name:
							if msg.attachments:
								for attachment in msg.attachments:
									await channel.send(f"**{msg.author.name}:** {msg.content}",
									                   file=discord.File(requests.get(attachment).content))
								return
							if msg.embeds:
								for embed in msg.embeds:
									await channel.send(f"**{msg.author.name}:** {msg.content}", embed=embed)
								return
							await channel.send(f"**{msg.author.name}:** {msg.content}")
			except:
				pass

	async def on_typing(self, c, m, when):
		if isinstance(c, discord.TextChannel):
			if c.guild.name.startswith("Polis"):
				if m.id == self.bot.user.id:
					pass
				else:
					ar = self.bot.get_guild(470961230362837002)
					for channel in ar.channels:
						if channel.name == c.name:
							await channel.trigger_typing()

def setup(bot):
	bot.add_cog(Owner(bot))
