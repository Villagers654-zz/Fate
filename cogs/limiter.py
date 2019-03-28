from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json

class Utility:
	def __init__(self, bot):
		self.bot = bot
		self.images = {}
		if isfile("./data/userdata/limiter.json"):
			with open("./data/userdata/limiter.json", "r") as infile:
				dat = json.load(infile)
				if "images" in dat:
					self.images = dat["images"]

	def save_data(self):
		with open("./data/userdata/limiter.json", "w") as outfile:
			json.dump({"images": self.images}, outfile, ensure_ascii=False)

	@commands.group(name="limit", aliases=["limiter"])
	@commands.has_permissions(manage_guild=True)
	async def _limit(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send('**Channel Limiter Instructions:**\n'
			               '.limit images ~ `toggles image limiter (per-channel)`\n'
			               'only allows messages with files attached\n')

	@_limit.command(name="images")
	@commands.has_permissions(manage_channels=True)
	async def _images(self, ctx):
		guild_id = str(ctx.guild.id)
		channel_id = str(ctx.channel.id)
		if guild_id not in self.images:
			self.images[guild_id] = {}
		if channel_id not in self.images[guild_id]:
			self.images[guild_id][channel_id] = "enabled"
			await ctx.message.add_reaction("👍")
			await ctx.send(f"Limited **{ctx.channel.name}** to only allow images")
		else:
			del self.images[guild_id][channel_id]
			await ctx.message.add_reaction("👍")
			await ctx.send("Disabled channel limiter")
		self.save_data()

	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			channel_id = str(m.channel.id)
			# image limiter
			for i in ['.limit', 'limited **', 'disabled channel']:
				if m.content.lower().startswith(i):
					return
			await asyncio.sleep(0.5)
			if guild_id in self.images:
				if channel_id in self.images[guild_id]:
					if len(m.attachments) < 1:
						await m.delete()

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.images:
			del self.images[guild_id]
			self.save_data()

def setup(bot):
	bot.add_cog(Utility(bot))
