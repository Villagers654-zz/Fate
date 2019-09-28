from os.path import isfile
import json
import random
from datetime import datetime, timedelta
import asyncio
from discord.ext import commands
import discord
from utils import utils, colors, checks


class Factions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last = {}
		self.appending = {}
		self.counter = {}
		self.factions = {}
		self.land_claims = {}
		self.notifs = []

		self.dir = './data/userdata/factions.json'
		if isfile(self.dir):
			with open(self.dir, 'r') as f:
				dat = json.load(f)
				if 'factions' in dat:
					self.factions = dat['factions']
				if 'land_claims' in dat:
					self.land_claims = dat['land_claims']
				if 'notifs' in dat:
					self.notifs = dat['notifs']

		self.items = {
			'icon': 250,
			'banner': 500,
			'5 slots': 250,
			'anti-raid': 75,
			'extra-income': 50,
			'land-guard': 100
		}

	def save_data(self):
		with open(self.dir, 'w') as f:
			json.dump({'factions': self.factions, 'land_claims': self.land_claims, 'notifs': self.notifs}, f, ensure_ascii=False)

	def init(self, guild_id: str, faction=None):
		if guild_id not in self.factions:
			self.factions[guild_id] = {}
		if guild_id not in self.land_claims:
			self.land_claims[guild_id] = {}
		if faction:
			f = self.factions[guild_id][faction]
			if faction not in self.land_claims[guild_id]:
				self.land_claims[guild_id][faction] = {}
			if 'co-owners' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['co-owners'] = []
			if 'access' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['access'] = 'private'
			if 'limit' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['limit'] = 15
			if 'items' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['items'] = []
			if 'bio' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['bio'] = ''
			if 'boosts' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['boosts'] = {
					'anti-raid': None,
					'extra-income': None,
					'land-guard': None
				}
			if not isinstance(f['boosts'], dict):
				self.factions[guild_id][faction]['boosts'] = {}
			for x in ['anti-raid', 'extra-income', 'land-guard']:
				if x not in self.factions[guild_id][faction]['boosts']:
					self.factions[guild_id][faction]['boosts'][x] = None

	def get_faction(self, user: discord.Member):
		guild_id = str(user.guild.id)
		self.init(guild_id)
		for faction, dat in self.factions[guild_id].items():
			if faction != 'category':
				if user.id in dat['members']:
					return faction
		return None

	def get_faction_named(self, ctx, name):
		guild_id = str(ctx.guild.id)
		self.init(guild_id)
		for faction in self.factions[guild_id].keys():
			faction_name = faction
			if name.lower() == faction.lower():
				return faction_name
		for faction in self.factions[guild_id].keys():
			faction_name = faction
			if name.lower() in faction.lower():
				return faction_name
		return None

	def get_owned_faction(self, user):
		guild_id = str(user.guild.id)
		self.init(guild_id)
		for faction, dat in self.factions[guild_id].items():
			if faction != 'category':
				if user.id == dat['owner'] or user.id in dat['co-owners']:
					return faction
		return None

	def get_members(self, ctx, faction):
		guild_id = str(ctx.guild.id); members = []; counter = 0; ids = []
		limit = self.factions[guild_id][faction]['limit']; index = 1
		if self.factions[guild_id][faction]['owner'] not in self.factions[guild_id][faction]['members']:
			self.factions[guild_id][faction]['members'].append(self.factions[guild_id][faction]['owner'])
		for member_id in self.factions[guild_id][faction]['members']:
			member = ctx.guild.get_member(member_id)
			if not isinstance(member, discord.Member) or member not in ctx.guild.members or member.id in ids:
				index = self.factions[guild_id][faction]['members'].index(member_id)
				self.factions[guild_id][faction]['members'].pop(index)
				self.save_data(); continue
			members.append([member, member.display_name])
			ids.append(member.id)
			index += 1
		member_list = ''
		for member, name in sorted(members, key=lambda kv: len(kv[1])):
			special_chars = False
			for x in list(name):
				if x.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789':
					member_list += f'{"," if member_list else ""}\n{member.display_name[:10]}'
					special_chars = True; break
			if special_chars:
				continue
			if len(name) < 9:
				counter += 1
				if counter % 2 == 1:
					member_list += f'{"," if member_list else ""}\n{member.display_name[:15]}'
				else:
					member_list += f', {member.display_name[:15]}'
			else:
				member_list += f'{"," if member_list else ""}\n{member.display_name[:15]}'
		return member_list

	def get_claims(self, guild_id, faction):
		claims = ''
		for channel_id in list(self.land_claims[guild_id][faction].keys()):
			channel = self.bot.get_channel(int(channel_id))
			if not isinstance(channel, discord.TextChannel):
				del self.land_claims[guild_id][faction][channel_id]
				self.factions[guild_id][faction]['balance'] += 500
				continue
			claims += f'{channel.mention}\n'
		return claims

	def get_boosts(self, guild_id, faction):
		active_boosts = {}
		boosts = self.factions[guild_id][faction]['boosts']
		for boost, date in boosts.items():
			date_string = self.factions[guild_id][faction]['boosts'][boost]
			if date_string:
				date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
				seconds = (datetime.now() - date).seconds
				time = (datetime.now() - date).days
				if time < 1 and boost == 'anti-raid':
					active_boosts['Anti-Raid'] = utils.get_time(86400 - seconds)
				time = (datetime.now() - date).seconds / 60 / 60
				if time < 2 and boost == 'extra-income':
					active_boosts['Extra-Income'] = utils.get_time(7200 - seconds)
				time = (datetime.now() - date).seconds / 60 / 60
				if time < 8 and boost == 'land-guard':
					active_boosts['Land-Guard'] = utils.get_time(28800 - seconds)
		return active_boosts

	def get_icon(self, user: discord.Member):
		guild_id = str(user.guild.id)
		icon_url = user.avatar_url
		faction = self.get_faction(user)
		if faction:
			faction = self.factions[guild_id][faction]
			owner = self.bot.get_user(faction['owner'])
			icon_url = owner.avatar_url
			if 'icon' in faction:
				if faction['icon']:
					icon_url = faction['icon']
		return icon_url

	def remove_alts(self, ctx, faction):
		guild_id = str(ctx.guild.id); members = []
		def delete(member_id):
			index = self.factions[guild_id][faction]['members'].index(member_id)
			self.factions[guild_id][faction]['members'].pop(index)
			self.save_data()
		for member_id in self.factions[guild_id][faction]['members']:
			member = ctx.guild.get_member(member_id)
			if not member:
				delete(member_id); continue
			name = str(member.name).lower()
			if name in members:
				delete(member_id); continue
			for char in list(name):
				if char not in 'abcdefghijklmnopqrstuvwxyz':
					name = name.replace(str(char), '')
			if len(name) > 0:
				if name in members:
					delete(member_id); continue
				members.append(name)
			else:
				members.append(member.name)

	def remove_member(self, guild_id, faction, member_id):
		index = self.factions[guild_id][faction]['members'].index(member_id)
		self.factions[guild_id][faction]['members'].pop(index)
		self.save_data()

	async def update_category(self, guild_id, user):
		if 'category' in self.factions[guild_id]:
			faction = self.get_faction(user)
			if faction:
				category = self.bot.get_channel(self.factions[guild_id]['category'])
				name = str(faction).lower().replace(' ', '-')
				if name not in [channel.name for channel in category.channels]:
					base = await category.create_text_channel(name=name)
					await base.set_permissions(user.guild.me, read_messages=True)
					await base.set_permissions(user.guild.roles[0], read_messages=False)
					for member_id in self.factions[guild_id][faction]['members']:
						member = user.guild.get_member(member_id)
						if not member:
							self.remove_member(guild_id, faction, member_id)
							continue
						await base.set_permissions(member, read_messages=True)
				base = discord.utils.get(category.channels, name=name)
				if not base:
					if 'channel' in self.factions[guild_id][faction]:
						base = self.bot.get_channel(self.factions[guild_id][faction]['channel'])
				if not base: return
				if 'channel' not in self.factions[guild_id][faction]:
					self.factions[guild_id][faction]['channel'] = base.id
				if base.id != self.factions[guild_id][faction]['channel']:
					self.factions[guild_id][faction]['channel'] = base.id
				if str(base.id) not in self.land_claims[guild_id][faction]:
					self.land_claims[guild_id][faction][str(base.id)] = str(datetime.now())
				for user_id in self.factions[guild_id][faction]['members']:
					user = self.bot.get_user(user_id)
					if user not in base.overwrites:
						await base.set_permissions(user, read_messages=True)
					for overwrite in base.overwrites.keys():
						if isinstance(overwrite, discord.Member):
							if overwrite.id not in self.factions[guild_id][faction]['members']:
								if overwrite.id != self.bot.user.id and overwrite.id != base.guild.roles[0].id:
									await base.set_permissions(overwrite, overwrite=None)
				if base.guild.roles[0] not in base.overwrites:
					await base.set_permissions(base.guild.roles[0], read_messages=False)
				for overwrite, perms in base.overwrites.items():
					if overwrite.id == base.guild.roles[0].id:
						if perms.read_messages is True or perms.read_messages is None:
							await base.set_permissions(overwrite, read_messages=False)
						continue
					if overwrite.id not in self.factions[guild_id][faction]['members']:
						if isinstance(overwrite, discord.Member):
							if overwrite.bot:
								continue
						await base.set_permissions(overwrite, overwrite=None)

	@commands.group(name='factions', aliases=['faction', 'f'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def _factions(self, ctx):
		if not ctx.invoked_subcommand:
			if len(ctx.message.content.split(' ')) > 1:
				if 'help' not in ctx.message.content.lower():
					return await ctx.send('Unknown command')
			e = discord.Embed(color=colors.purple())
			e.set_author(name='Usage', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name='◈ Core ◈', value=f'.factions create name\n' \
				'.factions rename {name}\n' \
				'.factions disband\n' \
				'.factions join {faction}\n' \
				'.factions invite {@user}\n'
				'.factions promote {@user}\n'
				'.factions demote {@user}\n' \
				'.factions kick {@user}\n' \
				'.factions leave\n', inline=False)
			e.add_field(name='◈ Utils ◈', value=f'.faction privacy\n'
			    '.factions setbio {your new bio}\n'
				'.factions seticon {file | url}\n' \
				'.factions setbanner {file | url}\n' \
			    '.factions togglenotifs', inline=False)
			e.add_field(name='◈ Economy ◈', value=f'.faction work\n'
			    f'.factions balance\n' \
				'.factions pay {faction} {amount}\n'
				'.factions raid {faction}\n' \
				'.factions annex {faction}\n'
				'.factions claim {#channel}\n' \
				'.factions unclaim {#channel}\n' \
				'.factions claims\n' \
			    '.factions boosts\n' \
				'.factions top', inline=False)
			await ctx.send(embed=e)

	@_factions.command(name='info')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _info(self, ctx, *, faction=None):
		guild_id = str(ctx.guild.id)
		if faction:
			faction = self.get_faction_named(ctx, faction)
			if not faction:
				return await ctx.send('Faction not found')
		else:
			faction = self.get_faction(ctx.author)
			if not faction:
				return await ctx.send('You\'re not currently in a faction')
		self.remove_alts(ctx, faction)
		self.init(guild_id, faction)
		await self.update_category(guild_id, ctx.author)
		f = self.factions[guild_id][faction]
		owner = self.bot.get_user(f["owner"])
		e = discord.Embed(color=colors.purple())
		e.set_author(name=faction, icon_url=owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		if 'icon' in f:
			if f['icon']:
				e.set_thumbnail(url=f['icon'])
		self.init(guild_id, faction); bio = None; active_boosts = ''
		boosts = self.get_boosts(guild_id, faction)
		if boosts:
			for boost, time in boosts.items():
				active_boosts += f'{boost} '
			active_boosts = f'\n{active_boosts}'
		if self.factions[guild_id][faction]['bio']:
			bio = f'\n__**Bio:**__ [`{self.factions[guild_id][faction]["bio"]}`]'
		if len(owner.name) > 10:
			e.description = f'__**Owner:**__ [{owner.name}]\n' \
				f'__**Balance:**__ [`${f["balance"]}`] ' \
				f'__**Access:**__ [`{"Public" if f["access"] == "public" else "Invite-Only"}`]\n' \
				f'__**MemberCount:**__ [`{len(f["members"])}/{f["limit"]}`]' \
				f'{active_boosts if active_boosts else ""}{bio if bio else ""}'
		else:
			e.description = f'__**Owner:**__ [{owner.name}] ' \
				f'__**Balance:**__ [`${f["balance"]}`]\n' \
				f'__**Access:**__ [`{"Public" if f["access"] == "public" else "Invite-Only"}`] ' \
				f'__**Members:**__ [`{len(f["members"])}/{f["limit"]}`]' \
				f'{active_boosts if active_boosts else ""}{bio if bio else ""}'
		members = self.get_members(ctx, faction)
		e.add_field(name='◈ Members ◈', value=members if members else 'none')
		claims = self.get_claims(guild_id, faction)
		e.add_field(name='◈ Land Claims ◈', value=claims if claims else 'none')
		if 'banner' in f:
			e.set_image(url=f['banner'])
		factions = []
		for fac, dat in self.factions[guild_id].items():
			if fac != 'category':
				balance = dat['balance']
				self.init(guild_id, fac)
				for i in range(len(self.land_claims[guild_id][fac].keys())):
					balance += 500
				factions.append([fac, balance])
		rank = 1
		for fac, balance in sorted(factions, key=lambda kv: kv[1], reverse=True):
			if fac == faction:
				break
			rank += 1
		e.set_footer(text=f'Leaderboard Ranking: #{rank}')
		await ctx.send(embed=e)

	@_factions.command(name='create')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _create(self, ctx, *, name):
		name = name.replace('  ', '')
		if len(name) > 25:
			return await ctx.send('Faction names cannot exceed 25 characters')
		guild_id = str(ctx.guild.id)
		if guild_id not in self.factions:
			self.factions[guild_id] = {}
		for faction, dat in self.factions[guild_id].items():
			if faction != 'category':
				faction_name = name.lower()
				if faction_name == faction.lower():
					return await ctx.send('That names already taken')
				if ctx.author.id in dat['members']:
					return await ctx.send('You\'re already in a faction')
		self.factions[guild_id][name] = {
			'owner': ctx.author.id,
			'co-owners': [],
			'members': [ctx.author.id],
			'balance': 0,
			'access': 'private',
			'limit': 15,
			'items': [],
			'boosts':{},
			'bio': ''
		}
		self.init(guild_id, name)
		await self.update_category(guild_id, ctx.author)
		e = discord.Embed(color=colors.purple())
		e.set_author(name='Created Your Faction', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f'__**Name:**__ [`{name}`]\n' \
			f'__**Owner:**__ [`{ctx.author.name}`]'
		await ctx.send(embed=e)
		self.save_data()

	@_factions.command(name="setbio")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _setbio(self, ctx, *, bio):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		self.factions[guild_id][faction]['bio'] = bio
		await ctx.send(f'Set {faction}\'s bio')
		self.save_data()

	@_factions.command(naem='promote')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def promote(self, ctx, user: discord.Member):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		if 'co-owners' not in self.factions[guild_id][faction]:
			self.factions[guild_id][faction]['co-owners'] = []
		if len(self.factions[guild_id][faction]['co-owners']) == 2:
			return await ctx.send('You can\'t have more than 2 co-owners')
		if user.id in self.factions[guild_id][faction]['co-owners']:
			return await ctx.send('This users already a co-owner')
		self.factions[guild_id][faction]['co-owners'].append(user.id)
		await ctx.send(f'Promoted {user.name} to co-owner')
		self.save_data()

	@_factions.command(naem='demote')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def demote(self, ctx, user: discord.Member):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		if 'co-owners' not in self.factions[guild_id][faction]:
			self.factions[guild_id][faction]['co-owners'] = []
		if user.id not in self.factions[guild_id][faction]['co-owners']:
			return await ctx.send('This users not a co-owner')
		index = self.factions[guild_id][faction]['co-owners'].index(user.id)
		self.factions[guild_id][faction]['co-owners'].pop(index)
		await ctx.send(f'Demoted {user.name} from co-owner')
		self.save_data()

	@_factions.command(name='rename')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _rename(self, ctx, *, name):
		if len(name) > 25:
			return await ctx.send('Faction names cannot exceed 25 characters')
		guild_id = str(ctx.guild.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction or ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send('You need to be owner of the faction to do this')
		if name in self.factions[guild_id]:
			return await ctx.send('That names already taken')
		self.init(guild_id, faction)
		await self.update_category(guild_id, ctx.author)
		self.factions[guild_id][name] = self.factions[guild_id].pop(faction)
		self.land_claims[guild_id][name] = self.land_claims[guild_id].pop(faction)
		if 'category' in self.factions[guild_id]:
			channel = self.bot.get_channel(self.factions[guild_id][name]['channel'])
			channel_name = str(name).lower().replace(' ', '-')
			await channel.edit(name=channel_name)
		await ctx.send(f'Renamed {faction} to {name}')
		self.save_data()

	@_factions.command(name='privacy')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _privacy(self, ctx):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to do this')
		guild_id = str(ctx.guild.id)
		if 'access' not in self.factions[guild_id][faction]:
			self.factions[guild_id][faction]['access'] = 'private'
		if self.factions[guild_id][faction]['access'] == 'public':
			self.factions[guild_id][faction]['access'] = 'private'
			await ctx.send(f'Made {faction} private')
			return self.save_data()
		self.factions[guild_id][faction]['access'] = 'public'
		await ctx.send(f'Made {faction} public')
		self.save_data()

	@_factions.command(name='seticon')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _set_icon(self, ctx, url=None):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		if 'icon' not in self.factions[guild_id][faction]:
			await ctx.send(f'Buying access to icons will cost you $250\n'
			    'Reply with .confirm to purchase')
			msg = await utils.wait_for_msg(self, ctx)
			if not msg: return
			if '.confirm' not in msg.content.lower():
				return await ctx.send('Maybe next time ;-;')
			if self.factions[guild_id][faction]['balance'] < 250:
				return await ctx.send('You don\'t have enough money to purchase this')
			self.factions[guild_id][faction]['balance'] -= 250
			self.factions[guild_id][faction]['icon'] = ''
			await ctx.send('👍'); self.save_data()
		if not ctx.message.attachments and not url:
			return await ctx.send('You need to attach a file or provide a url')
		if not url:
			url = ctx.message.attachments[0].url
		self.factions[guild_id][faction]['icon'] = url
		await ctx.send('Set your factions icon')
		self.save_data()

	@_factions.command(name='setbanner')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _set_banner(self, ctx, url=None):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		if 'banner' not in self.factions[guild_id][faction]:
			await ctx.send(f'Buying access to banners will cost you $500\n'
			    'Reply with .confirm to purchase')
			msg = await utils.wait_for_msg(self, ctx)
			if not msg: return
			if '.confirm' not in msg.content.lower():
				return await ctx.send('Maybe next time ;-;')
			if self.factions[guild_id][faction]['balance'] < 500:
				return await ctx.send('You don\'t have enough money to purchase this')
			self.factions[guild_id][faction]['balance'] -= 500
			self.factions[guild_id][faction]['banner'] = ''
			await ctx.send('👍'); self.save_data()
		if not ctx.message.attachments and not url:
			return await ctx.send('You need to attach a file or provide a url')
		if not url:
			url = ctx.message.attachments[0].url
		self.factions[guild_id][faction]['banner'] = url
		await ctx.send('Set your factions banner')
		self.save_data()

	@_factions.command(name='disband')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _disband(self, ctx):
		guild_id = str(ctx.guild.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction or ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send('You need to be owner of the faction to do this')
		guild_id = str(ctx.guild.id)
		del self.factions[guild_id][faction]
		if 'category' in self.factions[guild_id]:
			category = self.bot.get_channel(self.factions[guild_id]['category'])
			name = str(faction).lower().replace(' ', '-')
			channel = discord.utils.get(category.channels, name=name)
			await channel.delete()
		await ctx.send(f'Disbanded {faction}')
		self.save_data()

	@_factions.command(name='join')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _join(self, ctx, *, faction):
		faction = self.get_faction_named(ctx, faction)
		if not faction:
			return await ctx.send('Faction not found')
		guild_id = str(ctx.guild.id)
		if not self.factions[guild_id][faction]['access'] == 'public':
			return await ctx.send('This factions invite only')
		if self.get_faction(ctx.author):
			return await ctx.send('You need to leave your current faction first')
		f = self.factions[guild_id][faction]
		if len(f['members']) == f['limit']:
			return await ctx.send(f'This faction is full')
		self.factions[guild_id][faction]['members'].append(ctx.author.id)
		e = discord.Embed(color=colors.purple())
		count = len(self.factions[guild_id][faction]['members'])
		e.description = f'**{ctx.author.name} joined {faction}**\n' \
			f'__**Member Count:**__ [`{count}`]'
		await ctx.send(embed=e)
		self.remove_alts(ctx, faction)
		await self.update_category(guild_id, ctx.author)
		self.save_data()

	@_factions.command(name='invite')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _invite(self, ctx, *, user):
		user = utils.get_user(ctx, user)
		if not user:
			return await ctx.send('User not found')
		if user.bot:
			return await ctx.send('You can\'t invite bots')
		if user.id in self.appending:
			return await ctx.send('Wait until the previous invite is complete')
		guild_id = str(ctx.guild.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to invite')
		f = self.factions[guild_id][faction]
		if len(f['members']) == f['limit']:
			return await ctx.send(f'This faction is full')
		for fac, dat in self.factions[guild_id].items():
			if fac != 'category':
				if user.id in dat['members']:
					return await ctx.send('This users already in a faction')
		self.factions[guild_id][faction]['members'].append(ctx.author.id)
		await ctx.send(f'{user.mention}, {ctx.author.name} wants to invite you to {faction}. Reply with `.accept` to join')
		self.appending[user.id] = 'yeet'
		msg = await utils.wait_for_msg(self, ctx, user)
		if not msg:
			del self.appending[user.id]
			return
		if '.accept' not in msg.content.lower():
			del self.appending[user.id]
			return await ctx.send('Oop, maybe next time')
		self.factions[guild_id][faction]['members'].append(user.id)
		e = discord.Embed(color=colors.purple())
		count = len(self.factions[guild_id][faction]['members'])
		e.description = f'**{user.name} joined {faction}**\n' \
			f'__**Member Count:**__ [`{count}`]'
		await ctx.send(embed=e)
		self.remove_alts(ctx, faction)
		await self.update_category(guild_id, ctx.author)
		self.save_data()
		del self.appending[user.id]

	@_factions.command(name='kick')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _kick(self, ctx, *, user):
		user = utils.get_user(ctx, user)
		if not user:
			return await ctx.send('User not found')
		guild_id = str(ctx.guild.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of the faction for you to kick')
		dat = self.factions[guild_id][faction]
		if user.id not in dat['members']:
			return await ctx.send('This user isn\'t apart of your faction')
		index = dat['members'].index(user.id)
		self.factions[guild_id][faction]['members'].pop(index)
		await ctx.send(f'Kicked {user.name} from {faction}')
		return self.save_data()

	@_factions.command(name='leave')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _leave(self, ctx):
		faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('You\'re not currently in a faction')
		guild_id = str(ctx.guild.id)
		if self.get_owned_faction(ctx.author):
			if ctx.author.id == self.factions[guild_id][faction]['owner']:
				return await ctx.send('You can\'t leave a faction you own')
			index = self.factions[guild_id][faction]['co-owners'].index(ctx.author.id)
			self.factions[guild_id][faction]['co-owners'].pop(index)
		index = self.factions[guild_id][faction]['members'].index(ctx.author.id)
		self.factions[guild_id][faction]['members'].pop(index)
		self.init(guild_id, faction)
		await self.update_category(guild_id, ctx.author)
		await ctx.send('✔')
		self.save_data()

	@_factions.command(name='togglenotifs')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _toggle_notifs(self, ctx):
		user_id = ctx.author.id
		if user_id not in self.notifs:
			self.notifs.append(user_id)
		else:
			self.notifs.pop(self.notifs.index(user_id))
		await ctx.message.add_reaction('👍')

	@_factions.command(name='balance', aliases=['bal'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _bal(self, ctx):
		faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be in a faction to use this command')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		e = discord.Embed(color=colors.purple())
		e.description = f'${self.factions[guild_id][faction]["balance"]}'
		await ctx.send(embed=e)

	@_factions.command(name='work')
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def _work(self, ctx):
		faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be in a faction to use this command')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		paycheck = random.randint(15, 25)
		e = discord.Embed(color=colors.purple())
		e.description = f'You earned {faction} ${paycheck}'
		if 'Extra-Income' in self.get_boosts(guild_id, faction):
			paycheck += 5
			e.set_footer(text='With Bonus: $5', icon_url=self.get_icon(ctx.author))
		self.factions[guild_id][faction]['balance'] += paycheck
		await ctx.send(embed=e)
		self.save_data()
		if ctx.author.id in self.notifs:
			await asyncio.sleep(60)
			await ctx.send(f'{ctx.author.mention} your cooldowns up', delete_after=10)

	@_factions.command(name='suicide', aliases=['kms'], category='economy')
	@commands.cooldown(1, 120, commands.BucketType.user)
	async def _suicide(self, ctx):
		faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be in a faction to use this command')
		guild_id = str(ctx.guild.id)
		stories = random.randint(1, 8)
		building = '━━━━━┒\n┓┏┓┏┓┃Oof\n┛┗┛┗┛┃＼O／\n┓┏┓┏┓┃ /\n┛┗┛┗┛┃ノ)'
		for i in range(stories):
			building += '\n┓┏┓┏┓┃ \n┛┗┛┗┛┃ '
		building += '\n┓┏┓┏┓┃\n┃┃┃┃┃┃\n┻┻┻┻┻┻'
		e = discord.Embed(color=colors.purple())
		e.set_author(name='You Attempted to Commit Suicide', icon_url=self.get_icon(ctx.author))
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = F'{building}\n\n'
		money = random.randint(2, 10)
		if stories >= 4:
			e.colour = colors.green()
			e.description += f'You died and earned your faction ${money}\n' \
				f'seems that\'s all you\'re worth :c'
			self.factions[guild_id][faction]['balance'] += money
		else:
			e.colour = colors.red()
			e.description += f'You lived and were sent to \n' \
				f'get help costing your faction ${money}'
			self.factions[guild_id][faction]['balance'] -= money
		await ctx.send(embed=e)
		self.save_data()

	@_factions.command(name='pay', aliases=['give'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _pay(self, ctx, *, args):
		amount = [arg for arg in args.split(' ') if arg.isdigit()]
		if not amount or len(amount) > 1:
			return await ctx.send('Amount is either missing or I cant find it in your msg')
		faction = ' '.join([arg for arg in args.split(' ') if not arg.isdigit()])
		if not faction:
			return await ctx.send('Faction is a required argument that is missing')
		target_faction = self.get_faction_named(ctx, faction)
		if not target_faction:
			return await ctx.send('Faction not found')
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id); amount = int(amount[0])
		f = self.factions[guild_id][faction]
		if amount > f['balance']:
			return await ctx.send('You don\'t have that much money')
		self.factions[guild_id][faction]['balance'] -= amount
		self.factions[guild_id][target_faction]['balance'] += amount
		await ctx.send(f'Gave ${amount} to {target_faction}')
		self.save_data()

	@_factions.command(name='annex', aliases=['merge'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _annex(self, ctx, *, faction):
		target = self.get_faction_named(ctx, faction)
		if not target:
			return await ctx.send('Faction not found')
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		if target == faction:
			return await ctx.send('You can\'t annex yourself')
		guild_id = str(ctx.guild.id)
		f = self.factions[guild_id][faction]
		t = self.factions[guild_id][target]
		target_owner = self.bot.get_user(t['owner'])
		if target_owner.id in self.appending:
			return await ctx.send('This user already has a pending request')
		await ctx.send(f'{target_owner.mention}, {ctx.author.name} wants to merge factions with him/her as the owner\n'
		    f'Reply with .confirm to accept the offer')
		self.appending[target_owner.id] = 'yeet'
		msg = await utils.wait_for_msg(self, ctx, target_owner)
		if not msg:
			del self.appending[target_owner.id]
			return
		if '.confirm' not in msg.content.lower():
			del self.appending[target_owner.id]
			return await ctx.send('Maybe next time')
		for member_id in t['members']:
			self.factions[guild_id][faction]['members'].append(member_id)
		if t['owner'] not in self.factions[guild_id][faction]['members']:
			self.factions[guild_id][faction]['members'].append(t['owner'])
		self.factions[guild_id][faction]['balance'] += t['balance']
		owner = self.bot.get_user(f['owner'])
		icon_url = owner.avatar_url
		if 'icon' in f:
			if f['icon']:
				icon_url = f['icon']
		try: del self.factions[guild_id][target]
		except: pass
		e = discord.Embed(color=colors.purple())
		e.set_author(name=f'{faction} Annexed {target}', icon_url=icon_url)
		await ctx.send(embed=e)
		del self.appending[target_owner.id]
		self.save_data()

	@_factions.command(name='raid')
	@commands.cooldown(1, 120, commands.BucketType.user)
	async def _raid(self, ctx, *, faction):
		target = self.get_faction_named(ctx, faction)
		if not target:
			return await ctx.send('Faction not found')
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		t = self.factions[guild_id][target]
		f = self.factions[guild_id][faction]
		if t['boosts']['anti-raid'] is not None:
			date_string = self.factions[guild_id][target]['boosts']['anti-raid']
			date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
			if (datetime.now() - date).days < 1:
				pay = random.randint(10, 25)
				self.factions[guild_id][faction]['balance'] -= pay
				self.factions[guild_id][target]['balance'] += pay
				e = discord.Embed(color=colors.red())
				e.description = f'{target} is currently reinforced\n' \
				    f'your attack failed and you lost ${pay}'
				await ctx.send(embed=e)
				return self.save_data()
		chance = 60 if f['balance'] > t['balance'] else 40
		lmt = (5 * t['balance'] if t['balance'] < f['balance'] else f['balance']) / 100
		pay = random.randint(0, round(lmt))
		if random.randint(0, 100) < chance:
			self.factions[guild_id][target]['balance'] -= pay
			self.factions[guild_id][faction]['balance'] += pay
			e = discord.Embed(color=colors.green())
			e.description = f'{faction} raided {target} and gained ${pay}'
		else:
			self.factions[guild_id][target]['balance'] += pay
			self.factions[guild_id][faction]['balance'] -= pay
			e = discord.Embed(color=colors.red())
			e.description = f'{faction} attempted to raid {target} and lost ${pay}'
		await ctx.send(embed=e)
		self.save_data()

	@_factions.command(name='claim')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _claim(self, ctx, channel: discord.TextChannel=None):
		if not channel:
			channel = ctx.channel
		guild_id = str(ctx.guild.id)
		channel_id = str(channel.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to own the faction to use this')
		self.init(guild_id, faction)
		if channel_id in self.land_claims[guild_id][faction]:
			return await ctx.send('You already claimed this channel')
		cost = 500; old_claim = None
		for fac, land_claims in self.land_claims[guild_id].items():
			if channel_id in land_claims:
				boosts = self.get_boosts(guild_id, fac)
				for boost, time in boosts.items():
					if boost == 'Land-Guard':
						return await ctx.send(f'This claim is currently guarded, try again in {time} hours')
				cost += 250; old_claim = fac; break
		await ctx.send(f'Claiming this channel will cost you ${cost}\n'
			'Reply with .confirm to purchase')
		msg = await utils.wait_for_msg(self, ctx)
		if not msg: return
		if '.confirm' not in msg.content.lower():
			return await ctx.send('Maybe next time ;-;')
		if self.factions[guild_id][faction]['balance'] < cost:
			return await ctx.send('You don\'t have enough money to purchase this channel')
		if old_claim:
			del self.land_claims[guild_id][old_claim][channel_id]
		self.factions[guild_id][faction]['balance'] -= cost
		if faction not in self.land_claims[guild_id]:
			self.land_claims[guild_id][faction] = {}
		self.land_claims[guild_id][faction][channel_id] = str(datetime.now())
		e = discord.Embed(color=colors.purple())
		owner = self.bot.get_user(self.factions[guild_id][faction]['owner'])
		e.set_author(name=faction, icon_url=owner.avatar_url)
		e.description = f'Claimed {channel.mention}'
		await ctx.send(embed=e)
		self.save_data()

	@_factions.command(name='unclaim')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _unclaim(self, ctx, channel: discord.TextChannel=None):
		if not channel:
			channel = ctx.channel
		guild_id = str(ctx.guild.id)
		channel_id = str(channel.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to own the faction to use this')
		self.init(guild_id, faction)
		await self.update_category(guild_id, ctx.author)
		if 'category' in self.factions[guild_id]:
			if 'channel' in self.factions[guild_id][faction]:
				if channel.id == self.factions[guild_id][faction]['channel']:
					return await ctx.send('You cant unclaim this channel')
		if channel_id not in self.land_claims[guild_id][faction]:
			return await ctx.send('You need to claim this channel in order to unclaim it')
		await ctx.send(f'Unclaiming this channel will give you $250\n'
			'Reply with .confirm to unclaim')
		msg = await utils.wait_for_msg(self, ctx)
		if not msg: return
		if '.confirm' not in msg.content.lower():
			return await ctx.send('Maybe next time ;-;')
		self.factions[guild_id][faction]['balance'] += 250
		del self.land_claims[guild_id][faction][channel_id]
		self.save_data()

	@_factions.command(name='claims')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _claims(self, ctx, *, faction=None):
		guild_id = str(ctx.guild.id)
		if faction:
			faction = self.get_faction_named(ctx, faction)
			if not faction:
				return await ctx.send('Faction not found')
		else:
			faction = self.get_faction(ctx.author)
			if not faction:
				return await ctx.send('You\'re not apart of a faction')
		self.init(guild_id, faction)
		if not self.land_claims[guild_id][faction]:
			return await ctx.send('This faction has no land claims')
		owner = self.bot.get_user(self.factions[guild_id][faction]['owner'])
		e = discord.Embed(color=colors.purple())
		e.set_author(name=f'{faction} Claims', icon_url=owner.avatar_url)
		e.description = self.get_claims(guild_id, faction)
		await ctx.send(embed=e)

	@_factions.command(name='boosts')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _boosts(self, ctx, *, faction=None):
		if faction:
			faction = self.get_faction_named(ctx, faction)
			if not faction:
				return await ctx.send('Faction not found')
		else:
			faction = self.get_faction(ctx.author)
			if not faction:
				return await ctx.send('You\'re not apart of a faction')
		guild_id = str(ctx.guild.id)
		self.init(guild_id, faction)
		e = discord.Embed(color=colors.purple())
		e.set_author(name=f'{faction}\'s boosts', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=self.get_icon(ctx.author))
		e.description = ''
		for boost, time in self.get_boosts(guild_id, faction).items():
			e.description += f'• {boost} - {time}\n'
		await ctx.send(embed=e)

	@_factions.command(name='top', aliases=['lb'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _top(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.factions:
			return await ctx.send('This server has no factions')
		e = discord.Embed(color=colors.purple())
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = ''
		rank = 1
		factions = []
		for faction, dat in self.factions[guild_id].items():
			if faction != 'category':
				owner = self.bot.get_user(self.factions[guild_id][faction]['owner'])
				if not isinstance(owner, discord.User):
					continue
				balance = dat['balance']
				self.init(guild_id, faction)
				for i in range(len(self.land_claims[guild_id][faction].keys())):
					balance += 500
				factions.append([faction, balance])
		for faction, balance in sorted(factions, key=lambda kv: kv[1], reverse=True)[:8]:
			owner = self.bot.get_user(self.factions[guild_id][faction]['owner'])
			if rank == 1:
				e.set_author(name='Faction Leaderboard', icon_url=owner.avatar_url)
			e.description += f'#{rank}. {faction} - ${balance}\n'
			rank += 1
		await ctx.send(embed=e)

	@_factions.command(name='shop')
	@commands.cooldown(1, 16, commands.BucketType.channel)
	async def _shop(self, ctx):
		e = discord.Embed(color=colors.red())
		e.set_author(name='Faction Shop', icon_url=self.get_icon(ctx.author))
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = 'Buy upgrades for your faction'
		vanity = '》Info Icon\n• $250\n》Info Banner\n• $500'
		e.add_field(name='◈ Vanity ◈', value=vanity)
		upgrades = '》+5 member slots\n• $250\n'
		e.add_field(name='◈ Upgrades ◈', value=upgrades)
		boosts = '》2h extra-income\n• $50\n' \
			'》24h anti-raid\n• $75\n' \
		    '》8h land-guard\n• $100'
		e.add_field(name='◈ Boosts ◈', value=boosts)
		e.set_footer(text='Usage: .factions buy item_name', icon_url=self.bot.user.avatar_url)
		msg = await ctx.send(embed=e)
		for color in colors.ColorSets().rainbow():
			e.colour = color
			await msg.edit(embed=e)
			await asyncio.sleep(1.5)
		e.colour = colors.red()
		await msg.edit(embed=e)

	@_factions.command(name='buy', aliases=['buyitem', 'buy-item'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _buy(self, ctx, *, item_name):
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		item = item_name.lower().replace('+', '').replace('_', ' ')
		if item not in self.items.keys() and 'slots' not in item:
			return await ctx.send('Unknown Item')
		if 'slots' in item:
			item = '5 slots'
		cost = self.items[item]
		guild_id = str(ctx.guild.id)
		if self.factions[guild_id][faction]['balance'] < cost:
			return await ctx.send('You don\'t have enough money to purchase this')
		if item == 'icon':
			self.factions[guild_id][faction]['icon'] = ''
		if item == 'banner':
			self.factions[guild_id][faction]['banner'] = ''
		if 'slots' in item:
			self.factions[guild_id][faction]['limit'] += 5
		if 'anti-raid' in item:
			self.factions[guild_id][faction]['boosts']['anti-raid'] = str(datetime.now())
		if 'extra-income' in item:
			self.factions[guild_id][faction]['boosts']['extra-income'] = str(datetime.now())
		if 'land-guard' in item:
			self.factions[guild_id][faction]['boosts']['land-guard'] = str(datetime.now())
		self.factions[guild_id][faction]['balance'] -= cost
		await ctx.send(f'Purchased {item}')
		self.save_data()

	@_factions.command(name='setcategory')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_roles=True, manage_channels=True)
	async def _set_category(self, ctx, *, category_name=None):
		if not category_name:
			await ctx.send('This enables faction bases\n'
				'use `.f setcategory none` to disable')
		guild_id = str(ctx.guild.id)
		if category_name.lower() == 'none':
			if 'category' in self.factions[guild_id]:
				del self.factions[guild_id]['category']
				await ctx.send('Disabled faction bases')
				return self.save_data()
		category = None  # type: discord.CategoryChannel
		for channel in ctx.guild.categories:
			if category_name.lower() in channel.name.lower():
				category = channel; break
		if not category:
			return await ctx.send('Couldn\'t find that category')
		self.factions[guild_id]['category'] = category.id
		await ctx.send('Set the category')
		self.save_data()

	@_factions.command(name='debug')
	@commands.check(checks.luck)
	async def _debug(self, ctx, *, faction=None):
		if faction:
			faction = self.get_faction_named(ctx, faction)
		else:
			faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('Faction not found')
		info = self.factions[str(ctx.guild.id)][faction]
		sorted = json.dumps(info, sort_keys=True, indent=4, separators=(',', ': '))
		await ctx.send(f'```{sorted}```')

	@_factions.command(name='lclaim')
	@commands.check(checks.luck)
	async def luckyclaim(self, ctx):
		guild_id = str(ctx.guild.id)
		channel_id = str(ctx.channel.id)
		faction = self.get_owned_faction(ctx.author)
		await ctx.send(faction)
		self.init(guild_id, faction)
		self.land_claims[guild_id][faction][channel_id] = str(datetime.now())
		self.save_data()
		await ctx.send('✔')
		await ctx.send(self.land_claims[guild_id][faction])
		await ctx.send(f'```{self.land_claims[guild_id]}```')

	@_factions.command(name='lgive')
	@commands.check(checks.luck)
	async def _give(self, ctx, faction, amount: int):
		guild_id = str(ctx.guild.id)
		faction = self.get_faction_named(ctx, faction)
		self.factions[guild_id][faction]['balance'] += amount
		await ctx.send('👍')
		self.save_data()

	@_factions.command(name='ltake')
	@commands.check(checks.luck)
	async def _take(self, ctx, faction, amount: int):
		guild_id = str(ctx.guild.id)
		faction = self.get_faction_named(ctx, faction)
		self.factions[guild_id][faction]['balance'] -= amount
		await ctx.send('👍')
		self.save_data()

	@_factions.command(name='forcerename')
	@commands.check(checks.luck)
	async def _forcerename(self, ctx, faction, name):
		faction = self.get_faction_named(ctx, faction)
		if not faction:
			return await ctx.send('Faction not found')
		guild_id = str(ctx.guild.id)
		self.factions[guild_id][name] = self.factions[guild_id].pop(faction)
		await ctx.send('👍')

	@_factions.command(name='forcemove')
	@commands.check(checks.luck)
	async def _addtodict(self, ctx, faction):
		target = self.get_faction_named(ctx, faction)
		faction = self.get_owned_faction(ctx.author)
		guild_id = str(ctx.guild.id)
		for claim, date in self.land_claims[guild_id][target].items():
			self.land_claims[guild_id][faction][claim] = date
		del self.factions[guild_id][target]
		self.save_data()
		await ctx.send('👍')

	@_factions.command(name='forceleave')
	@commands.check(checks.luck)
	async def _force_leave(self, ctx, user: discord.User, *, faction):
		faction = self.get_faction_named(ctx, faction)
		if not faction:
			return await ctx.send('Faction not found')
		index = self.factions[str(ctx.guild.id)][faction]['members'].index(user.id)
		self.factions[str(ctx.guild.id)][faction]['members'].pop(index)
		await ctx.send('Done')
		self.save_data()

	@_factions.command(name='forceunclaim')
	@commands.check(checks.luck)
	async def _force_leave(self, ctx, faction, channel: discord.TextChannel):
		faction = self.get_faction_named(ctx, faction)
		if not faction:
			return await ctx.send('Faction not found')
		del self.land_claims[str(ctx.guild.id)][faction][str(channel.id)]

	@commands.Cog.listener()
	async def on_message(self, msg: discord.Message):
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			channel_id = str(msg.channel.id)
			if guild_id in self.land_claims:
				for faction, land_claims in self.land_claims[guild_id].items():
					if channel_id in land_claims:
						if guild_id not in self.counter:
							self.counter[guild_id] = {}
						if faction not in self.counter[guild_id]:
							self.counter[guild_id][faction] = 0
						self.counter[guild_id][faction] += 1
						if self.counter[guild_id][faction] == 5:
							self.init(guild_id, faction)
							pay = random.randint(1, 5)
							if self.factions[guild_id][faction]['boosts']['extra-income']:
								date_string = self.factions[guild_id][faction]['boosts']['extra-income']
								date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
								if (datetime.now() - date).seconds / 60 / 60 < 2:
									pay = random.randint(3, 7)
							self.factions[guild_id][faction]['balance'] += pay
							self.counter[guild_id][faction] = 0
							self.save_data()
			if guild_id in self.factions:
				if 'category' in self.factions[guild_id]:
					category = self.bot.get_channel(self.factions[guild_id]['category'])
					if msg.channel.category.id == category.id and not msg.author.bot:
						faction = self.get_faction(msg.author)
						async def wait_for_bot():
							def pred(m):
								return m.channel.id == msg.channel.id and m.author.bot
							try:
								m = await self.bot.wait_for('message', check=pred, timeout=1)
							except asyncio.TimeoutError:
								pass
							else:
								return await m.delete()
						if not faction:
							await wait_for_bot()
							return await msg.delete()
						if msg.channel.id != self.factions[guild_id][faction]['channel']:
							await wait_for_bot()
							await msg.delete()

def setup(bot):
	bot.add_cog(Factions(bot))
