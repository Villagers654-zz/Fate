from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import random
import json
import os

class Mod:
	def __init__(self, bot):
		self.bot = bot
		self.purge = {}
		self.massnick = {}
		self.warns = {}
		if isfile("./data/userdata/mod.json"):
			with open("./data/userdata/mod.json", "r") as infile:
				dat = json.load(infile)
				if "warns" in dat:
					self.warns = dat["warns"]

	@commands.command(name="delete", aliases=["d"])
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
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
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge(self, ctx, amount: int):
		if amount > 1000:
			return await ctx.send("You cannot purge more than 1000 messages at a time")
		channel_id = str(ctx.channel.id)
		if channel_id not in self.purge:
			self.purge[channel_id] = True
			await ctx.message.channel.purge(before=ctx.message, limit=amount)
			await ctx.message.delete()
			self.purge[channel_id] = False
			return await ctx.send("{}, successfully purged {} messages".format(ctx.author.name, amount), delete_after=5)
		if self.purge[channel_id] is True:
			return await ctx.send("I'm already purging..")
		if self.purge[channel_id] is False:
			self.purge[channel_id] = True
			await ctx.message.channel.purge(before=ctx.message, limit=amount)
			await ctx.message.delete()
			await ctx.send("{}, successfully purged {} messages".format(ctx.author.name, amount), delete_after=5)
			self.purge[channel_id] = False

	@commands.command(name="purge_user")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge_user(self, ctx, user: discord.Member, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 user specific at a time")
		channel_id = str(ctx.channel.id)
		current_position = 0
		if channel_id not in self.purge:
			self.purge[channel_id] = True
			async for msg in ctx.channel.history(limit=10000):
				if msg.author.id is user.id:
					await msg.delete()
					current_position += 1
					if current_position >= amount:
						del self.purge[channel_id]
						await ctx.send("{}, successfully purged {} images".format(ctx.author.name, amount), delete_after=5)
						return await ctx.message.delete()
		if channel_id in self.purge:
			return await ctx.send("I'm already purging..")

	@commands.command(name="purge_images")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge_images(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 images at a time")
		channel_id = str(ctx.channel.id)
		current_position = 0
		if channel_id not in self.purge:
			self.purge[channel_id] = True
			async for msg in ctx.channel.history(limit=10000):
				if msg.attachments:
					await msg.delete()
					current_position += 1
					if current_position == 250:
						if current_position >= amount:
							del self.purge[channel_id]
							await ctx.send("{}, successfully purged {} images".format(ctx.author.name, amount), delete_after=5)
							return await ctx.message.delete()
		if channel_id in self.purge:
			return await ctx.send("I'm already purging..")

	@commands.command(name="purge_embeds")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge_embeds(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 embeds at a time")
		channel_id = str(ctx.channel.id)
		current_position = 0
		if channel_id not in self.purge:
			self.purge[channel_id] = True
			async for msg in ctx.channel.history(limit=10000):
				if msg.embeds:
					await msg.delete()
					current_position += 1
					if current_position >= amount:
						del self.purge[channel_id]
						await ctx.send("{}, successfully purged {} embeds".format(ctx.author.name, amount), delete_after=5)
						return await ctx.message.delete()
		if channel_id in self.purge:
			return await ctx.send("I'm already purging..")

	@commands.command(name="purge_bots")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _purge_bots(self, ctx, amount: int):
		if amount > 250:
			return await ctx.send("You cannot purge more than 250 bot messages at a time")
		channel_id = str(ctx.channel.id)
		current_position = 0
		if channel_id not in self.purge:
			self.purge[channel_id] = True
			async for msg in ctx.channel.history(limit=10000):
				if msg.author.bot:
					await msg.delete()
					current_position += 1
					if current_position == 250:
						if current_position >= amount:
							del self.purge[channel_id]
							await ctx.send("{}, successfully purged {} bot messages".format(ctx.author.name, amount), delete_after=5)
							return await ctx.message.delete()
		if channel_id in self.purge:
			return await ctx.send("I'm already purging..")

	@commands.command(name="kick", aliases=["k"])
	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(kick_members=True)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def kick(self, ctx, user:discord.Member, *, reason:str=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
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

	@commands.command(name="ban", aliases=["b"])
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def _ban(self, ctx, user:discord.Member, *, reason=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
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
			except Exception as e:
				pass

	@commands.command(name="softban")
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def _softban(self, ctx, user:discord.Member, *, reason=None):
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
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
			except Exception as e:
				pass
		await user.unban(reason="softban")

	@commands.command(name="bans")
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	@commands.cooldown(1, 5, commands.BucketType.guild)
	async def _bans(self, ctx):
		bans = await ctx.guild.bans()
		for ban in bans:
			await ctx.send(f"{ban[0]}, {ban[1].id}")

	@commands.command(name="pin", aliases=["p"])
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def pin(self, ctx):
		c = 0
		async for msg in ctx.channel.history(limit=3):
			if c == 1:
				await msg.pin()
				await ctx.message.delete()
				break;
			c += 1

	@commands.command()
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
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(administrator=True)
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

	@commands.command(name="addrole")
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def _addrole(self, ctx, arg1: commands.clean_content=None, arg2: commands.clean_content=None):
		if arg2 is not None:
			arg1 = arg1.replace("@", "")
			arg2 = arg2.replace("@", "")
		# giving the author a role
		if arg2 is None:
			for i in ctx.guild.roles:
				if i.name.lower() == arg1.lower():
					for r in ctx.author.roles:
						if i.name == r.name:
							return await ctx.send("You already have this role")
					if i.position >= ctx.author.top_role.position:
						return await ctx.send("This role is above your paygrade, take a seat")
					await ctx.author.add_roles(i)
					return await ctx.send(f"Gave the role **{i.name}** to **{ctx.author.display_name}**")
		# giving a non author the role
		for member in ctx.guild.members:
			if arg1.lower() == member.name.lower():
				for i in ctx.guild.roles:
					if i.name.lower() == arg2.lower():
						if i.name.lower == arg2.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if arg2.lower() in i.name.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if i.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						await member.add_roles(i)
						return await ctx.send(f"Gave the role **{i.name}** to **{member.display_name}**")
				for i in ctx.guild.roles:
					if arg2.lower() in i.name.lower():
						if i.name.lower == arg2.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if arg2.lower() in i.name.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if i.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						await member.add_roles(i)
						return await ctx.send(f"Gave the role **{i.name}** to **{member.display_name}**")
			if arg1.lower() in member.name.lower():
				for i in ctx.guild.roles:
					if i.name.lower() == arg2.lower():
						if i.name.lower == arg2.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if arg2.lower() in i.name.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if i.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						await member.add_roles(i)
						return await ctx.send(f"Gave the role **{i.name}** to **{member.display_name}**")
				for i in ctx.guild.roles:
					if arg2.lower() in i.name.lower():
						if i.name.lower == arg2.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if arg2.lower() in i.name.lower():
							for role in member.roles:
								if arg2 == role.name.lower():
									return await ctx.send("User already has the role")
							for role in member.roles:
								if arg2 in role.name.lower():
									return await ctx.send("User already has the role")
						if i.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						await member.add_roles(i)
						return await ctx.send(f"Gave the role **{i.name}** to **{member.display_name}**")
		await ctx.send("Either the member or role was not found")

	@commands.command(name="removerole")
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def _removerole(self, ctx, arg1: commands.clean_content=None, arg2: commands.clean_content=None):
		if arg2 is not None:
			arg1 = arg1.replace("@", "")
			arg2 = arg2.replace("@", "")
		# removing the role from the author
		if arg2 is None:
			for i in ctx.guild.roles:
				if arg1.lower() == i.name.lower():
					if i.position >= ctx.author.top_role.position:
						return await ctx.send("This role is above your paygrade, take a seat")
					if i not in ctx.author.roles:
						return await ctx.send(f"You don't have the role **{i.name}**")
					await ctx.author.remove_roles(i)
					return await ctx.send(f"Removed the role **{i.name}** from **{ctx.author.display_name}**")
				if arg1.lower() in i.name.lower():
					if i.position >= ctx.author.top_role.position:
						return await ctx.send("This role is above your paygrade, take a seat")
					if i not in ctx.author.roles:
						return await ctx.send(f"You don't have the role **{i.name}**")
					await ctx.author.remove_roles(i)
					return await ctx.send(f"Removed the role **{i.name}** from **{ctx.author.display_name}**")
		# removing the role from a different user
		for member in ctx.guild.members:
			if arg1.lower() == member.name.lower():
				for r in ctx.guild.roles:
					if arg2.lower() == r.name.lower():
						if r.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						if r not in member.roles:
							return await ctx.send(f"**{member.name}** does'nt have the role **{r.name}**")
						await member.remove_roles(r)
						return await ctx.send(f"Removed the role **{r.name}** from **{member.display_name}**")
					if arg2.lower() in r.name.lower():
						if r.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						if r not in member.roles:
							return await ctx.send(f"**{member.name}** does'nt have the role **{r.name}**")
						await member.remove_roles(r)
						return await ctx.send(f"Removed the role **{r.name}** from **{member.display_name}**")
			if arg1.lower() in member.name.lower():
				for r in ctx.guild.roles:
					if arg2.lower() == r.name.lower():
						if r.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						if r not in member.roles:
							return await ctx.send(f"**{member.name}** does'nt have the role **{r.name}**")
						await member.remove_roles(r)
						return await ctx.send(f"Removed the role **{r.name}** from **{member.display_name}**")
					if arg2.lower() in r.name.lower():
						if r.position >= ctx.author.top_role.position:
							return await ctx.send("This role is above your paygrade, take a seat")
						if r not in member.roles:
							return await ctx.send(f"**{member.name}** does'nt have the role **{r.name}**")
						await member.remove_roles(r)
						return await ctx.send(f"Removed the role **{r.name}** from **{member.display_name}**")
		await ctx.send("There was an error finding the user or the role")

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def massrole(self, ctx, role: str):
		role = role.replace("<@&", "").replace(">", "").replace("<@", "").replace("@", "")
		check = False
		for r in ctx.guild.roles:
			if role.lower() == r.name.lower():
				role = r
				check = True
				break
		if check is False:
			for r in ctx.guild.roles:
				if role.lower() in r.name.lower():
					role = r
					check = True
					break
		if check is False:
			await ctx.send("Role not found")
		failed = "**Failed to edit the roles of:**"
		await ctx.message.add_reaction("🖍")
		for member in ctx.guild.members:
			try:
				await member.add_roles(role)
				await asyncio.sleep(0.25)
			except:
				failed += f"\n{member.name}"
		if failed.endswith("**"):
			await ctx.send(failed)
		await ctx.message.add_reaction("🏁")

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def vcmute(self, ctx, member: discord.Member):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		await member.edit(mute=True)
		await ctx.send(f'Muted {member.display_name} 👍')

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def vcunmute(self, ctx, member: discord.Member):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		await member.edit(mute=False)
		await ctx.send(f'Unmuted {member.display_name} 👍')

	@commands.command(name="mute")
	@commands.has_permissions(manage_roles=True)
	async def _mute(self, ctx, member: discord.Member=None, timer=None):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if member is None and timer is None:
			return await ctx.send(
				"**Mute Usage:**\n"
				".mute {user}\n"
				"**timer Usage:**\n"
				"m = minute(s), h = hour(s), d = day(s)\n"
				".mute {user} {number}{m/h/d}")
		role = None
		async with ctx.typing():
			for i in ctx.guild.roles:
				if i.name.lower() == "muted":
					role = i
		if role is None:
			return await ctx.send("this server does not have a muted role")
		if role in member.roles:
			return await ctx.send(f"{member.display_name} is already muted")
		await member.add_roles(role)
		if timer is None:
			return await ctx.send(f"**Muted:** {member.name}")
		r = timer.replace("m", " minutes").replace("1 minutes", "1 minute")
		r = r.replace("h", " hours").replace("1 hours", "1 hour")
		r = r.replace("d", " days").replace("1 days", "1 day")
		await ctx.send(f"Muted **{member.name}** for {r}")
		if "d" in timer:
			timer = float(timer.replace("d", "")) * 60 * 60 * 24
		if "h" in timer:
			timer = float(timer.replace("h", "")) * 60 * 60
		if "m" in timer:
			timer = float(timer.replace("m", "")) * 60
		if "s" in timer:
			timer = float(timer.replace("s", ""))
		await asyncio.sleep(timer)
		if role not in member.roles:
			pass
		else:
			await member.remove_roles(role)
			await ctx.send(f"**Unmuted:** {member.name}")

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def unmute(self, ctx, member: discord.Member=None):
		if member.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		if member is None:
			await ctx.send(
				"**Unmute Usage:**\n"
				".unmute {user}")
		else:
			role = 0
			for i in ctx.guild.roles:
				if i.name.lower() == "muted":
					role = i
			if role is 0:
				await ctx.send("this server does not have a muted role")
			else:
				if role not in member.roles:
					await ctx.send(f"{member.display_name} is not muted")
				else:
					await member.remove_roles(role)
					await ctx.send(f"**Unmuted:** {member.name}")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def warn(self, ctx, user, *, reason):
		if user.startswith("<@"):
			user = user.replace("<@", "")
			user = user.replace(">", "")
			user = user.replace("!", "")
			user = ctx.guild.get_member(eval(user))
		else:
			for member in ctx.guild.members:
				if str(user).lower() in str(member.display_name).lower():
					user_id = member.id
					user = ctx.guild.get_member(user_id)
					break
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		mute = False
		role = None
		try:
			await user.send(f"You have been warned in **{ctx.guild.name}** for `{reason}`")
		except:
			pass
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
			self.warns[guild_id][user_id] = 0
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = 0
		self.warns[guild_id][user_id] += 1
		if self.warns[guild_id][user_id] == 1:
			punishment = "none"
			next_punishment = "none"
		if self.warns[guild_id][user_id] == 2:
			punishment = "none"
			next_punishment = "2 hour mute"
		if self.warns[guild_id][user_id] == 3:
			punishment = "2 hour mute"
			next_punishment = "kick"
			mute = True
		if self.warns[guild_id][user_id] == 4:
			try:
				await ctx.guild.kick(user, reason=reason)
			except:
				await ctx.send("I couldn't kick this user, BUT HOWEVER")
			punishment = "kick"
			next_punishment = "ban"
		if self.warns[guild_id][user_id] >= 5:
			try:
				await ctx.guild.ban(user, reason=reason, delete_message_days=0)
			except:
				await ctx.send("I couldn't ban this user, BUT HOWEVER")
			punishment = "ban"
			next_punishment = "ban"
		await ctx.send(f"**{user.display_name} has been warned.**\n"
		               f"Reason: {reason}\n"
		               f"Warn count: [{self.warns[guild_id][user_id]}]\n"
		               f"Punishment: {punishment}\n"
		               f"Next Punishment: {next_punishment}")
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({"warns": self.warns}, outfile, ensure_ascii=False)
		if mute is True:
			for i in ctx.guild.roles:
				if i.name.lower() == "muted":
					role = i
			if role is None:
				await ctx.send("this server does not have a muted role")
			else:
				if role in user.roles:
					await ctx.send(f"{user.display_name} is already muted")
				else:
					await user.add_roles(role)
				await asyncio.sleep(7200)
				if role not in user.roles:
					pass
				else:
					await user.remove_roles(role)
					await ctx.send(f"**Unmuted:** {user.name}")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def clearwarns(self, ctx, *, user=None):
		if user.startswith("<@"):
			user = user.replace("<@", "")
			user = user.replace(">", "")
			user = user.replace("!", "")
			user = ctx.guild.get_member(eval(user))
		else:
			for member in ctx.guild.members:
				if str(user).lower() in str(member.display_name).lower():
					user_id = member.id
					user = ctx.guild.get_member(user_id)
					break
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = 0
		self.warns[guild_id][user_id] = 0
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({"warns": self.warns}, outfile, ensure_ascii=False)
		await ctx.send(f"Cleared {user.name}'s warn count")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(administrator=True)
	async def setwarns(self, ctx, user, count: int):
		if user.startswith("<@"):
			user = user.replace("<@", "")
			user = user.replace(">", "")
			user = user.replace("!", "")
			user = ctx.guild.get_member(eval(user))
		else:
			for member in ctx.guild.members:
				if str(user).lower() in str(member.display_name).lower():
					user_id = member.id
					user = ctx.guild.get_member(user_id)
					break
		if user.top_role.position >= ctx.author.top_role.position:
			return await ctx.send("That user is above your paygrade, take a seat")
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = 0
		self.warns[guild_id][user_id] = count
		with open("./data/userdata/mod.json", "w") as outfile:
			json.dump({"warns": self.warns}, outfile, ensure_ascii=False)
		await ctx.send(f"Set {user.name}'s warn count to {count}")

	@commands.command(name="warns")
	async def _warns(self, ctx, user=None):
		if user is None:
			user = ctx.author
		else:
			if user.startswith("<@"):
				user = user.replace("<@", "")
				user = user.replace(">", "")
				user = user.replace("!", "")
				user = ctx.guild.get_member(eval(user))
			else:
				for member in ctx.guild.members:
					if str(user).lower() in str(member.display_name).lower():
						user_id = member.id
						user = ctx.guild.get_member(user_id)
						break
		guild_id = str(ctx.guild.id)
		user_id = str(user.id)
		if guild_id not in self.warns:
			self.warns[guild_id] = {}
		if user_id not in self.warns[guild_id]:
			self.warns[guild_id][user_id] = 0
		await ctx.send(f"**{user.display_name}:** `{self.warns[guild_id][user_id]}`")

def setup(bot):
	bot.add_cog(Mod(bot))
