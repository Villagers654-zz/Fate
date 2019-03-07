from discord.ext import commands
from os.path import isfile
from utils import colors
import datetime
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

	def is_guild_owner(ctx):
		return ctx.author.id == ctx.guild.owner.id

	@commands.group(name="anti_purge")
	async def _anti_purge(self, ctx):
		if ctx.invoked_subcommand is None:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.red())
			e.set_author(name="| Anti Purge", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = "Bans a user if they attempt to mass kick/ban members ~ " \
				"this requires my role to be above theirs & can only be toggled by the guilds owner"
			e.add_field(name="◈ Usage ◈", value=
			    ".anti_purge enable\n"
			    ".anti_purge disable\n", inline=False)
			e.set_footer(text=f"Current Status: {toggle}")
			await ctx.send(embed=e)

	@_anti_purge.command(name="enable")
	@commands.check(is_guild_owner)
	@commands.bot_has_permissions(ban_members=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		self.toggle[guild_id] = "enabled"
		self.save()
		await ctx.message.add_reaction("👍")

	@_anti_purge.command(name="disable")
	@commands.check(is_guild_owner)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("Anti-Purge isn't enabled")
		del self.toggle[guild_id]
		self.save()
		await ctx.message.add_reaction("👍")

	async def on_member_remove(self, m):
		guild_id = str(m.guild.id)
		if guild_id in self.toggle:
			async for entry in m.guild.audit_logs(limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=3) < entry.created_at:
					if str(entry.action) in ["AuditLogAction.kick", "AuditLogAction.ban"]:
						user_id = str(entry.user.id)
						if guild_id not in self.cd:
							self.cd[guild_id] = {}
						if user_id not in self.cd[guild_id]:
							self.cd[guild_id][user_id] = 0
						self.cd[guild_id][user_id] = time.time() + 10
						if self.cd[guild_id][user_id] > time.time() + 21:
							await m.guild.ban(entry.user, reason="Attempted Purge", delete_message_days=0)

def setup(bot):
	bot.add_cog(AntiPurge(bot))
