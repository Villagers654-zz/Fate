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
		self.config = {}
		if isfile("./data/userdata/mod.json"):
			with open("./data/userdata/mod.json", "r") as infile:
				dat = json.load(infile)
				if "warns" in dat:
					self.warns = dat["warns"]
				if "roles" in dat:
					self.roles = dat["roles"]
				if "timers" in dat:
					self.timers = dat["timers"]
				if "warn_config" in dat:
					self.config = dat["warn_config"]

	def save_json(self):
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({"warns": self.warns, "roles": self.roles, "timers": self.timers, 'warn_config': self.config}, outfile, ensure_ascii=False)

	def save_config(self, config):
		with open('./data/config.json', 'w') as f:
			json.dump(config, f, ensure_ascii=False)

	async def start_timer(self, user_id):
		if user_id in self.timers:
			action = self.timers[user_id]['action']
			if action == 'mute':
				channel = self.bot.get_channel(self.timers[user_id]['channel'])  # type: discord.TextChannel
				user = channel.guild.get_member(self.timers[user_id]['user'])  # type: discord.Member
				if not user:
					del self.timers[user_id]
					return
				end_time = datetime.strptime(self.timers[user_id]['end_time'], "%Y-%m-%d %H:%M:%S.%f")  # type: datetime.now()
				mute_role = channel.guild.get_role(self.timers[user_id]['mute_role'])  # type: discord.Role
				removed_roles = self.timers[user_id]['roles']  # type: list
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
				del self.timers[user_id]
				self.save_json()

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
		return None

	@commands.command(name='getuser')
	async def getuser(self, ctx, user):
		before = monotonic()
		user = self.get_user(ctx, user)
		ping = str((monotonic() - before) * 1000)
		ping = ping[:ping.find('.')]
		await ctx.send(f'**{user}:** `{ping}ms`')

	@commands.Cog.listener()
	async def on_ready(self):
		for user_id in list(self.timers.keys()):
			await self.bot.get_channel(config.server("log")).send(f"Timer: {user_id}", delete_after=3)

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if m.channel.id == config.server("log"):
				if m.content.startswith("Timer:"):
					user_id = m.content.replace("Timer: ", "")
					await self.start_timer(user_id)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.warns:
			del self.warns[guild_id]
			self.save_json()
		if guild_id in self.roles:
			del self.warns[guild_id]
			self.save_json()
		if guild_id in self.timers:
			del self.timers[guild_id]
			self.save_json()
		config = self.bot.get_config
		if guild_id in config['restricted']:
			del config['restricted'][guild_id]
			self.save_config(config)

	@commands.command(name="cleartimers")
	@commands.check(checks.luck)
	async def cleartimers(self, ctx):
		keys = self.timers.keys()
		for key in keys:
			del self.timers[key]
		await ctx.message.add_reaction("👍")

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

	@commands.command(name="delete")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def delete(self, ctx):
		try:
			c = 0
			async for msg in ctx.channel.history(limit=3):
				if c == 1:
					await msg.delete()
					await ctx.message.delete()
					break;
				c += 1
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command(name="purge")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge(self, ctx, amount: int):
		if amount > 1000:
			return await ctx.send("You cannot purge more than 1000 messages at a time")
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		try:
			await ctx.message.channel.purge(before=ctx.message, limit=amount)
			await ctx.message.delete()
			await ctx.send(f'{ctx.author.name}, successfully purged {amount} messages', delete_after=5)
		except Exception as e:
			await ctx.send(e)
		del self.purge[channel_id]

	@commands.command(name="purge_user", description="Usage: `.purge_user @user amount`")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_user(self, ctx, user: discord.Member, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 user specific at a time")
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		position = 0
		try:
			async for msg in ctx.channel.history(limit=1000):
				if msg.author.id is user.id:
					await msg.delete()
					position += 1
					if position == amount:
						break
			await ctx.send(f"{ctx.author.display_name} purged {amount} images", delete_after=5)
			return await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)
		finally:
			del self.purge[channel_id]
		await ctx.send(f'{ctx.author.display_name} purged {position} messages')

	@commands.command(name="purge_images")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_images(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 images at a time")
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		position = 0
		try:
			async for msg in ctx.channel.history(limit=1000):
				if msg.attachments:
					await msg.delete()
					position += 1
					if position == amount:
						break
			await ctx.send(f"{ctx.author.display_name}, successfully purged {amount} images", delete_after=5)
			return await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)
		finally:
			del self.purge[channel_id]
		await ctx.send(f'{ctx.author.display_name} purged {position} messages')

	@commands.command(name="purge_embeds")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_embeds(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 embeds at a time")
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		position = 0
		try:
			async for msg in ctx.channel.history(limit=1000):
				if msg.embeds:
					await msg.delete()
					position += 1
					if position == amount:
						break
			await ctx.send(f"{ctx.author.display_name}, successfully purged {amount} embeds", delete_after=5)
			return await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)
		finally:
			del self.purge[channel_id]
		await ctx.send(f'{ctx.author.display_name} purged {position} messages')

	@commands.command(name="purge_bots")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_bots(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 bot messages at a time")
		channel_id = str(ctx.channel.id)
		if channel_id in self.purge:
			return await ctx.send('I\'m already purging')
		else:
			self.purge[channel_id] = True
		position = 0
		try:
			async for msg in ctx.channel.history(limit=1000):
				if msg.author.bot:
					await msg.delete()
					position += 1
					if position == amount:
						break
			await ctx.send(f"{ctx.author.display_name}, successfully purged {amount} bot messages", delete_after=5)
			return await ctx.message.delete()
		except Exception as e:
			await ctx.send(e)
		finally:
			del self.purge[channel_id]
		await ctx.send(f'{ctx.author.display_name} purged {position} messages')

	@commands.command(name="kick")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(kick_members=True)
	async def kick(self, ctx, user:discord.Member, *, reason:str=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		bot = ctx.guild.get_member(self.bot.user.id)
		if user.top_role.position >= bot.top_role.position:
			return await ctx.send('I can\'t kick that user ;-;')
		await ctx.guild.kick(user, reason=reason)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=0x80b0ff)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ {} kicked {} ◈'.format(ctx.message.author.display_name, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()
		if reason is None:
			pass
		else:
			try:
				await user.send(f"You have been kicked from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
			except Exception as e:
				pass

	@commands.command(name="ban")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def _ban(self, ctx, user:discord.Member, *, reason=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		bot = ctx.guild.get_member(self.bot.user.id)
		if user.top_role.position >= bot.top_role.position:
			return await ctx.send('I can\'t ban that user ;-;')
		await ctx.guild.ban(user, reason=reason, delete_message_days=0)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ {} banned {} ◈'.format(ctx.message.author.display_name, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()
		if reason is None:
			pass
		else:
			try:
				await user.send(f"You have been banned from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
			except:
				pass

	@commands.command(name="softban")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def _softban(self, ctx, user:discord.Member, *, reason=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		bot = ctx.guild.get_member(self.bot.user.id)
		if user.top_role.position >= bot.top_role.position:
			return await ctx.send('I can\'t kick that user ;-;')
		await ctx.guild.ban(user, reason=reason, delete_message_days=0)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ {} banned {} ◈'.format(ctx.message.author.display_name, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()
		if reason is None:
			pass
		else:
			try:
				await user.send(f"You have been soft-banned from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
			except:
				pass
		await user.unban(reason="softban")

	@commands.command(name="bans")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def _bans(self, ctx):
		bans = await ctx.guild.bans()
		for ban in bans:
			await ctx.send(f"{ban[0]}, {ban[1].id}")

	@commands.command(name="pin")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def pin(self, ctx):
		c = 0
		async for msg in ctx.channel.history(limit=3):
			if c == 1:
				await msg.pin()
				await ctx.message.delete()
				break;
			c += 1

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_nicknames=True)
	@commands.bot_has_permissions(manage_nicknames=True)
	async def nick(self, ctx, member: discord.Member, *, nick=None):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if nick is None:
			nick = ""
		await member.edit(nick=nick)
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
				return await ctx.send("Please wait until the previous mass-nick is done")
		failed = ""
		if nick is None:
			nick = ""
		self.massnick[guild_id] = True
		await ctx.message.add_reaction('🖍')
		for member in ctx.guild.members:
			try:
				await member.edit(nick=nick)
				await asyncio.sleep(0.25)
			except Exception as e:
				if failed == "":
					failed = f"**Failed to change the nicks of:**\n{member.name}"
				else:
					failed += f", {member.name}"
		self.massnick[guild_id] = False
		await ctx.message.add_reaction('🏁')
		if failed == "":
			pass
		else:
			await ctx.send(failed)

	@commands.command(name='role')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def role(self, ctx, user:commands.clean_content, role:commands.clean_content):
		user_name = str(user).lower().replace('@', '')
		user = None  # type: discord.Member
		for member in ctx.guild.members:
			if user_name in member.name.lower():
				user = member
				break
		if not user:
			return await ctx.send('User not found')
		role_name = str(role).lower().replace('@', '')
		role_name.replace('+', '').replace('-', '')
		role = None  # type: discord.Role
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
		role = None  # type: discord.Role
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
			mute_role = None  # type: discord.Role
			for role in ctx.guild.roles:
				if role.name.lower() == "muted":
					mute_role = role
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
			time = timer.replace("m", " minutes").replace("1 minutes", "1 minute")
			time = time.replace("h", " hours").replace("1 hours", "1 hour")
			time = time.replace("d", " days").replace("1 days", "1 day")
			if "d" in str(timer):
				timer = float(timer.replace("d", "")) * 60 * 60 * 24
			if "h" in str(timer):
				timer = float(timer.replace("h", "")) * 60 * 60
			if "m" in str(timer):
				timer = float(timer.replace("m", "")) * 60
			if "s" in str(timer):
				timer = float(timer.replace("s", ""))
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
		self.timers[user_id] = {
			'action': 'mute',
			'channel': ctx.channel.id,
			'user': user.id,
			'end_time': str(datetime.now() + timedelta(seconds=timer)),
			'mute_role': mute_role.id,
			'roles': removed_roles}
		self.save_json()
		await asyncio.sleep(timer)
		if user_id in self.timers:
			if mute_role in user.roles:
				await user.remove_roles(mute_role)
				await ctx.send(f"**Unmuted:** {user.name}")
			for role_id in removed_roles:
				role = ctx.guild.get_role(role_id)
				if role not in user.roles:
					await user.add_roles(role)
					await asyncio.sleep(0.5)
			del self.timers[user_id]
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
		mute_role = None  # type: discord.Role
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
		if user_id in self.timers:
			channel = self.bot.get_channel(self.timers[user_id]['channel'])  # type: discord.TextChannel
			removed_roles = self.timers[user_id]['roles']  # type: list
			for role_id in removed_roles:
				role = channel.guild.get_role(role_id)
				if role not in user.roles:
					await user.add_roles(channel.guild.get_role(role_id))
					await asyncio.sleep(0.5)
			del self.timers[user_id]
			self.save_json()
		await ctx.send(f"Unmuted {user.name}")

	@commands.command(name="warn")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(manage_roles=True)
	async def _warn(self, ctx, user, *, reason=None):
		if ctx.invoked_subcommand:
			return
		perms = list(perm for perm, value in ctx.author.guild_permissions)
		if "manage_guild" not in perms:
			if "manage_messages" not in perms:
				return await ctx.send("You are missing manage server "
				    "or manage messages permission(s) to run this command")
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send("User not found")
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if user.id == self.bot.user.id:
			return await ctx.send('nO')
		if not reason:
			reason = "unspecified"
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		punishments = ['None', 'Mute', 'Kick', 'Softban', 'Ban']
		if guild_id in self.config:
			if 'punishments' in self.config[guild_id]:
				punishments = self.config[guild_id]['punishments']
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
				if 'expire' in self.warns[guild_id]:
					if self.warns[guild_id]['expire'] == 'True':
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
				e.description += f'\n**Next Punishment:** [`{next_punishment}``]'
		if punishment != 'None' and next_punishment != 'None':
			e.add_field(name='Reason', value=reason, inline=False)
		await ctx.send(embed=e)
		try:
			await user.send(f"You've been warned in **{ctx.guild.name}** for `{reason}`")
		except:
			pass
		if punishment == 'Mute':
			mute_role = None  # type: discord.Role
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
			self.timers[user_id] = {
				'action': 'mute',
				'channel': ctx.channel.id,
				'user': user.id,
				'end_time': str(datetime.now() + timedelta(seconds=7200)),
				'mute_role': mute_role.id,
				'roles': user_roles}
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

	@commands.group(name='editconfig')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def _edit_config(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.description = '.editconfig warns'
			await ctx.send(embed=e)

	@_edit_config.command(name='warns')
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _warns(self, ctx):
		guild_id = str(ctx.guild.id)
		emojis = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣']
		async def wait_for_reaction():
			def check(reaction, user):
				return user == ctx.author
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except asyncio.TimeoutError:
				await ctx.send('Timeout Error')
			else:
				return str(reaction.emoji)
		def emoji(index):
			return emojis[index - 1]
		def default():
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Warn Config', icon_url=ctx.author.avatar_url)
			e.description = \
				f'{emoji(1)} : View Config\n' \
				f'{emoji(2)} : Edit Config\n' \
				f'{emoji(3)} : Cancel\n'
			return e
		complete = False
		msg = await ctx.send(embed=default())
		while not complete:
			await msg.edit(embed=default())
			await msg.clear_reactions()
			await msg.add_reaction(emoji(1))
			await msg.add_reaction(emoji(2))
			await msg.add_reaction(emoji(3))
			reaction = await wait_for_reaction()
			if reaction == emoji(1):
				await msg.clear_reactions()
				if guild_id not in self.config:
					self.config[guild_id] = {}
				dat = self.config[guild_id]
				expiring = False
				if 'expire' in dat:
					expiring = True
				punishments = 'None'
				if 'punishments' in dat:
					punishments = ''
					index = 1
					for punishment in dat['punishments']:
						punishments += f'**#{index}. `{punishment}`**\n'
				e = discord.Embed(color=colors.fate())
				e.set_author(name='Warn Config', icon_url=ctx.author.avatar_url)
				e.description = f'**Warns Expire: {expiring}\nCustom Punishments:**\n{punishments}'
				await msg.edit(embed=e)
				await msg.add_reaction('⏹')
				await msg.add_reaction('🔄')
				reaction = await wait_for_reaction()
				if reaction == '⏹':
					break
				if reaction == '🔄':
					continue
			if reaction == emoji(2):
				await msg.clear_reactions()
				e = discord.Embed(color=colors.fate())
				e.description = 'Should warns expire after a month?'
				await msg.edit(embed=e)
				await msg.add_reaction('✔')
				await msg.add_reaction('❌')
				reaction = await wait_for_reaction()
				if reaction == '✔':
					if guild_id not in self.config:
						self.config[guild_id] = {}
					self.config[guild_id]['expire'] = 'True'
				await msg.clear_reactions()
				e = discord.Embed(color=colors.fate())
				e.description = 'Set custom punishments?'
				await msg.edit(embed=e)
				await msg.add_reaction('✔')
				await msg.add_reaction('❌')
				reaction = await wait_for_reaction()
				if reaction == '❌':
					break
				else:
					await msg.clear_reactions()
					punishments = []
					def dump():
						if guild_id not in self.config:
							self.config[guild_id] = {}
						self.config[guild_id]['punishments'] = punishments
					def pos(index):
						positions = ['1st', '2nd', '3rd', '4th', '4th', '6th', '7th', '8th']
						return positions[index - 1]
					index = 1
					finished = False
					while not finished:
						if len(punishments) > 7:
							dump()
							break
						e = discord.Embed(color=colors.fate())
						e.description = f'**Punishments: {punishments}**\n\n' \
							f'Set the {pos(index)} punishment:\n' \
							f'1⃣: None\n2⃣ : Mute\n3⃣ : Kick\n' \
							f'4⃣ : Softban\n5⃣ : Ban\n'
						index += 1
						await msg.edit(embed=e)
						for emoji in emojis:
							await msg.add_reaction(emoji)
						await msg.add_reaction('✔')
						reaction = await wait_for_reaction()
						if reaction == '✔':
							dump()
							break
						options = ['None', 'Mute', 'Kick', 'Softban', 'Ban']
						reaction_index = emojis.index(reaction)
						punishments.append(options[reaction_index])
			else:
				if reaction == emoji(3):
					break
			break
		await ctx.message.delete()
		await msg.delete()
		self.save_json()

	@commands.command(name="clearwarns")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	async def clearwarns(self, ctx, *, user=None):
		perms = list(perm for perm, value in ctx.author.guild_permissions)
		if "manage_guild" not in perms:
			if "manage_messages" not in perms:
				return await ctx.send("You are missing manage server "
				    "or manage messages permission(s) to run this command")
		user = self.get_user(ctx, user)
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
