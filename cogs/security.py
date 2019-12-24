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
"""

from os import path
import json
from time import time, monotonic
from typing import *

from discord.ext import commands


class Security(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = {
			'guild_id': {
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
						'link_limit': None
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
						'levels': Union[
							None, {  # an example - customizable - overrides kick/ban/raid channel
								'1': 'verification',
								'2': 'mute',
								'3': 'kick',
								'4': 'ban'
							}
						],
						'lockdown_duration': 60*60*60,
						'complete_cleanup': True,
					},

				},
				'lock': {
					'mute': False,
					'kick': False,
					'ban': False
				}
			}
		}


def setup(bot):
	bot.add_cog(Security(bot))
