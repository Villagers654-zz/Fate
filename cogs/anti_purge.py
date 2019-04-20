from discord.ext import commands
from os.path import isfile
from utils import colors
from time import time
import datetime
import discord
import json

class AntiPurge(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.cd = {}
		if isfile("./data/userdata/anti_purge.json"):
			with open ("./data/userdata/anti_purge.json", "r") as infile:
				dat = json.load(infile)
				if "toggle" in dat:
					self.toggle = dat["toggle"]

	def save_json(self):
		with open("./data/userdata/anti_purge.json", "w") as outfile:
			json.dump({"toggle": self.toggle}, outfile, ensure_ascii=False)

	@commands.group(name="anti_purge")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def _anti_purge(self, ctx):
		if ctx.invoked_subcommand is None:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.red())
			e.set_author(name="| Anti Purge", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = "Bans a user if they attempt to mass kick/ban members or mass delete channels ~ " \
				"this requires my role to be above theirs & can only be toggled by the guilds owner"
			e.add_field(name="◈ Usage ◈", value=
			    ".anti_purge enable\n"
			    ".anti_purge disable\n", inline=False)
			e.set_footer(text=f"Current Status: {toggle}")
			await ctx.send(embed=e)

	@_anti_purge.command(name="enable")
	@commands.bot_has_permissions(ban_members=True)
	async def _enable(self, ctx):
		if ctx.author != ctx.guild.owner:
			return await ctx.send("Only the guild owner can toggle this")
		guild_id = str(ctx.guild.id)
		self.toggle[guild_id] = "enabled"
		self.save_json()
		await ctx.message.add_reaction("👍")

	@_anti_purge.command(name="disable")
	async def _disable(self, ctx):
		if ctx.author != ctx.guild.owner:
			return await ctx.send("Only the guild owner can toggle this")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("Anti-Purge isn't enabled")
		del self.toggle[guild_id]
		self.save_json()
		await ctx.message.add_reaction("👍")

	@commands.Cog.listener()
	async def on_member_remove(self, m):
		guild_id = str(m.guild.id)
		if guild_id in self.toggle:
			async for entry in m.guild.audit_logs(limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=3) < entry.created_at:
					if str(entry.action) in ["AuditLogAction.kick", "AuditLogAction.ban"]:
						user_id = str(entry.user.id)
						now = int(time() / 15)
						if guild_id not in self.cd:
							self.cd[guild_id] = {}
						if user_id not in self.cd[guild_id]:
							self.cd[guild_id][user_id] = [now, 0]
						if self.cd[guild_id][user_id][0] == now:
							self.cd[guild_id][user_id][1] += 1
						else:
							self.cd[guild_id][user_id] = [now, 0]
						if self.cd[guild_id][user_id][1] > 2:
							await m.guild.ban(entry.user, reason="Attempted Purge", delete_message_days=0)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		guild_id = str(channel.guild.id)
		if guild_id in self.toggle:
			async for entry in channel.guild.audit_logs(limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=3) < entry.created_at:
					if str(entry.action) in ["AuditLogAction.channel_delete"]:
						user_id = str(entry.user.id)
						now = int(time() / 15)
						if guild_id not in self.cd:
							self.cd[guild_id] = {}
						if user_id not in self.cd[guild_id]:
							self.cd[guild_id][user_id] = [now, 0]
						if self.cd[guild_id][user_id][0] == now:
							self.cd[guild_id][user_id][1] += 1
						else:
							self.cd[guild_id][user_id] = [now, 0]
						if self.cd[guild_id][user_id][1] > 2:
							try:
								await channel.guild.ban(entry.user, reason="Attempted Purge", delete_message_days=0)
								await channel.guild.owner.send(f"Banned `{entry.user}` in **{channel.guild.name}** for attempting a purge")
							except:
								pass

def setup(bot):
	bot.add_cog(AntiPurge(bot))
