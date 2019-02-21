from discord.ext import commands
from os.path import isfile
from utils import colors
import datetime
import discord
import asyncio
import json
import time

class Logger:
	def __init__(self, bot):
		self.bot = bot
		self.channel = {}
		self.messages = {}
		if isfile("./data/userdata/logger.json"):
			with open("./data/userdata/logger.json", "r") as infile:
				dat = json.load(infile)
				if "channel" in dat:
					self.channel = dat["channel"]

	def save(self):
		with open("./data/userdata/logger.json", "w") as outfile:
			json.dump({"channel": self.channel}, outfile, ensure_ascii=False)

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]

	@commands.group(name="logger")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _logger(self, ctx):
		if ctx.invoked_subcommand is None:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.channel:
				toggle = "enabled"
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Logger Usage", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = \
				f"**Current Status:** {toggle}\n" \
				".logger setchannel {channel}\n" \
				".logger disable\n"
			await ctx.send(embed=e)

	@_logger.command(name="disable")
	@commands.cooldown(1, 1, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]
			self.save()
			return await ctx.send("Disabled logging")
		await ctx.send("Logging is not enabled")

	@_logger.command(name="setchannel")
	@commands.cooldown(1, 1, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if channel is None:
			self.channel[guild_id] = ctx.channel.id
			self.save()
			return await ctx.send(f"I will now log actions to {ctx.channel.mention}")
		self.channel[guild_id] = channel.id
		self.save()
		await ctx.send(f"I will now log actions to {channel.mention}")

	async def on_message(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id not in self.messages:
			self.messages[guild_id] = []
		self.messages[guild_id].append(m.id)

	async def on_guild_update(self, before, after):
		guild_id = str(after.id)
		if guild_id in self.channel:
			if before.name != after.name:
				channel = self.bot.get_channel(self.channel[guild_id])
				e = discord.Embed(color=colors.cyan())
				e.title = "Guild Update"
				e.set_thumbnail(url=before.icon_url)
				e.add_field(name="Type: Name", value= \
				f"Before: `{before.name}`\n" \
				f"After: `{after.name}`")
				await channel.send(embed=e)

	async def on_guild_role_create(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "Role Created"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}"
			await channel.send(embed=e)

	async def on_guild_role_delete(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "Role Deleted"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}\n" \
				f"Color: {role.color}\n" \
				f"Users: [{len(list(role.members))}]"
			await channel.send(embed=e)

	async def on_guild_role_update(self, before, after):
		guild_id = str(before.guild.id)
		changed_permissions = ""
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "Role Updated"
			e.set_thumbnail(url=before.guild.icon_url)
			if before.name != after.name:
				e.add_field(name="Name:", value=f"Before: {before.name}\nAfter: {after.name}", inline=False)
			e.description = f"Role: {after.name}"
			if before.color != after.color:
				e.add_field(name="Color:", value=f"Before: {before.color}\nAfter: {after.color}")
			if before.permissions.value != after.permissions.value:
				if before.permissions.administrator != after.permissions.administrator:
					if before.permissions.administrator:
						changed_permissions += "❌ administrator\n"
					else:
						changed_permissions += "➕ administrator\n"
				if before.permissions.create_instant_invite != after.permissions.create_instant_invite:
					if before.permissions.create_instant_invite:
						changed_permissions += "❌ create instant invites\n"
					else:
						changed_permissions += "➕ create instant invites\n"
				if before.permissions.kick_members != after.permissions.kick_members:
					if before.permissions.kick_members:
						changed_permissions += "❌ kick members\n"
					else:
						changed_permissions += "➕ kick members\n"
				if before.permissions.ban_members != after.permissions.ban_members:
					if before.permissions.ban_members:
						changed_permissions += "❌ ban members\n"
					else:
						changed_permissions += "➕ ban members\n"
				if before.permissions.manage_channels != after.permissions.manage_channels:
					if before.permissions.manage_channels:
						changed_permissions += "❌ manage channels\n"
					else:
						changed_permissions += "➕ manage channels\n"
				if before.permissions.manage_guild != after.permissions.manage_guild:
					if before.permissions.manage_guild:
						changed_permissions += "❌ manage guild\n"
					else:
						changed_permissions += "➕ manage guild\n"
				if before.permissions.add_reactions != after.permissions.add_reactions:
					if before.permissions.add_reactions:
						changed_permissions += "❌ add reactions\n"
					else:
						changed_permissions += "➕ add reactions\n"
				if before.permissions.view_audit_log != after.permissions.view_audit_log:
					if before.permissions.view_audit_log:
						changed_permissions += "❌ view audit log\n"
					else:
						changed_permissions += "➕ view audit log\n"
				if before.permissions.priority_speaker != after.permissions.priority_speaker:
					if before.permissions.priority_speaker:
						changed_permissions += "❌ priority speaker\n"
					else:
						changed_permissions += "➕ priority speaker\n"
				if before.permissions.read_messages != after.permissions.read_messages:
					if before.permissions.read_messages:
						changed_permissions += "❌ read messages\n"
					else:
						changed_permissions += "➕ read messages\n"
				if before.permissions.send_messages != after.permissions.send_messages:
					if before.permissions.send_messages:
						changed_permissions += "❌ send messages\n"
					else:
						changed_permissions += "➕ send messages\n"
				if before.permissions.send_tts_messages != after.permissions.send_tts_messages:
					if before.permissions.send_tts_messages:
						changed_permissions += "❌ send tts messages\n"
					else:
						changed_permissions += "➕ send tts messages\n"
				if before.permissions.manage_messages != after.permissions.manage_messages:
					if before.permissions.manage_messages:
						changed_permissions += "❌ manage messages\n"
					else:
						changed_permissions += "➕ manage messages\n"
				if before.permissions.embed_links != after.permissions.embed_links:
					if before.permissions.embed_links:
						changed_permissions += "❌ embed links\n"
					else:
						changed_permissions += "➕ embed links\n"
				if before.permissions.attach_files != after.permissions.attach_files:
					if before.permissions.attach_files:
						changed_permissions += "❌ attach files\n"
					else:
						changed_permissions += "➕ attach files\n"
				if before.permissions.read_message_history != after.permissions.read_message_history:
					if before.permissions.read_message_history:
						changed_permissions += "❌ read message history\n"
					else:
						changed_permissions += "➕ read message history\n"
				if before.permissions.mention_everyone != after.permissions.mention_everyone:
					if before.permissions.mention_everyone:
						changed_permissions += "❌ mention everyone\n"
					else:
						changed_permissions += "➕ mention everyone\n"
				if before.permissions.external_emojis != after.permissions.external_emojis:
					if before.permissions.external_emojis:
						changed_permissions += "❌ external emojis\n"
					else:
						changed_permissions += "➕ external emojis\n"
				if before.permissions.connect != after.permissions.connect:
					if before.permissions.connect:
						changed_permissions += "❌ connect\n"
					else:
						changed_permissions += "➕ connect\n"
				if before.permissions.speak != after.permissions.speak:
					if before.permissions.speak:
						changed_permissions += "❌ speak\n"
					else:
						changed_permissions += "➕ speak\n"
				if before.permissions.mute_members != after.permissions.mute_members:
					if before.permissions.mute_members:
						changed_permissions += "❌ mute members\n"
					else:
						changed_permissions += "➕ mute members\n"
				if before.permissions.deafen_members != after.permissions.deafen_members:
					if before.permissions.deafen_members:
						changed_permissions += "❌ deafen members\n"
					else:
						changed_permissions += "➕ deafen members\n"
				if before.permissions.move_members != after.permissions.move_members:
					if before.permissions.move_members:
						changed_permissions += "❌ move members\n"
					else:
						changed_permissions += "➕ move members\n"
				if before.permissions.use_voice_activation != after.permissions.use_voice_activation:
					if before.permissions.use_voice_activation:
						changed_permissions += "❌ use voice activation\n"
					else:
						changed_permissions += "➕ use voice activation\n"
				if before.permissions.change_nickname != after.permissions.change_nickname:
					if before.permissions.change_nickname:
						changed_permissions += "❌ change nickname\n"
					else:
						changed_permissions += "➕ change nickname\n"
				if before.permissions.manage_nicknames != after.permissions.manage_nicknames:
					if before.permissions.manage_nicknames:
						changed_permissions += "❌ manage nicknames\n"
					else:
						changed_permissions += "➕ manage nicknames\n"
				if before.permissions.manage_roles != after.permissions.manage_roles:
					if before.permissions.manage_roles:
						changed_permissions += "❌ manage roles\n"
					else:
						changed_permissions += "➕ manage roles\n"
				if before.permissions.manage_webhooks != after.permissions.manage_webhooks:
					if before.permissions.manage_webhooks:
						changed_permissions += "❌ manage webhooks\n"
					else:
						changed_permissions += "➕ manage webhooks\n"
				if before.permissions.manage_emojis != after.permissions.manage_emojis:
					if before.permissions.manage_emojis:
						changed_permissions += "❌ manage emojis\n"
					else:
						changed_permissions += "➕ manage emojis\n"
				e.add_field(name="Perms", value=changed_permissions, inline=False)
			await channel.send(embed=e)

	async def on_message_edit(self, before, after):
		if before.pinned == after.pinned:
			guild_id = str(before.guild.id)
			if guild_id in self.channel:
				if before.channel.id != self.channel[guild_id]:
					if len(after.embeds) == 0:
						channel = self.bot.get_channel(self.channel[guild_id])
						e = discord.Embed(color=colors.pink())
						e.title = "Message Edited"
						e.set_thumbnail(url=before.author.avatar_url)
						e.description = f"**Author Name:** {before.author.display_name}\n" \
							f"**Channel:** {before.channel.mention}"
						e.add_field(name="Before:", value=f"`{before.content}`", inline=False)
						e.add_field(name="After:", value=f"`{after.content}`", inline=False)
						await channel.send(embed=e)

	async def on_message_delete(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			user = ""
			async for entry in m.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			if not user:
				user = "Author"
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.purple())
			e.title = "Message Deleted"
			e.set_thumbnail(url=m.author.avatar_url)
			e.description = f"**Author:** {m.author}\n" \
				f"**Deleted by:** {user}\n" \
				f"**Channel:** {m.channel.mention}"
			if m.pinned is True:
				e.description += f"\nMsg was pinned"
			if len(m.embeds) > 0:
				if m.content == "":
					m.content = "`Embed`"
			if m.content == "":
				m.content = "`None`"
			e.add_field(name="Content:", value=f"{m.content}", inline=False)
			if len(m.attachments) > 0:
				e.add_field(name="Cached Images:", value="They may not show")
			for attachment in m.attachments:
				e.set_image(url=attachment.proxy_url)
			await channel.send(embed=e)

	async def on_raw_message_delete(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.channel:
			await asyncio.sleep(1)
			if guild_id not in self.messages:
				self.messages[guild_id] = []
			if payload.message_id not in self.messages[guild_id]:
				e = discord.Embed(color=colors.purple())
				e.title = "Uncached Message Deleted"
				e.set_thumbnail(url=self.bot.get_guild(payload.guild_id).icon_url)
				e.description = f"**Channel:** {self.bot.get_channel(payload.channel_id).mention}\n" \
					f"**Msg ID:** `{payload.message_id}`"
				await self.bot.get_channel(self.channel[guild_id]).send(embed=e)

	async def on_member_update(self, before, after):
		guild_id = str(before.guild.id)
		user = before
		if guild_id in self.channel:
			async for entry in before.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=1):
				user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			if before.display_name != after.display_name:
				e = discord.Embed(color=colors.orange())
				e.title = "Nickname Changed"
				e.set_thumbnail(url=before.avatar_url)
				e.description = f"User: {after.name}\n" \
					f"Changed by: {user.name}\n" \
					f"Before: {before.display_name}\n" \
					f"After: {after.display_name}"
				await channel.send(embed=e)

	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.green())
			e.title = "Member Joined"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"Name: {m.name}\n" \
				f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_remove(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			async for entry in m.guild.audit_logs(limit=1, after=time.time() - 1):
				if str(entry.action) == "AuditLogAction.ban":
					return
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.title = "Member Left or Was Kicked"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"Name: {m.name}\n" \
				f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_ban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
				author = entry.user
				break
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.set_thumbnail(url=user.avatar_url)
			if isinstance(user, discord.Member):
				e.title = "Member Banned"
			if isinstance(user, discord.User):
				e.title = "User Banned"
			e.description = f"Member Name: {user.name}\n" \
				f"Banned by: {author.name}"
			await channel.send(embed=e)

	async def on_member_unban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.lime_green())
			e.title = "User Unbanned"
			e.set_thumbnail(url=user.avatar_url)
			e.description = f"Name: {user.name}"
			await channel.send(embed=e)

def setup(bot):
	bot.add_cog(Logger(bot))
