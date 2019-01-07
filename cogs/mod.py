from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json
import os

class Mod:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="delete", aliases=["d"])
	@commands.has_permissions(manage_messages=True)
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

	@commands.command()
	@commands.has_permissions(manage_messages=True)
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def purge(self, ctx, amount: int):
		await ctx.message.channel.purge(before=ctx.message, limit=amount)
		await ctx.message.delete()
		await ctx.send("{}, successfully purged {} messages".format(ctx.author.name, amount), delete_after=5)

	@commands.command(name="kick", aliases=["k"])
	@commands.has_permissions(kick_members=True)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def kick(self, ctx, user:discord.Member, *, reason:str=None):
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
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def ban(self, ctx, user:discord.Member, *, reason=None):
		await ctx.guild.ban(user, reason=reason, delete_message_days=0)
		path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
		e = discord.Embed(color=0x80b0ff)
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

	@commands.command(pass_context=True)
	async def listbans(self, ctx):
		server = ctx.guild
		bans = await server.bans()
		if len(bans) == 0:
			await ctx.send("There are no active bans currently on the server.")
		else:
			await ctx.send("The currently active bans for this server are: " + ", ".join(map(str, bans)))

	@commands.command(name="pin", aliases=["p"])
	@commands.has_permissions(manage_messages=True)
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
	async def nick(self, ctx, member: discord.Member, *, nick=None):
		if nick is None:
			nick = ""
		await member.edit(nick=nick)
		await ctx.message.add_reaction('👍')

	@commands.command()
	@commands.has_permissions(administrator=True)
	@commands.cooldown(1, 60, commands.BucketType.guild)
	async def massnick(self, ctx, *, nick=None):
		failed = ""
		if nick is None:
			nick = ""
		await ctx.message.add_reaction('🖍')
		for member in ctx.guild.members:
			try:
				await member.edit(nick=nick)
			except Exception as e:
				if failed == "":
					failed = f"**Failed to change the nicks of:**\n{member.name}"
				else:
					failed += f", {member.name}"
		await ctx.message.add_reaction('🏁')
		if failed == "":
			pass
		else:
			await ctx.send(failed)

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def vcmute(self, ctx, member: discord.Member):
		await member.edit(mute=True)
		await ctx.send(f'Muted {member.display_name} 👍')

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def vcunmute(self, ctx, member: discord.Member):
		await member.edit(mute=False)
		await ctx.send(f'Unmuted {member.display_name} 👍')

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def mute(self, ctx, member: discord.Member=None, timer=None):
		if member is None and timer is None:
			await ctx.send(
				"**Mute Usage:**\n"
				".mute {user}\n"
				"**timer Usage:**\n"
				"m = minute(s), h = hour(s), d = day(s)\n"
				".mute {user} {number}{m/h/d}")
		else:
			role = None
			async with ctx.typing():
				for i in ctx.guild.roles:
					if i.name.lower() == "muted":
						role = i
			if role is None:
				await ctx.send("this server does not have a muted role")
			else:
				if role in member.roles:
					await ctx.send(f"{member.display_name} is already muted")
				else:
					await member.add_roles(role)
					if timer is None:
						await ctx.send(f"**Muted:** {member.name}")
					else:
						r = timer.replace("m", " minutes")
						if r == "1 minutes":
							r = "1 minute"
						r = r.replace("h", " hours")
						if r == "1 hours":
							r = "1 hour"
						r = r.replace("d", " days")
						if r == "1 days":
							r = "1 day"
						await ctx.send(f"Muted **{member.name}** for {r}")
					if timer is not None:
						if "d" in timer:
							t = timer.replace("d", "")
							t = int(t) * 60 * 60 * 24
						if "h" in timer:
							t = timer.replace("h", "")
							t = int(t) * 60 * 60
						if "m" in timer:
							t = timer.replace("m", "")
							t = int(t) * 60
						await asyncio.sleep(t)
						if role not in member.roles:
							pass
						else:
							await member.remove_roles(role)
							await ctx.send(f"**Unmuted:** {member.name}")

	@commands.command()
	@commands.has_permissions(manage_roles=True)
	async def unmute(self, ctx, member: discord.Member=None):
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
	@commands.has_permissions(manage_guild=True)
	async def warn(self, ctx, m:discord.Member=None, *, reason):
		await m.send(f"You have been warned in **{ctx.guild.name}** for `{reason}`")
		await ctx.send(f"**{m.name} has been warned.**")

def setup(bot):
	bot.add_cog(Mod(bot))
