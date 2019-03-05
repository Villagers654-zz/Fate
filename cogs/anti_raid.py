from discord.ext import commands
from os.path import isfile
from utils import colors
from time import time
import discord
import asyncio
import json

class Anti_Raid:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.locked = []
		self.cd = {}
		if isfile("./data/userdata/anti_raid.json"):
			with open("./data/userdata/anti_raid.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]

	def save_data(self):
		with open("./data/userdata/anti_raid.json", "w") as f:
			json.dump({"toggle": self.toggle}, f)

	@commands.group(name="anti_raid")
	async def _anti_raid(self, ctx):
		if not ctx.invoked_subcommand:
			toggle = "disabled"
			if str(ctx.guild.id) in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.black())
			e.set_author(name="Anti Server Raid", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="Usage", value=
				".anti_raid enable\n"
			    ".anti_raid disable", inline=False)
			e.set_footer(text=f"Current Status: {toggle}")
			await ctx.send(embed=e)

	@_anti_raid.command(name="enable")
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(ban_members=True, manage_roles=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.toggle:
			return await ctx.send("Anti raid is already enabled")
		self.toggle[guild_id] = ctx.guild.name
		await ctx.send("Enabled anti raid")
		self.save_data()

	@_anti_raid.command(name="disable")
	@commands.has_permissions(administrator=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("Anti raid is not enabled")
		del self.toggle[guild_id]
		await ctx.send("Disabled anti raid")
		self.save_data()

	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.toggle:
			if guild_id in self.locked:
				await m.guild.ban(m, reason="Server locked due to raid", delete_message_days=0)
				try:
					await m.send(f"**{m.guild.name}** is currently locked due to an "
						f"attempted raid, you can try rejoining in an hour")
				except:
					pass
				await asyncio.sleep(3600)
				await m.guild.unban(m, reason="Server locked due to raid")
			if m.author.bot:
				return
			now = time()
			if guild_id not in self.cd:
				self.cd[guild_id] = {}
			self.cd[guild_id][str(time())] = (time() + 0.5) - now
			old_keys = []
			for key in self.cd[guild_id].keys():
				if float(key) < time() - 10:
					old_keys.append(key)
			for key in old_keys:
				del self.cd[guild_id][key]
			limit = time() + 1.5
			total = time()
			for key, value in (sorted(self.cd[guild_id].items(), key=lambda kv: kv[1], reverse=True)):
				total += value
			if total > limit:
				self.locked.append(guild_id)
				await asyncio.sleep(3600)
				self.locked.pop(self.locked.index(guild_id))

def setup(bot):
	bot.add_cog(Anti_Raid(bot))
