from discord.ext import commands
from utils import checks, colors
from os.path import isfile
import discord
import asyncio
import random
import time
import json

class ChatBot(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.cache = {}
		self.prefixes = {}
		self.dir = {}
		self.cd = {}
		self.dm_cd = {}
		if isfile("./data/userdata/chatbot.json"):
			with open("./data/userdata/chatbot.json", "r") as infile:
				dat = json.load(infile)
				if "prefixes" in dat and "cache" in dat and "prefixes" in dat and "dir" in dat:
					self.toggle = dat["toggle"]
					self.cache = dat["cache"]
					self.prefixes = dat["prefixes"]
					self.dir = dat["dir"]

	def save_data(self):
		with open("./data/userdata/chatbot.json", "w") as outfile:
			json.dump({"toggle": self.toggle, "cache": self.cache, "prefixes": self.prefixes, "dir": self.dir},
			          outfile, sort_keys=True, indent=4, separators=(',', ': '))

	@commands.group(name="chatbot")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_messages=True)
	async def _chatbot(self, ctx):
		if not ctx.invoked_subcommand:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			cache = "guilded"
			if guild_id in self.toggle:
				toggle = "enabled"
			if guild_id in self.dir:
				if self.dir[guild_id] == "global":
					cache = self.dir[guild_id]
			e = discord.Embed(color=colors.fate())
			e.set_author(name="| Chat Bot", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = f"**Current Status:** {toggle}\n" \
				f"**Cache Location:** {cache}\n"
			e.add_field(name="◈ Usage ◈", value=f".chatbot enable\n"
				f"`enables chatbot`\n"
				f".chatbot disable\n"
				f"`disables chatbot`\n"
				f".chatbot swap_cache\n"
				f"`swaps to global or guilded cache`\n"
				f".chatbot clear_cache\n"
				f"`clears guilded cache`",
			inline=False)
			await ctx.send(embed=e)

	@_chatbot.command(name="enable")
	@commands.has_permissions(manage_messages=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			self.toggle[guild_id] = ctx.channel.id
			if guild_id not in self.dir:
				self.dir[guild_id] = "guilded"
			await ctx.send("Enabled chatbot")
			return self.save_data()
		await ctx.send("Chatbot is already enabled")

	@_chatbot.command(name="disable")
	@commands.has_permissions(manage_messages=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			await ctx.send("Chatbot is not enabled")
		del self.toggle[guild_id]
		self.save_data()
		await ctx.send("Disabled chatbot")

	@_chatbot.command(name="swap_cache")
	@commands.has_permissions(manage_messages=True)
	async def _swap_cache(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.dir:
			return await ctx.send("Chatbot needs to be "
			    "enabled in order for you to use this command")
		if self.dir[guild_id] == "guilded":
			self.dir[guild_id] = "global"
		else:
			self.dir[guild_id] = "guilded"
		await ctx.send(f"Swapped cache location to {self.dir[guild_id]}")
		self.save_data()

	@_chatbot.command(name="clear_cache")
	@commands.has_permissions(manage_messages=True)
	async def _clear_cache(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.cache:
			return await ctx.send("No cached data found")
		del self.cache[guild_id]
		await ctx.send("Cleared cache")
		self.save_data()

	@_chatbot.command(name="load_preset")
	@commands.has_permissions(manage_messages=True)
	async def _load_preset(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.cache:
			self.cache[guild_id] = []
		presets = []
		for response in open("./data/misc/responses.txt", "r").readlines():
			presets.append(response)
		for response in presets:
			if response not in self.cache[guild_id]:
				self.cache[guild_id].append(response)
		await ctx.send("Loaded preset")
		self.save_data()

	@commands.command(name="pop")
	@commands.check(checks.luck)
	async def _pop(self, ctx, *, phrase):
		guild_id = str(ctx.guild.id)
		for response in self.cache[guild_id]:
			if phrase in response:
				self.cache[guild_id].pop(self.cache[guild_id].index(response))
		await ctx.message.delete()

	@commands.command(name="globalpop")
	@commands.check(checks.luck)
	async def _globalpop(self, ctx, *, phrase):
		popped = []
		for response in self.cache["global"]:
			if phrase in response:
				self.cache["global"].pop(self.cache["global"].index(response))
				popped.append(response)
		await ctx.send(f"Removed: {popped}")
		await ctx.message.delete()

	@commands.command(name="prefixes")
	async def _prefixes(self, ctx):
		guild_id = str(ctx.guild.id)
		await ctx.send(self.prefixes[guild_id])

	@commands.command(name="delprefix")
	@commands.check(checks.luck)
	async def _delprefix(self, ctx, prefix):
		guild_id = str(ctx.guild.id)
		self.prefixes[guild_id].pop(self.prefixes[guild_id].index(prefix))
		await ctx.message.delete()

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if not m.author.bot:
				guild_id = str(m.guild.id)
				if m.content.startswith("<@506735111543193601>"):
					m.content = m.content.replace("<@506735111543193601>", m.author.mention)
				if m.content.startswith(self.bot.user.mention):
					return
				if "help" in m.content[:8]:
					def pred(m):
						return m.channel.id == m.channel.id and m.author.bot is True
					try:
						await self.bot.wait_for('message', check=pred, timeout=2)
					except asyncio.TimeoutError:
						return
					else:
						if guild_id not in self.prefixes:
							self.prefixes[guild_id] = []
						if m.content[:m.content.find("help")] not in self.prefixes[guild_id]:
							self.prefixes[guild_id].append(m.content[:m.content.find("help")])
						return
				blocked = ["http", "discord.gg", "discord,gg", "py", "js", "python", "javascript", "`"]
				for i in blocked:
					if i in m.content.lower():
						return
				if guild_id in self.toggle:
					if m.channel.id == self.toggle[guild_id]:
						if len(m.content) is 0:
							return
						if guild_id not in self.cd:
							self.cd[guild_id] = 0
						if self.cd[guild_id] > time.time():
							return
						self.cd[guild_id] = time.time() + 2
						if guild_id in self.prefixes:
							for prefix in self.prefixes[guild_id]:
								if m.content.startswith(prefix):
									return
						if m.content.startswith("."):
							return
						keys = m.content.split(" ")
						key = random.choice(keys)
						if "the" in keys:
							key = keys[keys.index("the") + 1]
						if "if" in keys:
							key = keys[keys.index("if") + 2]
						cache = self.cache["global"]
						if self.dir[guild_id] == "guilded":
							if guild_id not in self.cache:
								self.cache[guild_id] = []
							cache = self.cache[guild_id]
							if m.content not in cache:
								self.cache[guild_id].append(m.content)
								self.cache["global"].append(m.content)
								self.save_data()
						else:
							if m.content not in cache:
								self.cache["global"].append(m.content)
								self.save_data()
						matches = []
						found = False
						for msg in cache:
							if key in msg:
								matches.append(msg)
								found = True
						if found:
							choice = random.choice(matches)
							if choice.lower() == m.content.lower():
								return
							try:
								async with m.channel.typing():
									await asyncio.sleep(1)
								await m.channel.send(choice)
							except:
								pass
		else:
			if not m.author.bot:
				found = False
				user_id = str(m.author.id)
				blocked = ["http", "discord.gg", "discord,gg", "py", "js", "python", "javascript", "`"]
				for i in blocked:
					if i in m.content.lower():
						return
				if len(m.content) is 0:
					return
				if user_id not in self.dm_cd:
					self.cd[user_id] = 0
				if self.cd[user_id] > time.time():
					return
				self.cd[user_id] = time.time() + 2
				if m.content.startswith("."):
					return
				keys = m.content.split(" ")
				key = random.choice(keys)
				if "the" in keys:
					key = keys[keys.index("the") + 1]
				if "if" in keys:
					key = keys[keys.index("if") + 2]
				cache = self.cache["global"]
				if m.content not in cache:
					self.cache["global"].append(m.content)
					self.save_data()
				matches = []
				for msg in cache:
					if key in msg:
						matches.append(msg)
						found = True
				if found:
					choice = random.choice(matches).lower().replace("fate", f"{m.author.display_name}")
					if choice.lower() == m.content.lower():
						return
					try:
						async with m.channel.typing():
							await asyncio.sleep(1)
						await m.channel.send(choice)
					except:
						pass

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.toggle:
			del self.toggle[guild_id]
			self.save_data()
		if guild_id in self.cache:
			del self.cache[guild_id]
			self.save_data()
		if guild_id in self.prefixes:
			del self.prefixes[guild_id]
			self.save_data()
		if guild_id in self.dir:
			del self.dir[guild_id]
			self.save_data()

def setup(bot):
	bot.add_cog(ChatBot(bot))
