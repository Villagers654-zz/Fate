from discord.ext import commands
from os.path import isfile
import discord
import json
import time

class Lock(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.lock = {}
		self.cd = {}
		if isfile("./data/userdata/lock.json"):
			with open("./data/userdata/lock.json", "r") as infile:
				dat = json.load(infile)
				if "lock" in dat:
					self.lock = dat["lock"]

	async def save_data(self):
		await self.bot.save_json("./data/userdata/lock.json", {"lock": self.lock})

	@commands.command(name="lock")
	@commands.has_permissions(administrator=True)
	async def _lock(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			self.lock[guild_id] = "lock-kick"
			await self.save_data()
			await ctx.send("Locked the server")
			return await ctx.message.add_reaction("👍")
		if self.lock[guild_id] != "lock-kick":
			self.lock[guild_id] = "lock-kick"
			await self.save_data()
			await ctx.send("Changed the server lock type to kick")
			return await ctx.message.add_reaction("👍")
		del self.lock[guild_id]
		await self.save_data()
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	@commands.command(name="lockb")
	@commands.has_permissions(administrator=True)
	async def _lockb(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			self.lock[guild_id] = "lock-ban"
			await self.save_data()
			await ctx.send("Locked the server")
			return await ctx.message.add_reaction("👍")
		if self.lock[guild_id] != "lock-ban":
			self.lock[guild_id] = "lock-ban"
			await self.save_data()
			await ctx.send("Changed the server lock type to ban")
			return await ctx.message.add_reaction("👍")
		del self.lock[guild_id]
		await self.save_data()
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	@commands.command(name="lockm")
	@commands.has_permissions(administrator=True)
	async def _lockm(self, ctx):
		def check_roles():
			for i in ctx.guild.roles:
				if i.name.lower() == "muted":
					return True
			return False
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			if check_roles() is False:
				return await ctx.send("Failed to find a muted role")
			self.lock[guild_id] = "lock-mute"
			await self.save_data()
			await ctx.send("Locked the server")
			return await ctx.message.add_reaction("👍")
		if self.lock[guild_id] != "lock-mute":
			if check_roles() is False:
				return await ctx.send("Failed to find a muted role")
			self.lock[guild_id] = "lock-mute"
			await self.save_data()
			await ctx.send("Changed the server lock type to mute")
			return await ctx.message.add_reaction("👍")
		del self.lock[guild_id]
		await self.save_data()
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	@commands.command(name="unlock")
	@commands.has_permissions(administrator=True)
	async def _unlock(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.lock:
			await ctx.send("there is currently no active lock")
			return await ctx.message.add_reaction("⚠")
		del self.lock[guild_id]
		await self.save_data()
		await ctx.send("Unlocked the server")
		await ctx.message.add_reaction("👍")

	@commands.Cog.listener()
	async def on_member_join(self, m:discord.Member):
		guild_id = str(m.guild.id)
		member_id = str(m.id)
		if guild_id in self.lock:
			if self.lock[guild_id] == "lock-kick":
				await m.guild.kick(m, reason="Server locked")
				try:
					await m.send(f"**{m.guild.name}** is currently locked. Contact an admin or try again later")
				except:
					pass
			if self.lock[guild_id] == "lock-ban":
				await m.guild.ban(m, reason="Server locked", delete_message_days=0)
				if member_id not in self.cd:
					self.cd[member_id] = 0
				if self.cd[member_id] < time.time():
					try:
						await m.send(f"**{m.guild.name}** is currently locked. Contact an admin or try again later")
					except:
						pass
					self.cd[member_id] = time.time() + 25
			if self.lock[guild_id] == "lock-mute":
				role = None  # type: discord.Role
				for i in m.guild.roles:
					if i.name.lower() == "muted":
						role = i
				if role is None:
					await m.channel.send("this server does not have a muted role")
				else:
					if role in m.roles:
						pass
					else:
						await m.add_roles(role)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.lock:
			del self.lock[guild_id]
			await self.save_data()

def setup(bot):
	bot.add_cog(Lock(bot))
