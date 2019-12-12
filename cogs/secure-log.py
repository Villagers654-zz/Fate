"""
Discord.Py v1.5+ Action Logs Module
+ can split up into multiple channels
+ logs can't be deleted or purged by anyone
- re-creates deleted log channels and resends the last 50 logs
"""

import asyncio
from os import path
import json
import os
from datetime import datetime, timedelta
import requests

from discord.ext import commands
import discord
from discord import AuditLogAction as audit

from utils.colors import *
from utils import utils, config


def is_guild_owner():
	async def predicate(ctx):
		return ctx.author.id == ctx.guild.owner.id or (
			ctx.author.id == config.owner_id())  # for testing

	return commands.check(predicate)


class SecureLog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		self.config = {}
		self.path = './data/userdata/secure-log.json'
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)  # type: dict

		self.channel_types = [
			"system+", "updates", "actions", "chat", "misc", "sudo"
		]

		self.queue = {g_id: [] for g_id in self.config.keys()}
		self.recent_logs = {
			guild_id: {
				Type: [] for Type in self.channel_types
			} for guild_id, dat in self.config.items() if (
				dat['type'] == 'multi'
			)
		}
		self.static = {}

		self.queues = {}
		for guild_id in self.config.keys():
			queue = bot.loop.create_task(self.start_queue(guild_id))
			self.queues[guild_id] = queue

	def save_data(self):
		""" Saves local variables """
		with open(self.path, 'w+') as f:
			json.dump(self.config, f)

	async def initiate_category(self, guild):
		""" Sets up a new multi-log category"""
		if str(guild.id) not in self.config:
			self.config[str(guild.id)] = {
				"channels": {},
				"type": "multi"
			}
		category = await guild.create_category(name='MultiLog')
		for channelType in self.channel_types:
			channel = await guild.create_text_channel(
				name=channelType,
				category=category
			)
			self.config[str(guild.id)]['channels'][channelType] = channel.id
		guild_id = str(guild.id)
		self.config[guild_id]['channel'] = category.id
		return category

	async def start_queue(self, guild_id: str):
		""" Loop for managing the guilds queue
		+ checks guild permissions
		+ checks channel permissions
		+ can wait to send logs
		+ archives the last 50 logs to
		be able to resend if deleted """

		guild = self.bot.get_guild(int(guild_id))
		if guild_id not in self.queue:
			self.queue[guild_id] = []
		if guild_id not in self.recent_logs:
			if self.config[guild_id]['type'] == 'single':
				self.recent_logs[guild_id] = []
			else:
				self.recent_logs[guild_id] = {
					Type: [] for Type in self.channel_types
				}

		while True:
			while not self.queue[guild_id]:
				await asyncio.sleep(1.21)

			log_type = self.config[guild_id]['type']  # type: str

			for embed, channelType in self.queue[guild_id][-175:]:
				list_obj = [embed, channelType]
				file_paths = []; files = []
				if isinstance(embed, tuple):
					embed, file_paths = embed
					if not isinstance(file_paths, list):
						file_paths = [file_paths]
					files = [discord.File(file) for file in file_paths if os.path.isfile(file)]

				sent = False
				while not guild.me.guild_permissions.administrator:
					if not sent:
						try:
							await guild.owner.send(
								f"I need administrator permissions in {guild} for the multi-log to function securely. "
								f"Until that's satisfied, i'll keep a maximum of 175 logs in queue"
							)
						except:
							pass
						sent = True
					await asyncio.sleep(60)

				category = self.bot.get_channel(self.config[guild_id]['channel'])
				if not category:
					if log_type == 'multi':
						category = await self.initiate_category(guild)
						self.save_data()
					elif log_type == 'single':
						category = await guild.create_text_channel(name='bot-logs')
						self.config[guild_id]['channel'] = category.id
					self.save_data()

				if isinstance(category, discord.TextChannel):  # single channel log
					await category.send(embed=embed, files=files)
					if file_paths:
						for file in file_paths:
							if os.path.isfile(file):
								os.remove(file)
					self.queue[guild_id].remove(list_obj)
					self.recent_logs[guild_id].append(embed)

				for Type, channel_id in self.config[guild_id]['channels'].items():
					if Type == channelType:
						channel = self.bot.get_channel(channel_id)
						if not channel:
							channel = await guild.create_text_channel(
								name=channelType,
								category=category
							)
							self.config[guild_id]['channels'][Type] = channel.id
							self.save_data()
						await channel.send(embed=embed, files=files)
						if file_paths:
							for file in file_paths:
								if os.path.isfile(file):
									os.remove(file)
						self.queue[guild_id].remove(list_obj)
						self.recent_logs[guild_id][channelType].append(embed)
						break

				if log_type == 'multi':
					# noinspection PyUnboundLocalVariable
					self.recent_logs[guild_id][channelType] = self.recent_logs[guild_id][channelType][-50:]
				elif log_type == 'single':
					self.recent_logs[guild_id] = self.recent_logs[guild_id][-175:]

	def past(self):
		""" gets the time 2 seconds ago in utc for audit searching """
		return datetime.utcnow() - timedelta(seconds=10)

	async def search_audit(self, guild, action) -> dict:
		""" Returns a dictionary of who performed an action """
		dat = {
			'user': 'Unknown',
			'target': 'Unknown',
			'icon_url': guild.icon_url,
			'thumbnail_url': guild.icon_url,
			'reason': None,
			'extra': None,
			'changes': None,
			'before': None,
			'after': None,
			'recent': False
		}
		if guild.me.guild_permissions.view_audit_log:
			async for entry in guild.audit_logs(limit=1, action=action, after=self.past()):
				dat['user'] = entry.user.mention
				if entry.target and isinstance(entry.target, discord.Member):
					dat['target'] = entry.target.mention
					dat['icon_url'] = entry.target.avatar_url
				else:
					dat['icon_url'] = entry.user.avatar_url
				dat['thumbnail_url'] = entry.user.avatar_url
				dat['reason'] = entry.reason
				dat['extra'] = entry.extra
				dat['changes'] = entry.changes
				dat['before'] = entry.before
				dat['after'] = entry.after
				dat['recent'] = True
				if entry.created_at < datetime.utcnow() - timedelta(seconds=3):
					dat['recent'] = False
					if action is audit.message_delete:
						dat['user'] = "Can't determine"
						dat['thumbnail_url'] = guild.icon_url
		else:
			await guild.owner.send(f"I'm missing audit log permissions for secure-log in {guild}\n"
			                       f"run `.secure-log disable` to stop recieving msgs")
		return dat

	def split_into_groups(self, text):
		return [text[i:i + 1000] for i in range(0, len(text), 1000)]

	@commands.group(name='secure-log')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@is_guild_owner()
	async def secure_log(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=fate())
			e.set_author(name='Multi Channel Log', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = ""
			e.add_field(
				name='Security',
				value="Logs can't be deleted by anyone, they aren't purge-able, and it " \
				      "re-creates deleted log channels and resends the last 50 logs",
				inline=False
			)
			p = utils.get_prefix(ctx)
			e.add_field(
				name='◈ Commands',
				value = f"{p}secure-log enable - `creates a log`"
				        f"\n{p}secure-log switch - `toggles multi-log`"
				        f"\n{p}secure-log disable - `deletes the log`",
				inline=False
			)
			await ctx.send(embed=e)

	@secure_log.group(name='enable')
	@commands.has_permissions(administrator=True)
	async def _enable(self, ctx):
		""" Creates a multi-log """
		guild_id = str(ctx.guild.id)
		if guild_id in self.config:
			return await ctx.send("Secure-Log is already enabled")
		channel = await ctx.guild.create_text_channel(name='secure-log')
		self.config[guild_id] = {
			"channel": channel.id,
			"channels": {},
			"type": "single"
		}
		self.bot.loop.create_task(self.start_queue(guild_id))
		await ctx.send("Enabled Secure-Log")
		self.save_data()

	@secure_log.command(name='switch')
	@commands.has_permissions(administrator=True)
	async def _switch(self, ctx):
		""" Switches a log between multi and single """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.config:
			return await ctx.send("Multi-Log isn't enabled")
		if self.config[guild_id]['type'] == 'single':
			await self.initiate_category(ctx.guild)
			self.config[guild_id]['type'] = 'multi'
			self.recent_logs[guild_id] = {
				Type: [] for Type in self.channel_types
			}
			await ctx.send("Enabled Multi-Log")
		else:
			log = await ctx.guild.create_text_channel(name='bot-logs')
			self.config[guild_id]['channel'] = log.id
			self.config[guild_id]['channels'] = {}
			self.config[guild_id]['type'] = 'single'
			self.recent_logs[guild_id] = []
			await ctx.send('Enabled Single-Log')
		self.save_data()

	@secure_log.command(name='disable')
	@commands.has_permissions(administrator=True)
	async def _disable(self, ctx):
		""" Deletes a multi-log """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.config:
			return await ctx.send("Secure-Log isn't enabled")
		del self.config[guild_id]
		await ctx.send('Disabled Secure-Log')
		self.save_data()

	@commands.command(name='start-loop')
	async def start_loop(self, ctx):
		self.bot.loop.create_task(self.start_queue(str(ctx.guild.id)))
		await ctx.send('Loop started')



	""" LISTENERS / EVENTS """  # this will be removed after initial development

	@commands.Cog.listener()
	async def on_ready(self):
		for guild_id in self.config.keys():
			self.bot.loop.create_task(self.start_queue(guild_id))

	@commands.Cog.listener()
	async def on_message(self, msg):
		""" @everyone and @here event """
		guild_id = str(msg.guild.id)
		if guild_id in self.config:
			mention = None
			content = str(msg.content).lower()
			if '!everyone' in content:
				mention = '@everyone'
			if '!here' in content:
				mention = '@here'
			if mention:
				msg = await msg.channel.fetch_message(msg.id)
				e = discord.Embed(color=white())
				e.title = f"~==🍸{mention} mentioned🍸==~"
				e.set_thumbnail(url=msg.author.avatar_url)
				is_successful = False
				if msg.author.guild_permissions.administrator:
					is_successful = True
				elif msg.author.guild_permissions.mention_everyone and (
						not msg.channel.permissions_for(msg.author).mention_everyone == False):
					is_successful = True
				elif msg.channel.permissions_for(msg.author).mention_everyone:
					is_successful = True
				e.description = f"Author: [{msg.author.mention}]" \
				                f"\nPing Worked: [{is_successful}]" \
				                f"\nChannel: [{msg.channel.mention}]"
				e.add_field(name='Content', value=msg.content, inline=False)
				self.queue[guild_id].append([e, 'system+'])

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		guild_id = str(before.guild.id)
		if guild_id in self.config and not after.author.bot:
			if before.content != after.content:
				e = discord.Embed(color=pink())
				e.set_author(name='~==🍸Msg Edited🍸==~', icon_url=before.author.avatar_url)
				e.set_thumbnail(url=before.author.avatar_url)
				e.description = f"__**Author:**__ [{before.author.mention}]" \
				                f"\n__**Channel:**__ [{before.channel.mention}]" \
				                f"\n[Jump to MSG]({before.jump_url})\n"
				for group in [before.content[i:i + 1000] for i in range(0, len(before.content), 1000)]:
					e.add_field(name='◈ Before', value=group, inline=False)
				for group in [after.content[i:i + 1000] for i in range(0, len(after.content), 1000)]:
					e.add_field(name='◈ After', value=group, inline=False)
				self.queue[guild_id].append([e, 'chat'])

			if before.embeds and not after.embeds:
				if before.channel.id == self.config[guild_id]['channel'] or(  # a message in the log was suppressed
						before.channel.id in self.config[guild_id]['channels']):
					await asyncio.sleep(0.5)  # prevent updating too fast and not showing on the users end
					return await after.edit(suppress=False)
				e = discord.Embed(color=lime_green())
				e.set_author(name='~==🍸Embed Hidden🍸==~', icon_url=before.author.avatar_url)
				e.set_thumbnail(url=before.author.avatar_url)
				e.description = f"__**Author:**__ [{before.author.mention}]" \
				                f"\n__**Channel:**__ [{before.channel.mention}]" \
				                f"\n[Jump to MSG]({before.jump_url})\n"
				em = before.embeds[0].to_dict()
				path = f'./static/embed-{before.id}.json'
				with open(path, 'w+') as f:
					json.dump(em, f, sort_keys=True, indent=4, separators=(',', ': '))
				self.queue[guild_id].append([(e, path), 'chat'])

			if before.pinned != after.pinned:
				action = 'Unpinned' if before.pinned else 'Pinned'
				audit_dat = await self.search_audit(after.guild, audit.message_pin)
				e = discord.Embed(color=cyan())
				e.set_author(name=f'~==🍸Msg {action}🍸==~', icon_url=after.author.avatar_url)
				e.set_thumbnail(url=after.author.avatar_url)
				e.description = f"__**Author:**__ [{after.author.mention}]" \
				                f"\n__**Channel:**__ [{after.channel.mention}]" \
				                f"__**Who Pinned:**__ [{audit_dat['user']}]" \
				                f"\n[Jump to MSG]({after.jump_url})"
				for text_group in self.split_into_groups(after.content):
					e.add_field(name="◈ Content", value=text_group, inline=False)
				self.queue[guild_id].append([e, 'chat'])

	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		channel = self.bot.get_channel(int(payload.data['channel_id']))
		guild_id = str(channel.guild.id)
		if guild_id in self.config and not payload.cached_message:
			msg = await channel.fetch_message(payload.message_id)
			e = discord.Embed(color=pink())
			e.set_author(name='Uncached Msg Edited', icon_url=msg.author.avatar_url)
			e.set_thumbnail(url=msg.author.avatar_url)
			e.description = f"__**Author:**__ [{msg.author.mention}]" \
			                f"\n__**Channel:**__ [{channel.mention}]" \
			                f"\n[Jump to MSG]({msg.jump_url})"
			for text_group in self.split_into_groups(msg.content):
				e.add_field(name='◈ Content', value=text_group, inline=False)
			self.queue[guild_id].append([e, 'chat'])

	@commands.Cog.listener()
	async def on_message_delete(self, msg):
		guild_id = str(msg.guild.id)
		if guild_id in self.config:
			if msg.embeds and msg.channel.id == self.config[guild_id]['channel'] or (
					msg.channel.id in [v for v in self.config[guild_id]['channels'].values()]):

				await msg.channel.send("OwO what's this", embed=msg.embeds[0])
				if msg.attachments:
					files = []
					for attachment in msg.attachments:
						path = os.path.join('static', attachment.filename)
						file = requests.get(attachment.proxy_url).content
						with open(path, 'wb') as f:
							f.write(file)
						files.append(path)
					self.queue[guild_id].append([(msg.embeds[0], files), 'sudo'])
				else:
					self.queue[guild_id].append([msg.embeds[0], 'sudo'])

				return

			if msg.author.id == self.bot.user.id and 'your cooldowns up' in msg.content:
				return  # is from work notifs within the factions module

			e = discord.Embed(color=purple())
			e.set_author(name='~==🍸Msg Deleted🍸==~', icon_url=msg.author.avatar_url)
			dat = await self.search_audit(msg.guild, audit.message_delete)
			e.set_thumbnail(url=dat['thumbnail_url'])
			e.description = f"__**Author:**__ {msg.author.mention}" \
			                f"\n__**Channel:**__ {msg.channel.mention}" \
			                f"\n__**Deleted by:**__ {dat['user']}"
			for text_group in self.split_into_groups(msg.content):
				e.add_field(name='◈ MSG Content', value=text_group, inline=False)
			if msg.embeds:
				e.set_footer(text='⇓ Embed ⇓')
			if msg.attachments:
				files = []
				for attachment in msg.attachments:
					path = os.path.join('static', attachment.filename)
					file = requests.get(attachment.proxy_url).content
					with open(path, 'wb') as f:
						f.write(file)
					files.append(path)
				self.queue[guild_id].append([(e, files), 'chat'])
			else:
				self.queue[guild_id].append([e, 'chat'])
			if msg.embeds:
				self.queue[guild_id].append([msg.embeds[0], 'chat'])

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.config and not payload.cached_message:
			guild = self.bot.get_guild(payload.guild_id)
			e = discord.Embed(color=purple())
			dat = await self.search_audit(guild, audit.message_delete)
			e.set_author(name='Uncached Message Deleted', icon_url=dat['icon_url'])
			e.set_thumbnail(url=dat['thumbnail_url'])
			e.description = f"__**Author:**__ {dat['target']}" \
			                f"\n__**MSG ID:**__ {payload.message_id}" \
			                f"\n__**Channel:**__ {self.bot.get_channel(payload.channel_id).mention}" \
			                f"\n__**Deleted By:**__ {dat['user']}"
			self.queue[guild_id].append([e, 'chat'])

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.config:
			guild = self.bot.get_guild(payload.guild_id)
			channel = self.bot.get_channel(payload.channel_id)
			purged_messages = ''
			for msg in payload.cached_messages:

				if msg.embeds:
					if msg.channel.id == self.config[guild_id]['channel']:
						self.queue[guild_id].append([msg.embeds[0], 'sudo'])
						continue
					if msg.channel.id in self.config[guild_id]['channels']:
						await msg.channel.send("OwO what's this", embed=msg.embeds[0])
						self.queue[guild_id].append([msg.embeds[0], 'sudo'])
						continue

				timestamp = msg.created_at.strftime('%I:%M%p')
				purged_messages = f"{timestamp} | {msg.author}: {msg.content}\n{purged_messages}"

			if payload.cached_messages and not purged_messages:  # only logs were purged
				return

			path = f'./static/purged-messages-{r.randint(0, 9999)}'
			with open(path, 'w') as f:
				f.write(purged_messages)

			e = discord.Embed(color=lime_green())
			dat = await self.search_audit(guild, audit.message_bulk_delete)
			if dat['extra'] and dat['icon_url']:
				e.set_author(name=f"~==🍸{dat['extra']['count']} Msgs Purged🍸==~", icon_url=dat['icon_url'])
			else:
				e.set_author(name=f"~==🍸{len(payload.cached_messages)} Msgs Purged🍸==~")
			if dat['thumbnail_url']:
				e.set_thumbnail(url=dat['thumbnail_url'])
			e.description = f"__**Users Effected:**__ [{len(list(set([msg.author for msg in payload.cached_messages])))}]" \
			                f"\n__**Channel:**__ [{channel.mention}]" \
			                f"\n__**Purged By:**__ [{dat['user']}]"
			self.queue[guild_id].append([(e, path), 'chat'])

	@commands.Cog.listener()
	async def on_raw_reaction_clear(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.config:
			channel = self.bot.get_channel(payload.channel_id)
			msg = await channel.fetch_message(payload.message_id)
			e = discord.Embed(color=yellow())
			e.set_author(name='~==🍸Reactions Cleared🍸==~', icon_url=msg.author.avatar_url)
			e.set_thumbnail(url=msg.author.avatar_url)
			e.description = f"__**Author:**__ [{msg.author.mention}]" \
			                f"\n__**Channel:**__ [{channel.mention}]" \
			                f"\n[Jump to MSG]({msg.jump_url})"
			self.queue[guild_id].append([e, 'chat'])

	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		guild_id = str(channel.guild.id)
		if guild_id in self.config:
			e = discord.Embed(color=yellow())
			dat = await self.search_audit(channel.guild, audit.channel_create)
			e.set_author(name='~==🍸Channel Created🍸==~', icon_url=dat['icon_url'])
			e.set_thumbnail(url=dat['thumbnail_url'])
			member_count = 'Unknown'
			if not isinstance(channel, discord.CategoryChannel):
				member_count = len(channel.members)
			mention = 'None'
			if isinstance(channel, discord.TextChannel):
				mention = channel.mention
			e.description = f"__**Name:**__ [{channel.name}]" \
			                f"\n__**Mention:**__ [{mention}]" \
			                f"\n__**ID:**__ [{channel.id}]" \
			                f"\n__**Creator:**__ [{dat['user']}]" \
			                f"\nMembers: [{member_count}]"
			self.queue[guild_id].append([e, 'actions'])

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		guild_id = str(channel.guild.id)
		if guild_id in self.config:

			# anti log channel deletion
			type = self.config[guild_id]['type']
			if channel.id == self.config[guild_id]['channel']:
				if type == 'single':
					for embed in self.recent_logs[guild_id]:
						self.queue[guild_id].append([embed, 'actions'])
					return
				for channelType, embeds in self.recent_logs[guild_id].items():
					for embed in embeds:
						self.queue[guild_id].append([embed, channelType])
			for channelType, channel_id in self.config[guild_id]['channels'].items():
				if channel_id == channel.id:
					for embed in self.recent_logs[guild_id][channelType]:
						self.queue[guild_id].append([embed, channelType])

			dat = await self.search_audit(channel.guild, audit.channel_delete)
			member_count = 'Unknown'
			if not isinstance(channel, discord.CategoryChannel):
				member_count = len(channel.members)
			category = 'None'
			if channel.category:
				category = channel.category.name

			e = discord.Embed(color=red())
			e.set_author(name='~==🍸Channel Deleted🍸==~', icon_url=dat['icon_url'])
			e.set_thumbnail(url=dat['thumbnail_url'])
			e.description = f"__**Name:**__ [{channel.name}]" \
			                f"\n__**ID:**__ [{channel.id}]" \
			                f"\n__**Category:**__ [{category}]" \
			                f"\n__**User:**__ [{dat['user']}]" \
			                f"\n__**Members:**__ [{member_count}]" \
			                f"\n__**Deleted by:**__ [{dat['user']}]"

			if isinstance(channel, discord.CategoryChannel):
				self.queue[guild_id].append([e, 'actions'])
				return

			path = f'./static/members-{r.randint(1, 9999)}.txt'
			members = f"{channel.name} - Member List"
			for member in channel.members:
				members += f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
			with open(path, 'w') as f:
				f.write(members)

			self.queue[guild_id].append([(e, path), 'actions'])

	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		guild_id = str(after.guild.id)
		if guild_id in self.config:
			e = discord.Embed(color=orange())
			dat = await self.search_audit(after.guild, audit.channel_update)
			e.set_author(name='~==🍸Channel Updated🍸==~', icon_url=dat['icon_url'])
			e.set_thumbnail(url=after.guild.icon_url)
			category = 'None, or Changed'
			if after.category and before.category == after.category:
				category = after.category.name

			if before.name != after.name:
				e.description = f"> 》__**Name Changed**__《" \
				                f"\n__**Before:**__ [{before.name}]" \
				                f"\n__**After:**__ [{after.name}]" \
				                f"\n__**Mention:**__ [{after.mention}]" \
				                f"\n__**Category:**__ [{category}]" \
				                f"\n__**ID:**__ [`{after.id}`]" \
				                f"\n__**Changed by:**__ [{dat['user']}]"
				self.queue[guild_id].append([e, 'updates'])

			if before.position != after.position:
				e.description = f"> 》__**Position Changed**__《" \
				                f"\n__**Name:**__ [{after.name}]" \
				                f"\n__**Mention:**__ [{after.mention}]" \
				                f"\n__**ID:**__ [{after.id}]" \
				                f"\n__**Category:**__ [{category}]" \
				                f"\n__**Before:**__ [{before.position}]" \
				                f"\n__**After:**__ [{after.position}]" \
				                f"\n__**Changed By:**__ [{dat['user']}]"
				self.queue[guild_id].append([e, 'updates'])

			if before.topic != after.topic:
				e.description = f"> 》__**Topic Changed**__《" \
				                f"\n__**Name:**__ [{after.name}]" \
				                f"\n__**Mention:**__ [{after.mention}]" \
				                f"\n__**ID:**__ [{after.id}]" \
				                f"\n__**Category:**__ [{category}]" \
				                f"\n__**Changed by:**__ [{dat['user']}]"
				for text_group in self.split_into_groups(before.topic):
					e.add_field(name='◈ Before', value=text_group, inline=False)
				for text_group in self.split_into_groups(after.topic):
					e.add_field(name='◈ After', value=text_group, inline=False)
				self.queue[guild_id].append([e, 'updates'])

			if before.category != after.category:
				e.description = f"> 》__**Category Changed**__《" \
				                f"\n__**Name:**__ [{after.name}]" \
				                f"\n__**Mention:**__ [{after.mention}]" \
				                f"\n__**ID:**__ [{after.id}]" \
				                f"\nChanged by:** [{dat['user']}]"
				name = 'None'
				if before.category:
					name = before.category.name
				e.add_field(
					name='◈ Before',
					value=f"__**Name:**__ [{name}]"
					      f"\n__**ID:**__ [{before.id}]",
					inline=False
				)
				name = 'None'
				if after.category:
					name = after.category.name
				e.add_field(
					name='◈ After',
					value=f"__**Name:**__ [{name}]"
					      f"\n__**ID:**__ [{after.id}]",
					inline=False
				)
				self.queue[guild_id].append([e, 'updates'])

			if before.overwrites != after.overwrites:

				for obj, permissions in list(before.overwrites.items()):
					after_objects = [x[0] for x in after.overwrites.items()]
					if obj not in after_objects:
						dat = await self.search_audit(after.guild, audit.overwrite_delete)
						perms = '\n'.join([f"{perm} - {value}" for perm, value in list(permissions) if value])
						e.add_field(
							name=f'❌ {obj.name} removed',
							value=perms if perms else "-had no permissions",
							inline=False
						)
						continue

					after_values = list(list(after.overwrites.items())[after_objects.index(obj)][1])
					if list(permissions) != after_values:
						dat = await self.search_audit(after.guild, audit.overwrite_update)
						e.add_field(
							name=f'<:edited:550291696861315093> {obj.name}',
							value='\n'.join([
								f"{perm} - {after_values[iter][1]}" for iter, (perm, value) in enumerate(list(permissions)) if (
									value != after_values[iter][1])
							]),
							inline=False
						)

				for obj, permissions in after.overwrites.items():
					if obj not in [x[0] for x in before.overwrites.items()]:
						dat = await self.search_audit(after.guild, audit.overwrite_create)
						perms = '\n'.join([f"{perm} - {value}" for perm, value in list(permissions) if value])
						e.add_field(
							name=f'<:plus:548465119462424595> {obj.name}',
							value=perms if perms else "-has no permissions",
							inline=False
						)

				e.set_author(name='~==🍸Channel Updated🍸==~', icon_url=dat['icon_url'])
				e.description = f"> 》__**Overwrites Changed**__《" \
				                f"\n__**Name:**__ [{after.name}]" \
				                f"\n__**Mention:**__ [{after.mention}]" \
				                f"\n__**ID:**__ [{after.id}]" \
				                f"\n__**Category:**__ {category}" \
				                f"\n__**Changed by:**__ {dat['user']}"
				self.queue[guild_id].append([e, 'updates'])

	@commands.Cog.listener()
	async def on_guild_channel_pins_update(self, before, after):
		pass

def setup(bot):
	bot.add_cog(SecureLog(bot))
