from discord.ext import commands
from utils import colors, config
from os.path import isfile
import datetime
import discord
import asyncio
import json

class Logger:
	def __init__(self, bot):
		self.bot = bot
		self.cache = {}
		self.channel = {}
		if isfile("./data/userdata/logger.json"):
			with open("./data/userdata/logger.json", "r") as infile:
				dat = json.load(infile)
				if "channel" in dat:
					self.channel = dat["channel"]

	def save_channel(self):
		with open("./data/userdata/logger.json", "w") as outfile:
			json.dump({"channel": self.channel}, outfile, ensure_ascii=False)

	@commands.group(name="logger")
	@commands.cooldown(1, 3, commands.BucketType.user)
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
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]
			self.save_channel()
			return await ctx.send("Disabled logging")
		await ctx.send("Logging is not enabled")

	@_logger.command(name="setchannel")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(view_audit_log=True,
	embed_links=True, external_emojis=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if channel is None:
			self.channel[guild_id] = ctx.channel.id
			self.save_channel()
			return await ctx.send(f"I will now log actions to {ctx.channel.mention}")
		self.channel[guild_id] = channel.id
		self.save_channel()
		await ctx.send(f"I will now log all actions to {channel.mention}")

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]

	async def on_message(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id not in self.cache:
			self.cache[guild_id] = []
		self.cache[guild_id].append(m.id)

	async def on_message_edit(self, before, after):
		if before.pinned == after.pinned:
			guild_id = str(before.guild.id)
			if guild_id in self.channel:
				if before.channel.id != self.channel[guild_id]:
					if len(after.embeds) == 0:
						channel = self.bot.get_channel(self.channel[guild_id])
						e = discord.Embed(color=colors.pink())
						e.title = "~===🥂🍸🍷Msg Edited🍷🍸🥂===~"
						e.set_thumbnail(url=before.author.avatar_url)
						e.description = f"**Author:** {before.author}\n" \
							f"**Channel:** {before.channel.mention}"
						e.add_field(name="◈ Before ◈", value=before.content, inline=False)
						e.add_field(name="◈ After ◈", value=after.content, inline=False)
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
			e.title = "~===🥂🍸🍷Msg Deleted🍷🍸🥂===~"
			e.set_thumbnail(url=m.author.avatar_url)
			e.description = f"**Author:** {m.author}\n" \
				f"**Deleted by:** {user}\n" \
				f"**Channel:** {m.channel.mention}"
			if m.pinned:
				e.description += f"\nMsg was pinned"
			if not m.content:
				m.content = "`None`"
			e.add_field(name="◈ Content ◈", value=m.content, inline=False)
			if m.attachments:
				e.add_field(name="◈ Cached Images ◈", value="They may not show")
			for attachment in m.attachments:
				e.set_image(url=attachment.proxy_url)
			if m.embeds:
				e.footer("Embed ⇓")
			await channel.send(embed=e)

	async def on_raw_message_delete(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.channel:
			await asyncio.sleep(1)
			if guild_id not in self.cache:
				self.cache[guild_id] = []
			if payload.message_id not in self.cache[guild_id]:
				e = discord.Embed(color=colors.purple())
				e.title = "🥂🍸🍷Uncached Msg Deleted🍷🍸🥂"
				e.set_thumbnail(url=self.bot.get_guild(payload.guild_id).icon_url)
				e.description = f"**Msg ID:** `{payload.message_id}`\n" \
					f"**Channel:** {self.bot.get_channel(payload.channel_id).mention}"
				await self.bot.get_channel(self.channel[guild_id]).send(embed=e)

	async def on_guild_update(self, before, after):
		guild_id = str(after.id)
		if guild_id in self.channel:
			if before.name != after.name:
				channel = self.bot.get_channel(self.channel[guild_id])
				e = discord.Embed(color=colors.cyan())
				e.title = "~==🥂🍸🍷Guild Update🍷🍸🥂==~"
				e.set_thumbnail(url=before.icon_url)
				e.add_field(name="◈ Name ◈", value= \
				f"Before: `{before.name}`\n" \
				f"After: `{after.name}`")
				await channel.send(embed=e)

	async def on_guild_role_create(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Created🍷🍸🥂==~"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}"
			await channel.send(embed=e)

	async def on_guild_role_delete(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Deleted🍷🍸🥂==~"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}\n" \
				f"Color: {role.color}\n" \
				f"Users: [{len(list(role.members))}]"
			await channel.send(embed=e)

	async def on_guild_emojis_update(self, guild, before, after):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			user = "error"
			async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_update, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_create, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_delete, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			if user == "error":
				return
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.yellow())
			e.set_thumbnail(url=user.avatar_url)
			for emoji in before:
				if emoji not in after:
					e.title = "~==🥂🍸🍷Emoji Deleted🍷🍸🥂==~"
					e.description = \
						f"Deleted by: {user.display_name}\n" \
						f"Name: {emoji.name}"
					return await channel.send(embed=e)
			for emoji in after:
				if emoji not in before:
					e.title = "~==🥂🍸🍷Emoji Created🍷🍸🥂==~"
					e.description = \
						f"Created by: {user.display_name}\n" \
						f"Emoji: {emoji}\n" \
						f"Name: {emoji.name}"
					return await channel.send(embed=e)
			for emoji in before:
				for future_emoji in after:
					if emoji.id == future_emoji.id:
						if emoji.name != future_emoji.name:
							e.title = "~==🥂🍸🍷Emoji Updated🍷🍸🥂==~"
							e.description = \
								f"Updated by: {user.display_name}\n" \
								f"Emoji: {emoji}"
							e.add_field(name="◈ Name ◈", value=
								f"**Before:** {emoji.name}\n"
								f"**After:** {future_emoji.name}")
							return await channel.send(embed=e)

	async def on_guild_role_update(self, before, after):
		guild_id = str(before.guild.id)
		changed_permissions = ""
		if guild_id in self.channel:
			is_changed = None
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Updated🍷🍸🥂==~"
			e.set_thumbnail(url=before.guild.icon_url)
			if before.name != after.name:
				is_changed = True
				e.add_field(name="◈ Name ◈", value=f"Before: {before.name}\nAfter: {after.name}", inline=False)
			e.description = f"Role: {after.name}"
			if before.color != after.color:
				is_changed = True
				e.add_field(name="◈ Color ◈", value=f"Before: {before.color}\nAfter: {after.color}")
			if before.permissions.value != after.permissions.value:
				is_changed = True
				if before.permissions.administrator != after.permissions.administrator:
					if before.permissions.administrator:
						changed_permissions += "❌ administrator\n"
					else:
						changed_permissions += f"{config.emojis('plus')} administrator\n"
				if before.permissions.create_instant_invite != after.permissions.create_instant_invite:
					if before.permissions.create_instant_invite:
						changed_permissions += "❌ create instant invites\n"
					else:
						changed_permissions += f"{config.emojis('plus')} create instant invites\n"
				if before.permissions.kick_members != after.permissions.kick_members:
					if before.permissions.kick_members:
						changed_permissions += "❌ kick members\n"
					else:
						changed_permissions += f"{config.emojis('plus')} kick members\n"
				if before.permissions.ban_members != after.permissions.ban_members:
					if before.permissions.ban_members:
						changed_permissions += "❌ ban members\n"
					else:
						changed_permissions += f"{config.emojis('plus')} ban members\n"
				if before.permissions.manage_channels != after.permissions.manage_channels:
					if before.permissions.manage_channels:
						changed_permissions += "❌ manage channels\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage channels\n"
				if before.permissions.manage_guild != after.permissions.manage_guild:
					if before.permissions.manage_guild:
						changed_permissions += "❌ manage guild\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage guild\n"
				if before.permissions.add_reactions != after.permissions.add_reactions:
					if before.permissions.add_reactions:
						changed_permissions += "❌ add reactions\n"
					else:
						changed_permissions += f"{config.emojis('plus')} add reactions\n"
				if before.permissions.view_audit_log != after.permissions.view_audit_log:
					if before.permissions.view_audit_log:
						changed_permissions += "❌ view audit log\n"
					else:
						changed_permissions += f"{config.emojis('plus')} view audit log\n"
				if before.permissions.priority_speaker != after.permissions.priority_speaker:
					if before.permissions.priority_speaker:
						changed_permissions += "❌ priority speaker\n"
					else:
						changed_permissions += f"{config.emojis('plus')} priority speaker\n"
				if before.permissions.read_messages != after.permissions.read_messages:
					if before.permissions.read_messages:
						changed_permissions += "❌ read messages\n"
					else:
						changed_permissions += f"{config.emojis('plus')} read messages\n"
				if before.permissions.send_messages != after.permissions.send_messages:
					if before.permissions.send_messages:
						changed_permissions += "❌ send messages\n"
					else:
						changed_permissions += f"{config.emojis('plus')} send messages\n"
				if before.permissions.send_tts_messages != after.permissions.send_tts_messages:
					if before.permissions.send_tts_messages:
						changed_permissions += "❌ send tts messages\n"
					else:
						changed_permissions += f"{config.emojis('plus')} send tts messages\n"
				if before.permissions.manage_messages != after.permissions.manage_messages:
					if before.permissions.manage_messages:
						changed_permissions += "❌ manage messages\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage messages\n"
				if before.permissions.embed_links != after.permissions.embed_links:
					if before.permissions.embed_links:
						changed_permissions += "❌ embed links\n"
					else:
						changed_permissions += f"{config.emojis('plus')} embed links\n"
				if before.permissions.attach_files != after.permissions.attach_files:
					if before.permissions.attach_files:
						changed_permissions += "❌ attach files\n"
					else:
						changed_permissions += f"{config.emojis('plus')} attach files\n"
				if before.permissions.read_message_history != after.permissions.read_message_history:
					if before.permissions.read_message_history:
						changed_permissions += "❌ read message history\n"
					else:
						changed_permissions += f"{config.emojis('plus')} read message history\n"
				if before.permissions.mention_everyone != after.permissions.mention_everyone:
					if before.permissions.mention_everyone:
						changed_permissions += "❌ mention everyone\n"
					else:
						changed_permissions += f"{config.emojis('plus')} mention everyone\n"
				if before.permissions.external_emojis != after.permissions.external_emojis:
					if before.permissions.external_emojis:
						changed_permissions += "❌ external emojis\n"
					else:
						changed_permissions += f"{config.emojis('plus')} external emojis\n"
				if before.permissions.connect != after.permissions.connect:
					if before.permissions.connect:
						changed_permissions += "❌ connect\n"
					else:
						changed_permissions += f"{config.emojis('plus')} connect\n"
				if before.permissions.speak != after.permissions.speak:
					if before.permissions.speak:
						changed_permissions += "❌ speak\n"
					else:
						changed_permissions += f"{config.emojis('plus')} speak\n"
				if before.permissions.mute_members != after.permissions.mute_members:
					if before.permissions.mute_members:
						changed_permissions += "❌ mute members\n"
					else:
						changed_permissions += f"{config.emojis('plus')} mute members\n"
				if before.permissions.deafen_members != after.permissions.deafen_members:
					if before.permissions.deafen_members:
						changed_permissions += "❌ deafen members\n"
					else:
						changed_permissions += f"{config.emojis('plus')} deafen members\n"
				if before.permissions.move_members != after.permissions.move_members:
					if before.permissions.move_members:
						changed_permissions += "❌ move members\n"
					else:
						changed_permissions += f"{config.emojis('plus')} move members\n"
				if before.permissions.use_voice_activation != after.permissions.use_voice_activation:
					if before.permissions.use_voice_activation:
						changed_permissions += "❌ use voice activation\n"
					else:
						changed_permissions += f"{config.emojis('plus')} use voice activation\n"
				if before.permissions.change_nickname != after.permissions.change_nickname:
					if before.permissions.change_nickname:
						changed_permissions += "❌ change nickname\n"
					else:
						changed_permissions += f"{config.emojis('plus')} change nickname\n"
				if before.permissions.manage_nicknames != after.permissions.manage_nicknames:
					if before.permissions.manage_nicknames:
						changed_permissions += "❌ manage nicknames\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage nicknames\n"
				if before.permissions.manage_roles != after.permissions.manage_roles:
					if before.permissions.manage_roles:
						changed_permissions += "❌ manage roles\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage roles\n"
				if before.permissions.manage_webhooks != after.permissions.manage_webhooks:
					if before.permissions.manage_webhooks:
						changed_permissions += "❌ manage webhooks\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage webhooks\n"
				if before.permissions.manage_emojis != after.permissions.manage_emojis:
					if before.permissions.manage_emojis:
						changed_permissions += "❌ manage emojis\n"
					else:
						changed_permissions += f"{config.emojis('plus')} manage emojis\n"
				e.add_field(name="◈ Perms ◈", value=changed_permissions, inline=False)
			if is_changed:
				await channel.send(embed=e)

	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.green())
			e.title = "~==🥂🍸🍷Member Joined🍷🍸🥂==~"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"User: {m.mention}\n" \
				f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_remove(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			is_kick = None
			async for entry in m.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
				if str(entry.action) == "AuditLogAction.ban":
					if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
						user = entry.user
						is_kick = True
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			if not is_kick:
				e.title = "~==🥂🍸🍷Member Left🍷🍸🥂==~"
				e.set_thumbnail(url=m.avatar_url)
				e.description = \
					f"User: {m}\n" \
					f"ID: {m.id}\n"
			if is_kick:
				e.title = "~==🥂🍸🍷Member Kicked🍷🍸🥂==~"
				e.set_thumbnail(url=m.avatar_url)
				e.description = \
					f"Member: {m}\n" \
					f"Kicked by: {user.display_name}" \
					f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_ban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
				author = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.set_thumbnail(url=user.avatar_url)
			if isinstance(user, discord.Member):
				e.title = "~==🥂🍸🍷Member Banned🍷🍸🥂==~"
			if isinstance(user, discord.User):
				e.title = "~==🥂🍸🍷User Banned🍷🍸🥂==~"
			e.description = f"User: {user}\n" \
				f"Banned by: {author.name}"
			await channel.send(embed=e)

	async def on_member_unban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.orange())
			e.title = "~==🥂🍸🍷User Unbanned🍷🍸🥂==~"
			e.set_thumbnail(url=user.avatar_url)
			e.description = f"User: {user}"
			await channel.send(embed=e)

	async def on_member_update(self, before, after):
		guild_id = str(before.guild.id)
		change_value = None
		user = before
		if guild_id in self.channel:
			async for entry in before.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			async for entry in before.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=1):
				if datetime.datetime.utcnow() - datetime.timedelta(seconds=2) < entry.created_at:
					user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.lime_green())
			e.set_thumbnail(url=before.avatar_url)
			e.title = "~==🥂🍸🍷Member Updated🍷🍸🥂==~"
			e.description = f"User: {after}\n" \
				f"Changed by: {user.name}\n"
			if before.display_name != after.display_name:
				change_value = True
				e.add_field(name="◈ Nickname ◈", value=f"**Before:** {before.display_name}\n"
				f"**After:** {after.display_name}", inline=False)
			if before.roles != after.roles:
				change_value = True
				role_changes = ""
				for role in before.roles:
					if role not in after.roles:
						role_changes += f"❌ {role.name}"
				for role in after.roles:
					if role not in before.roles:
						role_changes += f"{config.emojis('plus')} {role.name}"
				e.add_field(name="◈ Roles ◈", value=role_changes, inline=False)
			if change_value:
				await channel.send(embed=e)

def setup(bot):
	bot.add_cog(Logger(bot))
