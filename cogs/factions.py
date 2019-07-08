from os.path import isfile
import json
import random
from datetime import datetime
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
		self.dir = './data/userdata/factions.json'
		self.path = './data/userdata/factions'
		if isfile(self.dir):
			with open(self.dir, 'r') as f:
				dat = json.load(f)
				if 'factions' in dat:
					self.factions = dat['factions']
				if 'land_claims' in dat:
					self.land_claims = dat['land_claims']

	def save_data(self):
		with open(self.dir, 'w') as f:
			json.dump({'factions': self.factions, 'land_claims': self.land_claims}, f, ensure_ascii=False)

	def init(self, guild_id: str, faction=None):
		if guild_id not in self.factions:
			self.factions[guild_id] = {}
		if guild_id not in self.land_claims:
			self.land_claims[guild_id] = {}
		if faction:
			if faction not in self.land_claims[guild_id]:
				self.land_claims[guild_id][faction] = {}
			if 'co-owners' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['co-owners'] = []
			if 'access' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['access'] = 'private'
			if 'limit' not in self.factions[guild_id][faction]:
				self.factions[guild_id][faction]['limit'] = 15

	def get_faction(self, user: discord.Member):
		guild_id = str(user.guild.id)
		self.init(guild_id)
		for faction, dat in self.factions[guild_id].items():
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
			if user.id == dat['owner'] or user.id in dat['co-owners']:
				return faction
		return None

	def get_members(self, ctx, faction):
		guild_id = str(ctx.guild.id); members = []; counter = 0; ids = []
		for member_id in self.factions[guild_id][faction]['members']:
			member = ctx.guild.get_member(member_id)
			if not isinstance(member, discord.Member) or member not in ctx.guild.members or member.id in ids:
				index = self.factions[guild_id][faction]['members'].index(member_id)
				self.factions[guild_id][faction]['members'].pop(index)
				self.save_data(); continue
			members.append([member, member.display_name])
			ids.append(member.id)
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

	@commands.group(name='factions', aliases=['faction', 'f'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def _factions(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.purple())
			e.set_author(name='Usage', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name='◈ Core ◈', value=f'.faction create name\n' \
				'.faction rename {name}\n' \
				'.faction disband\n' \
				'.faction join {faction}\n' \
				'.faction invite {@user}\n'
				'.faction promote {@user}\n'
				'.faction demote {@user}\n' \
				'.faction kick {@user}\n' \
				'.faction leave\n', inline=False)
			e.add_field(name='◈ Utils ◈', value=f'.faction privacy\n' \
				'.faction seticon {url | file}\n' \
				'.faction setbanner {url | file}\n', inline=False)
			e.add_field(name='◈ Economy ◈', value=f'.faction work\n' \
				'.faction pay {faction} {amount}\n'
				'.faction raid {faction}' \
				'.faction annex {faction}\n'
				'.faction claim {#channel}\n' \
				'.faction unclaim {#channel}\n' \
				'.faction claims\n' \
				'.faction top', inline=False)
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
		self.init(guild_id, faction)
		f = self.factions[guild_id][faction]
		owner = self.bot.get_user(f["owner"])
		e = discord.Embed(color=colors.purple())
		e.set_author(name=faction, icon_url=owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		if 'icon' in f:
			if f['icon']:
				e.set_thumbnail(url=f['icon'])
		if len(owner.name) > 10:
			e.description = f'__**Owner:**__ [{owner.name}]\n' \
				f'__**Balance:**__ [`${f["balance"]}`] ' \
				f'__**Access:**__ [`{"Public" if f["access"] == "public" else "Invite-Only"}`]\n' \
				f'__**MemberCount:**__ [`{len(f["members"])}/{f["limit"]}`]'
		else:
			e.description = f'__**Owner:**__ [{owner.name}] ' \
				f'__**Balance:**__ [`${f["balance"]}`]\n' \
				f'__**Access:**__ [`{"Public" if f["access"] == "public" else "Invite-Only"}`] ' \
				f'__**Members:**__ [`{len(f["members"])}/{f["limit"]}`]'
		members = self.get_members(ctx, faction)
		e.add_field(name='◈ Members ◈', value=members if members else 'none')
		claims = self.get_claims(guild_id, faction)
		e.add_field(name='◈ Land Claims ◈', value=claims if claims else 'none')
		e.set_footer(text=f'')
		if 'banner' in f:
			e.set_image(url=f['banner'])
		await ctx.send(embed=e)

	@_factions.command(name='create')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _create(self, ctx, *, name):
		name = name.replace('  ', '')
		if len(name) > 20:
			return await ctx.send('Faction names cannot exceed 20 characters')
		guild_id = str(ctx.guild.id)
		if guild_id not in self.factions:
			self.factions[guild_id] = {}
		for faction, dat in self.factions[guild_id].items():
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
			'limit': 15
		}
		e = discord.Embed(color=colors.purple())
		e.set_author(name='Created Your Faction', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f'__**Name:**__ [`{name}`]\n' \
			f'__**Owner:**__ [`{ctx.author.name}`]'
		await ctx.send(embed=e)
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
		if len(name) > 15:
			return await ctx.send('Faction names cannot exeed 15 characters')
		guild_id = str(ctx.guild.id)
		faction = self.get_owned_faction(ctx.author)
		if not faction or ctx.author.id != self.factions[guild_id][faction]['owner']:
			return await ctx.send('You need to be owner of the faction to do this')
		if name in self.factions[guild_id]:
			return await ctx.send('That names already taken')
		self.init(guild_id, faction)
		self.factions[guild_id][name] = self.factions[guild_id].pop(faction)
		self.land_claims[guild_id][name] = self.land_claims[guild_id].pop(faction)
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
		self.factions[guild_id][faction]['members'].append(ctx.author.id)
		e = discord.Embed(color=colors.purple())
		count = len(self.factions[guild_id][faction]['members'])
		e.description = f'**{ctx.author.name} joined {faction}**\n' \
			f'__**Member Count:**__ [`{count}`]'
		await ctx.send(embed=e)
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
		if len(self.factions[guild_id][faction]['members']) == 15:
			return await ctx.send('You can\'t have more than 15 members')
		for fac, dat in self.factions[guild_id].items():
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
			if ctx.author.id != self.factions[guild_id][faction]['owner']:
				return await ctx.send('You can\'t leave a faction you own')
		index = self.factions[guild_id][faction]['members'].index(ctx.author.id)
		self.factions[guild_id][faction]['members'].pop(index)
		self.init(guild_id, faction)
		if ctx.author.id in self.factions[guild_id][faction]['co-owners']:
			index = self.factions[guild_id][faction]['co-owners'].index(ctx.author.id)
			self.factions[guild_id][faction]['co-owners'].pop(index)
		await ctx.send('✔')
		self.save_data()

	@_factions.command(name='work')
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def _work(self, ctx):
		user_id = str(ctx.author.id)
		if user_id not in self.last:
			self.last[user_id] = {}
			self.last[user_id]['intervals'] = []
		if 'last' not in self.last[user_id]:
			self.last[user_id]['last'] = datetime.now()
		else:
			last = self.last[user_id]['last']
			self.last[user_id]['intervals'].append((datetime.now() - last).seconds)
			intervals = self.last[user_id]['intervals']
			self.last[user_id]['intervals'] = intervals[-3:]
			if len(intervals) > 2:
				if all(interval == intervals[0] or interval - 1 == intervals[0] or interval + 1 == intervals[0] for interval in intervals):
					return await ctx.send('Get off that macro :]')
		faction = self.get_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be in a faction to use this command')
		guild_id = str(ctx.guild.id)
		paycheck = random.randint(10, 25)
		self.factions[guild_id][faction]['balance'] += paycheck
		e = discord.Embed(color=colors.purple())
		e.description = f'You earned {faction} ${paycheck}'
		await ctx.send(embed=e)
		self.save_data()
		await asyncio.sleep(60)
		await ctx.send(f'{ctx.author.mention} your cooldowns up', delete_after=3)

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
		await ctx.send(f'{target_owner.mention}, {ctx.author.name} wants to merge factions with him/her as the owner\n'
		    f'Reply with .confirm to accept the offer')
		msg = await utils.wait_for_msg(self, ctx, target_owner)
		if not msg:
			return
		if '.confirm' not in msg.content.lower():
			return await ctx.send('Maybe next time')
		for member_id in t['members']:
			self.factions[guild_id][faction]['members'].append(member_id)
		if t['owner'] not in self.factions[guild_id][faction]['members']:
			self.factions[guild_id][faction]['members'].append(t['owner'])
		self.factions[guild_id][faction]['balance'] += t['balance']
		owner = self.bot.get_user(f['owner'])
		icon_url = owner.avatar_url
		if f['icon']:
			icon_url = f['icon']
		e = discord.Embed(color=colors.purple())
		e.set_author(name=f'{faction} Annexed {target}', icon_url=icon_url)
		await ctx.send(embed=e)
		self.save_data()

	@_factions.command(name='raid', enabled=False)
	@commands.cooldown(1, 120, commands.BucketType.user)
	async def _raid(self, ctx, *, faction):
		target = self.get_faction_named(ctx, faction)
		if not target:
			return await ctx.send('Faction not found')
		faction = self.get_owned_faction(ctx.author)
		if not faction:
			return await ctx.send('You need to be owner of a faction to use this')
		guild_id = str(ctx.guild.id)
		t = self.factions[guild_id][target]
		f = self.factions[guild_id][faction]
		chance = 60 if t['balance'] > f['balance'] else 40
		lmt = (25 * t['balance'] if t['balance'] < f['balance'] else f['balance']) / 100
		pay = random.randint(0, round(lmt))
		if random.randint(0, 100) < chance:
			self.factions[guild_id][target]['balance'] -= pay
			self.factions[guild_id][faction]['balance'] += pay
			e = discord.Embed(color=colors.green())
			e.description = f'You raided {target} and gained {pay}'
		else:
			self.factions[guild_id][target]['balance'] += pay
			self.factions[guild_id][faction]['balance'] -= pay
			e = discord.Embed(color=colors.red())
			e.description = f'You attempted to raid {target} and lost {pay}'
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
			balance = dat['balance']
			self.init(guild_id, faction)
			for i in range(len(self.land_claims[guild_id][faction].keys())):
				balance += 500
			factions.append([faction, balance])
		for faction, balance in sorted(factions, key=lambda kv: kv[1], reverse=True)[:8]:
			owner = self.bot.get_user(self.factions[guild_id][faction]['owner'])
			if not isinstance(owner, discord.User):
				del self.factions[guild_id][faction]
				continue
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
		upgrades = '》+5 member slots\n• $250'
		e.add_field(name='◈ Upgrades ◈', value=upgrades)
		e.set_footer(text='Usage: .factions buy item_name', icon_url=self.bot.user.avatar_url)
		msg = await ctx.send(embed=e)
		for color in colors.ColorSets().rainbow():
			e.colour = color
			await msg.edit(embed=e)
			await asyncio.sleep(1)
		e.colour = colors.red()
		await msg.edit(embed=e)

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

	@_factions.command(name='d')
	@commands.check(checks.luck)
	async def _addtodict(self, ctx):
		guild_id = str(ctx.guild.id)
		for faction in self.factions[guild_id]:
			del self.factions[guild_id][faction]['banner']
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

	@_factions.command(name='reset')
	@commands.check(checks.luck)
	async def reset(self, ctx):
		guild_id = str(ctx.guild.id)
		f = self.factions[guild_id]['Casa Nostra']
		for member_id in f['members']:
			if member_id != f['owner']:
				index = f['members'].index(member_id)
				self.factions[guild_id]['Casa Nostra'].pop(index)
				self.save_data()

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
							pay = random.randint(1, 5)
							self.factions[guild_id][faction]['balance'] += pay
							self.counter[guild_id][faction] = 0
							self.save_data()

def setup(bot):
	bot.add_cog(Factions(bot))
