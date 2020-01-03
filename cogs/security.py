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

	def save_data(self):
		return  # don't wanna save during testing uwu
		with open(self.path, 'w+') as f:
			json.dump(self.conf, f)

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
		""" More complex and detailed overview """
		guild_id = str(ctx.guild.id)
		self.init(guild_id)

		e = discord.Embed(color=colors.purple())
		e.set_author(name='Detailed Security Overview', icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)

		for key, value in self.conf[guild_id]['anti_spam'].items():
			if not isinstance(value, dict):
				channels = '\n'.join([f'{self.bot.get_channel(c).mention}' for c in value])
				if channels:
					e.add_field(
						name=f'◈ Ignored {len(value)}',
						value=channels if channels else f'{emoji(False)} None'
					)
				continue
			stuffs = []
			for k, v in value.items():
				is_toggle = isinstance(v, bool) or v == None
				if is_toggle:
					stuff = f"{emoji(v)} {k.replace('_', '-')}"
				else:
					stuff = f"{k.replace('_', '-')}**:** {v}"
				stuffs.append(stuff)
			e.add_field(
				name=f'◈ {key.replace("_", " ")}',
				value='\n'.join(stuffs),
				inline=False
			)
		await ctx.send(embed=e)

# events / listeners:


def setup(bot):
	bot.add_cog(Security(bot))
