from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json

class ChatFilter:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = []
		self.blacklist = {}
		if isfile("./data/userdata/chatfilter.json"):
			with open("./data/userdata/chatfilter.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat and "blacklist" in dat:
					self.toggle = dat["toggle"]
					self.blacklist = dat["blacklist"]

	def save_data(self):
		with open("./data/userdata/chatfilter.json", "w") as f:
			json.dump({"toggle": self.toggle, "blacklist": self.blacklist}, f)

	@commands.group(name="chatfilter", description="Deletes messages containing blocked words/phrases")
	@commands.cooldown(1, 3, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _chatfilter(self, ctx):
		if not ctx.invoked_subcommand:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if ctx.guild.id in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.pink())
			e.set_author(name="| Chat Filter", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = "Deletes messages containing blocked words/phrases"
			e.add_field(name="◈ Usage ◈", value=
				".chatfilter enable\n"
			    ".chatfilter disable\n"
			    ".chatfilter add {word/phrase}\n"
				".chatfilter remove {word/phrase}\n", inline=False)
			if guild_id in self.blacklist:
				e.add_field(name="◈ Forbidden Shit ◈", value=self.blacklist[guild_id], inline=False)
			e.set_footer(text=f"Current Status: {toggle}")
			await ctx.send(embed=e)

	@_chatfilter.command(name="enable")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _enable(self, ctx):
		if ctx.guild.id in self.toggle:
			return await ctx.send("Chatfilter is already enabled")
		self.toggle.append(ctx.guild.id)
		await ctx.send("Enabled chatfilter")
		self.save_data()

	@_chatfilter.command(name="disable")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _disable(self, ctx):
		if ctx.guild.id not in self.toggle:
			return await ctx.send("Chatfilter is not enabled")
		self.toggle.pop(self.toggle.index(ctx.guild.id))
		await ctx.send("Disabled chatfilter")
		self.save_data()

	@_chatfilter.command(name="add")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _add(self, ctx, *, phrase):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.blacklist:
			self.blacklist[guild_id] = []
		if phrase in self.blacklist[guild_id]:
			return await ctx.send("That word/phrase is already blacklisted")
		self.blacklist[guild_id].append(phrase)
		await ctx.send(f"Added `{phrase}`")
		self.save_data()

	@_chatfilter.command(name="remove")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _remove(self, ctx, *, phrase):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.blacklist:
			return await ctx.send("This server has no blacklist")
		if phrase not in self.blacklist[guild_id]:
			return await ctx.send("Phrase/word not found")
		self.blacklist[guild_id].pop(self.blacklist[guild_id].index(phrase))
		await ctx.send(f"Removed `{phrase}`")
		if len(self.blacklist[guild_id]) < 1:
			del self.blacklist[guild_id]
		self.save_data()

	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if m.guild.id in self.toggle:
				if guild_id in self.blacklist:
					for phrase in self.blacklist[guild_id]:
						if "manage_messages" not in list(perm for perm, value in m.author.guild_permissions if value):
							if phrase in m.content:
								await asyncio.sleep(0.5)
								await m.delete()
						else:
							if phrase in m.content.replace(" ", ""):
									await asyncio.sleep(0.5)
									await m.delete()

	async def on_message_edit(self, before, after):
		if isinstance(before.guild, discord.Guild):
			guild_id = str(before.guild.id)
			if before.guild.id in self.toggle:
				if guild_id in self.blacklist:
					for phrase in self.blacklist[guild_id]:
						if "manage_messages" not in list(perm for perm, value in before.author.guild_permissions if value):
							if phrase in after.content:
								await asyncio.sleep(0.5)
								await after.delete()
						else:
							if phrase in after.content.replace(" ", ""):
								await asyncio.sleep(0.5)
								await after.delete()

def setup(bot):
	bot.add_cog(ChatFilter(bot))
