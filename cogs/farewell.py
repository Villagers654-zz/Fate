from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import random
import json
import os

class Farewell:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.channel = {}
		self.useimages = {}
		self.format = {}
		if isfile("./data/userdata/farewell.json"):
			with open("./data/userdata/farewell.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]
					self.channel = dat["channel"]
					self.useimages = dat["useimages"]
					self.format = dat["format"]

	def save_data(self):
		with open("./data/userdata/farewell.json", "w") as f:
			json.dump({"toggle": self.toggle, "channel": self.channel, "useimages": self.useimages,
			    "format": self.format}, f, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

	@commands.group(name="farewell", description="Gives a farewell in chat when a user leaves the guild")
	@commands.cooldown(1, 3, commands.BucketType.channel)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def _farewell(self, ctx):
		if not ctx.invoked_subcommand:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.tan())
			e.set_author(name="Farewell Messages", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = "Gives a farewell in chat when a user leaves the guild"
			e.add_field(name="◈ Basic Usage ◈", value=
				".farewell enable\n"
				".farewell disable\n"
				".farewell config\n"
				".farewell setchannel {channel}\n"
				".farewell useimages\n"
				".farewell format {message}\n", inline=False)
			e.add_field(name="◈ Msg Format ◈", value=
				"$NAME\n"
				"`uses a users name`\n"
				"$USER\n"
				"`uses a users name & tag`\n"
				"**Example:**\n"
				"`.farewell format Cya $NAME`", inline=False)
			e.set_footer(text=f"Current Status: {toggle}", icon_url=ctx.guild.owner.avatar_url)
			await ctx.send(embed=e)

	@_farewell.command(name="enable")
	@commands.has_permissions(manage_guild=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.toggle:
			return await ctx.send("This module is already enabled")
		self.toggle[guild_id] = "enabled"
		e = discord.Embed(color=colors.tan())
		e.set_author(name="Enabled Farewell Messages", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		useimages = "disabled"
		if guild_id in self.useimages:
			useimages = "enabled"
		if guild_id not in self.channel:
			self.channel[guild_id] = ctx.channel.id
		if guild_id not in self.format:
			self.format[guild_id] = "Cya $USER"
		e.description = \
			f"**Channel:** {self.bot.get_channel(self.channel[guild_id]).mention}\n" \
			f"**UseImages:** {useimages}\n" \
			f"**Format:** `{self.format[guild_id]}`\n"
		await ctx.send(embed=e)
		self.save_data()

	@_farewell.command(name="disable")
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("This module isn't enabled")
		del self.toggle[guild_id]
		await ctx.send("Disabled welcome messages")
		self.save_data()

	@_farewell.command(name="config")
	async def _config(self, ctx):
		guild_id = str(ctx.guild.id)
		toggle = "disabled"
		channel = "none"
		useimages = "disabled"
		format = "none"
		if guild_id in self.toggle:
			toggle = "enabled"
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id]).mention
		if guild_id in self.useimages:
			useimages = self.useimages[guild_id]
		if guild_id in self.format:
			format = self.format[guild_id]
		e = discord.Embed(color=colors.tan())
		e.set_author(name="Farewell Config", icon_url=self.bot.user.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"**Toggle:** {toggle}\n" \
			f"**Channel:** {channel}\n" \
			f"**UseImages:** {useimages}\n" \
			f"**Format:** {format}\n"
		await ctx.send(embed=e)

	@_farewell.command(name="setchannel")
	@commands.has_permissions(manage_guild=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if not channel:
			channel = ctx.channel
		self.channel[guild_id] = channel.id
		await ctx.send(f"Set the farewell message channel to {channel.mention}")
		self.save_data()

	@_farewell.command(name="useimages")
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(attach_files=True)
	async def _useimages(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.useimages:
			del self.useimages[guild_id]
			return await ctx.send("Disabled UseImages")
		self.useimages[guild_id] = "enabled"
		await ctx.send("Enabled UseImages")
		self.save_data()

	@_farewell.command(name="format")
	@commands.has_permissions(manage_guild=True)
	async def _format(self, ctx, *, message):
		guild_id = str(ctx.guild.id)
		self.format[guild_id] = message
		await ctx.message.add_reaction("👍")
		self.save_data()

	async def on_member_remove(self, m: discord.Member):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if guild_id in self.toggle:
				try:
					channel = self.bot.get_channel(self.channel[guild_id])
				except:
					del self.toggle[guild_id]
					return self.save_data()
				msg = self.format[guild_id]
				msg = msg.replace("$NAME", str(m.name)).replace("$USER", str(m))
				path = os.getcwd() + "/data/images/reactions/farewell/" + random.choice(
					os.listdir(os.getcwd() + "/data/images/reactions/farewell/"))
				if guild_id in self.useimages:
					e = discord.Embed(color=colors.fate())
					e.set_image(url="attachment://" + os.path.basename(path))
					try:
						await channel.send(msg, file=discord.File(path, filename=os.path.basename(path)), embed=e)
					except:
						del self.useimages[guild_id]
						self.save_data()
				else:
					try:
						await channel.send(msg)
					except:
						del self.toggle[guild_id]
						self.save_data()

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.toggle:
			del self.toggle[guild_id]
		if guild_id in self.channel:
			del self.channel[guild_id]
		if guild_id in self.useimages:
			del self.useimages[guild_id]
		if guild_id in self.format:
			del self.format[guild_id]
		self.save_data()

def setup(bot):
	bot.add_cog(Farewell(bot))
