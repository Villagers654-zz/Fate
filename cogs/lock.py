from discord.ext import commands
from os.path import isfile
import discord
import json

class Utility:
	def __init__(self, bot):
		self.bot = bot
		self.lock = {}
		if isfile("./data/userdata/lock.json"):
			with open("./data/userdata/lock.json", "r") as infile:
				dat = json.load(infile)
				if "lock" in dat:
					self.lock = dat["lock"]

	@commands.command(name="lock")
	@commands.has_permissions(administrator=True)
	async def _lock(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			self.lock[guild_id] = "lock-kick"
			with open("./data/userdata/lock.json", "w") as outfile:
				json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
			await ctx.send("Locked the server")
			return await ctx.message.add_reaction("👍")
		if self.lock[guild_id] == "lock-ban":
			self.lock[guild_id] = "lock-kick"
			with open("./data/userdata/lock.json", "w") as outfile:
				json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
			await ctx.send("Changed the server lock type to kick")
			return await ctx.message.add_reaction("👍")
		del self.lock[guild_id]
		with open("./data/userdata/lock.json", "w") as outfile:
			json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	@commands.command(name="lockb")
	@commands.has_permissions(administrator=True)
	async def _lockb(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			self.lock[guild_id] = "lock-ban"
			with open("./data/userdata/lock.json", "w") as outfile:
				json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
			await ctx.send("Locked the server")
			return await ctx.message.add_reaction("👍")
		if self.lock[guild_id] == "lock-kick":
			self.lock[guild_id] = "lock-ban"
			with open("./data/userdata/lock.json", "w") as outfile:
				json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
			await ctx.send("Changed the server lock type to ban")
			return await ctx.message.add_reaction("👍")
		del self.lock[guild_id]
		with open("./data/userdata/lock.json", "w") as outfile:
			json.dump({"lock": self.lock}, outfile, ensure_ascii=False)
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	async def on_member_join(self, m:discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.lock:
			if self.lock[guild_id] == "lock-kick":
				await m.guild.kick(m, reason="Server locked")
			if self.lock[guild_id] == "lock-ban":
				return await m.guild.ban(m, reason="Server locked", delete_message_days=0)

def setup(bot):
	bot.add_cog(Utility(bot))
