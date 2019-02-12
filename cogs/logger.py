from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import json

class Logger:
	def __init__(self, bot):
		self.bot = bot
		self.messages = {}
		self.guild_names = {}
		self.channel = {}
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
			return await ctx.send(f"I will not log actions to {ctx.channel.mention}")
		self.channel[guild_id] = channel.id
		self.save()
		await ctx.send(f"I will now log actions to {channel.mention}")

	async def on_ready(self):
		for guild in self.bot.guilds:
			guild_id = str(guild.id)
			self.guild_names[guild_id] = guild.name

	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			message_id = str(m.id)
			guild_id = str(m.guild.id)
			if guild_id not in self.messages:
				self.messages[guild_id] = {}
			self.messages[guild_id][message_id] = m.content

	async def on_message_edit(self, before, after):
		if not before.author.bot:
			message_id = str(before.id)
			guild_id = str(before.guild.id)
			if guild_id in self.channel:
				channel = self.bot.get_channel(self.channel[guild_id])
				msg = await before.channel.get_message(before.id)
				if guild_id not in self.messages:
					self.messages[guild_id] = {}
				if message_id in self.messages[guild_id]:
					cached = self.messages[guild_id][message_id]
				else:
					cached = "Uncached Message"
				e = discord.Embed(color=colors.pink())
				e.title = "Message Edited"
				e.set_thumbnail(url=before.author.avatar_url)
				e.description = f"User Name: {before.author.display_name}\n"
				e.add_field(name="Before:", value=f"`{cached}`", inline=False)
				e.add_field(name="After:", value=f"`{msg.content}`", inline=False)
				await channel.send(embed=e)
				self.messages[guild_id][message_id] = msg.content

	async def on_message_delete(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			e = discord.Embed(color=colors.purple())
			e.title = "Message Deleted"
			e.set_thumbnail(url=m.author.avatar_url)
			e.description = f"User: {m.author.display_name}"
			if len(m.embeds) > 0:
				if m.content == "":
					m.content = "Discord Embed"
			if m.content == "":
				m.content = "None"
			e.add_field(name="Content:", value=f"`{m.content}`", inline=False)
			if len(m.attachments) > 0:
				e.add_field(name="Images:", value="`they may not show after time`")
			for attachment in m.attachments:
				e.set_image(url=attachment.proxy_url)
			await channel.send(embed=e)

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
