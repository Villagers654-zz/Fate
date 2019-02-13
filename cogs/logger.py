from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json

class Logger:
	def __init__(self, bot):
		self.bot = bot
		self.channel = {}
		self.messages = {}
		if isfile("./data/userdata/logger.json"):
			with open("./data/userdata/logger.json", "r") as infile:
				dat = json.load(infile)
				if "channel" in dat:
					self.channel = dat["channel"]

	def save(self):
		with open("./data/userdata/logger.json", "w") as outfile:
			json.dump({"channel": self.channel}, outfile, ensure_ascii=False)

	@commands.group(name="logger")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _logger(self, ctx):
		if ctx.invoked_subcommand is None:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.channel:
				toggle = "enabled"
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Logger Usage", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = \
				f"**Current Status:** {toggle}\n" \
				".logger setchannel {channel}\n" \
				".logger disable\n"
			await ctx.send(embed=e)

	@_logger.command(name="disable")
	@commands.cooldown(1, 1, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.channel:
			del self.channel[guild_id]
			self.save()
			return await ctx.send("Disabled logging")
		await ctx.send("Logging is not enabled")

	@_logger.command(name="setchannel")
	@commands.cooldown(1, 1, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if channel is None:
			self.channel[guild_id] = ctx.channel.id
			self.save()
			return await ctx.send(f"I will now log actions to {ctx.channel.mention}")
		self.channel[guild_id] = channel.id
		self.save()
		await ctx.send(f"I will now log actions to {channel.mention}")

	async def on_message(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id not in self.messages:
			self.messages[guild_id] = []
		self.messages[guild_id].append(m.id)

	async def on_guild_update(self, before, after):
		guild_id = str(after.id)
		if guild_id in self.channel:
			if before.name != after.name:
				channel = self.bot.get_channel(self.channel[guild_id])
				e = discord.Embed(color=colors.cyan())
				e.title = "Guild Update"
				e.set_thumbnail(url=before.icon_url)
				e.add_field(name="Type: Name", value= \
				f"Before: `{before.name}`\n" \
				f"After: `{after.name}`")
				await channel.send(embed=e)

	async def on_guild_role_create(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "Role Created"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}"
			await channel.send(embed=e)

	async def on_guild_role_delete(self, role):
		guild_id = str(role.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.blue())
			e.title = "Role Deleted"
			e.set_thumbnail(url=role.guild.icon_url)
			e.description = f"Name: {role.name}\n" \
				f"Color: {role.color}\n" \
				f"Users: [{len(list(role.members))}]"
			await channel.send(embed=e)

	async def on_message_edit(self, before, after):
		if not before.author.bot:
			guild_id = str(before.guild.id)
			if guild_id in self.channel:
				channel = self.bot.get_channel(self.channel[guild_id])
				e = discord.Embed(color=colors.pink())
				e.title = "Message Edited"
				e.set_thumbnail(url=before.author.avatar_url)
				e.description = f"**Author Name:** {before.author.display_name}\n" \
					f"**Channel:** {before.channel.mention}"
				e.add_field(name="Before:", value=f"`{before.content}`", inline=False)
				e.add_field(name="After:", value=f"`{after.content}`", inline=False)
				await channel.send(embed=e)

	async def on_message_delete(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.purple())
			e.title = "Message Deleted"
			e.set_thumbnail(url=m.author.avatar_url)
			e.description = f"**Author Name:** {m.author.display_name}\n" \
				f"**Channel:** {m.channel.mention}"
			if m.pinned is True:
				e.description += f"\nMsg was pinned"
			if len(m.embeds) > 0:
				if m.content == "":
					m.content = "Embed"
			if m.content == "":
				m.content = "None"
			if "`" not in m.content:
				m.content = f"`{m.content}`"
			e.add_field(name="Content:", value=f"{m.content}", inline=False)
			if len(m.attachments) > 0:
				e.add_field(name="Cached Images:", value="`they may not show`")
			for attachment in m.attachments:
				e.set_image(url=attachment.proxy_url)
			await channel.send(embed=e)

	async def on_raw_message_delete(self, payload):
		await asyncio.sleep(0.21)
		guild_id = str(payload.guild_id)
		if guild_id in self.channel:
			if guild_id not in self.messages:
				self.messages[guild_id] = []
			if payload.message_id not in self.messages[guild_id]:
				e = discord.Embed(color=colors.purple())
				e.title = "Uncached Message Deleted"
				e.set_thumbnail(url=self.bot.get_guild(payload.guild_id).icon_url)
				e.description = f"**Channel:** {self.bot.get_channel(payload.channel_id).mention}\n" \
					f"**Msg ID:** `{payload.message_id}`"
				await self.bot.get_channel(self.channel[guild_id]).send(embed=e)

	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.green())
			e.title = "Member Joined"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"Name: {m.name}\n" \
				f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_remove(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.title = "Member Left or Was Kicked"
			e.set_thumbnail(url=m.avatar_url)
			e.description = \
				f"Name: {m.name}\n" \
				f"ID: {m.id}\n"
			await channel.send(embed=e)

	async def on_member_ban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.red())
			e.set_thumbnail(url=user.avatar_url)
			if isinstance(user, discord.Member):
				e.title = "Member Banned"
			if isinstance(user, discord.User):
				e.title = "User Banned"
			e.description = f"Name: {user.name}\n"
			await channel.send(embed=e)

	async def on_member_unban(self, guild, user):
		guild_id = str(guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.lime_green())
			e.title = "User Unbanned"
			e.set_thumbnail(url=user.avatar_url)
			e.description = f"Name: {user.name}"
			await channel.send(embed=e)

def setup(bot):
	bot.add_cog(Logger(bot))
