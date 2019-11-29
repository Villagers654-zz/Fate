"""
Factions Game For Discord.Py
- Supports versions 1.1 - 1.3
- Create factions, group up, complete work tasks to earn money
- Raid other factions while they're not guarded
- Challenge enemys to minigame battles
- Rank up on the faction leaderboard
"""

import json
from os import path
import random
import asyncio

from discord.ext import commands
import discord

from utils.colors import *
from utils import utils, checks


class MiniGames:
	def __init__(self, *users):
		self.users = users

	async def scrabble(self, ctx):
		""" Randomize the order of letters in a word """
		def pred(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id in self.users and (
				str(msg.content).lower() == word)

		words = []  # stay wholesome uwu
		word = random.choice(words)
		scrambled_word = list(str(word).lower())
		random.shuffle(scrambled_word)

		e = discord.Embed(color=fate())
		e.description = f"Scrambled word: `{scrambled_word}`"
		e.set_footer(text="You have 20 seconds..", icon_url=ctx.bot.user.avatar_url)
		await ctx.send(embed=e)

		try:
			msg = ctx.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			await ctx.send("You failed :/")
			return None
		else:
			if len(self.users) > 1:
				await ctx.send(f"{msg.author.display_name} won!")
			else:
				await ctx.send("You won!")
			return msg.author


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
		self.pending = []
		self.factions = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.factions = json.load(f)  # type: dict

	def save_data(self) -> None:
		""" Saves the current variables """
		return
		with open(self.path, 'w+') as f:
			json.dump(self.factions, f)

	def init(self, guild_id: str):
		""" Creates guild dictionary if it doesnt exist """
		if guild_id not in self.factions:
			self.factions[guild_id] = {}

	def faction_icon(self, ctx, faction: str)->str:
		""" returns an icon for the faction """
		guild_id = str(ctx.guild.id)
		if 'icon' in self.factions[guild_id][faction]:
			if self.factions[guild_id][faction]['icon']:
				return self.factions[guild_id][faction]['icon']
		owner_id = self.factions[guild_id][faction]['owner']
		owner = self.bot.get_user(owner_id)
		return owner.avatar_url

	def get_users_faction(self, ctx, user=None):
		""" fetch a users faction by context or partial name """
		if not user:
			user = ctx.author
		guild_id = str(ctx.guild.id)
		if not isinstance(user, discord.Member):
			user = utils.get_user(ctx, user)
		if not user:
			return None
		if guild_id in self.factions:
			for faction, data in self.factions[guild_id].items():
				if user.id in data['members']:
					return faction
		return None

	def get_owned_faction(self, ctx, user=None):
		""" returns a users owned faction if it exists """
		if not user:
			user = ctx.author.mention
		user = utils.get_user(ctx, user)
		if not user:
			return
		guild_id = str(ctx.guild.id)
		for faction, data in self.factions[guild_id].items():
			if user.id == data['owner']:
				return faction
		return None

	async def get_faction_named(self, ctx, name):
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
				channel = self.bot.get_channel(int(claim))
				if not isinstance(channel, discord.TextChannel):
					self.factions[guild_id]['balance'] += 250
					self.factions[guild_id][faction]['claims'].remove(claim)
					continue
				is_guarded = False
				if claim in self.boosts['boosts']['land-guard']:
					is_guarded = True
				claims[int(claim)] = {
					'faction': faction,
					'guarded': is_guarded,
					'position': channel.position
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

	def get_faction_rankings(self, guild_id):
		factions = []
		def get_value(kv):
			value = kv[1]['balance']
			for i in range(len(kv[1]['claims'])):
				value += 500
			return value
		for faction, data in sorted(self.factions[guild_id].items(), key=get_value, reverse=True):
			factions.append([faction, get_value([faction, data])])
		return factions

	def update_income_board(self, guild_id, faction, **kwargs) -> None:
		for key, value in kwargs.items():
			self.factions[guild_id][faction]['income'][key] += value

	@commands.command(name='convert-factions')
	@commands.check(checks.luck)
	async def convert_factions(self, ctx):
		new_dict = {}
		with open('./data/userdata/factions.json', 'r') as f:
			dat = json.load(f)  # type: dict
		for guild_id, factions in dat['factions'].items():
			new_dict[guild_id] = {}
			for faction, metadata in factions.items():
				if faction == 'category':
					continue
				claims = []
				if guild_id in dat['land_claims']:
					if faction in dat['land_claims'][guild_id]:
						claims = [int(k) for k in dat['land_claims'][guild_id][faction].keys()]
				new_dict[faction] = {
					"owner": metadata['owner'],
					"co-owners": [],
					"members": metadata['members'],
					"balance": metadata['balance'],
					"claims": claims,
					"public": True,
					"limit": 15,
					"income": {},
					"bio": None
				}
				if 'limit' in metadata:
					new_dict['limit'] = metadata['limit']
				if 'access' in metadata:
					new_dict['public'] = True if metadata['access'] == 'public' else False
				if 'co-owners' in metadata:
					new_dict['co-owners'] = metadata['co-owners']
				if 'bio' in metadata:
					new_dict['bio'] = metadata['bio'] if metadata['bio'] else None
				if 'icon' in metadata:
					new_dict['icon'] = metadata['icon']
				if 'banner' in metadata:
					new_dict['banner'] = metadata['banner']
		await ctx.send("Conversion Would Succeed")

	@commands.group(name='fac')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(send_messages=True, embed_links=True)
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
			value=f'{p}factions create [name]'
			      f'\n{p}factions rename [name]'
			      f'\n{p}factions disband'
			      f'\n{p}factions join [faction]'
			      f'\n{p}factions invite @user'
			      f'\n{p}factions promote @user'
			      f'\n{p}factions demote @user'
			      f'\n{p}factions kick @user'
			      f'\n{p}factions leave',
			inline=False
		)
		e.add_field(
			name='◈ Utils ◈',
			value=f'{p}faction privacy'  # incomplete
			      f'\n{p}factions setbio [your new bio]'  # incomplete
			      f'\n{p}factions seticon [file | url]'  # incomplete
			      f'\n{p}factions setbanner [file | url]'  # incomplete
			      f'\n{p}factions togglenotifs',  # incomplete
			inline=False
		)
		e.add_field(
			name='◈ Economy ◈',
			value=f'{p}faction work'
			      f'\n{p}factions balance'  # incomplete
			      f'\n{p}factions pay [faction] [amount]'  # incomplete
			      f'\n{p}factions raid [faction]'  # incomplete
			      f'\n{p}factions battle [faction]'  # incomplete
			      f'\n{p}factions annex [faction]'  # incomplete
			      f'\n{p}factions claim #channel'  # incomplete
			      f'\n{p}factions unclaim #channel'  # incomplete
			      f'\n{p}factions claims'
			      f'\n{p}factions boosts'  # incomplete
			      f'\n{p}factions info'
			      f'\n{p}factions members [faction]'
			      f'\n{p}factions top',  # incomplete
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
			'members': [ctx.author.id],
			'balance': 0,
			'limit': 15,
			'public': True,
			'claims': [],
			'bio': None,
			'income': {}
		}
		await ctx.send('Created your faction')
		self.save_data()

	@factions.command(name='disband')
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def disband(self, ctx):
		""" Deletes the owned faction """
		def pred(msg):
			return msg.author.id == ctx.author.id and msg.channel.id == msg.channel.id and (
				'yes' in msg.content or 'no' in msg.content)

		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to be owner to use this cmd")
		guild_id = str(ctx.guild.id)
		if ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send("You need to be owner to use this cmd")

		instruction = await ctx.send("Are you sure you want to delete your faction?\nReply with 'yes' or 'no'")
		try:
			msg = self.bot.wait_for('message', check=pred, timeout=30)
		except asyncio.TimeoutError:
			await instruction.delete()
			return await ctx.message.delete()
		else:
			if 'yes' in msg.content.lower():
				del self.factions[guild_id][faction]
				await ctx.send("Ok.. deleted your faction")
				self.save_data()
			else:
				await ctx.send("Ok, I won't delet")

	@factions.command(name='join')
	async def join(self, ctx, *, faction):
		""" Joins a public faction via name """
		is_in_faction = self.get_users_faction(ctx)  # type: str
		if is_in_faction:
			return await ctx.send("You're already in a faction")
		faction = await self.get_faction_named(ctx, faction)
		if not faction:
			return await ctx.send("Couldn't find a faction under that name :[")
		guild_id = str(ctx.guild.id)
		if not self.factions[guild_id][faction]['public']:
			return await ctx.send("That factions not public :[")
		self.factions[guild_id][faction]['members'].append(ctx.author.id)
		e = discord.Embed(color=purple())
		e.set_author(name=faction, icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=self.faction_icon(ctx, faction))
		e.description = f"{ctx.author.display_name} joined\nMember Count: " \
		                f"[`{len(self.factions[guild_id][faction]['members'])}`]"
		await ctx.send(embed=e)
		self.save_data()

	@factions.command(name='invite')
	async def invite(self, ctx, user: discord.Member):
		""" Invites a user to a private faction """
		def pred(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == user.id and (
				'yes' in msg.content and 'no' in msg.content)

		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to have at least co-owner to use this cmd")
		users_in_faction = self.get_users_faction(ctx, user)
		if users_in_faction:
			return await ctx.send("That users already in a faction :[")
		if user.id in self.pending:
			return await ctx.send("That user already has a pending invite")
		self.pending.append(user.id)

		request = await ctx.send(f"{user.mention}, {ctx.author.display_name} invited you to join {faction}\n"
		                         f"Reply with 'yes' to join, or 'no' to reject")
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=60)
		except asyncio.TimeoutError:
			await request.edit(content=f"~~{request.content}~~\n\nRequest Expired")
			await ctx.message.delete()
		else:
			if 'yes' in msg.content.lower():
				self.factions[str(ctx.guild.id)][faction]['members'].append(ctx.author.id)
				await ctx.send(f"{user.display_name} joined {faction}")
				self.save_data()
			else:
				await ctx.send("Alrighty then :[")
		self.pending.remove(user.id)

	@factions.command(name='leave')
	async def leave(self, ctx):
		""" Leaves a faction """
		faction = self.get_users_faction(ctx)
		if not faction:
			return await ctx.send("You're not currently in a faction")
		if self.get_owned_faction(ctx):
			return await ctx.send("You cannot leave a faction you own, you must "
			                      "transfer ownership, or disband it")
		guild_id = str(ctx.guild.id)
		self.factions[guild_id][faction]['members'].remove(ctx.author.id)
		if ctx.author.id in self.factions[guild_id]['co-owners']:
			self.factions[guild_id]['co-owners'].remove(ctx.author.id)
		await ctx.send('👍')
		self.save_data()

	@factions.command(name='kick')
	async def kick(self, ctx, *, user):
		""" Kicks a user from the faction """
		user = utils.get_user(ctx, user)
		if not user:
			return await ctx.send("User not found")
		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to at least be co-owner to use this cmd")
		users_faction = self.get_users_faction(ctx, user)
		if not users_faction:
			return await ctx.send("That users not in a faction")
		if users_faction != faction:
			return await ctx.send("That user isn't in your faction :/")
		guild_id = str(ctx.guild.id)
		if user.id == self.factions[guild_id][faction]['owner']:
			return await ctx.send("You cant demote the owner ._.")
		if user.id in self.factions[guild_id][faction]['co-owners'] and (
				ctx.author.id != self.factions[guild_id][faction]['owner']):
			return await ctx.send("Only the owner can demote a co-owner!")
		self.factions[guild_id][faction]['members'].remove(user.id)
		if user.id in self.factions[guild_id]['co-owners']:
			self.factions[guild_id]['co-owners'].remove(user.id)
		await ctx.send(f"Kicked {user.display_name} from {faction}")
		self.save_data()

	@factions.command(name='promote')
	async def promote(self, ctx, *, user):
		""" Promotes a faction member to Co-Owner"""
		user = await utils.get_user(ctx, user)
		if not user:
			return await ctx.send("User not found")
		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		guild_id = str(ctx.guild.id)
		if ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		if user.id in self.factions[guild_id][faction]['co-owners']:
			return await ctx.send("That users already co-owner")
		self.factions[guild_id][faction]['co-owners'].append(user.id)
		await ctx.send(f"Promoted {user.display_name} to co-owner")
		self.save_data()

	@factions.command(name='demote')
	async def demote(self, ctx, *, user):
		""" Demotes a faction member from Co-Owner """
		user = await utils.get_user(ctx, user)
		if not user:
			return await ctx.send("User not found")
		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		guild_id = str(ctx.guild.id)
		if ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		if user.id not in self.factions[guild_id][faction]['co-owners']:
			return await ctx.send("That users not co-owner")
		self.factions[guild_id][faction]['co-owners'].remove(user.id)
		await ctx.send(f"Demoted {user.display_name} from co-owner")

	@factions.command(name='annex', enabled=False)
	async def annex(self, ctx, *, faction):
		""" Merges a faction with another """

	@factions.command(name='rename')
	async def rename(self, ctx, *, name):
		""" Renames their faction """
		faction = self.get_owned_faction(ctx)
		if not faction:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		guild_id = str(ctx.guild.id)
		if ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send("You need to be owner of a faction to use this cmd")
		if str(name).lower() in [str(fac).lower() for fac in self.factions[guild_id].keys()]:
			return await ctx.send("That names already taken")
		self.factions[guild_id][name] = self.factions[guild_id].pop(faction)
		await ctx.send(f"Changed your factions name from {faction} to {name}")
		self.save_data()

	@factions.command(name='info')
	async def info(self, ctx, *, faction=None):
		""" Bulk information on a faction """
		if faction:
			faction = await self.get_faction_named(ctx, faction)
		else:
			faction = self.get_users_faction(ctx)
		if not faction:
			return await ctx.send("Faction not found")

		guild_id = str(ctx.guild.id)
		dat = self.factions[guild_id][faction]  # type: dict
		owner = self.bot.get_user(dat['owner'])
		icon_url = self.faction_icon(ctx, faction)
		rankings = self.get_faction_rankings(guild_id)  # type: list
		rank = 1
		for fac, value in rankings:
			if fac == faction:
				break
			rank += 1

		e = discord.Embed(color=purple())
		e.set_author(name=faction, icon_url=owner.avatar_url)
		e.set_thumbnail(url=icon_url)
		e.description = f"__**Owner:**__ `{owner}`" \
						f"\n__**Members:**__ [`{len(dat['members'])}`] " \
						f"__**Public:**__ [`{dat['public']}`]" \
						f"\n__**Balance:**__ [`${dat['balance']}`]\n"
		if dat['bio']:
			e.description += f"__**Bio:**__ [`{dat['bio']}`]"
		if 'banner' in dat:
			if dat['banner']:
				e.set_image(url=dat['banner'])
		e.set_footer(text=f"Leaderboard Rank: #{rank}")
		await ctx.send(embed=e)

	@factions.command(name='members')
	async def members(self, ctx, *, faction=None):
		""" lists a factions members """
		if faction:
			faction = await self.get_faction_named(ctx, faction)
		else:
			faction = self.get_users_faction(ctx)
		if not faction:
			return await ctx.send("Faction not found")

		guild_id = str(ctx.guild.id)
		owner_id = self.factions[guild_id][faction]['owner']
		owner = self.bot.get_user(owner_id)
		users = []
		co_owners = []
		for user_id in self.factions[guild_id][faction]['members']:
			user = self.bot.get_user(user_id)
			if not isinstance(user, discord.User):
				self.factions[guild_id][faction].remove(user_id)
				self.save_data()
				continue

			income = 0
			if user_id in self.factions[guild_id][faction]['income']:
				income = self.factions[guild_id][faction][income][user_id]
			if user_id in self.factions[guild_id][faction]['co-owners']:
				co_owners.append([user, income])
			else:
				users.append([user, income])

		e = discord.Embed(color=purple())
		e.set_author(name=f"{faction}'s members", icon_url=owner.avatar_url)
		e.set_thumbnail(url=self.faction_icon(ctx, faction))
		e.description = ''
		for user, income in users:
			if user.id in self.factions[guild_id][faction]['co-owners']:
				e.description += f"Co: "
			e.description += f"{user.mention} - ${income}\n"
		await ctx.send(embed=e)

	@factions.command(name='claims')
	async def claims(self, ctx, *, faction):
		""" Returns a factions sorted claims """
		if faction:
			faction = await self.get_faction_named(ctx, faction)
		else:
			faction = self.get_users_faction(ctx)
		if not faction:
			return await ctx.send('Faction not found')
		guild_id = str(ctx.guild.id)
		e = discord.Embed(color=purple())
		e.set_author(name=f"{faction}'s claims", icon_url=self.faction_icon(ctx, faction))
		claims = self.collect_claims(guild_id, faction)
		claims = {
			self.bot.get_channel(chnl_id): data for chnl_id, data in claims.items()
		}
		for channel, data in sorted(claims.items, reverse=True, key=lambda kv: kv[1]['position']):
			e.description = f"• {channel.mention} {'- guarded' if data['guarded'] else ''}\n"
		await ctx.send(embed=e)

	@factions.command(name='battle', enabled=False)
	async def battle(self, ctx, *args):
		""" Battle other factions in games like scrabble """

	@factions.command(name='raid', enabled=False)
	async def raid(self, ctx, *, faction):
		""" Starts a raid against another faction """

	@factions.command(name='work')
	async def work(self, ctx):
		""" Get money for your faction """
		faction = self.get_users_faction(ctx)
		if not faction:
			return await ctx.send("You need to be in a faction to use this cmd")

		require_game_completion = True if random.choice(1, 4) == 4 else False
		g = MiniGames(ctx.author)
		games = [g.scrabble]
		if require_game_completion:
			is_winner = await random.choice(games)(ctx)
			if not is_winner:
				return await ctx.send("Maybe next time :[")

		e = discord.Embed(color=purple())
		pay = random.randint(15, 25)
		e.description = f"You earned {faction} {pay}"
		if faction in self.boosts['extra-income']:
			e.set_footer(text="With Bonus: $5", icon_url=self.faction_icon(ctx, faction))
			pay += 5
		self.factions[str(ctx.guild.id)][faction]['balance'] += pay
		await ctx.send(embed=e)
		self.save_data()

	@factions.command(name='balance', aliases=['bal'], enabled=False)
	async def balance(self, ctx, *, faction=None):
		""" Sends a factions balance """

	@factions.command(name='pay', enabled=False)
	async def pay(self, ctx, faction, amount):
		""" Pays a faction from the author factions balance """

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
