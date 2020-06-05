"""
no snooping or get raped like the orphan you are uwu
"""

from os.path import isfile
import json
from datetime import datetime, timedelta
from time import monotonic
import asyncio
import random
import os
from time import time
import re

from discord.ext import commands
import discord
from discord.ext.commands import Greedy
from discord import *

from utils import colors, config, checks, utils

class Mod(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.purge = {}
		self.massnick = {}
		self.warns = {}
		self.roles = {}
		self.timers = {}
		self.mods = {}
		self.wipe = []
		if isfile("./data/userdata/mod.json"):
			with open("./data/userdata/mod.json", "r") as infile:
				dat = json.load(infile)
				if "warns" in dat:
					self.warns = dat["warns"]
				if "roles" in dat:
					self.roles = dat["roles"]
				if 'timers' in dat:
					self.timers = dat['timers']
				if 'mods' in dat:
					self.mods = dat['mods']
				if 'clearwarns' in dat:
					self.wipe = dat['clearwarns']
		self.path = './data/userdata/rolepersist.json'
		self.rp = {}
		if isfile(self.path):
			with open(self.path, 'r') as f:
				self.rp = json.load(f)  # type: dict

	def save_json(self):
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({'mods': self.mods, "warns": self.warns, "roles": self.roles, "timers": self.timers, 'clearwarns': self.wipe}, outfile, ensure_ascii=False)

	def save_config(self, config):
		with open('./data/userdata/config.json', 'w') as f:
			json.dump(config, f, ensure_ascii=False)

	async def start_mute_timer(self, guild_id, user_id):
		dat = self.timers['mute'][guild_id][user_id]
		channel = self.bot.get_channel(dat['channel'])
		if not channel:
			del self.timers['mute'][guild_id][user_id]
			return
		user = channel.guild.get_member(dat['user'])
		if not user:
			del self.timers['mute'][guild_id][user_id]
			return
		format = '%Y-%m-%d %H:%M:%S.%f'
		end_time = datetime.strptime(dat['end_time'], format)
		mute_role = channel.guild.get_role(dat['mute_role'])
		removed_roles = dat['roles']  # type: list
		sleep_time = (end_time - datetime.now()).seconds
		async def unmute():
			if mute_role:
				if mute_role in user.roles:
					try:
						await user.remove_roles(mute_role)
					except discord.errors.Forbidden:
						pass
			for role_id in removed_roles:
				role = channel.guild.get_role(role_id)
				if role:
					if role not in user.roles:
						try:
							await user.add_roles(role)
						except discord.errors.Forbidden:
							pass
						await asyncio.sleep(0.5)
		if datetime.now() < end_time:
			await asyncio.sleep(sleep_time)
			await unmute()
		else:
			await unmute()
		try:
			del self.timers['mute'][guild_id][user_id]
		except KeyError:
			pass
		self.save_json()

	async def start_ban_timer(self, guild_id, user_id):
		dat = self.timers['ban'][guild_id][user_id]
		guild = self.bot.get_guild(int(guild_id))
		user = await self.bot.fetch_user(dat['user'])
		format = '%Y-%m-%d %H:%M:%S.%f'
		end_time = datetime.strptime(dat['end_time'], format)
		if datetime.now() < end_time:
			sleep_time = (end_time - datetime.now()).seconds
			await asyncio.sleep(sleep_time)
			try: await guild.unban(user)
			except discord.errors.NotFound: pass
		else:
			try: await guild.unban(user)
			except discord.errors.NotFound: pass
		del self.timers['ban'][guild_id][user_id]

	def convert_timer(self, timer):
		if 'd' in timer:
			time = timer.replace("d", " days").replace("1 days", "1 day")
		else:
			if 'h' in timer:
				time = timer.replace("h", " hours").replace("1 hours", "1 hour")
			else:
				if 'm' in timer:
					time = timer.replace("m", " minutes").replace("1 minutes", "1 minute")
				else:
					time = timer.replace('s', 'seconds').replace('1 seconds', '1 second')
		if "d" in str(timer):
			try: timer = float(timer.replace("d", "")) * 60 * 60 * 24
			except Exception as e: return (time, e)
		if "h" in str(timer):
			try: timer = float(timer.replace("h", "")) * 60 * 60
			except Exception as e: return (time, e)
		if "m" in str(timer):
			try: timer = float(timer.replace("m", "")) * 60
			except Exception as e: return (time, e)
		if "s" in str(timer):
			try: timer = float(timer.replace("s", ""))
			except Exception as e: return (time, e)
		return (timer, time)

	# @commands.command(name='getuser')
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# async def getuser(self, ctx, user):
	# 	before = monotonic()
	# 	user = utils.get_user(ctx, user)
	# 	ping = str((monotonic() - before) * 1000)
	# 	ping = ping[:ping.find('.')]
	# 	await ctx.send(f'**{user}:** `{ping}ms`')
#
	# @commands.Cog.listener()
	# async def on_ready(self):
	# 	channel = self.bot.get_channel(config.server('log'))
	# 	for guild_id in list(self.timers['mute'].keys()):
	# 		for user_id in list(self.timers['mute'][guild_id].keys()):
	# 			await channel.send(f"Mute Timer:{guild_id}|{user_id}", delete_after=3)
	# 	for guild_id in list(self.timers['ban'].keys()):
	# 		for user_id in list(self.timers['ban'][guild_id].keys()):
	# 			await channel.send(f'Ban Timer:{guild_id}|{user_id}')
#
	# @commands.Cog.listener()
	# async def on_message(self, m: discord.Message):
	# 	if isinstance(m.guild, discord.Guild):
	# 		if m.channel.id == self.bot.config['log_channel']:
	# 			if m.content.startswith('Mute Timer:'):
	# 				guild_id, user_id = m.content.replace('Mute Timer:', '').split('|')
	# 				await self.start_mute_timer(guild_id, user_id)
	# 			if m.content.startswith('Ban Timer:'):
	# 				guild_id, user_id = m.content.replace('Ban Timer:', '').split('|')
	# 				await self.start_ban_timer(guild_id, user_id)
#
	# @commands.Cog.listener()
	# async def on_member_ban(self, guild, member):
	# 	guild_id = str(guild.id)
	# 	user_id = str(member.id)
	# 	if guild_id in self.wipe:
	# 		if guild_id in self.warns:
	# 			if user_id in self.warns[guild_id]:
	# 				del self.warns[guild_id][user_id]
	# 				self.save_json()
#
	# @commands.command(name="cleartimers")
	# @commands.check(checks.luck)
	# async def cleartimers(self, ctx):
	# 	self.timers = {}
	# 	await ctx.message.add_reaction("👍")
	# 	self.save_json()
#
	# @commands.command(name='clearwarnsonban')
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.has_permissions(administrator=True)
	# async def clear_warns_on_ban(self, ctx):
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id not in self.wipe:
	# 		self.wipe.append(guild_id)
	# 		await ctx.send('I\'ll now wipe warns on ban')
	# 		return self.save_json()
	# 	index = self.wipe.index(guild_id)
	# 	self.wipe.pop(index)
	# 	self.save_json()
#
	# @commands.command(name='modlogs', aliases=['actions'])
	# @commands.guild_only()
	# @commands.bot_has_permissions(embed_links=True)
	# async def mod_logs(self, ctx):
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id not in self.timers['mute'] and guild_id not in self.timers['ban']:
	# 		return await ctx.send('No data')
	# 	def get_time(end_time):
	# 		days = (end_time - datetime.now()).days
	# 		seconds = (end_time - datetime.now()).seconds
	# 		hours = str(seconds / 60 / 60)
	# 		hours = int(hours[:hours.find('.')])
	# 		minutes = str(seconds / 60)
	# 		minutes = int(minutes[:minutes.find('.')])
	# 		if days > 0:
	# 			hours = hours - (days * 24)
	# 		if hours > 0:
	# 			minutes = minutes - (hours * 60)
	# 		return days, hours, minutes, seconds
	# 	moderations = []
	# 	if guild_id in self.timers['mute']:
	# 		for user_id in self.timers['mute'][guild_id].keys():
	# 			dat = self.timers['mute'][guild_id][user_id]
	# 			channel = self.bot.get_channel(dat['channel'])
	# 			if not channel:
	# 				del self.timers['mute'][guild_id][user_id]
	# 				return None, None
	# 			user = channel.guild.get_member(dat['user'])
	# 			if not user:
	# 				del self.timers['mute'][guild_id][user_id]
	# 				return None, None
	# 			format = '%Y-%m-%d %H:%M:%S.%f'
	# 			end_time = datetime.strptime(dat['end_time'], format)
	# 			days, hours, minutes, seconds = get_time(end_time)
	# 			moderation = f'\n✦ Mute | {user} | '
	# 			if days > 0:
	# 				moderation += f'{days} {"day" if days == 1 else "days"} '
	# 			if hours > 0:
	# 				moderation += f'{hours} {"hour" if hours == 1 else "hours"} '
	# 			if hours > 0 and minutes > 0:
	# 				moderation += f'and {minutes} {"minute" if minutes == 1 else "minutes"} '
	# 			else:
	# 				moderation += f'{minutes} {"minute" if minutes == 1 else "minutes"} '
	# 			moderation += 'remaining'
	# 			if moderation:
	# 				moderations.append([seconds, moderation])
	# 	if guild_id in self.timers['ban']:
	# 		for user_id in self.timers['ban'][guild_id].keys():
	# 			dat = self.timers['ban'][guild_id][user_id]
	# 			user = self.bot.get_user(dat['user'])
	# 			format = '%Y-%m-%d %H:%M:%S.%f'
	# 			end_time = datetime.strptime(dat['end_time'], format)
	# 			days, hours, minutes, seconds = get_time(end_time)
	# 			moderation = f'\n✦ Ban | {user} | '
	# 			if days > 0:
	# 				moderation += f'{days} days '
	# 			if hours > 0:
	# 				moderation += f'{hours} hours '
	# 			if hours > 0 and minutes > 0:
	# 				moderation += f'and {minutes} minutes '
	# 			else:
	# 				moderation += f'{minutes} minutes '
	# 			moderation += 'remaining\n'
	# 			if moderation:
	# 				moderations.append([seconds, moderation])
	# 	mod_log = ''
	# 	for seconds, moderation in (sorted(moderations, key=lambda kv: kv[0], reverse=True)):
	# 		mod_log += moderation
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_author(name=f'{ctx.guild.name} Mod Logs')
	# 	e.description = mod_log
	# 	await ctx.send(embed=e)
#
	# @commands.command(name='addmod')
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(administrator=True)
	# @commands.bot_has_permissions(embed_links=True)
	# async def addmod(self, ctx, *, user):
	# 	user = utils.get_user(ctx, user)
	# 	if not isinstance(user, discord.Member):
	# 		return await ctx.send('User not found')
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id not in self.mods:
	# 		self.mods[guild_id] = []
	# 	if user.id in self.mods[guild_id]:
	# 		return await ctx.send('That users already a mod')
	# 	self.mods[guild_id].append(user.id)
	# 	e = discord.Embed(color=colors.fate())
	# 	e.description = f'Made {user.mention} a mod'
	# 	await ctx.send(embed=e)
	# 	self.save_json()
#
	# @commands.command(name='delmod')
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(administrator=True)
	# @commands.bot_has_permissions(embed_links=True)
	# async def delmod(self, ctx, *, user):
	# 	user = utils.get_user(ctx, user)
	# 	if not isinstance(user, discord.Member):
	# 		return await ctx.send('User not found')
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id not in self.mods:
	# 		return await ctx.send('That user isn\'t a mod')
	# 	if user.id not in self.mods[guild_id]:
	# 		return await ctx.send('That user isn\'t a mod')
	# 	index = self.mods[guild_id].index(user.id)
	# 	self.mods[guild_id].pop(index)
	# 	e = discord.Embed(color=colors.fate())
	# 	e.description = f'{user.mention} is no longer a mod'
	# 	await ctx.send(embed=e)
	# 	self.save_json()
#
	# @commands.command(name='mods')
	# @commands.cooldown(1, 5, commands.BucketType.channel)
	# @commands.guild_only()
	# @commands.bot_has_permissions(embed_links=True)
	# async def mods(self, ctx):
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id not in self.mods:
	# 		return await ctx.send('This server has no mods')
	# 	mods = ''
	# 	for user_id in self.mods[guild_id]:
	# 		user = ctx.guild.get_member(user_id)
	# 		if not isinstance(user, discord.Member):
	# 			index = self.mods[guild_id].index(user_id)
	# 			self.mods[guild_id].pop(index)
	# 			continue
	# 		mods += f'• {user.mention}'
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_author(name='Discord Mods', icon_url=ctx.guild.owner.avatar_url)
	# 	e.set_thumbnail(url=ctx.guild.icon_url)
	# 	e.description = mods
	# 	await ctx.send(embed=e)
#
	# @commands.command(name='restrict')
	# @commands.guild_only()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.has_permissions(administrator=True)
	# async def restrict(self, ctx, args=None):
	# 	if not args:
	# 		e = discord.Embed(color=colors.fate())
	# 		e.set_author(name='Channel Restricting')
	# 		e.description = 'Prevents everyone except mods from using commands'
	# 		e.add_field(name='Usage', value='.restrict #channel_mention\n'
	# 			'.unrestrict #channel_mention\n.restricted')
	# 		return await ctx.send(embed=e)
	# 	guild_id = str(ctx.guild.id)
	# 	config = self.bot.get_config  # type: dict
	# 	if 'restricted' not in config:
	# 		config['restricted'] = {}
	# 	if guild_id not in config['restricted']:
	# 		config['restricted'][guild_id] = {}
	# 		config['restricted'][guild_id]['channels'] = []
	# 		config['restricted'][guild_id]['users'] = []
	# 	restricted = '**Restricted:**'
	# 	dat = config['restricted'][guild_id]
	# 	for channel in ctx.message.channel_mentions:
	# 		if channel.id in dat['channels']:
	# 			continue
	# 		config['restricted'][guild_id]['channels'].append(channel.id)
	# 		restricted += f'\n{channel.mention}'
	# 	for member in ctx.message.mentions:
	# 		if member.id in dat['users']:
	# 			continue
	# 		config['restricted'][guild_id]['users'].append(member.id)
	# 		restricted += f'\n{member.mention}'
	# 	e = discord.Embed(color=colors.fate(), description=restricted)
	# 	await ctx.send(embed=e)
	# 	self.save_config(config)
#
	# @commands.command(name='unrestrict')
	# @commands.guild_only()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.has_permissions(administrator=True)
	# async def unrestrict(self, ctx):
	# 	guild_id = str(ctx.guild.id)
	# 	config = self.bot.get_config  # type: dict
	# 	if 'restricted' not in config:
	# 		config['restricted'] = {}
	# 	unrestricted = '**Unrestricted:**'
	# 	dat = config['restricted'][guild_id]
	# 	if guild_id not in config['restricted']:
	# 		config['restricted'][guild_id] = {}
	# 		config['restricted'][guild_id]['channels'] = []
	# 		config['restricted'][guild_id]['users'] = []
	# 	for channel in ctx.message.channel_mentions:
	# 		if channel.id in dat['channels']:
	# 			index = config['restricted'][guild_id]['channels'].index(channel.id)
	# 			config['restricted'][guild_id]['channels'].pop(index)
	# 			unrestricted += f'\n{channel.mention}'
	# 	for member in ctx.message.mentions:
	# 		if member.id in dat['users']:
	# 			index = config['restricted'][guild_id]['users'].index(member.id)
	# 			config['restricted'][guild_id]['users'].pop(index)
	# 			unrestricted += f'\n{member.mention}'
	# 	e = discord.Embed(color=colors.fate(), description=unrestricted)
	# 	await ctx.send(embed=e)
	# 	self.save_config(config)
#
	# @commands.command(name='restricted')
	# @commands.guild_only()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.bot_has_permissions(embed_links=True)
	# async def restricted(self, ctx):
	# 	guild_id = str(ctx.guild.id)
	# 	config = self.bot.get_config  # type: dict
	# 	if guild_id not in config['restricted']:
	# 		return await ctx.send('No restricted channels/users')
	# 	dat = config['restricted'][guild_id]
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_author(name='Restricted:', icon_url=ctx.author.avatar_url)
	# 	e.description = ''
	# 	if dat['channels']:
	# 		changelog = ''
	# 		for channel_id in dat['channels']:
	# 			channel = self.bot.get_channel(channel_id)
	# 			if not isinstance(channel, discord.TextChannel):
	# 				position = config['restricted'][guild_id]['channels'].index(channel_id)
	# 				config['restricted'][guild_id]['channels'].pop(position)
	# 				self.save_config(config)
	# 			else:
	# 				changelog += '\n' + channel.mention
	# 		if changelog:
	# 			e.description += changelog
	# 	if dat['users']:
	# 		changelog = ''
	# 		for user_id in dat['users']:
	# 			user = self.bot.get_user(user_id)
	# 			if not isinstance(user, discord.User):
	# 				position = config['restricted'][guild_id]['users'].index(user_id)
	# 				config['restricted'][guild_id]['users'].pop(position)
	# 				self.save_config(config)
	# 			else:
	# 				changelog += '\n' + user.mention
	# 		if changelog:
	# 			e.description += changelog
	# 	await ctx.send(embed=e)
#
	# @commands.command(name="purge")
	# @commands.cooldown(1, 5, commands.BucketType.channel)
	# @commands.guild_only()
	# @commands.has_permissions(manage_messages=True)
	# @commands.bot_has_permissions(manage_messages=True)
	# async def purge(self, ctx, *args):
	# 	def help_embed():
	# 		e = discord.Embed(color=colors.fate())
	# 		u = '.purge amount\n' \
	# 		    '.purge @user amount\n' \
	# 		    '.purge images amount\n' \
	# 		    '.purge embeds amount\n' \
	# 		    '.purge mentions amount\n' \
	# 		    '.purge users amount\n' \
	# 		    '.purge bots amount\n' \
	# 		    '.purge word/phrase amount'
	# 		e.description = u
	# 		return e
	# 	if not args:
	# 		return await ctx.send(embed=help_embed())
	# 	channel_id = str(ctx.channel.id)
	# 	if channel_id in self.purge:
	# 		return await ctx.send('I\'m already purging')
	# 	else:
	# 		self.purge[channel_id] = True
	# 	if args[0].isdigit():  # no special option used
	# 		try:
	# 			amount = int(args[0])
	# 		except:
	# 			del self.purge[channel_id]
	# 			return await ctx.send('Invalid amount')
	# 		if amount > 1000:
	# 			del self.purge[channel_id]
	# 			return await ctx.send("You cannot purge more than 1000 messages at a time")
	# 		try:
	# 			await ctx.message.channel.purge(limit=amount, before=ctx.message)
	# 			await ctx.send(f'{ctx.author.mention}, successfully purged {amount} messages', delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 	if len(args) == 1:
	# 		return await ctx.send(embed=help_embed())
	# 	try:
	# 		amount = int(args[1])
	# 	except:
	# 		del self.purge[channel_id]
	# 		return await ctx.send('Invalid amount')
	# 	if ctx.message.mentions:
	# 		user = ctx.message.mentions[0]
	# 		if amount > 250:
	# 			del self.purge[channel_id]
	# 			return await ctx.send("You cannot purge more than 250 user messages at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.author.id == user.id:
	# 					if msg.id != ctx.message.id:
	# 						await msg.delete()
	# 						position += 1
	# 						if position == amount:
	# 							break
	# 			await ctx.send(f'{ctx.author.mention}, purged {position} messages from {user.display_name}', delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	option = args[0].lower()  # type: str
	# 	if option == 'image' or option == 'images':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 images at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.attachments:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} images", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	if option == 'embed' or option == 'embeds':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 embeds at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.embeds:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} embeds", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	if option == 'user' or option == 'users':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 user messages at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if not msg.author.bot:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} user messages", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	if option == 'bot' or option == 'bots':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 bot messages at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.author.bot:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} bot messages", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	if option == 'mention' or option == 'mentions':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 mentions at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.mentions:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} mentions", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	if option == 'reaction' or option == 'reactions':
	# 		if amount > 250:
	# 			return await ctx.send("You cannot purge more than 250 reactions at a time")
	# 		try:
	# 			position = 0
	# 			async for msg in ctx.channel.history(limit=500):
	# 				if msg.reactions:
	# 					await msg.clear_reactions()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 			await ctx.send(f"{ctx.author.mention}, purged {position} reactions", delete_after=5)
	# 			return await ctx.message.delete()
	# 		except discord.errors.Forbidden as e:
	# 			await ctx.send(e)
	# 		finally:
	# 			del self.purge[channel_id]
	# 		return
	# 	phrase = args[0]
	# 	amount = int(args[1])
	# 	if amount > 250:
	# 		return await ctx.send("You cannot purge more than 250 phrases at a time")
	# 	try:
	# 		position = 0
	# 		async for msg in ctx.channel.history(limit=500):
	# 			if phrase.lower() in msg.content.lower():
	# 				if msg.id != ctx.message.id:
	# 					await msg.delete()
	# 					position += 1
	# 					if position == amount:
	# 						break
	# 		await ctx.send(f"{ctx.author.mention}, purged {position} messages", delete_after=5)
	# 		return await ctx.message.delete()
	# 	except discord.errors.Forbidden as e:
	# 		await ctx.send(e)
	# 	finally:
	# 		del self.purge[channel_id]
#
	# @commands.command(name='ban')
	# @commands.cooldown(2, 10, commands.BucketType.guild)
	# @commands.guild_only()
	# @commands.has_permissions(ban_members=True)
	# @commands.bot_has_permissions(embed_links=True, ban_members=True)
	# async def ban(self, ctx, ids: Greedy[int], users: Greedy[discord.User], *, reason='Unspecified'):
	# 	""" Ban cmd that supports more than just members """
	# 	reason = f"{ctx.author}: {reason}"
	# 	users_to_ban = len(ids if ids else []) + len(users if users else [])
	# 	e = discord.Embed(color=colors.fate())
	# 	if users_to_ban == 0:
	# 		return await ctx.send("You need to specify who to ban")
	# 	elif users_to_ban > 1:
	# 		e.set_author(name=f"Banning {users_to_ban} user{'' if users_to_ban > 1 else ''}", icon_url=ctx.author.avatar_url)
	# 	e.set_thumbnail(url='https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif')
	# 	msg = await ctx.send(embed=e)
	# 	for id in ids:
	# 		member = ctx.guild.get_member(id)
	# 		if isinstance(member, discord.Member):
	# 			if member.top_role.position >= ctx.author.top_role.position:
	# 				e.add_field(name=f'◈ Failed to ban {member}', value="This users is above your paygrade", inline=False)
	# 				await msg.edit(embed=e)
	# 				continue
	# 			elif member.top_role.position >= ctx.guild.me.top_role.position:
	# 				e.add_field(name=f'◈ Failed to ban {member}', value="I can't ban this user", inline=False)
	# 				await msg.edit(embed=e)
	# 				continue
	# 		try:
	# 			user = await self.bot.fetch_user(id)
	# 		except:
	# 			e.add_field(name=f'◈ Failed to ban {id}', value="That user doesn't exist", inline=False)
	# 		else:
	# 			await ctx.guild.ban(user, reason=reason)
	# 			e.add_field(name=f'◈ Banned {user}', value=f'Reason: {reason}', inline=False)
	# 		await msg.edit(embed=e)
	# 	for user in users:
	# 		member = discord.utils.get(ctx.guild.members, id=user.id)
	# 		if member:
	# 			if member.top_role.position >= ctx.author.top_role.position:
	# 				e.add_field(name=f'◈ Failed to ban {member}', value="This users is above your paygrade", inline=False)
	# 				await msg.edit(embed=e)
	# 				continue
	# 			if member.top_role.position >= ctx.guild.me.top_role.position:
	# 				e.add_field(name=f'◈ Failed to ban {member}', value="I can't ban this user", inline=False)
	# 				await msg.edit(embed=e)
	# 				continue
	# 		await ctx.guild.ban(user, reason=reason)
	# 		e.add_field(name=f'◈ Banned {user}', value=f'Reason: {reason}', inline=False)
	# 	if not e.fields:
	# 		e.colour = colors.red()
	# 		e.set_author(name="Couldn't ban any of the specified user(s)")
	# 	await msg.edit(embed=e)
#
	# @commands.command(name='kick')
	# @commands.guild_only()
	# @commands.has_permissions(kick_members=True)
	# @commands.bot_has_permissions(embed_links=True, kick_members=True)
	# async def kick(self, ctx, user:discord.Member, *, reason='unspecified'):
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# 		return await ctx.send('I can\'t kick that user ;-;')
	# 	await user.kick(reason=reason)
	# 	e = discord.Embed(color=0x80b0ff)
	# 	e.set_author(name=f'kicked {user}', icon_url=user.avatar_url)
	# 	await ctx.send(embed=e)
	# 	try:
	# 		await user.send(f"You have been kicked from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
	# 	except:
	# 		pass
#
	# # @commands.command(name='ban')
	# # @commands.guild_only()
	# # @commands.has_permissions(ban_members=True)
	# # @commands.bot_has_permissions(ban_members=True)
	# # async def _ban(self, ctx, user:discord.Member, *, reason='unspecified reasons'):
	# # 	if user.top_role.position >= ctx.author.top_role.position:
	# # 		return await ctx.send('That user is above your paygrade, take a seat')
	# # 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# # 		return await ctx.send('I can\'t ban that user ;-;')
	# # 	await ctx.guild.ban(user, reason=reason, delete_message_days=0)
	# # 	e = discord.Embed(color=0x80b0ff)
	# # 	e.set_author(name=f'banned {user}', icon_url=user.avatar_url)
	# # 	await ctx.send(embed=e)
	# # 	try:
	# # 		await user.send(f"You have been banned from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
	# # 	except:
	# # 		pass
#
	# @commands.command(name='softban', aliases=['tempban'])
	# @commands.cooldown(1, 5, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(ban_members=True)
	# @commands.bot_has_permissions(embed_links=True, manage_messages=True, ban_members=True)
	# async def _softban(self, ctx, user: discord.Member, timer='0s', *, reason='unspecified reasons'):
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# 		return await ctx.send('I can\'t kick that user ;-;')
	# 	await user.ban(reason=reason)
	# 	path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
	# 	file = discord.File(path, filename=os.path.basename(path))
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_image(url='attachment://' + os.path.basename(path))
	# 	await ctx.send(f'◈ {ctx.author.display_name} banned {user} ◈', file=file, embed=e)
	# 	await ctx.message.delete()
	# 	timer, time = self.convert_timer(timer)
	# 	try: await user.send(f'You\'ve been banned from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}` for {time}')
	# 	except: pass
	# 	if not isinstance(timer, float):
	# 		return await ctx.send('Invalid character used in timer field\nYou\'ll have to manually unban this user')
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	if guild_id not in self.timers['ban']:
	# 		self.timers['ban'][guild_id] = {}
	# 	now = datetime.now()
	# 	timer_info = {'user': user.id, 'time': str(now), 'end_time': str(now + timedelta(seconds=timer))}
	# 	self.timers['ban'][guild_id][user_id] = timer_info
	# 	self.save_json()
	# 	await asyncio.sleep(timer)
	# 	if user_id in self.timers['ban'][guild_id]:
	# 		try: await user.unban(reason='softban')
	# 		except Exception as e: await ctx.send(f'Failed to unban {user.name}: {e}')
	# 		else: await ctx.send(f'**Unbanned {user}**')
	# 		del self.timers['ban'][guild_id][user_id]
	# 		self.save_json()
#
	# @commands.command(name='unban')
	# @commands.cooldown(*utils.default_cooldown())
	# @commands.has_permissions(ban_members=True)
	# @commands.bot_has_permissions(embed_links=True, ban_members=True, view_audit_log=True)
	# async def unban(self, ctx, users: Greedy[discord.User], *, reason=':author:'):
	# 	if not users:
	# 		async for entry in ctx.guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
	# 			users = entry.target,
	# 	if len(users) == 1:
	# 		user = users[0]
	# 		await ctx.guild.unban(user, reason=reason.replace(':author:', str(ctx.author)))
	# 		e = discord.Embed(color=colors.red())
	# 		e.set_author(name=f'{user} unbanned', icon_url=user.avatar_url)
	# 		await ctx.send(embed=e)
	# 	else:
	# 		e = discord.Embed(color=colors.green())
	# 		e.set_author(name=f'Unbanning {len(users)} users', icon_url=ctx.author.avatar_url)
	# 		e.description = ''
	# 		msg = await ctx.send(embed=e)
	# 		index = 1
	# 		for user in users:
	# 			e.description += f'✅ {user}'
	# 			if index == 5:
	# 				await msg.edit(embed=e)
	# 				index = 1
	# 			else:
	# 				index += 1
	# 		await msg.edit(embed=e)
#
	# @commands.command(name='bans')
	# @commands.cooldown(1, 10, commands.BucketType.channel)
	# @commands.guild_only()
	# @commands.bot_has_permissions(embed_links=True, ban_members=True)
	# async def bans(self, ctx):
	# 	bans = await ctx.guild.bans()
	# 	ban_list = ''
	# 	e = discord.Embed(color=colors.fate())
	# 	icon_url = self.bot.user.avatar_url
	# 	if ctx.guild.owner.avatar_url:
	# 		icon_url = ctx.guild.owner.avatar_url
	# 	e.set_author(name=f'{ctx.guild.name} bans', icon_url=icon_url)
	# 	e.set_thumbnail(url=ctx.guild.icon_url)
	# 	for BanEntry in bans:
	# 		user = BanEntry.user  # type: discord.User
	# 		reason = BanEntry.reason  # type: str
	# 		reason = reason if reason != "Unspecified" else 'unspecified reasons'
	# 		ban_list += f'__**{user}:**__, **reason:** [`{reason}`]\n'
	# 	ban_list = [ban_list[i:i + 1000] for i in range(0, len(ban_list), 1000)]
	# 	if len(ban_list) > 5:
	# 		ban_list = ban_list[:5]
	# 		e.set_footer(text='Character Limit Reached')
	# 	for i in range(len(ban_list)):
	# 		if i == 0:
	# 			e.description = ban_list[i]; continue
	# 		e.add_field(name='~', value=ban_list[i])
	# 	await ctx.send(embed=e)
#
	# @commands.command()
	# @commands.cooldown(1, 5, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_nicknames=True)
	# @commands.bot_has_permissions(manage_nicknames=True)
	# async def nick(self, ctx, user, *, nick=''):
	# 	user = utils.get_user(ctx, user)
	# 	if not user:
	# 		return await ctx.send('User not found')
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send('That user is above your paygrade, take a seat')
	# 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# 		return await ctx.send('I can\'t edit that users nick ;-;')
	# 	if len(nick) > 32:
	# 		return await ctx.send('That nickname is too long! Must be `32` or fewer in length')
	# 	await user.edit(nick=nick)
	# 	await ctx.message.add_reaction('👍')
#
	# @commands.command(name="massnick")
	# @commands.cooldown(1, 10, commands.BucketType.guild)
	# @commands.guild_only()
	# @commands.has_permissions(manage_nicknames=True)
	# @commands.bot_has_permissions(manage_nicknames=True)
	# async def _massnick(self, ctx, *, nick=None):
	# 	guild_id = str(ctx.guild.id)
	# 	if guild_id in self.massnick:
	# 		if self.massnick[guild_id] is True:
	# 			return await ctx.send('Please wait until the previous mass-nick is complete')
	# 	if not nick:
	# 		nick = ''
	# 	self.massnick[guild_id] = True
	# 	await ctx.message.add_reaction('🖍')
	# 	count = 0
	# 	if ctx.guild.members > 600:
	# 		await ctx.send("I can't do too many at a time, so you'll have to run the command again after to get everyone else")
	# 	for member in ctx.guild.members[:600]:
	# 		if not nick and not member.nick:
	# 			continue
	# 		try:
	# 			await member.edit(nick=nick)
	# 			count += 1
	# 			await asyncio.sleep(1)
	# 		except:
	# 			pass
	# 	self.massnick[guild_id] = False
	# 	await ctx.send(f'Changed nicks for {count} users')
#
	# @commands.command(name='role')
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_roles=True)
	# @commands.bot_has_permissions(manage_roles=True)
	# async def role(self, ctx, user, role, *, args=''):
	# 	def time_to_sleep(timers):
	# 		time_to_sleep = [0, []]
	# 		for timer in timers:
	# 			raw = ''.join(x for x in list(timer) if x.isdigit())
	# 			if 'd' in timer:
	# 				time = int(timer.replace('d', '')) * 60 * 60 * 24
	# 				repr = 'day'
	# 			elif 'h' in timer:
	# 				time = int(timer.replace('h', '')) * 60 * 60
	# 				repr = 'hour'
	# 			elif 'm' in timer:
	# 				time = int(timer.replace('m', '')) * 60
	# 				repr = 'minute'
	# 			else:  # 's' in timer
	# 				time = int(timer.replace('s', ''))
	# 				repr = 'second'
	# 			time_to_sleep[0] += time
	# 			time_to_sleep[1].append(f"{raw} {repr if raw == '1' else repr + 's'}")
	# 		timer, expanded_timer = time_to_sleep
	# 		return [timer, expanded_timer]
#
	# 	timers = []
	# 	for timer in [re.findall('[0-9]+[smhd]', arg) for arg in args.split()]:
	# 		timers = [*timers, *timer]
	# 	user = self.bot.utils.get_user(ctx, user)
	# 	if not user:
	# 		return await ctx.send('User not found')
	# 	converter = commands.RoleConverter()
	# 	try:
	# 		result = await converter.convert(ctx, role)
	# 		role = result  # type: discord.Role
	# 	except:
	# 		pass
	# 	if not isinstance(role, discord.Role):
	# 		role = await utils.get_role(ctx, role)
	# 	if not role:
	# 		return await ctx.send('Role not found')
#
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	role_id = str(role.id)
	# 	timer = expanded_timer = None
#
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send('This user is above your paygrade, take a seat')
	# 	if role.position >= ctx.author.top_role.position:
	# 		return await ctx.send('This role is above your paygrade, take a seat')
	# 	if role in user.roles:
	# 		add = False
	# 		await user.remove_roles(role)
	# 		msg = f'Removed **{role.name}** from @{user.name}'
	# 		if guild_id in self.rp and user_id in self.rp[guild_id]:
	# 			if role_id in self.rp[guild_id][user_id]:
	# 				del self.rp[guild_id][user_id][role_id]
	# 				if not self.rp[guild_id][user_id]:
	# 					del self.rp[guild_id][user_id]
	# 				if not self.rp[guild_id]:
	# 					del self.rp[guild_id]
	# 				await ctx.send('Removed role persist as well')
	# 				with open(self.path, 'w') as f:
	# 					json.dump(self.rp, f, ensure_ascii=False)
	# 	else:
	# 		add = True
	# 		await user.add_roles(role)
	# 		msg = f'Gave **{role.name}** to **@{user.name}**'
	# 		if timers:
	# 			timer, expanded_timer = time_to_sleep(timers)
	# 			await ctx.send(f"I'll keep this stuck to them for {', '.join(expanded_timer)}")
	# 			if '-np' not in args:
	# 				if guild_id not in self.rp:
	# 					self.rp[guild_id] = {}
	# 				if user_id not in self.rp[guild_id]:
	# 					self.rp[guild_id][user_id] = {}
	# 				self.rp[guild_id][user_id][str(role.id)] = time() + timer
	# 				with open(self.path, 'w') as f:
	# 					json.dump(self.rp, f, ensure_ascii=False)
	# 	await ctx.send(msg)
	# 	if timer:
	# 		await asyncio.sleep(timer)
	# 		if add:
	# 			await user.remove_roles(role)
	# 			await ctx.send(f"Removed `{role}` from @{user}")
	# 		else:
	# 			await user.add_roles(role)
	# 			await ctx.send(f"Added `{role}` to @{user}")
	# 		if '-np' not in args:
	# 			del self.rp[guild_id][user_id][role_id]
	# 			if not self.rp[guild_id][user_id]:
	# 				del self.rp[guild_id][user_id]
	# 			if not self.rp[guild_id]:
	# 				del self.rp[guild_id]
	# 			with open(self.path, 'w') as f:
	# 				json.dump(self.rp, f, ensure_ascii=False)
#
	# # @commands.command(name='rolepersist')
	# # @commands.cooldown(2, 5, commands.BucketType.user)
	# # async def role_persist(self, ctx, user: User, *, role):
	# # 	role = self.bot.utils.get_role(role)
	# # 	if not role:
#
#
	# @commands.Cog.listener('on_member_join')
	# async def role_persist(self, member):
	# 	guild_id = str(member.guild.id)
	# 	user_id = str(member.id)
	# 	if guild_id in self.rp and user_id in self.rp[guild_id]:
	# 		for role_id, end_time in self.rp[guild_id][user_id].items():
	# 			if time() > end_time():
	# 				del self.rp[guild_id][user_id][role_id]
	# 				continue
	# 			role = member.guild.get_role(int(role_id))
	# 			if role:
	# 				await member.add_roles(role)
#
	# @commands.command(name="massrole")
	# @commands.cooldown(1, 25, commands.BucketType.guild)
	# @commands.guild_only()
	# @commands.has_permissions(manage_roles=True)
	# @commands.bot_has_permissions(manage_roles=True)
	# async def massrole(self, ctx, *, role):
	# 	role = await utils.get_role(ctx, role)
	# 	if not role:
	# 		return await ctx.send('Role not found')
	# 	await ctx.message.add_reaction("🖍")
	# 	bot = ctx.guild.get_member(self.bot.user.id)
	# 	members = [m for m in ctx.guild.members if role not in m.roles and m.top_role.position < bot.top_role.position]
	# 	msg = await ctx.send(f'Estimated time: {str(len(members)) + " seconds" if len(members) < 60 else utils.get_time(len(members))}')
	# 	index = 1; counter = 0; total = len(members)
	# 	if total > 600:
	# 		await ctx.send("I can't do too many at a time, so you'll have to run the command again after to get everyone else")
	# 	for member in members[:600]:
	# 		counter += 1
	# 		try:
	# 			await member.add_roles(role)
	# 		except discord.errors.Forbidden:
	# 			return await ctx.send('Missing permissions')
	# 		except discord.errors.NotFound:
	# 			pass
	# 		if index == len(members):
	# 			await msg.edit(content=f'{index}/{len(members)} members updated')
	# 			break
	# 		if counter == 10:  # update progress/estimate every 10 members
	# 			estimate = str(str(total) + " seconds" if total < 60 else utils.get_time(total))
	# 			await msg.edit(content=f'Estimated time: {estimate}\n{index}/{len(members)} members updated')
	# 			counter = 0
	# 		index += 1
	# 		total -= 1
	# 		await asyncio.sleep(1)
	# 	await ctx.message.add_reaction("🏁")
#
	# @commands.command(name="mass-remove-role")
	# @commands.cooldown(1, 25, commands.BucketType.guild)
	# @commands.guild_only()
	# @commands.has_permissions(manage_roles=True)
	# @commands.bot_has_permissions(manage_roles=True)
	# async def mass_remove_role(self, ctx, *, role):
	# 	role = await utils.get_role(ctx, role)
	# 	if not role:
	# 		return await ctx.send('Role not found')
	# 	await ctx.message.add_reaction("🖍")
	# 	bot = ctx.guild.get_member(self.bot.user.id)
	# 	members = [m for m in ctx.guild.members if role in m.roles and m.top_role.position < bot.top_role.position]
	# 	msg = await ctx.send(f'Estimated time: {str(len(members)) + " seconds" if len(members) < 60 else utils.get_time(len(members))}')
	# 	index = 1; counter = 0; total = len(members)
	# 	if total > 600:
	# 		await ctx.send("I can't do too many at a time, so you'll have to run the command again after to get everyone else")
	# 	for member in members[:600]:
	# 		counter += 1
	# 		try:
	# 			await member.remove_roles(role)
	# 		except discord.errors.Forbidden:
	# 			return await ctx.send('Missing permissions')
	# 		except discord.errors.NotFound:
	# 			pass
	# 		if index == len(members):
	# 			await msg.edit(content=f'{index}/{len(members)} members updated')
	# 			break
	# 		if counter == 10:  # update progress/estimate every 10 members
	# 			estimate = str(str(total) + " seconds" if total < 60 else utils.get_time(total))
	# 			await msg.edit(content=f'Estimated time: {estimate}\n{index}/{len(members)} members updated')
	# 			counter = 0
	# 		index += 1
	# 		total -= 1
	# 		await asyncio.sleep(1)
	# 	await ctx.message.add_reaction("🏁")
#
	# @commands.command(name="del-cat")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_channels=True)
	# @commands.bot_has_permissions(manage_channels=True)
	# async def del_cat(self, ctx, category: discord.CategoryChannel):
	# 	for channel in category.text_channels:
	# 		await channel.delete()
	# 	await category.delete()
	# 	await ctx.send(f"Deleted category")
#
	# @commands.command(name="vcmute")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_roles=True)
	# @commands.bot_has_permissions(manage_roles=True)
	# async def vcmute(self, ctx, member: discord.Member):
	# 	if member.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	await member.edit(mute=True)
	# 	await ctx.send(f'Muted {member.display_name} 👍')
#
	# @commands.command(name="vcunmute")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_roles=True)
	# async def vcunmute(self, ctx, member: discord.Member):
	# 	if member.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	await member.edit(mute=False)
	# 	await ctx.send(f'Unmuted {member.display_name} 👍')
#
	# @commands.command(name="mute", description="Blocks a user from sending messages")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.bot_has_permissions(manage_roles=True)
	# async def mute(self, ctx, user: discord.Member=None, timer=None):
	# 	if not ctx.author.guild_permissions.manage_roles and (str(ctx.guild.id) in self.mods and ctx.author.id not in self.mods[str(ctx.guild.id)]):
	# 		return await ctx.send("You need manage role(s) permission(s) to use this")
	# 	async with ctx.typing():
	# 		if not user:
	# 			return await ctx.send("**Format:** `.mute {@user} {timer: 2m, 2h, or 2d}`")
	# 		if user.top_role.position >= ctx.author.top_role.position:
	# 			return await ctx.send("That user is above your paygrade, take a seat")
	# 		guild_id = str(ctx.guild.id)
	# 		user_id = str(user.id)
	# 		mute_role = None
	# 		for role in ctx.guild.roles:
	# 			if role.name.lower() == "muted":
	# 				mute_role = role
	# 				for channel in ctx.guild.text_channels:
	# 					if mute_role not in channel.overwrites:
	# 						await channel.set_permissions(mute_role, send_messages=False)
	# 						await asyncio.sleep(0.5)
	# 				for channel in ctx.guild.voice_channels:
	# 					if mute_role not in channel.overwrites:
	# 						await channel.set_permissions(mute_role, speak=False)
	# 						await asyncio.sleep(0.5)
	# 		if not mute_role:
	# 			perms = [perm for perm, value in ctx.guild.me.guild_permissions if value]
	# 			if 'manage_channels' not in perms:
	# 				return await ctx.send('No muted role found, and I\'m missing manage_channel permissions to set one up')
	# 			mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
	# 			for channel in ctx.guild.text_channels:
	# 				try:
	# 					await channel.set_permissions(mute_role, send_messages=False)
	# 				except:
	# 					await ctx.send(f"Couldn't modify mute role in {channel.mention}s overwrites")
	# 				await asyncio.sleep(0.5)
	# 			for channel in ctx.guild.voice_channels:
	# 				try:
	# 					await channel.set_permissions(mute_role, speak=False)
	# 				except:
	# 					await ctx.send(f"Couldn't modify mute role in {channel.name}s overwrites")
	# 				await asyncio.sleep(0.5)
	# 		if mute_role in user.roles:
	# 			return await ctx.send(f'{user.display_name} is already muted')
	# 		if not timer:
	# 			if guild_id not in self.roles:
	# 				self.roles[guild_id] = {}
	# 			self.roles[guild_id][user_id] = []
	# 			await user.add_roles(mute_role)
	# 			await ctx.send(f'Muted {user.display_name}')
	# 			await ctx.message.add_reaction('👍')
	# 			for role in [role for role in sorted(user.roles, reverse=True) if role is not mute_role]:
	# 				try:
	# 					await user.remove_roles(role)
	# 					self.roles[guild_id][user_id].append(role.id)
	# 					await asyncio.sleep(1)
	# 				except:
	# 					pass
	# 			return self.save_json()
	# 		for x in list(timer):
	# 			if x not in '1234567890dhms':
	# 				return await ctx.send("Invalid character used in timer field")
	# 		timer, time = self.convert_timer(timer)
	# 		if not isinstance(timer, float):
	# 			return await ctx.send("Invalid character used in timer field")
	# 		await user.add_roles(mute_role)
	# 		if not timer:
	# 			await ctx.send(f"**Muted:** {user.name}")
	# 		else:
	# 			await ctx.send(f"Muted **{user.name}** for {time}")
	# 		removed_roles = []
	# 		for role in [role for role in sorted(user.roles, reverse=True) if role is not mute_role]:
	# 			try:
	# 				await user.remove_roles(role)
	# 				removed_roles.append(role.id)
	# 				await asyncio.sleep(0.5)
	# 			except:
	# 				pass
	# 	try:
	# 		timer_info = {
	# 			'channel': ctx.channel.id,
	# 			'user': user.id,
	# 			'end_time': str(datetime.now() + timedelta(seconds=round(timer))),
	# 			'mute_role': mute_role.id,
	# 			'roles': removed_roles
	# 		}
	# 	except OverflowError:
	# 		return await ctx.send("No way in hell I'm waiting that long to unmute")
	# 	if guild_id not in self.timers['mute']:
	# 		self.timers['mute'][guild_id] = {}
	# 	self.timers['mute'][guild_id][user_id] = timer_info
	# 	self.save_json()
	# 	await asyncio.sleep(timer)
	# 	if user_id in self.timers['mute'][guild_id]:
	# 		user = ctx.guild.get_member(int(user_id))
	# 		if user:
	# 			if mute_role in user.roles:
	# 				await user.remove_roles(mute_role)
	# 				await ctx.send(f"**Unmuted:** {user.name}")
	# 			for role_id in removed_roles:
	# 				role = ctx.guild.get_role(role_id)
	# 				if role not in user.roles:
	# 					await user.add_roles(role)
	# 					await asyncio.sleep(0.5)
	# 			if guild_id in self.timers:
	# 				if user_id in self.timers[guild_id]:
	# 					del self.timers['mute'][guild_id][user_id]
	# 					self.save_json()
#
	# @commands.command(name="unmute", description="Unblocks users from sending messages")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
	# async def unmute(self, ctx, user: discord.Member=None):
	# 	if not ctx.author.guild_permissions.manage_roles and (str(ctx.guild.id) in self.mods and ctx.author.id not in self.mods[str(ctx.guild.id)]):
	# 		return await ctx.send("You need manage role(s) permission(s) to use this")
	# 	if user is None:
	# 		return await ctx.send("**Unmute Usage:**\n.unmute {@user}")
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	mute_role = None
	# 	for role in ctx.guild.roles:
	# 		if role.name.lower() == "muted":
	# 			mute_role = role
	# 	if not mute_role:
	# 		mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
	# 		for channel in ctx.guild.text_channels:
	# 			await channel.set_permissions(mute_role, send_messages=False)
	# 		for channel in ctx.guild.voice_channels:
	# 			await channel.set_permissions(mute_role, speak=False)
	# 	if mute_role not in user.roles:
	# 		return await ctx.send(f"{user.display_name} is not muted")
	# 	await user.remove_roles(mute_role)
	# 	if guild_id in self.roles:
	# 		if user_id in self.roles[guild_id]:
	# 			for role_id in self.roles[guild_id][user_id]:
	# 				role = ctx.guild.get_role(role_id)
	# 				if role and role not in user.roles:
	# 					await user.add_roles(role)
	# 					await asyncio.sleep(0.5)
	# 			del self.roles[guild_id][user_id]
	# 			self.save_json()
	# 	if guild_id in self.timers['mute']:
	# 		if user_id in self.timers['mute'][guild_id]:
	# 			dat = self.timers['mute'][guild_id][user_id]
	# 			channel = self.bot.get_channel(dat['channel'])  # type: discord.TextChannel
	# 			removed_roles = dat['roles']  # type: list
	# 			for role_id in removed_roles:
	# 				role = channel.guild.get_role(role_id)
	# 				if role and role not in user.roles:
	# 					await user.add_roles(channel.guild.get_role(role_id))
	# 					await asyncio.sleep(0.5)
	# 			del self.timers['mute'][guild_id][user_id]
	# 			self.save_json()
	# 	await ctx.send(f"Unmuted {user.name}")
#
	# @commands.command(name="warn")
	# @commands.cooldown(1, 5, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_guild=True)
	# @commands.bot_has_permissions(manage_roles=True)
	# async def _warn(self, ctx, user, *, reason=None):
	# 	user = utils.get_user(ctx, user)
	# 	if not isinstance(user, discord.Member):
	# 		return await ctx.send("User not found")
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	if not reason:
	# 		reason = "unspecified"
	# 	user_id = str(user.id)
	# 	guild_id = str(ctx.guild.id)
	# 	punishments = ['None', 'None', 'Mute', 'Kick', 'Softban', 'Ban']
	# 	config = self.bot.utils.get_config()  # type: dict
	# 	if guild_id in config['warns']['punishments']:
	# 		punishments = config['warns']['punishments'][guild_id]
	# 	if guild_id not in self.warns:
	# 		self.warns[guild_id] = {}
	# 	if user_id not in self.warns[guild_id]:
	# 		self.warns[guild_id][user_id] = []
	# 	if not isinstance(self.warns[guild_id][user_id], list):
	# 		self.warns[guild_id][user_id] = []
	# 	self.warns[guild_id][user_id].append([reason, str(datetime.now())])
	# 	warns = 0
	# 	for reason, time in self.warns[guild_id][user_id]:
	# 		time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
	# 		if (datetime.now() - time).days > 30:
	# 			if guild_id in config['warns']['expire']:
	# 				index = self.warns[guild_id][user_id].index([reason, str(time)])
	# 				self.warns[guild_id][user_id].pop(index)
	# 				continue
	# 		warns += 1
	# 	self.save_json()
	# 	if warns > len(punishments):
	# 		punishment = punishments[-1:][0]
	# 	else:
	# 		punishment = punishments[warns - 1]
	# 	if warns >= len(punishments):
	# 		next_punishment = punishments[-1:][0]
	# 	else:
	# 		next_punishment = punishments[warns]
	# 	e = discord.Embed(color=colors.fate())
	# 	url = self.bot.user.avatar_url
	# 	if user.avatar_url:
	# 		url = user.avatar_url
	# 	e.set_author(name=f'{user.name} has been warned', icon_url=url)
	# 	e.description = f'**Warns:** [`{warns}`] '
	# 	if punishment != 'None':
	# 		e.description += f'**Punishment:** [`{punishment}`]'
	# 	if punishment == 'None' and next_punishment != 'None':
	# 		e.description += f'**Next Punishment:** [`{next_punishment}`]'
	# 	else:
	# 		if punishment == 'None' and next_punishment == 'None':
	# 			e.description += f'**Reason:** [`{reason}`]'
	# 		if next_punishment != 'None':
	# 			e.description += f'\n**Next Punishment:** [`{next_punishment}`]'
	# 	if punishment != 'None' and next_punishment != 'None':
	# 		e.add_field(name='Reason', value=reason, inline=False)
	# 	await ctx.send(embed=e)
	# 	try:
	# 		await user.send(f"You've been warned in **{ctx.guild.name}** for `{reason}`")
	# 	except:
	# 		pass
	# 	if punishment == 'Mute':
	# 		mute_role = None
	# 		for role in ctx.guild.roles:
	# 			if role.name.lower() == "muted":
	# 				mute_role = role
	# 		if not mute_role:
	# 			bot = discord.utils.get(ctx.guild.members, id=self.bot.user.id)
	# 			perms = list(perm for perm, value in bot.guild_permissions if value)
	# 			if "manage_channels" not in perms:
	# 				return await ctx.send("No muted role found, and I'm missing manage_channel permissions to set one up")
	# 			mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
	# 			for channel in ctx.guild.text_channels:
	# 				await channel.set_permissions(mute_role, send_messages=False)
	# 			for channel in ctx.guild.voice_channels:
	# 				await channel.set_permissions(mute_role, speak=False)
	# 		if mute_role in user.roles:
	# 			return await ctx.send(f"{user.display_name} is already muted")
	# 		user_roles = []
	# 		for role in user.roles:
	# 			try:
	# 				await user.remove_roles(role)
	# 				user_roles.append(role.id)
	# 				await asyncio.sleep(0.5)
	# 			except:
	# 				pass
	# 		await user.add_roles(mute_role)
	# 		timer_info = {
	# 			'action': 'mute',
	# 			'channel': ctx.channel.id,
	# 			'user': user.id,
	# 			'end_time': str(datetime.now() + timedelta(seconds=7200)),
	# 			'mute_role': mute_role.id,
	# 			'roles': user_roles}
	# 		if guild_id not in self.timers:
	# 			self.timers[guild_id] = {}
	# 		if user_id not in self.timers[guild_id]:
	# 			self.timers[guild_id][user_id] = []
	# 		self.timers[guild_id][user_id].append(timer_info)
	# 		self.save_json()
	# 		await asyncio.sleep(7200)
	# 		if mute_role in user.roles:
	# 			await user.remove_roles(mute_role)
	# 			await ctx.send(f"**Unmuted:** {user.name}")
	# 		if user_id in self.timers:
	# 			del self.timers[user_id]
	# 		self.save_json()
	# 	if punishment == 'Kick':
	# 		try:
	# 			await ctx.guild.kick(user, reason='Reached Sufficient Warns')
	# 		except:
	# 			await ctx.send('Failed to kick that user')
	# 	if punishment == 'Softban':
	# 		try:
	# 			await ctx.guild.kick(user, reason='Softban - Reached Sufficient Warns')
	# 			await ctx.guild.unban(user, reason='Softban')
	# 		except:
	# 			await ctx.send('Failed to softban that user')
	# 	if punishment == 'Ban':
	# 		try:
	# 			await ctx.guild.ban(user, reason='Reached Sufficient Warns')
	# 		except:
	# 			await ctx.send('Failed to ban that user')
#
	# @commands.command(name='removewarn', aliases=['delwarn'])
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.has_permissions(manage_guild=True)
	# @commands.bot_has_permissions(embed_links=True)
	# async def remove_warns(self, ctx, user, *, reason):
	# 	user = utils.get_user(ctx, user)
	# 	if not isinstance(user, discord.Member):
	# 		return await ctx.send("User not found")
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	if guild_id not in self.warns:
	# 		return await ctx.send('This guild has no warns')
	# 	if user_id not in self.warns[guild_id]:
	# 		return await ctx.send('That user doesn\'t have any warns')
	# 	warns = self.warns[guild_id][user_id]
	# 	for warn_reason, time in warns:
	# 		if reason.lower() in warn_reason.lower():
	# 			e = discord.Embed(color=colors.fate())
	# 			e.description = warn_reason
	# 			msg = await ctx.send(embed=e)
	# 			await msg.add_reaction('✔')
	# 			await asyncio.sleep(0.5)
	# 			await msg.add_reaction('❌')
	# 			def check(reaction, user):
	# 				return user == ctx.author and str(reaction.emoji) in ['✔', '❌']
	# 			try:
	# 				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
	# 			except asyncio.TimeoutError:
	# 				return await ctx.send('Timeout Error')
	# 			else:
	# 				if str(reaction.emoji) == '✔':
	# 					index = warns.index([warn_reason, time])
	# 					self.warns[guild_id][user_id].pop(index)
	# 					await ctx.message.delete()
	# 					return await msg.delete()
	# 				else:
	# 					await msg.delete()
#
	# @commands.command(name="clearwarns")
	# @commands.cooldown(1, 5, commands.BucketType.user)
	# @commands.has_permissions(manage_guild=True)
	# @commands.guild_only()
	# async def clearwarns(self, ctx, *, user):
	# 	user = utils.get_user(ctx, user)
	# 	if not isinstance(user, discord.Member):
	# 		return await ctx.send("User not found")
	# 	if user.top_role.position >= ctx.author.top_role.position:
	# 		return await ctx.send("That user is above your paygrade, take a seat")
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	if guild_id not in self.warns:
	# 		self.warns[guild_id] = {}
	# 	self.warns[guild_id][user_id] = []
	# 	await ctx.send(f"Cleared {user.name}'s warn count")
	# 	self.save_json()
#
	# @commands.command(name="warns")
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# @commands.guild_only()
	# @commands.bot_has_permissions(embed_links=True)
	# async def _warns(self, ctx, *, user=None):
	# 	if not user: user = ctx.author
	# 	else: user = utils.get_user(ctx, user)
	# 	if not user:
	# 		return await ctx.send('User not found')
	# 	guild_id = str(ctx.guild.id)
	# 	user_id = str(user.id)
	# 	if guild_id not in self.warns:
	# 		self.warns[guild_id] = {}
	# 	if user_id not in self.warns[guild_id]:
	# 		self.warns[guild_id][user_id] = []
	# 	warns = 0
	# 	reasons = ''
	# 	for reason, time in self.warns[guild_id][user_id]:
	# 		time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
	# 		if (datetime.now() - time).days > 30:
	# 			if 'expire' in self.warns[guild_id]:
	# 				if self.warns[guild_id]['expire'] == 'True':
	# 					index = self.warns[guild_id][user_id].index([reason, time])
	# 					self.warns[guild_id][user_id].pop(index)
	# 					continue
	# 		warns += 1
	# 		reasons += f'\n• `{reason}`'
	# 	e = discord.Embed(color=colors.fate())
	# 	url = self.bot.user.avatar_url
	# 	if user.avatar_url:
	# 		url = user.avatar_url
	# 	e.set_author(name=f'{user.name}\'s Warns', icon_url=url)
	# 	e.description = f'**Total Warns:** [`{warns}`]' + reasons
	# 	await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Mod(bot))