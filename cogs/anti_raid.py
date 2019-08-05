from datetime import datetime, timedelta
from discord.ext import commands
from os.path import isfile
from utils import colors
from time import time
import discord
import asyncio
import json

class Anti_Raid(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.locked = []
		self.last = {}
		self.join_cd = {}
		self.macro_cd = {}
		self.cd = {}
		if isfile("./data/userdata/anti_raid.json"):
			with open("./data/userdata/anti_raid.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]

	def save_data(self):
		with open("./data/userdata/anti_raid.json", "w") as f:
			json.dump({"toggle": self.toggle}, f)

	async def ensure_permissions(self, guild):
		guild_id = str(guild.id)
		bot = guild.get_member(self.bot.user.id)
		perms = [perm for perm, value in bot.guild_permissions if value]
		required = ['view_audit_log', 'ban_members']
		for perm in required:
			if perm not in perms:
				del self.toggle[guild_id]
				self.save_data()
				for channel in guild.text_channels:
					if channel.permissions_for(guild.me).send_messages:
						await guild.owner.send(f'Disabled anti raid, missing {perm} permissions')
						break
				return False
		return True

	@commands.group(name='antiraid', aliases=['anti_raid'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(embed_links=True)
	async def _anti_raid(self, ctx):
		if not ctx.invoked_subcommand:
			toggle = "disabled"
			if str(ctx.guild.id) in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.red())
			e.set_author(name="Anti Raid", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = 'Prevents mass-join and mass-kick/ban raids'
			e.add_field(name="Usage", value=
				".antiraid enable\n"
			    ".antiraid disable", inline=False)
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

	@commands.Cog.listener()
	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		user_id = str(m.id)
		if guild_id in self.toggle:
			required_permission = await self.ensure_permissions(m.guild)
			if not required_permission:
				return
			if guild_id in self.locked:
				await m.guild.ban(m, reason="Server locked due to raid", delete_message_days=0)
				try:
					await m.send(f"**{m.guild.name}** is currently locked due to an "
						f"attempted raid, you can try rejoining in an hour")
				except:
					pass
				await asyncio.sleep(3600)
				return await m.guild.unban(m, reason="Server locked due to raid")
			if m.bot:
				return
			if guild_id not in self.last:
				self.last[guild_id] = {}
			self.last[guild_id][user_id] = time()
			now = int(time() / 20)
			if guild_id not in self.join_cd:
				self.join_cd[guild_id] = [now, 0]
			if self.join_cd[guild_id][0] == now:
				self.join_cd[guild_id][1] += 1
			else:
				self.join_cd[guild_id] = [now, 0]
			if self.join_cd[guild_id][1] > 4:
				self.locked.append(guild_id)
				for junkie in list(filter(lambda id: self.last[guild_id][id] > time() - 15, self.last[guild_id].keys())):
					await m.guild.ban(junkie, reason="raid")
					await junkie.send(f'**{m.guild.name}** is currently locked due to an attempted raid, you can try rejoining in an hour')
				await asyncio.sleep(3600)
				self.locked.pop(self.locked.index(guild_id))

	@commands.Cog.listener()
	async def on_member_remove(self, m):
		guild_id = str(m.guild.id)
		if guild_id in self.toggle:
			required_permission = await self.ensure_permissions(m.guild)
			if not required_permission:
				return
			async for entry in m.guild.audit_logs(limit=1):
				if entry.created_at > datetime.utcnow() - timedelta(seconds=3):
					actions = [discord.AuditLogAction.kick, discord.AuditLogAction.ban]
					if entry.action in actions:
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
							if m.id == self.bot.user.id:
								await m.guild.leave()
								print(f'Left {m.guild.name} for my user attempting a purge')
							await m.guild.ban(entry.user, reason="Attempted Purge", delete_message_days=0)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel: discord.TextChannel):
		guild = channel.guild
		guild_id = str(guild.id)
		if guild_id in self.toggle:
			required_permission = await self.ensure_permissions(guild)
			if not required_permission:
				return
			async for entry in guild.audit_logs(limit=1):
				if datetime.utcnow() - timedelta(seconds=3) < entry.created_at:
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
								await guild.ban(entry.user, reason="Attempted Purge", delete_message_days=0)
								await guild.owner.send(f"Banned `{entry.user}` in **{guild.name}** for attempting a purge")
							except:
								pass

	@commands.Cog.listener()
	async def on_guild_update(self, before, after):
		guild_id = str(before.id); guild = after
		if guild_id in self.toggle:
			if before.name != after.name:
				required_permission = await self.ensure_permissions(guild)
				if not required_permission:
					return
				if 'discord.gg' in guild.name or 'discord,gg' in guild.name:
					async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
						try:
							await guild.ban(entry.user, reason='Attempted Raid')
						except:
							try: await guild.owner.send(f'Failed to ban {entry.user} for attempting a raid')
							except: pass
						await guild.edit(name=before.name)

def setup(bot):
	bot.add_cog(Anti_Raid(bot))
