"""
Security Dashboard & Commands
+ Security Command - Overview / Module Toggles
- overview sub-command - detailed configs for nerds
- usage/help sub-command
"""

from os import path
import json
from time import time, monotonic
from typing import *
import asyncio
from datetime import datetime

from discord.ext import commands
import discord

from utils import colors, utils


def emoji(Type):
	""" returns a status emoji depending on the type """
	if isinstance(Type, bool) or Type == None:
		if Type:
			return '<:status_online:659976003334045727>'
		else:
			return '<:status_offline:659976011651219462>'
	if isinstance(Type, str):
		if any(sensitivity in Type.lower() for sensitivity in ['high', 'medium', 'low']):
			if Type == 'high':
				return '<:status_dnd:596576774364856321>'
			if Type == 'medium':
				return '<:status_idle:659976006030983206>'
			if Type == 'low':
				return '<:status_online:659976003334045727>'
		else:
			return 'wtf m8 im unprepared ;-;'
	else:
		return 'wtf m8 im unprepared ;-;'

class Security(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/security.json'
		self.conf = {}
		self.spam_cd = {}
		self.macro_cd = {}
		self.dupes = {}
		self.dupez = {}
		self.msgs = {}
		self.punished = {}

	def save_data(self):
		return  # don't wanna save during testing uwu
		#with open(self.path, 'w+') as f:
		#	json.dump(self.conf, f)

	def init(self, guild_id: str):
		self.conf[guild_id] = {
				'anti_spam': {
					'ignored': [],
					'rate_limit': {
						'toggle': True,
						'message_limit': 3,
						'timeframe': 5
					},
					'macro': {
						'toggle': True,
						'max_time_difference': 1,
						'check_last_msgs': 3
					},
					'mass_ping': {
						'toggle': False,
						'per_msg_user_limit': 5,
						'per_msg_role_limit': 1,
						'user_pings_per_min': 3,
						'role_pings_per_min': 1,
						'limit': 3
					},
					'duplicates': {
						'toggle': True,
						'repeated_lines': 3,
						'repeated_messages': 3,
						'timeframe': 15
					},
					'filter': {
						'invites': True,
						'zaglo': False,
						'caps': True,
						'max_lines': None,
						'emoji_limit': None,
						'custom_emoji_limit': True,
						'attachment_limit': None,
						'link_limit': None,
						'custom': ['uwu']
					}
				},
				'anti_raid': {
					'mass_join': {
						'toggle': False,
						'rate_limit': 5,
						'timeframe': 15
					},
					'mass_remove': {
						'toggle': False,
						'rate_limit': 4,
						'timeframe': 15,
						'hourly_limit': 25
					},
					'object_to_inv': False,
					'perm_transfer': False,
					'lockdown': {  # for when multiple people trigger security modules
						'toggle': False,
						'kick': False,  # disables lockdown channel if enabled
						'ban': False,  # disables lockdown channel if enabled
						'channel': None,  # create one if not exists, and uses roles
						'verification': True,
						'lock_overwrites': {
							'toggle': False,
							'only_malicious': True
						},
						'levels': {  # an example - customizable - overrides kick/ban/raid channel/verification
								'1': 'verification',
								'2': 'mute',
								'4': 'ban'
						},
						'lockdown_duration': 60 * 60 * 60,
						'complete_cleanup': True,
					},

				},
				'lock': {
					'silence': False,
					'mute': False,
					'kick': False,
					'ban': False
				}
			}
		self.save_data()

	@commands.group(name='security')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def security(self, ctx):
		""" General overview of security related modules """
		if not ctx.invoked_subcommand:
			p = utils.get_prefix(ctx)  # type: str
			guild_id = str(ctx.guild.id)
			if guild_id not in self.conf:
				self.init(guild_id)
			config = self.conf[guild_id]  # type: dict

			e = discord.Embed(color=colors.purple())
			e.set_author(name='Basic Security Info', icon_url=ctx.guild.owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.add_field(
				name='◈ Sub Commands',
				value=f"{p}**security overview** - `shows more detailed overview`"
				      f"\n{p}**security module** - `info on a security module`",
				inline=False
			)
			conf = config['anti_spam']
			e.add_field(
				name='◈ Anti Spam',
				value=f"{emoji(conf['rate_limit']['toggle'])} **Rate Limit**"
				      f"\n{emoji(conf['macro']['toggle'])} **Anti Macro**"
				      f"\n{emoji(conf['macro']['toggle'])} **Mass Ping**"
				      f"\n{emoji(conf['duplicates']['toggle'])} **Duplicates**"
				      f"\n{emoji(any(conf['filter'][key] for key in conf['filter'].keys()))} **Filter**"
			)
			conf = config['anti_raid']
			e.add_field(
				name='◈ Anti Raid',
				value=f"{emoji(conf['mass_join']['toggle'])} **Mass Join**"
				      f"\n{emoji(conf['mass_remove']['toggle'])} **Mass Remove**"
				      f"\n{emoji(conf['object_to_inv'])} **Obj to Invite**"
				      f"\n{emoji(conf['perm_transfer'])} **Perm Transfer**"
				      f"\n{emoji(conf['lockdown']['toggle'])} **Lockdown**"
			)
			conf = config['lock']
			e.add_field(
				name='◈ Lock',
				value=f"{emoji(conf['silence'])} **Silence**"
				      f"\n{emoji(conf['mute'])} **Mute**"
				      f"\n{emoji(conf['kick'])} **Kick**"
				      f"\n{emoji(conf['ban'])} **Ban**"
			)
			e.set_footer(text=f"API Response Time: {round(self.bot.latency * 1000)}ms")
			await ctx.send(embed=e)

	@security.command(name='overview')
	async def _overview(self, ctx):
		guild_id = str(ctx.guild.id)
		self.init(guild_id)
		config = self.conf[guild_id]

		e = discord.Embed(color=colors.purple())
		e.set_author(name='Detailed Security Overview', icon_url=self.bot.user.avatar_url)
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/632084935506788385/662903270884245514/network-security.png')

		conf = config['anti_spam']
		value = f"{emoji(len(conf['ignored']) > 0)} **Ignored Channels**"
		if not conf['ignored']:
			value += f"\n》None Ignored"
		for channel_id in conf['ignored']:
			channel = self.bot.get_channel(channel_id)
			value += f"\n• {channel.mention}"
		value += f"\n{emoji(conf['rate_limit']['toggle'])} **Rate Limit**" \
		         f"\n》Msg Limit: {conf['rate_limit']['message_limit']}" \
		         f"\n》Within Timeframe Of: {conf['rate_limit']['timeframe']}"
		value += f"\n{emoji(conf['macro']['toggle'])} **Macro Detection**" \
		         f"\n》Safe Time Difference: {conf['macro']['max_time_difference']}+ secs" \
		         f"\n》Last X Msgs to Check: {conf['macro']['check_last_msgs']}" \
		         f"\n{emoji(conf['mass_ping']['toggle'])} **Mass Pings**" \
		         f"\n》Max User Pings Per Msg: {conf['mass_ping']['per_msg_user_limit']}" \
		         f"\n》Max Role Pings Per Msg: {conf['mass_ping']['per_msg_role_limit']}" \
		         f"\n》Max User Pings Mer Min: {conf['mass_ping']['user_pings_per_min']}" \
		         f"\n》Max Role Pings Per Min: {conf['mass_ping']['role_pings_per_min']}"
		e.add_field(
			name='◈ Anti Spam',
			value=value
		)
		await ctx.send(embed=e)

	#@commands.Cog.listener()
	async def on_message(self, msg):
		""" anti spam related stuff """
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			if guild_id in self.conf:
				user_id = str(msg.author.id)
				sensitivity_level = self.conf[guild_id]['anti_spam']['rate_limit']['message_limit']
				if msg.channel.id in self.conf[guild_id]['anti_spam']['ignored']:
					return

				# msgs to delete if triggered
				if user_id not in self.msgs:
					self.msgs[user_id] = []
				self.msgs[user_id].append([msg, time()])
				self.msgs[user_id] = self.msgs[user_id][-15:]

				# rate limit
				# needs updated
				now = int(time() / 5)
				if guild_id not in self.spam_cd:
					self.spam_cd[guild_id] = {}
				if user_id not in self.spam_cd[guild_id]:
					self.spam_cd[guild_id][user_id] = [now, 0]
				if self.spam_cd[guild_id][user_id][0] == now:
					self.spam_cd[guild_id][user_id][1] += 1
				else:
					self.spam_cd[guild_id][user_id] = [now, 0]
				if self.spam_cd[guild_id][user_id][1] > sensitivity_level:
					if self.conf[guild_id]['anti_spam']['rate_limit']:
						triggered = True

				# mass pings
				# needs updated
				conf = self.conf[guild_id]['anti_spam']['mass_ping']
				mentions = [*msg.mentions, *msg.role_mentions]
				if len(mentions) > sensitivity_level + 1 or msg.guild.default_role in mentions:
					if msg.guild.default_role in mentions:
						if mentions.count(msg.guild.default_role) > 1 or len(mentions) > sensitivity_level + 1:
							if self.conf[guild_id]['anti_spam']['mass_ping']:
								triggered = True
					else:
						if self.conf[guild_id]['anti_spam']['mass_ping']:
							triggered = True

				# anti macro
				conf = self.conf[guild_id]['anti_spam']['macro']
				if user_id not in self.macro_cd:
					self.macro_cd[user_id] = {}
					self.macro_cd[user_id]['intervals'] = []
				if 'last' not in self.macro_cd[user_id]:
					self.macro_cd[user_id]['last'] = datetime.now()
				else:
					last = self.macro_cd[user_id]['last']
					self.macro_cd[user_id]['intervals'].append((datetime.now() - last).seconds)
					intervals = self.macro_cd[user_id]['intervals']
					self.macro_cd[user_id]['intervals'] = intervals[-conf['check_last_msgs'] + 1:]
					if len(intervals) > 2:
						if all(interval == intervals[0] for interval in intervals):
							if conf['toggle']:
								triggered = True

				# duplicates
				conf = self.conf[guild_id]['anti_spam']['duplicates']
				if guild_id not in self.dupes:
					self.dupes[guild_id] = []
					self.dupez[guild_id] = []
				self.dupes[guild_id].append([msg, time()])
				self.dupes[guild_id] = self.dupes[guild_id][:10]
				self.dupez[guild_id].append([msg, time()])
				self.dupez[guild_id] = self.dupes[guild_id][:10]
				data = [(m, m.content) for m, m_time in self.dupes[guild_id] if m_time > time() - conf['timeframe']]
				contents = [x[1] for x in data]
				duplicates = [m for m in contents if contents.count(m) > conf['repeated_messages']]
				if msg.content in duplicates:
					def pred(m):
						return m.channel.id == msg.channel.id and m.author.bot
					try:
						msg = await self.bot.wait_for('message', check=pred, timeout=2)
					except asyncio.TimeoutError:
						data = [(m, m_time) for m, m_time in self.dupez[guild_id] if
						        msg.content == m.content and [m, m_time] in data]
						for m, m_time in data:
							self.dupez[guild_id].pop(self.dupez[guild_id].index([m, m_time]))
							if m in self.msgs[str(m.author.id)]:
								self.msgs[user_id].pop(self.msgs[user_id].index(m))
						await msg.channel.delete_messages([m[1] for m in data])
						if conf['toggle']:
							triggered = True
				lines = msg.content.split('\n')
				lines = [line for line in lines if len(line) > 0]
				if any(lines.count(line) > conf['repeated_lines'] for line in lines):
					if conf['toggle']:
						triggered = True

def setup(bot):
	bot.add_cog(Security(bot))
