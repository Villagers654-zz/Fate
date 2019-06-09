from datetime import datetime, timedelta
from discord.ext import commands
from utils import colors, config, checks
from time import monotonic
from os.path import isfile
import discord
import asyncio
import random
import json
import os

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

	def save_json(self):
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({'mods': self.mods, "warns": self.warns, "roles": self.roles, "timers": self.timers, 'clearwarns': self.wipe}, outfile, ensure_ascii=False)

	def save_config(self, config):
		with open('./data/config.json', 'w') as f:
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
					await user.remove_roles(mute_role)
					await channel.send(f"**Unmuted:** {user.name}")
			for role_id in removed_roles:
				role = channel.guild.get_role(role_id)
				if role:
					if role not in user.roles:
						await user.add_roles(role)
						await asyncio.sleep(0.5)
		if datetime.now() < end_time:
			await asyncio.sleep(sleep_time)
			await unmute()
		else:
			await unmute()
		del self.timers['mute'][guild_id][user_id]
		self.save_json()

	async def start_ban_timer(self, guild_id, user_id):
		dat = self.timers['ban'][guild_id][user_id]
		guild = self.bot.get_guild(int(guild_id))
		user = self.bot.get_user(dat['user'])
		format = '%Y-%m-%d %H:%M:%S.%f'
		end_time = datetime.strptime(dat['end_time'], format)
		if datetime.now() < end_time:
			sleep_time = (end_time - datetime.now()).seconds
			await asyncio.sleep(sleep_time)
			await guild.unban(user)
		else:
			await guild.unban(user)
		del self.timers['ban'][guild_id][user_id]

	def get_user(self, ctx, user):
		if user.startswith("<@"):
			for char in list(user):
				if char not in list('1234567890'):
					user = user.replace(str(char), '')
			return ctx.guild.get_member(int(user))
		else:
			user = user.lower()
			for member in ctx.guild.members:
				if user == member.name.lower():
					return member
			for member in ctx.guild.members:
				if user == member.display_name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.display_name.lower():
					return member
		return

	async def convert_arg_to_timer(self, timer):
		time = timer.replace("m", " minutes").replace("1 minutes", "1 minute")
		time = time.replace("h", " hours").replace("1 hours", "1 hour")
		time = time.replace("d", " days").replace("1 days", "1 day")
		time = time.replace('s', 'seconds').replace('1 seconds', '1 second')
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

	@commands.command(name='getuser')
	async def getuser(self, ctx, user):
		before = monotonic()
		user = self.get_user(ctx, user)
		ping = str((monotonic() - before) * 1000)
		ping = ping[:ping.find('.')]
		await ctx.send(f'**{user}:** `{ping}ms`')

	@commands.Cog.listener()
	async def on_ready(self):
		channel = self.bot.get_channel(config.server('log'))
		for guild_id in list(self.timers['mute'].keys()):
			for user_id in list(self.timers['mute'][guild_id].keys()):
				await channel.send(f"Mute Timer:{guild_id}|{user_id}", delete_after=3)
		for guild_id in list(self.timers['ban'].keys()):
			for user_id in list(self.timers['ban'][guild_id].keys()):
				await channel.send(f'Ban Timer:{guild_id}|{user_id}')

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if m.channel.id == config.server('log'):
				if m.content.startswith('Mute Timer:'):
					guild_id, user_id = m.content.replace('Mute Timer:', '').split('|')
					await self.start_mute_timer(guild_id, user_id)
				if m.content.startswith('Ban Timer:'):
					guild_id, user_id = m.content.replace('Ban Timer:', '').split('|')
					await self.start_ban_timer(guild_id, user_id)

	@commands.Cog.listener()
	async def on_member_ban(self, member):
		guild_id = str(member.guild.id)
		user_id = str(member.id)
		if guild_id in self.wipe:
			if guild_id in self.warns:
				if user_id in self.warns[guild_id]:
					del self.warns[guild_id][user_id]
					self.save_json()

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.warns:
			del self.warns[guild_id]
			self.save_json()
		if guild_id in self.roles:
			del self.warns[guild_id]
			self.save_json()
		if guild_id in self.timers['mute']:
			del self.timers['mute'][guild_id]
			self.save_json()
		if guild_id in self.timers['ban']:
			del self.timers['ban'][guild_id]
			self.save_json()
		if guild_id in self.mods:
			del self.mods[guild_id]
			self.save_json()
		config = self.bot.get_config
		if guild_id in config['restricted']:
			del config['restricted'][guild_id]
			self.save_config(config)

	@commands.command(name="cleartimers")
	@commands.check(checks.luck)
	async def cleartimers(self, ctx):
		self.timers = {}
		await ctx.message.add_reaction("👍")
		self.save_json()

	@commands.command(name='clearwarnsonban')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def clear_warns_on_ban(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.wipe:
			self.wipe.append(guild_id)
			await ctx.send('I\'ll now wipe warns on ban')
			return self.save_json()
		index = self.wipe.index(guild_id)
		self.wipe.pop(index)
		self.save_json()

	@commands.command(name='modlogs', aliases=['actions'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def mod_logs(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.timers['mute'] and guild_id not in self.timers['ban']:
			return await ctx.send('No data')
		def get_time(end_time):
			days = (end_time - datetime.now()).days
			seconds = (end_time - datetime.now()).seconds
			hours = str(seconds / 60 / 60)
			hours = int(hours[:hours.find('.')])
			minutes = str(seconds / 60)
			minutes = int(minutes[:minutes.find('.')])
			if days > 0:
				hours = hours - (days * 24)
			if hours > 0:
				minutes = minutes - (hours * 60)
			return days, hours, minutes, seconds
		moderations = []
		if guild_id in self.timers['mute']:
			for user_id in self.timers['mute'][guild_id].keys():
				dat = self.timers['mute'][guild_id][user_id]
				channel = self.bot.get_channel(dat['channel'])
				if not channel:
					del self.timers['mute'][guild_id][user_id]
					return None, None
				user = channel.guild.get_member(dat['user'])
				if not user:
					del self.timers['mute'][guild_id][user_id]
					return None, None
				format = '%Y-%m-%d %H:%M:%S.%f'
				end_time = datetime.strptime(dat['end_time'], format)
				days, hours, minutes, seconds = get_time(end_time)
				moderation = f'✦ Mute | {user} | '
				if days > 0:
					moderation += f'{days} {"day" if days == 1 else "days"} '
				if hours > 0:
					moderation += f'{hours} {"hour" if hours == 1 else "hours"} '
				if hours > 0 and minutes > 0:
					moderation += f'and {minutes} {"minute" if minutes == 1 else "minutes"} '
				else:
					moderation += f'{minutes} {"minute" if minutes == 1 else "minutes"} '
				moderation += 'remaining'
				if moderation:
					moderations.append([seconds, moderation])
		if guild_id in self.timers['ban']:
			for user_id in self.timers['ban'][guild_id].keys():
				dat = self.timers['ban'][guild_id][user_id]
				user = self.bot.get_user(dat['user'])
				format = '%Y-%m-%d %H:%M:%S.%f'
				end_time = datetime.strptime(dat['end_time'], format)
				days, hours, minutes, seconds = get_time(end_time)
				moderation = f'✦ Ban | {user} | '
				if days > 0:
					moderation += f'{days} days '
				if hours > 0:
					moderation += f'{hours} hours '
				if hours > 0 and minutes > 0:
					moderation += f'and {minutes} minutes '
				else:
					moderation += f'{minutes} minutes '
				moderation += 'remaining\n'
				if moderation:
					moderations.append([seconds, moderation])
		mod_log = ''
		for seconds, moderation in (sorted(moderations, key=lambda kv: kv[0], reverse=True)):
			mod_log += moderation
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f'{ctx.guild.name} Mod Logs')
		e.description = mod_log
		await ctx.send(embed=e)

	@commands.command(name='addmod')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(embed_links=True)
	async def addmod(self, ctx, *, user):
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send('User not found')
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			self.mods[guild_id] = []
		if user.id in self.mods[guild_id]:
			return await ctx.send('That users already a mod')
		self.mods[guild_id].append(user.id)
		e = discord.Embed(color=colors.fate())
		e.description = f'Made {user.mention} a mod'
		await ctx.send(embed=e)
		self.save_json()

	@commands.command(name='delmod')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(embed_links=True)
	async def delmod(self, ctx, *, user):
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send('User not found')
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			return await ctx.send('That user isn\'t a mod')
		if user.id not in self.mods[guild_id]:
			return await ctx.send('That user isn\'t a mod')
		index = self.mods[guild_id].index(user.id)
		self.mods[guild_id].pop(index)
		e = discord.Embed(color=colors.fate())
		e.description = f'{user.mention} is no longer a mod'
		await ctx.send(embed=e)
		self.save_json()

	@commands.command(name='mods')
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def mods(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			return await ctx.send('This server has no mods')
		mods = ''
		for user_id in self.mods[guild_id]:
			user = ctx.guild.get_member(user_id)
			if not isinstance(user, discord.Member):
				index = self.mods[guild_id].index(user_id)
				self.mods[guild_id].pop(index)
				continue
			mods += f'• {user.mention}'
		e = discord.Embed(color=colors.fate())
		e.set_author(name='Discord Mods', icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = mods
		await ctx.send(embed=e)

	@commands.command(name='restrict')
	@commands.guild_only()
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def restrict(self, ctx, args=None):
		if not args:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Channel Restricting')
			e.description = 'Prevents everyone except mods from using commands'
			e.add_field(name='Usage', value='.restrict #channel_mention\n'
				'.unrestrict #channel_mention\n.restricted')
			return await ctx.send(embed=e)
		guild_id = str(ctx.guild.id)
		config = self.bot.get_config  # type: dict
		if 'restricted' not in config:
			config['restricted'] = {}
		if guild_id not in config['restricted']:
			config['restricted'][guild_id] = {}
			config['restricted'][guild_id]['channels'] = []
			config['restricted'][guild_id]['users'] = []
		restricted = '**Restricted:**'
		dat = config['restricted'][guild_id]
		for channel in ctx.message.channel_mentions:
			if channel.id in dat['channels']:
				continue
			config['restricted'][guild_id]['channels'].append(channel.id)
			restricted += f'\n{channel.mention}'
		for member in ctx.message.mentions:
			if member.id in dat['users']:
				continue
			config['restricted'][guild_id]['users'].append(member.id)
			restricted += f'\n{member.mention}'
		e = discord.Embed(color=colors.fate(), description=restricted)
		await ctx.send(embed=e)
		self.save_config(config)

	@commands.command(name='unrestrict')
	@commands.guild_only()
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def unrestrict(self, ctx):
		guild_id = str(ctx.guild.id)
		config = self.bot.get_config  # type: dict
		if 'restricted' not in config:
			config['restricted'] = {}
		unrestricted = '**Unrestricted:**'
		dat = config['restricted'][guild_id]
		if guild_id not in config['restricted']:
			config['restricted'][guild_id] = {}
			config['restricted'][guild_id]['channels'] = []
			config['restricted'][guild_id]['users'] = []
		for channel in ctx.message.channel_mentions:
			if channel.id in dat['channels']:
				index = config['restricted'][guild_id]['channels'].index(channel.id)
				config['restricted'][guild_id]['channels'].pop(index)
				unrestricted += f'\n{channel.mention}'
		for member in ctx.message.mentions:
			if member.id in dat['users']:
				index = config['restricted'][guild_id]['users'].index(member.id)
				config['restricted'][guild_id]['users'].pop(index)
				unrestricted += f'\n{member.mention}'
		e = discord.Embed(color=colors.fate(), description=unrestricted)
		await ctx.send(embed=e)
		self.save_config(config)

	@commands.command(name='restricted')
	@commands.guild_only()
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def restricted(self, ctx):
		guild_id = str(ctx.guild.id)
		config = self.bot.get_config  # type: dict
		if guild_id not in config['restricted']:
			return await ctx.send('No restricted channels/users')
		dat = config['restricted'][guild_id]
		e = discord.Embed(color=colors.fate())
		e.set_author(name='Restricted:', icon_url=ctx.author.avatar_url)
		e.description = ''
		if dat['channels']:
			changelog = ''
			for channel_id in dat['channels']:
				channel = self.bot.get_channel(channel_id)
				if not isinstance(channel, discord.TextChannel):
					position = config['restricted'][guild_id]['channels'].index(channel_id)
					config['restricted'][guild_id]['channels'].pop(position)
					self.save_config(config)
				else:
					changelog += '\n' + channel.mention
			if changelog:
				e.description += changelog
		if dat['users']:
			changelog = ''
			for user_id in dat['users']:
				user = self.bot.get_user(user_id)
				if not isinstance(user, discord.User):
					position = config['restricted'][guild_id]['users'].index(user_id)
					config['restricted'][guild_id]['users'].pop(position)
					self.save_config(config)
				else:
					changelog += '\n' + user.mention
			if changelog:
				e.description += changelog
		await ctx.send(embed=e)

	@commands.command(name="purge")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge(self, ctx, *args):
		def help_embed():
			e = discord.Embed(color=colors.fate())
			u = '.purge amount\n' \
			    '.purge @user amount\n' \
			    '.purge images amount\n' \
			    '.purge embeds amount\n' \
			    '.purge mentions amount' \
			    '.purge users amount\n' \
			    '.purge bots amount'
			e.description = u
			return e
		if not args:
			return await ctx.send(embed=help_embed())
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		if args[0].isdigit():  # no special option used
			amount = int(args[0])
			if amount > 1000:
				del self.purge[channel_id]
				return await ctx.send("You cannot purge more than 1000 messages at a time")
			try:
				await ctx.message.channel.purge(before=ctx.message, limit=amount)
				await ctx.send(f'{ctx.author.mention}, successfully purged {amount} messages', delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		if len(args) == 1:
			return await ctx.send(embed=help_embed())
		amount = int(args[1])
		if ctx.message.mentions:
			user = ctx.message.mentions[0]
			if amount > 250:
				del self.purge[channel_id]
				return await ctx.send("You cannot purge more than 250 user messages at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if msg.author.id == user.id:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f'{ctx.author.mention}, purged {position} messages from {user.display_name}', delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		option = args[0].lower()  # type: str
		if option == 'image' or option == 'images':
			if amount > 250:
				return await ctx.send("You cannot purge more than 250 images at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if msg.attachments:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f"{ctx.author.mention}, purged {position} images", delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		if option == 'embed' or option == 'embeds':
			if amount > 250:
				return await ctx.send("You cannot purge more than 250 embeds at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if msg.embeds:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f"{ctx.author.mention}, purged {position} embeds", delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		if option == 'user' or option == 'users':
			if amount > 250:
				return await ctx.send("You cannot purge more than 250 user messages at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if not msg.author.bot:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f"{ctx.author.mention}, purged {position} user messages", delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		if option == 'bot' or option == 'bots':
			if amount > 250:
				return await ctx.send("You cannot purge more than 250 bot messages at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if msg.author.bot:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f"{ctx.author.mention}, purged {position} bot messages", delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		if option == 'mention' or option == 'mentions':
			if amount > 250:
				return await ctx.send("You cannot purge more than 250 mentions at a time")
			try:
				position = 0
				async for msg in ctx.channel.history(limit=500):
					if msg.mentions:
						await msg.delete()
						position += 1
						if position == amount:
							break
				await ctx.send(f"{ctx.author.mention}, purged {position} mentions", delete_after=5)
				return await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
			finally:
				del self.purge[channel_id]
		phrase = args[0]
		amount = int(args[1])
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 phrases at a time")
		try:
			position = 0
			async for msg in ctx.channel.history(limit=500):
				if phrase.lower() in msg.content.lower():
					if msg.id != ctx.message.id:
						await msg.delete()
						position += 1
						if position == amount:
							break
			await ctx.send(f"{ctx.author.mention}, purged {position} messages", delete_after=5)
			return await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)
		finally:
			del self.purge[channel_id]

	@commands.command(name='kick')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(embed_links=True, kick_members=True)
	async def kick(self, ctx, user:discord.Member, *, reason='unspecified'):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if user.top_role.position >= ctx.guild.me.top_role.position:
			return await ctx.send('I can\'t kick that user ;-;')
		await user.kick(reason=reason)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=0x80b0ff)
		e.set_image(url="attachment://" + os.path.basename(path))
		file = discord.File(path, filename=os.path.basename(path))
		await ctx.send(f'◈ {ctx.message.author.display_name} kicked {user} ◈', file=file, embed=e)
		await ctx.message.delete()
		try: await user.send(f"You have been kicked from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
		except: pass

	@commands.command(name='ban')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def _ban(self, ctx, user:discord.Member, *, reason='unspecified reasons'):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send('That user is above your paygrade, take a seat')
		if user.top_role.position >= ctx.guild.me.top_role.position:
			return await ctx.send('I can\'t ban that user ;-;')
		await ctx.guild.ban(user, reason=reason, delete_message_days=0)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url='attachment://' + os.path.basename(path))
		file = discord.File(path, filename=os.path.basename(path))
		await ctx.send(f'◈ {ctx.author.display_name} banned {user} ◈', file=file, embed=e)
		try: await user.send(f'You\'ve been banned in **{ctx.guild.name}** by **{ctx.author.name}** for {reason}')
		except: pass

	@commands.command(name='softban', aliases=['tempban'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(embed_links=True, manage_messages=True, ban_members=True)
	async def _softban(self, ctx, user: discord.Member, timer='0s', *, reason='unspecified reasons'):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if user.top_role.position >= ctx.guild.me.top_role.position:
			return await ctx.send('I can\'t kick that user ;-;')
		await user.ban(reason=reason)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		file = discord.File(path, filename=os.path.basename(path))
		e = discord.Embed(color=colors.fate())
		e.set_image(url='attachment://' + os.path.basename(path))
		await ctx.send(f'◈ {ctx.author.display_name} banned {user} ◈', file=file, embed=e)
		await ctx.message.delete()
		timer, time = self.convert_arg_to_timer(timer)
		try: await user.send(f'You\'ve been banned from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}` for {time}')
		except: pass
		if not isinstance(timer, float):
			return await ctx.send('Invalid character used in timer field\nYou\'ll have to manually unban this user')
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.timers['ban']:
			self.timers['ban'][guild_id] = {}
		now = datetime.now()
		timer_info = {'user': user.id, 'time': str(now), 'end_time': str(now + timedelta(seconds=timer))}
		self.timers['ban'][guild_id][user_id] = timer_info
		self.save_json()
		await asyncio.sleep(timer)
		if user_id in self.timers['ban'][guild_id]:
			try: await user.unban(reason='softban')
			except Exception as e: await ctx.send(f'Failed to unban {user.name}: {e}')
			else: await ctx.send(f'**Unbanned {user}**')
			del self.timers['ban'][guild_id][user_id]
			self.save_json()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_nicknames=True)
	@commands.bot_has_permissions(manage_nicknames=True)
	async def nick(self, ctx, user, *, nick=''):
		user = self.get_user(ctx, user)
		if not user:
			return await ctx.send('User not found')
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send('That user is above your paygrade, take a seat')
		if user.top_role.position >= ctx.guild.me.top_role.position:
			return await ctx.send('I can\'t edit that users nick ;-;')
		await user.edit(nick=nick)
		await ctx.message.add_reaction('👍')

	@commands.command(name="massnick")
	@commands.cooldown(1, 10, commands.BucketType.guild)
	@commands.guild_only()
	@commands.has_permissions(manage_nicknames=True)
	@commands.bot_has_permissions(manage_nicknames=True)
	async def _massnick(self, ctx, *, nick=None):
		guild_id = str(ctx.guild.id)
		if guild_id in self.massnick:
			if self.massnick[guild_id] is True:
				return await ctx.send('Please wait until the previous mass-nick is complete')
		if not nick:
			nick = ''
		self.massnick[guild_id] = True
		await ctx.message.add_reaction('🖍')
		count = 0
		for member in ctx.guild.members:
			try:
				await member.edit(nick=nick)
				count += 1
				await asyncio.sleep(0.25)
			except:
				pass
		self.massnick[guild_id] = False
		await ctx.send(f'Changed nicks for {count} users')

	@commands.command(name='role')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def role(self, ctx, user:commands.clean_content, role:commands.clean_content):
		user_name = str(user).lower().replace('@', '')
		user = None
		for member in ctx.guild.members:
			if user_name in member.name.lower():
				user = member
				break
		if not user:
			return await ctx.send('User not found')
		role_name = str(role).lower().replace('@', '')
		role_name.replace('+', '').replace('-', '')
		role = None
		for guild_role in ctx.guild.roles:
			if role_name in guild_role.name.lower():
				role = guild_role
				break
		if not role:
			return await ctx.send('Role not fount')
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send('This user is above your paygrade, take a seat')
		if role.position >= ctx.author.top_role.position:
			return await ctx.send('This role is above your paygrade, take a seat')
		if role in user.roles:
			await user.remove_roles(role)
			msg = f'Removed **{role.name}** from @{user.name}'
		else:
			await user.add_roles(role)
			msg = f'Gave **{role.name}** to **@{user.name}**'
		await ctx.send(msg)

	@commands.command(name="massrole")
	@commands.cooldown(1, 25, commands.BucketType.guild)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def massrole(self, ctx, role: commands.clean_content):
		target_name = str(role).lower().replace('@', '')
		role = None
		for guild_role in ctx.guild.roles:
			if target_name in guild_role.name.lower():
				role = guild_role
				break
		if not role:
			await ctx.send("Role not found")
		await ctx.message.add_reaction("🖍")
		for member in ctx.guild.members:
			bot = ctx.guild.get_member(self.bot.user.id)
			if member.top_role.position < bot.top_role.position:
				await member.add_roles(role)
				await asyncio.sleep(1)
		await ctx.message.add_reaction("🏁")

	@commands.command(name="vcmute")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def vcmute(self, ctx, member: discord.Member):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		await member.edit(mute=True)
		await ctx.send(f'Muted {member.display_name} 👍')

	@commands.command(name="vcunmute")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	async def vcunmute(self, ctx, member: discord.Member):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		await member.edit(mute=False)
		await ctx.send(f'Unmuted {member.display_name} 👍')

	@commands.command(name="mute", description="Blocks a user from sending messages")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def mute(self, ctx, user: discord.Member=None, timer=None):
		async with ctx.typing():
			if not user:
				return await ctx.send("**Format:** `.mute {@user} {timer: 2m, 2h, or 2d}`")
			if user.top_role.position >= ctx.author.top_role.position:
				return await ctx.send("That user is above your paygrade, take a seat")
			guild_id = str(ctx.guild.id)
			user_id = str(user.id)
			mute_role = None
			for role in ctx.guild.roles:
				if role.name.lower() == "muted":
					mute_role = role
					for channel in ctx.guild.text_channels:
						if mute_role not in channel.overwrites:
							await channel.set_permissions(mute_role, send_messages=False)
							await asyncio.sleep(0.5)
					for channel in ctx.guild.voice_channels:
						if mute_role not in channel.overwrites:
							await channel.set_permissions(mute_role, speak=False)
							await asyncio.sleep(0.5)
			if not mute_role:
				bot = discord.utils.get(ctx.guild.members, id=self.bot.user.id)
				perms = [perm for perm, value in bot.guild_permissions if value]
				if "manage_channels" not in perms:
					return await ctx.send("No muted role found, and I'm missing manage_channel permissions to set one up")
				mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
				for channel in ctx.guild.text_channels:
					await channel.set_permissions(mute_role, send_messages=False)
					await asyncio.sleep(0.5)
				for channel in ctx.guild.voice_channels:
					await channel.set_permissions(mute_role, speak=False)
					await asyncio.sleep(0.5)
			if mute_role in user.roles:
				return await ctx.send(f"{user.display_name} is already muted")
			if not timer:
				if guild_id not in self.roles:
					self.roles[guild_id] = {}
				self.roles[guild_id][user_id] = []
				for role in user.roles:
					try:
						await user.remove_roles(role)
						self.roles[guild_id][user_id].append(role.id)
						await asyncio.sleep(0.5)
					except:
						pass
				self.save_json()
				await user.add_roles(mute_role)
				await ctx.send(f"Muted {user.display_name}")
				return await ctx.message.add_reaction("👍")
			for x in list(timer):
				if x not in "1234567890dhms":
					return await ctx.send("Invalid character used in timer field")
			timer, time = self.convert_arg_to_timer(timer)
			if not isinstance(timer, float):
				return await ctx.send("Invalid character used in timer field")
			removed_roles = []
			for role in user.roles:
				try:
					await user.remove_roles(role)
					removed_roles.append(role.id)
					await asyncio.sleep(0.5)
				except:
					pass
			await user.add_roles(mute_role)
			if timer is None:
				return await ctx.send(f"**Muted:** {user.name}")
			await ctx.send(f"Muted **{user.name}** for {time}")
		timer_info = {
			'channel': ctx.channel.id,
			'user': user.id,
			'end_time': str(datetime.now() + timedelta(seconds=round(timer))),
			'mute_role': mute_role.id,
			'roles': removed_roles}
		if guild_id not in self.timers['mute']:
			self.timers['mute'][guild_id] = {}
		self.timers['mute'][guild_id][user_id] = timer_info
		self.save_json()
		await asyncio.sleep(timer)
		if user_id in self.timers['mute'][guild_id]:
			if mute_role in user.roles:
				await user.remove_roles(mute_role)
				await ctx.send(f"**Unmuted:** {user.name}")
			for role_id in removed_roles:
				role = ctx.guild.get_role(role_id)
				if role not in user.roles:
					await user.add_roles(role)
					await asyncio.sleep(0.5)
			del self.timers['mute'][guild_id][user_id]
			self.save_json()

	@commands.command(name="unmute", description="Unblocks users from sending messages")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True, manage_channels=True)
	async def unmute(self, ctx, user: discord.Member=None):
		if user is None:
			return await ctx.send("**Unmute Usage:**\n.unmute {@user}")
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		mute_role = None
		for role in ctx.guild.roles:
			if role.name.lower() == "muted":
				mute_role = role
		if not mute_role:
			mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
			for channel in ctx.guild.text_channels:
				await channel.set_permissions(mute_role, send_messages=False)
			for channel in ctx.guild.voice_channels:
				await channel.set_permissions(mute_role, speak=False)
		if mute_role not in user.roles:
			return await ctx.send(f"{user.display_name} is not muted")
		await user.remove_roles(mute_role)
		if guild_id in self.roles:
			if user_id in self.roles:
				for role_id in self.roles[guild_id][user_id]:
					role = ctx.guild.get_role(role_id)
					if role not in user.roles:
						await user.add_roles(role)
						await asyncio.sleep(0.5)
				del self.roles[guild_id][user_id]
				self.save_json()
		if guild_id in self.timers['mute']:
			if user_id in self.timers['mute'][guild_id]:
				dat = self.timers['mute'][guild_id][user_id]
				channel = self.bot.get_channel(dat['channel'])  # type: discord.TextChannel
				removed_roles = dat['roles']  # type: list
				for role_id in removed_roles:
					role = channel.guild.get_role(role_id)
					if role not in user.roles:
						await user.add_roles(channel.guild.get_role(role_id))
						await asyncio.sleep(0.5)
				del self.timers['mute'][guild_id][user_id]
				self.save_json()
		await ctx.send(f"Unmuted {user.name}")

	@commands.command(name="warn")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(manage_roles=True)
	async def _warn(self, ctx, user, *, reason=None):
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send("User not found")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			self.mods[guild_id] = []
		if user.id not in self.mods[guild_id]:
			perms = list(perm for perm, value in ctx.author.guild_permissions)
			if "manage_guild" not in perms:
				if "manage_messages" not in perms:
					return await ctx.send("You are missing manage server "
					    "or manage messages permission(s) to run this command")
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if user.id == self.bot.user.id:
			return await ctx.send('nO')
		if not reason:
			reason = "unspecified"
		user_id = str(user.id)
		punishments = ['None', 'None', 'Mute', 'Kick', 'Softban', 'Ban']
		config = self.bot.get_config  # type: dict
		if guild_id in config['warns']['punishments']:
			punishments = config['warns']['punishments'][guild_id]
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = []
		if not isinstance(self.warns[guild_id][user_id], list):
			self.warns[guild_id][user_id] = []
		self.warns[guild_id][user_id].append([reason, str(datetime.now())])
		warns = 0
		for reason, time in self.warns[guild_id][user_id]:
			time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
			if (datetime.now() - time).days > 30:
				if guild_id in config['warns']['expire']:
					index = self.warns[guild_id][user_id].index([reason, time])
					self.warns[guild_id][user_id].pop(index)
					continue
			warns += 1
		self.save_json()
		if warns > len(punishments):
			punishment = punishments[-1:][0]
		else:
			punishment = punishments[warns - 1]
		if warns >= len(punishments):
			next_punishment = punishments[-1:][0]
		else:
			next_punishment = punishments[warns]
		e = discord.Embed(color=colors.fate())
		url = self.bot.user.avatar_url
		if user.avatar_url:
			url = user.avatar_url
		e.set_author(name=f'{user.name} has been warned', icon_url=url)
		e.description = f'**Warns:** [`{warns}`] '
		if punishment != 'None':
			e.description += f'**Punishment:** [`{punishment}`]'
		if punishment == 'None' and next_punishment != 'None':
			e.description += f'**Next Punishment:** [`{next_punishment}`]'
		else:
			if punishment == 'None' and next_punishment == 'None':
				e.description += f'**Reason:** [`{reason}`]'
			if next_punishment != 'None':
				e.description += f'\n**Next Punishment:** [`{next_punishment}`]'
		if punishment != 'None' and next_punishment != 'None':
			e.add_field(name='Reason', value=reason, inline=False)
		await ctx.send(embed=e)
		try:
			await user.send(f"You've been warned in **{ctx.guild.name}** for `{reason}`")
		except:
			pass
		if punishment == 'Mute':
			mute_role = None
			for role in ctx.guild.roles:
				if role.name.lower() == "muted":
					mute_role = role
			if not mute_role:
				bot = discord.utils.get(ctx.guild.members, id=self.bot.user.id)
				perms = list(perm for perm, value in bot.guild_permissions if value)
				if "manage_channels" not in perms:
					return await ctx.send("No muted role found, and I'm missing manage_channel permissions to set one up")
				mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
				for channel in ctx.guild.text_channels:
					await channel.set_permissions(mute_role, send_messages=False)
				for channel in ctx.guild.voice_channels:
					await channel.set_permissions(mute_role, speak=False)
			if mute_role in user.roles:
				return await ctx.send(f"{user.display_name} is already muted")
			user_roles = []
			for role in user.roles:
				try:
					await user.remove_roles(role)
					user_roles.append(role.id)
					await asyncio.sleep(0.5)
				except:
					pass
			await user.add_roles(mute_role)
			timer_info = {
				'action': 'mute',
				'channel': ctx.channel.id,
				'user': user.id,
				'end_time': str(datetime.now() + timedelta(seconds=7200)),
				'mute_role': mute_role.id,
				'roles': user_roles}
			if guild_id not in self.timers:
				self.timers[guild_id] = {}
			if user_id not in self.timers[guild_id]:
				self.timers[guild_id][user_id] = []
			self.timers[guild_id][user_id].append(timer_info)
			self.save_json()
			await asyncio.sleep(7200)
			if mute_role in user.roles:
				await user.remove_roles(mute_role)
				await ctx.send(f"**Unmuted:** {user.name}")
			del self.timers[user_id]
			self.save_json()
		if punishment == 'Kick':
			try:
				await ctx.guild.kick(user, reason='Reached Sufficient Warns')
			except:
				await ctx.send('Failed to kick that user')
		if punishment == 'Softban':
			try:
				await ctx.guild.kick(user, reason='Softban - Reached Sufficient Warns')
				await ctx.guild.unban(user, reason='Softban')
			except:
				await ctx.send('Failed to softban that user')
		if punishment == 'Ban':
			try:
				await ctx.guild.ban(user, reason='Reached Sufficient Warns')
			except:
				await ctx.send('Failed to ban that user')

	@commands.command(name='removewarn', aliases=['delwarn'])
	async def remove_warns(self, ctx, user, *, reason):
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send("User not found")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			self.mods[guild_id] = []
		if user.id not in self.mods[guild_id]:
			perms = list(perm for perm, value in ctx.author.guild_permissions)
			if "manage_guild" not in perms:
				if "manage_messages" not in perms:
					return await ctx.send("You are missing manage server "
						"or manage messages permission(s) to run this command")
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			return await ctx.send('This guild has no warns')
		if user_id not in self.warns[guild_id]:
			return await ctx.send('That user doesn\'t have any warns')
		warns = self.warns[guild_id][user_id]
		for warn_reason, time in warns:
			if reason.lower() in warn_reason.lower():
				e = discord.Embed(color=colors.fate())
				e.description = warn_reason
				msg = await ctx.send(embed=e)
				await msg.add_reaction('✔')
				await asyncio.sleep(0.5)
				await msg.add_reaction('❌')
				def check(reaction, user):
					return user == ctx.author and str(reaction.emoji) in ['✔', '❌']
				try:
					reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
				except asyncio.TimeoutError:
					return await ctx.send('Timeout Error')
				else:
					if str(reaction.emoji) == '✔':
						index = warns.index([warn_reason, time])
						self.warns[guild_id][user_id].pop(index)
						await ctx.message.delete()
						return await msg.delete()
					else:
						await msg.delete()

	@commands.command(name="clearwarns")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	async def clearwarns(self, ctx, *, user):
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send("User not found")
		guild_id = str(ctx.guild.id)
		if guild_id not in self.mods:
			self.mods[guild_id] = []
		if user.id not in self.mods[guild_id]:
			perms = list(perm for perm, value in ctx.author.guild_permissions)
			if "manage_guild" not in perms:
				if "manage_messages" not in perms:
					return await ctx.send("You are missing manage server "
						"or manage messages permission(s) to run this command")
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		self.warns[guild_id][user_id] = []
		await ctx.send(f"Cleared {user.name}'s warn count")
		self.save_json()

	@commands.command(name="warns")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	async def _warns(self, ctx, *, user=None):
		if not user:
			user = ctx.author
		else:
			user = self.get_user(ctx, user)
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = []
		warns = 0
		reasons = ''
		for reason, time in self.warns[guild_id][user_id]:
			time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
			if (datetime.now() - time).days > 30:
				if 'expire' in self.warns[guild_id]:
					if self.warns[guild_id]['expire'] == 'True':
						index = self.warns[guild_id][user_id].index([reason, time])
						self.warns[guild_id][user_id].pop(index)
						continue
			warns += 1
			reasons += f'\n• `{reason}`'
		e = discord.Embed(color=colors.fate())
		url = self.bot.user.avatar_url
		if user.avatar_url:
			url = user.avatar_url
		e.set_author(name=f'{user.name}\'s Warns', icon_url=url)
		e.description = f'**Total Warns:** [`{warns}`]' + reasons
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Mod(bot))
