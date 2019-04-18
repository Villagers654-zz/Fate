from discord.ext import commands
from utils import colors, config
from os.path import isfile
from time import time
import datetime
import discord
import asyncio
import json
import os

class Logger(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cache = {}
		self.channel = {}
		self.blacklist = {}
		self.blocked = {}
		self.waiting = {}
		self.cd = {}
		if isfile("./data/userdata/logger.json"):
			with open("./data/userdata/logger.json", "r") as infile:
				dat = json.load(infile)
				if "channel" in dat and "blacklist" in dat and "blocked" in dat:
					self.channel = dat["channel"]
					self.blacklist = dat["blacklist"]
					self.blocked = dat["blocked"]

	def save_json(self):
		with open("./data/userdata/logger.json", "w") as outfile:
			json.dump({"channel": self.channel, "blacklist": self.blacklist,
			           "blocked": self.blocked}, outfile, ensure_ascii=False)

	def wipe_data(self, guild_id):
		if guild_id in self.channel:
			del self.channel[guild_id]
		if guild_id in self.blacklist:
			del self.blacklist[guild_id]
		if guild_id in self.blocked:
			del self.blocked[guild_id]
		return self.save_json()

	async def wait_for_access(self, guild_id):
		guild = self.bot.get_guild(int(guild_id))
		bot = guild.get_member(self.bot.user.id)
		channel_access = False
		loops = 0
		while channel_access is False:
			loops += 1
			await asyncio.sleep(25)
			channel = self.bot.get_channel(self.channel[guild_id])
			if channel:
				loops = 0
				break
			else:
				if loops >= 72:
					self.wipe_data(guild_id)
					return False
		while channel_access is False:
			loops += 1
			channel = self.bot.get_channel(self.channel[guild_id])
			if channel.permissions_for(bot).send_messages:
				return True
			else:
				if loops >= 72:
					self.wipe_data(guild_id)
					return False
			await asyncio.sleep(25)

	async def channel_check(self, guild_id):
		guild = self.bot.get_guild(int(guild_id))
		bot = guild.get_member(self.bot.user.id)
		channel = self.bot.get_channel(self.channel[guild_id])
		if not channel:
			channel_access = await self.wait_for_access(guild_id)
			if not channel_access:
				return False
		else:
			if not channel.permissions_for(bot).send_messages:
				channel_access = await self.wait_for_access(guild_id)
				if not channel_access:
					return False
		return True

	def past(self, seconds):
		return datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		self.wipe_data(str(guild.id))

	@commands.group(name="logger")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	@commands.guild_only()
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
				".logger blacklist {event}\n" \
				".logger whitelist {event}\n" \
				".logger blockchannel {channel}\n" \
				".logger disable\n" \
				".logger events"
			await ctx.send(embed=e)

	@_logger.command(name="blacklist")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(embed_links=True)
	async def _blacklist(self, ctx, event=None):
		guild_id = str(ctx.guild.id)
		if event is None:
			blacklist = "None"
			if guild_id in self.blacklist:
				blacklist = self.blacklist[guild_id]
			e = discord.Embed(color=colors.fate())
			e.set_author(name=f"| {ctx.guild.name}", icon_url=ctx.guild.owner.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="◈ Blacklisted Events", value=blacklist, inline=False)
			return await ctx.send(embed=e)
		event = event.lower()
		events = ["message_delete", "message_edit", "guild_update",
		    "channel_create", "channel_delete", "channel_update", "ghost_typing",
		    "role_create", "role_delete", "role_update", "emoji_update",
		    "member_join", "member_remove", "member_unban", "member_update"]
		if event not in events:
			return await ctx.send("Unknown Event")
		if guild_id not in self.blacklist:
			self.blacklist[guild_id] = []
		self.blacklist[guild_id].append(event)
		self.save_json()
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"| {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"Blacklisted {event}"
		await ctx.send(embed=e)

	@_logger.command(name="whitelist")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(embed_links=True)
	async def _whitelist(self, ctx, event):
		event = event.lower()
		known_events = ["message_delete", "message_edit", "guild_update",
		    "channel_create", "channel_delete", "channel_update", "ghost_typing",
		    "role_create", "role_delete", "role_update", "emoji_update",
		    "member_join", "member_remove", "member_unban", "member_update"]
		if event not in known_events:
			return await ctx.send("Unknown Event")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.blacklist:
			self.blacklist[guild_id] = []
		if event not in self.blacklist[guild_id]:
			return await ctx.send("That events not blacklisted")
		target = self.blacklist[guild_id].index(event)
		self.blacklist[guild_id].pop(target)
		if len(self.blacklist[guild_id]) is 0:
			del self.blacklist[guild_id]
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"| {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"Whitelisted {event}"
		await ctx.send(embed=e)
		self.save_json()

	@_logger.command(name="blockchannel")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(embed_links=True)
	async def _blockchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if channel:
			if guild_id not in self.blocked:
				self.blocked[guild_id] = []
			self.blocked[guild_id].append(channel.id)
			await ctx.send(f"Blocked {channel.mention}")
			return self.save_json()
		if guild_id in self.blocked:
			channels = []
			for channel_id in self.blocked[guild_id]:
				channel = self.bot.get_channel(channel_id)
				if isinstance(channel, discord.TextChannel):
					channels.append(self.bot.get_channel(channel_id).mention)
				else:
					self.blocked[guild_id].pop(self.blocked[guild_id].index(channel_id))
					if len(self.blocked[guild_id]) is 0:
						del self.blocked[guild_id]
					self.save_json()
			if guild_id not in self.blocked:
				return await ctx.send("This server currently has no blocked channels")
			e = discord.Embed(color=colors.fate())
			e.set_author(name="| Blocked Channels", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = channels
			await ctx.send(embed=e)
		else:
			await ctx.send("This server currently has no blocked channels")

	@_logger.command(name="disable")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]
			self.save_json()
			return await ctx.send("Disabled logger")
		await ctx.send("Logger is not enabled")

	@_logger.command(name="setchannel")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(view_audit_log=True, embed_links=True, external_emojis=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if channel is None:
			self.channel[guild_id] = ctx.channel.id
			self.save_json()
			return await ctx.send(f"I will now log actions to {ctx.channel.mention}")
		self.channel[guild_id] = channel.id
		self.save_json()
		await ctx.send(f"I will now log all actions to {channel.mention}")

	@_logger.command(name="events")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _events(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.description = "[message_delete, message_edit, guild_update, " \
		    "channel_create, channel_delete, channel_update, role_create, " \
		    "role_delete, role_update, emoji_update, member_join, member_remove, " \
		    "member_unban, member_update, ghost_typing]"
		await ctx.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]

	@commands.Cog.listener()
	async def on_typing(self, channel, user, when):
		if not isinstance(channel, discord.DMChannel):
			guild_id = str(channel.guild.id)
			user_id = str(user.id)
			if guild_id in self.channel:
				if guild_id in self.blacklist:
					if "ghost_typing" in self.blacklist[guild_id]:
						return
				if guild_id in self.blocked:
					if channel.id in self.blocked[guild_id]:
						return
				if guild_id not in self.waiting:
					self.waiting[guild_id] = {}
				if user_id in self.waiting[guild_id]:
					return
				self.waiting[guild_id][user_id] = "waiting"
				def pred(m):
					return m.channel.id == channel.id and m.author.id == user.id
				try:
					await self.bot.wait_for('message', check=pred, timeout=120)
				except asyncio.TimeoutError:
					log = self.bot.get_channel(self.channel[guild_id])
					e = discord.Embed(color=colors.white())
					e.title = "~===🥂🍸🍷Ghost Typing🍷🍸🥂===~"
					e.set_thumbnail(url=channel.guild.icon_url)
					e.description = f"**User:** {user.mention}\n" \
						f"**Channel:** {channel.mention}"
					e.set_footer(text=datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p'))
					await log.send(embed=e)
					del self.waiting[guild_id][user_id]
				else:
					del self.waiting[guild_id][user_id]

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if guild_id not in self.cache:
				self.cache[guild_id] = []
			self.cache[guild_id].append(m.id)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		if isinstance(before.guild, discord.Guild):
			if before.pinned == after.pinned:
				guild_id = str(before.guild.id)
				if guild_id in self.channel:
					if before.channel.id != self.channel[guild_id]:
						if guild_id in self.blacklist:
							if "message_edit" in self.blacklist[guild_id]:
								return
						if guild_id in self.blocked:
							if before.channel.id in self.blocked[guild_id]:
								return
						user_id = str(before.author.id)
						if user_id not in self.cd:
							self.cd[user_id] = 0
						self.cd[user_id] += time() + 1
						if self.cd[user_id] > time() + 2:
							return
						if len(after.embeds) == 0:
							channel = self.bot.get_channel(self.channel[guild_id])
							e = discord.Embed(color=colors.pink())
							e.title = "~===🥂🍸🍷Msg Edited🍷🍸🥂===~"
							e.set_thumbnail(url=before.author.avatar_url)
							e.description = f"**Author:** {before.author.mention}\n" \
								f"**Channel:** {before.channel.mention}\n" \
								f"[Jump to MSG]({before.jump_url})\n"
							for text_group in [before.content[i:i + 1000] for i in range(0, len(before.content), 1000)]:
								e.add_field(name="◈ Before ◈", value=text_group, inline=False)
							for text_group in [after.content[i:i + 1000] for i in range(0, len(after.content), 1000)]:
								e.add_field(name="◈ After ◈", value=text_group, inline=False)
							e.set_footer(text=datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p'))
							await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_message_delete(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if guild_id in self.channel:
				if guild_id in self.blacklist:
					if "message_delete" in self.blacklist[guild_id]:
						return
				if guild_id in self.blocked:
					if m.channel.id in self.blocked[guild_id]:
						return
				user = "Author"
				async for entry in m.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
					if self.past(2) < entry.created_at:
						user = entry.user.mention
				channel = self.bot.get_channel(self.channel[guild_id])
				channel_requirements = await self.channel_check(guild_id)
				if not channel_requirements:
					return
				if m.channel.id == self.channel[guild_id]:
					if not m.embeds:
						e = discord.Embed(color=colors.purple())
						e.title = "~===🥂🍸🍷Msg Deleted🍷🍸🥂===~"
						e.set_thumbnail(url=m.author.avatar_url)
						e.description = f"**Author:** {m.author.mention}\n" \
							f"**Deleted by:** {user}\n" \
							f"**Channel:** {m.channel.mention}\n" \
							f"[Jump to MSG]({m.jump_url})\n"
						if m.pinned:
							e.description += f"\nMsg was pinned"
						if not m.content:
							m.content = "`None`"
						for text_group in [m.content[i:i + 1000] for i in range(0, len(m.content), 1000)]:
							e.add_field(name="◈ Content ◈", value=text_group, inline=False)
						if m.attachments:
							e.add_field(name="◈ Cached Images ◈", value="They may not show")
						for attachment in m.attachments:
							e.set_image(url=attachment.proxy_url)
						footer = f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}"
						if m.embeds:
							footer += " | Embed ⇓"
						e.set_footer(text=footer)
						await channel.send(embed=e)
					for embed in m.embeds:
						await channel.send(embed=embed)
				else:
					e = discord.Embed(color=colors.purple())
					e.title = "~===🥂🍸🍷Msg Deleted🍷🍸🥂===~"
					e.set_thumbnail(url=m.author.avatar_url)
					e.description = f"**Author:** {m.author.mention}\n" \
						f"**Deleted by:** {user}\n" \
						f"**Channel:** {m.channel.mention}\n" \
						f"[Jump to MSG]({m.jump_url})\n"
					if m.pinned:
						e.description += f"\nMsg was pinned"
					if not m.content:
						m.content = "`None`"
					n = 1000
					for text_group in [m.content[i:i + n] for i in range(0, len(m.content), n)]:
						e.add_field(name="◈ Content ◈", value=text_group, inline=False)
					if m.attachments:
						e.add_field(name="◈ Cached Images ◈", value="They may not show")
					for attachment in m.attachments:
						e.set_image(url=attachment.proxy_url)
					footer = f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}"
					if m.embeds:
						footer += " | Embed ⇓"
					e.set_footer(text=footer)
					await channel.send(embed=e)
					for embed in m.embeds:
						await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "message_delete" in self.blacklist[guild_id]:
					return
			if guild_id in self.blocked:
				if payload.channel_id in self.blocked[guild_id]:
					return
			await asyncio.sleep(1)
			if guild_id not in self.cache:
				self.cache[guild_id] = []
			if payload.message_id not in self.cache[guild_id]:
				e = discord.Embed(color=colors.purple())
				e.title = "🥂🍸🍷Uncached Msg Deleted🍷🍸🥂"
				e.set_thumbnail(url=self.bot.get_guild(payload.guild_id).icon_url)
				e.description = f"**Msg ID:** `{payload.message_id}`\n" \
					f"**Channel:** {self.bot.get_channel(payload.channel_id).mention}"
				e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
				await self.bot.get_channel(self.channel[guild_id]).send(embed=e)

	@commands.Cog.listener()
	async def on_bulk_message_delete(self, messages):
		guild_id = str(messages[0].guild.id)
		m = messages[0]  # type: discord.Message
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "message_delete" in self.blacklist[guild_id]:
					return
			if guild_id in self.blocked:
				if messages[0].channel.id in self.blocked[guild_id]:
					return
			user = "unknown"
			async for entry in messages[0].guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
				if self.past(2) < entry.created_at:
					user = entry.user.mention
			channel = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			if m.channel.id == self.channel[guild_id]:
				for msg in messages:
					if not msg.embeds:
						e = discord.Embed(color=colors.purple())
						e.title = "~===🥂🍸🍷Msg Deleted🍷🍸🥂===~"
						e.set_thumbnail(url=msg.author.avatar_url)
						e.description = f"**Author:** {msg.author.mention}\n" \
							f"**Deleted by:** {user}\n" \
							f"**Channel:** {msg.channel.mention}\n" \
							f"[Jump to MSG]({msg.jump_url})\n"
						if msg.pinned:
							e.description += f"\nMsg was pinned"
						if not msg.content:
							msg.content = "`None`"
						e.add_field(name="◈ Content ◈", value=msg.content, inline=False)
						if msg.attachments:
							e.add_field(name="◈ Cached Images ◈", value="They may not show")
						for attachment in msg.attachments:
							e.set_image(url=attachment.proxy_url)
						footer = f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}"
						e.set_footer(text=footer)
						await channel.send(embed=e)
					for embed in msg.embeds:
						await channel.send(embed=embed)
			else:
				purged_messages = ""
				authors = []
				for msg in messages:
					purged_messages = f"{msg.created_at.strftime('%I:%M%p')} | {msg.author.display_name}: {msg.content}\n{purged_messages}"
					if msg.author.id not in authors:
						authors.append(msg.author.id)
				with open('./data/temp/purged_messages.txt', 'w') as f:
					f.write(purged_messages)
				path = os.getcwd() + "/data/temp/purged_messages.txt"
				e = discord.Embed(color=colors.black())
				e.title = "~===🥂🍸🍷Bulk Msg Delete🍷🍸🥂===~"
				e.set_thumbnail(url=m.author.avatar_url)
				e.description = f"**Users Affected:** {len(authors)}\n" \
					f"**Messages Deleted:** {len(messages)}\n" \
					f"**Triggered by:** {user}\n" \
					f"**Channel:** {m.channel.mention}"
				footer = f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}"
				e.set_footer(text=footer)
				await channel.send(embed=e, file=discord.File(path))
				os.system("rm ./data/temp/purged_messages.txt")

	@commands.Cog.listener()
	async def on_guild_update(self, before, after):
		guild_id = str(after.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "guild_update" in self.blacklist[guild_id]:
					return
			if before.name != after.name:
				user = "unknown"
				async for entry in after.audit_logs(action=discord.AuditLogAction.guild_update, limit=1):
					user = entry.user.mention
				channel = self.bot.get_channel(self.channel[guild_id])
				e = discord.Embed(color=colors.cyan())
				e.title = "~==🥂🍸🍷Guild Update🍷🍸🥂==~"
				e.set_thumbnail(url=before.icon_url)
				e.description = f"**Updated by:** {user}"
				e.add_field(name="◈ Name ◈", value= \
					f"**Before:** `{before.name}`\n" \
					f"**After:** `{after.name}`")
				e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
				await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		guild_id = str(channel.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "channel_create" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
				user = entry.user
			log_channel = self.bot.get_channel(self.channel[guild_id])
			channel_name = channel.name
			if isinstance(channel, discord.TextChannel):
				channel_name = channel.mention
			e = discord.Embed(color=colors.fate())
			e.title = "~==🥂🍸🍷Channel Created🍷🍸🥂==~"
			if user:
				e.set_thumbnail(url=user.avatar_url)
			e.description = f"**Channel:** {channel_name}\n" \
				f"**Created by:** {user.mention if user else '`unknown`'}\n" \
				f"**ID:** {channel.id}\n" \
				f"**Members:** [{len(channel.members)}]"
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await log_channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		guild_id = str(channel.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blocked:
				if channel.id in self.blocked[guild_id]:
					self.blocked[guild_id].pop(channel.id)
					if len(self.blocked[guild_id]) is 0:
						del self.blocked[guild_id]
					self.save_json()
			if channel.id == self.channel[guild_id]:
				del self.channel[guild_id]
				return self.save_json()
			if guild_id in self.blacklist:
				if "channel_delete" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.User
			async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
				user = entry.user
			log = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			e = discord.Embed(color=colors.fate())
			e.title = "~==🥂🍸🍷Channel Deleted🍷🍸🥂==~"
			e.set_thumbnail(url=user.avatar_url)
			e.description = f"**Channel:** {channel.name}\n" \
				f"**Deleted by:** {user.mention}\n" \
				f"**ID:** {channel.id}\n" \
				f"**Members:** [{len(channel.members)}]"
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await log.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		guild_id = str(before.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "channel_update" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			async for entry in before.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.channel_update, limit=1):
				user = entry.user
			async for entry in before.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.overwrite_create, limit=1):
				user = entry.user
			async for entry in before.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.overwrite_delete, limit=1):
				user = entry.user
			async for entry in before.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.overwrite_update, limit=1):
				user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			e = discord.Embed(color=colors.fate())
			e.title = "~==🥂🍸🍷Channel Updated🍷🍸🥂==~"
			if user:
				e.set_thumbnail(url=user.avatar_url)
			e.description = \
				f"**Channel:** {after.mention}\n" \
				f"**Updated by:** {user.mention if user else '`unknown`'}"
			if before.name != after.name:
				e.add_field(name="◈ Name ◈", value=f"**Before:** {before.name}\n"
					f"**After:** {after.name}", inline=False)
			if before.category != after.category:
				e.add_field(name="◈ Category ◈", value=f"**Before:** {before.category}\n"
					f"**After:** {after.category}", inline=False)
			if before.overwrites != after.overwrites:

				# old
				value = ""
				updated = None
				existed_before = []
				existed_after = []
				for dat in before.overwrites:
					existed_before.append(dat[0])
				for dat in after.overwrites:
					existed_after.append(dat[0])
				for object in existed_after:
					if object not in existed_before:
						updated = True
						value += f"\n{config.emojis('plus')} {object}"
				for object in existed_before:
					if object not in existed_after:
						perms = ""
						updated = True
						for perm_object in before.overwrites[existed_before.index(object)][1]:
							if perm_object[1]:
								perms += f"\n✦ {perm_object[0]}"
						value += f"\n❌ {object}{perms}"
				if not updated:
					before_roles = {}
					after_roles = {}
					for dat in before.overwrites:
						before_roles[dat[0].name] = dat[1]
					for dat in after.overwrites:
						after_roles[dat[0].name] = dat[1]
					for key in list(before_roles.keys()):
						if key != after_roles[list(after_roles.keys())[list(after_roles).index(key)]]:
							before_perm = []
							before_value = []
							after_perm = []
							after_value = []
							for perm in before_roles[key]:
								before_perm.append(perm[0])
								before_value.append(perm[1])
							for perm in after_roles[list(after_roles.keys())[list(after_roles).index(key)]]:
								after_perm.append(perm[0])
								after_value.append(perm[1])
							difference = ""
							for perm in before_perm:
								if before_value[before_perm.index(perm)] != after_value[after_perm.index(perm)]:
									difference += f"\n□ {after_perm[after_perm.index(perm)]}: {after_value[after_perm.index(perm)]}"
							if difference:
								value += f"\n<:edited:550291696861315093> {list(after_roles.keys())[list(after_roles).index(key)] + difference}"
				e.add_field(name="◈ Overwrites ◈", value=value, inline=False)
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "role_create" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			async for entry in role.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.role_create, limit=1):
				user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Created🍷🍸🥂==~"
			if user:
				e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"**Role:** {role.mention}\n" \
				f"**Created by:** {user.mention if user else '`unknown`'}"
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "role_delete" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			async for entry in role.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.role_delete, limit=1):
				user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Deleted🍷🍸🥂==~"
			if user:
				e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"**Name:** {role.name}\n" \
				f"**Deleted by:** {user.mention if user else '`unknown`'}\n" \
				f"**Color:** {role.color}\n" \
				f"**Users:** [{len(list(role.members))}]"
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_role_update(self, before, after):
		guild_id = str(before.guild.id)
		changed_permissions = ""
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "role_update" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			async for entry in after.guild.audit_logs(after=self.past(2), action=discord.AuditLogAction.role_delete, limit=1):
				user = entry.user.mention
			async for entry in after.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=1):
				if self.past(2) < entry.created_at:
					user = entry.user
			is_changed = False
			channel = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			e = discord.Embed(color=colors.blue())
			e.title = "~==🥂🍸🍷Role Updated🍷🍸🥂==~"
			e.set_thumbnail(url=before.guild.icon_url)
			e.description = f"**Role:** {after.mention}\n**Updated by:** {user.display_name if user else '`unknown`'}"
			if before.name != after.name:
				is_changed = True
				e.add_field(name="◈ Name ◈", value=f"**Before:** {before.name}\n**After:** {after.name}", inline=False)
			e.description = f"**Role:** {after.name}\n" \
				f"**Updated by:** {user}"
			if before.color != after.color:
				is_changed = True
				e.add_field(name="◈ Color ◈", value=f"**Before:** {before.color}\n**After:** {after.color}")
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
				e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
				async for msg in channel.history(limit=1):
					for embed in msg.embeds:
						if embed == e:
							return
				await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_guild_emojis_update(self, guild, before, after):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "emoji_update" in self.blacklist[guild_id]:
					return
			user = None  # type: discord.Member
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.yellow())
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			for emoji in before:
				if emoji not in after:
					async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_delete, limit=1):
						if self.past(2) < entry.created_at:
							user = entry.user
							e.set_thumbnail(url=user.avatar_url)
					e.title = "~==🥂🍸🍷Emoji Deleted🍷🍸🥂==~"
					e.description = \
						f"**Deleted by:** {user.mention if user else '`unknown`'}\n" \
						f"**Name:** {emoji.name}"
					return await channel.send(embed=e)
			for emoji in after:
				if emoji not in before:
					async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_create, limit=1):
						if self.past(2) < entry.created_at:
							user = entry.user
							e.set_thumbnail(url=user.avatar_url)
					e.title = "~==🥂🍸🍷Emoji Created🍷🍸🥂==~"
					e.description = \
						f"**Created by:** {user.mention if user else '`unknown`'}\n" \
						f"**Name:** {emoji.name}\n" \
						f"**Emoji:** {emoji}"
					return await channel.send(embed=e)
			for emoji in before:
				for future_emoji in after:
					if emoji.id == future_emoji.id:
						if emoji.name != future_emoji.name:
							async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_update, limit=1):
								if self.past(2) < entry.created_at:
									user = entry.user
									e.set_thumbnail(url=user.avatar_url)
							e.title = "~==🥂🍸🍷Emoji Updated🍷🍸🥂==~"
							e.description = \
								f"**Updated by:** {user.mention if user else '`unknown`'}\n" \
								f"**Emoji:** {emoji}"
							e.add_field(name="◈ Name ◈", value=
								f"**Before:** {emoji.name}\n"
								f"**After:** {future_emoji.name}")
							return await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "member_join" in self.blacklist[guild_id]:
					return
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.green())
			e.title = "~==🥂🍸🍷Member Joined🍷🍸🥂==~"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"**User:** {m}\n" \
				f"**ID:** {m.id}\n"
			await channel.send(embed=e)
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")

	@commands.Cog.listener()
	async def on_member_remove(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "member_remove" in self.blacklist[guild_id]:
					return
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			async for entry in m.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
				if self.past(2) < entry.created_at:
					user = entry.user
					e.title = "~==🥂🍸🍷Member Kicked🍷🍸🥂==~"
					e.set_thumbnail(url=m.avatar_url)
					e.description = \
						f"**Member:** {m}\n" \
						f"**Kicked by:** {user.mention}" \
						f"**ID:** {m.id}\n"
					return await channel.send(embed=e)
			async for entry in m.guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
				if self.past(2) > entry.created_at:
					e.title = "~==🥂🍸🍷Member Left🍷🍸🥂==~"
					e.set_thumbnail(url=m.avatar_url)
					e.description = \
						f"**User:** {m}\n" \
						f"**ID:** {m.id}\n"
					await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "member_remove" in self.blacklist[guild_id]:
					return
			author = None  # type: discord.Member
			async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
				author = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.set_thumbnail(url=user.avatar_url)
			if isinstance(user, discord.Member):
				e.title = "~==🥂🍸🍷Member Banned🍷🍸🥂==~"
			if isinstance(user, discord.User):
				e.title = "~==🥂🍸🍷User Banned🍷🍸🥂==~"
			e.description = f"**User:** {user}\n" + f"**Banned by:** {author.mention}" if author else ""
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			if guild_id in self.blacklist:
				if "member_unban" in self.blacklist[guild_id]:
					return
			author = None  # type: discord.Member
			async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, after=self.past(2), limit=1):
				author = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.orange())
			e.title = "~==🥂🍸🍷User Unbanned🍷🍸🥂==~"
			e.set_thumbnail(url=user.avatar_url)
			e.description = f"**User:** {user}\nUnbanned by: {author.mention if author else '`unknown`'}"
			e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		guild_id = str(before.guild.id)
		if guild_id in self.channel:
			member_changed = False
			user = before  # type: discord.Member
			if guild_id in self.blacklist:
				if "member_update" in self.blacklist[guild_id]:
					return
			if before.name != after.name:
				return
			async for entry in before.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=1):
				if self.past(2) < entry.created_at:
					user = entry.user
			async for entry in before.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=1):
				if self.past(2) < entry.created_at:
					user = entry.user
			channel = self.bot.get_channel(self.channel[guild_id])
			channel_requirements = await self.channel_check(guild_id)
			if not channel_requirements:
				return
			e = discord.Embed(color=colors.lime_green())
			e.set_thumbnail(url=before.avatar_url)
			e.title = "~==🥂🍸🍷Member Updated🍷🍸🥂==~"
			e.description = f"**User:** {after.mention}\n" \
				f"**Changed by:** {user.mention}\n"
			if before.display_name != after.display_name:
				member_changed = True
				e.add_field(name="◈ Nickname ◈", value=f"**Before:** {before.display_name}\n"
				f"**After:** {after.display_name}", inline=False)
			if before.roles != after.roles:
				member_changed = True
				role_changes = ""
				for role in before.roles:
					if role not in after.roles:
						role_changes += f"❌ {role.name}\n"
				for role in after.roles:
					if role not in before.roles:
						role_changes += f"{config.emojis('plus')} {role.name}\n"
				e.add_field(name="◈ Roles ◈", value=role_changes, inline=False)
			if member_changed:
				e.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p')}")
				await channel.send(embed=e)

def setup(bot):
	bot.add_cog(Logger(bot))
