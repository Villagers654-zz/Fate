"""
Security Dashboard & Commands
+ Security Command - Detailed Status
- overview sub-command - simplified status
- usage/help sub-command

+ Anti Raid Command
- multiple types of spam prevention:
  rate limit, macro, mass ping, duplicates
- spamming on multiple accounts - organized raid
- lock the server on mass join

+ Anti Mod Raid - Part Of Anti Raid
- mass kick and ban
- mass channel/role delete - light punishment
- turning things like server name into adverts

+ Raid Alerts - Part Of Anti Raid
- Make a raid alert role mentionable, mention it,
  and make it no longer mentionable
- Send a message to the staff channel

+ Lockdown / Raider Gate -  Part Of Anti Raid
- when multiple people raid, create a temp channel
- send instructions on how an admin can unlock in temp channel
  alongside a reaction verification; which when failed
  the user/user-bot is banned. Other users have to wait it out
- create a raider role
- set overwrites in temp channel for only raider to be able to see or send
- set overwrites for raider to not see everywhere else but make
  sure to use category overwrites first in the instance of channel
  overwrites being sync'd so nothing gets fucked up
- give any raiders that triggered it the raider role
- release command with option to ban those with raider role

+ Server Lock
- kick users on join
- ban users on join - the lock anti raid will use

+ All lock functionality under the same lock so you
  can disable all locks with .unlock for ease of use

this shit needs updated
"""

from os import path
import json
from time import time, monotonic
from typing import *

from discord.ext import commands
import discord

from utils import colors, utils


def emoji(Type):
	if isinstance(Type, bool):
		if Type:
			return '<:status_online:659976003334045727>'
		else:
			return '<:status_offline:659976011651219462>'
	if isinstance(Type, str):
		if any(sensitivity in Type.lower()
	        for sensitivity in ['high', 'medium', 'low']):
			if Type == 'high':
				return '<:status_dnd:596576774364856321>'
			if Type == 'medium':
				return '<:status_idle:659976006030983206>'
			if Type == 'low':
				return '<:status_online:659976003334045727>'
		else:
			return 'wtf m8 im unprepared ;-;'

class Security(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/security.json'
		self.conf = {}

	def save_data(self):
		return  # don't wanna save during testing
		with open(self.path, 'w+') as f:
			json.dump(self.conf, f)

	def init(self, guild_id: str):
		self.conf[guild_id] = {
				'anti_spam': {
					'ignored': [],
					'rate_limit': {
						'toggle': False,
						'message_limit': 3,
						'timeframe': 5
					},
					'macro': {
						'toggle': False,
						'max_time_difference': 1,
						'last_x_messages': 3
					},
					'mass_ping': {
						'toggle': False,
						'per_msg_user_limit': 5,
						'per_msg_role_limit': 1,
						'limit': 3
					},
					'duplicates': {
						'toggle': False,
						'repeated_lines': 3,
						'repeated_messages': 3,
						'timeframe': 15
					},
					'filter': {
						'invites': False,
						'zaglo': False,
						'caps': False,
						'max_lines': None,
						'emoji_limit': None,
						'custom_emoji_limit': None,
						'attachment_limit': None,
						'link_limit': None,
						'custom': []
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
					'lockdown': {
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
								'3': 'kick',
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
			#e.add_field(
			#	name='◈ Bot',
			#	value=f"__**API Response Time:**__ {round(self.bot.latency * 1000)}ms"
			#)
			conf = config['anti_spam']
			e.add_field(
				name='◈ Anti Spam',
				value=f"{emoji(conf['rate_limit']['toggle'])} __**Rate Limit**__"
				      f"\n{emoji(conf['macro']['toggle'])} __**Anti Macro**__"
				      f"\n{emoji(conf['macro']['toggle'])} __**Mass Ping**__"
				      f"\n{emoji(conf['duplicates']['toggle'])} __**Duplicates**__"
				      f"\n{emoji(any(conf['filter'][key] for key in conf['filter'].keys()))} __**Filter**__"
			)
			conf = config['anti_raid']
			e.add_field(
				name='◈ Anti Raid',
				value=f"{emoji(conf['mass_join']['toggle'])} __**Mass Join**__ "
				      f"\n{emoji(conf['mass_remove']['toggle'])} __**Mass Remove**__"
				      f"\n{emoji(conf['object_to_inv'])} __**Obj to Invite**__"
				      f"\n{emoji(conf['perm_transfer'])} __**Perm Transfer**__"
				      f"\n{emoji(conf['lockdown']['toggle'])} __**Lockdown**__"
			)
			conf = config['lock']
			e.add_field(
				name='◈ Lock',
				value=f"{emoji(conf['silence'])} __**Silence**__"
				      f"\n{emoji(conf['mute'])} __**Mute**__"
				      f"\n{emoji(conf['kick'])} __**Kick**__"
				      f"\n{emoji(conf['ban'])} __**Ban**__"
			)
			await ctx.send(embed=e)

	@security.command(name='overview')
	async def _overview(self, ctx):
		""" More complex and detailed overview """


# events / listeners:


def setup(bot):
	bot.add_cog(Security(bot))
