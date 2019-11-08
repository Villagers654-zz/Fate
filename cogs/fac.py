"""
Factions Game For Discord.Py
- Supports discord.py v1.0 - v1.3
"""

import json
from os import path
import random
import asyncio

from discord.ext import commands
import discord

from utils.colors import *
from utils import utils


class Factions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './'
		self.icon = 'https://cdn.discordapp.com/attachments/641032731962114096/641742675808223242/13_Swords-512.png'
		self.banner = ''
		self.boosts = {
			'extra-income': {},
			'land-guard': [],
			'anti-raid': {}
		}
		self.game_data = {}
		self.factions = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.factions = json.load(f)  # type: dict


	def save_data(self) -> None:
		""" Saves the current variables """
		with open(self.path, 'w+') as f:
			json.dump(self.factions, f)


	def collect_claims(self, guild_id, faction=None) -> dict:
		""" Fetches claims for the whole guild or a single faction
		    for easy use when needing all the claims """
		def claims(faction) -> dict:
			""" returns claims & their data """
			claims = {}
			fac = self.factions[guild_id][faction]
			for claim in fac['claims']:
				is_guarded = False
				if claim in self.boosts['boosts']['land-guard']:
					is_guarded = True
				claims[claim] = {
					'faction': faction,
					'guarded': is_guarded
				}
			return claims

		if faction:
			return claims(faction)
		global_claims = {}
		for faction in self.factions[guild_id].keys():
			claims = claims(faction)  # type: dict
			for claim, data in claims.items():
				global_claims[claim] = data
		return global_claims


	def update_income_board(self, guild_id, faction, **kwargs) -> None:
		for key, value in kwargs.items():
			self.factions[guild_id][faction]['income'][key] += value


	@commands.group(name='fac')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def fac(self, ctx):
		""" Information about the module """
		if not ctx.invoked_subcommand:
			p = utils.get_prefix(ctx)  # type: str
			if len(ctx.message.content.split()) > 1:
				return await ctx.send(f'Unknown command\nTry using `{p}factions help`')
			e = discord.Embed(color=purple())
			e.set_author(name='Discord Factions', icon_url=self.icon)
			e.description = 'Create factions, group up, complete work tasks to earn ' \
			                'your faction money, raid other factions while they\'re ' \
			                'not guarded, challenge enemys to minigame battles, and ' \
			                'rank up on the faction leaderboard'
			await ctx.send(embed=e)


	@fac.command(name='help', aliases=['commands'])
	async def _help(self, ctx):
		""" Command usage and descriptions """
		e = discord.Embed(color=purple())
		e.set_author(name='Usage', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		p = utils.get_prefix(ctx)  # type: str
		e.add_field(
			name='◈ Core ◈',
			value=f'{p}factions create [name]\n'
			      f'{p}factions rename [name]\n' \
			      f'{p}factions disband\n' \
			      f'{p}factions join [faction]\n' \
			      f'{p}factions invite @user\n'
			      f'{p}factions promote @user\n'
			      f'{p}factions demote @user\n' \
			      f'{p}factions kick @user\n' \
			      f'{p}factions leave\n',
			inline=False
		)
		e.add_field(
			name='◈ Utils ◈',
			value=f'{p}faction privacy\n'
			      f'{p}factions setbio [your new bio]\n'
			      f'{p}factions seticon [file | url]\n' \
			      f'{p}factions setbanner [file | url]\n' \
			      f'{p}factions togglenotifs',
			inline=False
		)
		e.add_field(
			name='◈ Economy ◈',
			value=f'{p}faction work\n' \
			      f'{p}factions balance\n' \
			      f'{p}factions pay [faction] [amount]\n' \
			      f'{p}factions raid [faction]\n'
			      f'{p}factions battle [faction]\n' \
			      f'{p}factions annex [faction]\n' \
			      f'{p}factions claim #channel\n' \
			      f'{p}factions unclaim #channel\n' \
			      f'{p}factions claims\n' \
			      f'{p}factions boosts\n' \
			      f'{p}factions top',
			inline=False
		)
		await ctx.send(embed=e)


	@commands.Cog.listener()
	async def on_message(self, msg):
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			if guild_id in self.factions:
				claims = self.collect_claims(guild_id)  # type: dict
				channel_id = str(msg.channel.id)
				if channel_id in claims:
					faction = claims[channel_id]['faction']
					pay = random.randint(1, 5)
					self.factions[guild_id][faction]['balance'] += pay
					self.update_income_board(guild_id, faction, land_claims=pay)


def setup(bot):
	bot.add_cog(Factions(bot))
