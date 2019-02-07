from discord.ext import commands
from os.path import isfile
import discord
import json
import time

class AntiPurge:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.cd = {}
		if isfile("./data/userdata/anti_purge.json"):
			with open ("./data/userdata/anti_purge.json", "r") as infile:
				dat = json.load(infile)
				if "toggle" in dat:
					self.toggle = dat["toggle"]

	def save(self):
		with open("./data/userdata/anti_purge.json", "w") as outfile:
			json.dump({"toggle": self.toggle}, outfile, ensure_ascii=False)

	@commands.group(name="anti_purge")
	async def _anti_purge(self, ctx):
		if ctx.invoked_subcommand is None:
			guild_id = str(ctx.guild.id)
			if guild_id not in self.toggle:
				self.toggle[guild_id] = "disabled"
			await ctx.send("**Anti Purge Instructions:**\n"
			               ".anti_purge enable\n"
			               ".anti_purge disable\n"
			               f"**Current Status:** {self.toggle[guild_id]}\n")

	@_anti_purge.command(name="enable")
	@commands.has_permissions(administrator=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			self.toggle[guild_id] = "enabled"
			self.save()
			return await ctx.message.add_reaction("👍")
		self.toggle[guild_id] = "enabled"
		self.save()
		await ctx.message.add_reaction("👍")

	@_anti_purge.command(name="disable")
	@commands.has_permissions(administrator=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			self.toggle[guild_id] = "disabled"
			self.save()
			return await ctx.message.add_reaction("👍")
		self.toggle[guild_id] = "disabled"
		self.save()
		await ctx.message.add_reaction("👍")

	async def on_member_remove(self, m):
		guild_id = str(m.guild.id)
		if guild_id not in self.cd:
			self.cd[guild_id] = 0
		self.cd[guild_id] = time.time() + 10
		if self.cd[guild_id] > time.time() + 21:
			perms = discord.PermissionOverwrite
			perms.kick_members = False
			perms.ban_members = False
			for role in m.guild.roles:
				if role.position > self.bot.get_guild(m.guild.id).get_member(self.bot.user.id).top_role.position:
					pass
				else:
					await role.edit(permissions=perms)

def setup(bot):
	bot.add_cog(AntiPurge(bot))
