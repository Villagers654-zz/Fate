from discord.ext import commands
from os.path import isfile
from utils import checks
import asyncio
import random
import time
import json

class ChatBot:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.cache = []
		self.cd = {}
		if isfile("./data/misc/chatbot.json"):
			with open("./data/misc/chatbot.json", "r") as f:
				dat = json.load(f)
				self.cache = dat

	def save(self):
		with open("./data/misc/chatbot.json", "w") as f:
			json.dump(self.cache, f)

	@commands.command(name="chatbot")
	@commands.has_permissions(manage_messages=True)
	async def _chatbot(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.toggle:
			del self.toggle[guild_id]
			await ctx.send("disabled chatbot", delete_after=5)
			await asyncio.sleep(5)
			return await ctx.message.delete()
		self.toggle[guild_id] = "enabled"
		await ctx.send("enabled chatbot", delete_after=5)
		await asyncio.sleep(5)
		await ctx.message.delete()

	@commands.command(name="pop")
	@commands.check(checks.luck)
	async def _pop(self, ctx, *, phrase):
		for response in self.cache:
			if phrase in response:
				self.cache.pop(self.cache.index(response))
		await ctx.message.delete()

	async def on_message(self, m: commands.clean_content):
		if not m.author.bot:
			guild_id = str(m.guild.id)
			found = None
			if guild_id in self.toggle:
				if len(m.content) is 0:
					return
				if guild_id not in self.cd:
					self.cd[guild_id] = 0
				if self.cd[guild_id] > time.time():
					return
				self.cd[guild_id] = time.time() + 2
				if m.content.startswith("."):
					return
				key = random.choice(m.content.split(" "))
				if m.content not in self.cache:
					self.cache.append(m.content)
					self.save()
				matches = []
				for msg in self.cache:
					if key in msg:
						matches.append(msg)
						found = True
				if found:
					choice = random.choice(matches)
					if choice.lower() == m.content.lower():
						return
					async with m.channel.typing():
						await asyncio.sleep(1)
					await m.channel.send(choice)

def setup(bot):
	bot.add_cog(ChatBot(bot))
