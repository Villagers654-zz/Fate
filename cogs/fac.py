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


	def init(self, guild_id: str):
		""" Creates guild dictionary if it doesnt exist """
		if guild_id not in self.factions:
			self.factions[guild_id] = {}


	async def get_users_faction(self, ctx, user=None):
		""" fetch a users faction by context or partial name """
		guild_id = str(ctx.guild.id)
		if ctx and user:
			user = utils.get_user(ctx, user)
			if not user:
				return None
			for faction, data in self.factions[guild_id].items():
				if user.id in data['members']:
					return faction
		elif ctx and not user:
			for faction, data in self.factions[guild_id].items():
				if ctx.author.id in data['members']:
					return faction


	def get_faction_named(self, ctx, name):
		""" gets a faction via partial name """
		def pred(m) -> bool:
			""" A check for waiting on a message """
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

		guild_id = str(ctx.guild.id)
		factions = [f for f in self.factions[guild_id].keys() if str(f).lower() == str(name).lower()]
		if not factions:
			factions = [f for f in self.factions[guild_id].keys() if str(name).lower() in str(f).lower()]
		if len(factions) > 1:
			e = discord.Embed(color=cyan())
			e.description = ''
			index = 1
			for faction in factions:
				owner_id = self.factions[str(ctx.guild.id)][faction]['owner']
				owner = self.bot.get_user(owner_id)
				e.description += f'{index}. {faction} - {owner.mention}\n'
			embed = await ctx.send(embed=e)
			try:
				msg = await ctx.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send('Timeout error', delete_after=5)
				await embed.delete()
				return None
			else:
				try:
					choice = int(msg.content)
				except:
					await ctx.send('Invalid response')
					await embed.delete()
					return None
				if choice > len(factions):
					return await ctx.send('Invalid number')
				return factions[index - 1]
		elif len(factions) == 1:
			return factions[0]
		else:
			return None


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
	async def factions(self, ctx):
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


	@factions.command(name='help', aliases=['commands'])
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


	@factions.command(name='create')
	async def create(self, ctx, *, name):
		""" Creates a faction """
		guild_id = str(ctx.guild.id)
		faction = self.get_users_faction(ctx)
		if faction:
			return await ctx.send('You must leave your current faction to create a new one')
		if ctx.message.mentions or ctx.message.role_mentions or '@everyone' in name or '@here' in name:
			return await ctx.send('biTcH nO')
		self.init(guild_id)  # make sure the key is setup properly
		if str(name).lower() in [str(f).lower() for f in self.factions[guild_id].keys()]:
			return await ctx.send('That name is already taken')
		self.factions[guild_id][name] = {
			'owner': ctx.author.id,
			'co-owners': [],
			'members': [],
			'claims': []
		}
		await ctx.send('Created your faction')
		self.save_data()


	@factions.command(name='disband')
	async def disband(self, ctx):
		""" Deletes the owned faction """


	@factions.command(name='join')
	async def join(self, ctx, *, faction):
		""" Join a public faction """


	@factions.command(name='invite')
	async def invite(self, ctx, user: discord.Member):
		""" Invites a user to a private faction """


	@factions.command(name='kick')
	async def kick(self, ctx, *, user):
		""" Kicks a user from the faction """
		user = utils.get_user(ctx, user)


	@commands.command(name='rename')
	async def rename(self, ctx, *, name):
		""" Renames their faction """


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
