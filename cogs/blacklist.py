from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json

class Blacklist:
	def __init__(self, bot):
		self.bot = bot
		self.discord = {}
		self.youtube = {}
		self.all_urls = {}
		if isfile("./data/userdata/blacklist.json"):
			with open("./data/userdata/blacklist.json") as f:
				dat = json.load(f)
				if "discord" in dat and "youtube" in dat and "all_urls" in dat and "images" in dat:
					self.discord = dat["discord"]
					self.youtube = dat["youtube"]
					self.all_urls = dat["all_urls"]

	def save_data(self):
		with open("./data/userdata/blacklist.json") as f:
			json.dump({"discord": self.discord, "youtube": self.youtube, "all_urls": self.all_urls},
			          f, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

	@commands.group(name="blacklist")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _blacklist(self, ctx):
		if ctx.invoked_subcommand is None:
			e = discord.Embed(color=colors.black())
			e.description = \
			"**Message Blacklisting (per-channel):**\n" \
			".blacklist disable blacklisted_object\n" \
			".blacklist discord ~ `blocks discord links`\n" \
			".blacklist youtube ~ `blocks youtube links`\n" \
			".blacklist all_urls ~ `blocks all urls`\n"
			await ctx.send(embed=e)

	@_blacklist.command(name="help")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _help(self, ctx):
		await ctx.send("if you wish you turn off blacklisting, use"
		"`.blacklist disable the_blacklisted_thing`")

	@_blacklist.command(name="discord")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _discord(self, ctx):
		channel_id = str(ctx.channel.id)
		if channel_id not in self.discord:
			self.discord[channel_id] = "enabled"
			await ctx.message.add_reaction("👍")
			return self.save_data()
		await ctx.send("Discord links are already blacklisted")

	@_blacklist.command(name="youtube")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _youtube(self, ctx):
		channel_id = str(ctx.channel.id)
		if channel_id not in self.youtube:
			self.youtube[channel_id] = "enabled"
			await ctx.message.add_reaction("👍")
			return self.save_data()
		await ctx.send("Youtube links are already blacklisted")

	@_blacklist.command(name="all_urls")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _all_urls(self, ctx):
		channel_id = str(ctx.channel.id)
		if channel_id not in self.all_urls:
			self.all_urls[channel_id] = "enabled"
			await ctx.message.add_reaction("👍")
			return self.save_data()
		await ctx.send("All urls are already blacklisted")

	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			await asyncio.sleep(0.5)
			guild_id = str(m.guild.id)
			if guild_id in self.discord:
				if "discord.gg" in m.content.lower().replace(" ", ""):
					return await m.delete()
			if guild_id in self.youtube:
				if "youtu.be" in m.content.lower().replace(" ", ""):
					return await m.delete()
			if guild_id in self.all_urls:
				for i in list("abcdefghijklmnopqrstuvwxyz1234567890"):
					if "." + i in m.content:
						return await m.delete()

def setup(bot):
	bot.add_cog(Blacklist(bot))
