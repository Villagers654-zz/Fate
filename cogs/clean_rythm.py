from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json

class Utility:
	def __init__(self, bot):
		self.bot = bot
		self.identifier = {}
		if isfile("./data/config/clean_rythm.json"):
			with open("./data/config/clean_rythm.json", "r") as infile:
				dat = json.load(infile)
				if "identifier" in dat:
					self.identifier = dat["identifier"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.group(name="clean_rythm")
	async def _clean_rythm(self, ctx):
		if ctx.invoked_subcommand is None:
			if str(ctx.guild.id) not in self.identifier:
				self.identifier[str(ctx.guild.id)] = "Disabled"
			await ctx.send(f'**Clean Rythm Instructions:**\n'
			               f'.clean_rythm enable ~ `enables clean_rythm`\n'
			               f'.clean_rythm disable ~ `disables clean_rythm`\n'
			               f'**Current Status:** {self.identifier[str(ctx.guild.id)]}')

	@_clean_rythm.command(name="enable")
	async def enable(self, ctx):
		self.identifier[str(ctx.guild.id)] = "Enabled"
		with open("./data/config/clean_rythm.json", "w") as outfile:
			json.dump({"identifier": self.identifier}, outfile, ensure_ascii=False)
		await ctx.send("Enabled clean_rythm", delete_after=20)
		await asyncio.sleep(20)
		await ctx.message.delete()

	@_clean_rythm.command(name="disable")
	async def disable(self, ctx):
		self.identifier[str(ctx.guild.id)] = "Disabled"
		with open("./data/config/clean_rythm.json", "w") as outfile:
			json.dump({"identifier": self.identifier}, outfile, ensure_ascii=False)
		await ctx.send("Disabled clean_rythm", delete_after=20)
		await asyncio.sleep(20)
		await ctx.message.delete()

	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):
			listed = ["!help", "!play", "!skip", "!np", "!lyrics", "!queue", "!q", "!clear", "!remove", "!repeat", "!dc", "!disconnect",
			          "!pause", "!resume"]
			if str(m.guild.id) not in self.identifier:
				pass
			else:
				if self.identifier[str(m.guild.id)] == "Enabled":
					if m.author.id == 235088799074484224:
						await asyncio.sleep(9)
						await m.delete()
					for i in listed:
						if m.content.startswith(i):
							if m.content.startswith("!play"):
								await asyncio.sleep(1)
								await m.delete()
							else:
								if i == "!lyrics":
									await asyncio.sleep(60)
									await m.delete()
								else:
									await asyncio.sleep(10)
									await m.delete()

def setup(bot):
	bot.add_cog(Utility(bot))
