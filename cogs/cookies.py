from discord.ext import commands
from cogs.utils import colors
from os.path import isfile
import discord
import random
import json
import time

class Cookies:
	def __init__(self, bot):
		self.bot = bot
		self.cookies = {}
		self.sent = {}
		self.received = {}
		self.eaten = {}
		self.cd = {}
		if isfile("./data/userdata/cookies.json"):
			with open("./data/userdata/cookies.json", "r") as infile:
				dat = json.load(infile)
				if "cookies" in dat and "sent" in dat and "received" in dat and "eaten" in dat:
					self.cookies = dat["cookies"]
					self.sent = dat["sent"]
					self.received = dat["received"]
					self.eaten = dat["eaten"]
					self.cd = dat["cd"]

	def save(self):
		with open("./data/userdata/cookies.json", "w") as outfile:
			json.dump({"cookies": self.cookies, "sent": self.sent, "received": self.received,
			           "eaten": self.eaten, "cd": self.cd}, outfile, ensure_ascii=False)

	@commands.command(name="cookie")
	async def _cookie(self, ctx, user: discord.Member=None):
		author_id = str(ctx.author.id)
		e = discord.Embed(color=colors.fate())
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/507914723858186261/542465014099869697/580b57fbd9996e24bc43c103.png")
		if user is not None:
			user_id = str(user.id)
			if user.bot is True:
				return await ctx.send("You cannot give cookies to bots")
			if user_id not in self.cookies:
				self.cookies[user_id] = 0
				self.sent[user_id] = 0
				self.received[user_id] = 0
				self.eaten[user_id] = 0
				self.cd[user_id] = 0
				self.save()
		if author_id not in self.cookies:
			self.cookies[author_id] = 0
			self.sent[author_id] = 0
			self.received[author_id] = 0
			self.eaten[author_id] = 0
			self.cd[author_id] = 0
			self.save()
		if user is not None:
			if self.cd[author_id] > time.time():
				return await ctx.send("You cannot send another cookie yet\nCooldown: 1 hour")
			if user_id == author_id:
				return await ctx.send("You cannot give yourself cookies")
			self.sent[author_id] += 1
			self.received[user_id] += 1
			self.cookies[user_id] += 1
			e.set_author(name=f"Cookies: {self.cookies[author_id]} | Sent: {self.sent[author_id]} | Received: {self.received[author_id]} | Eaten: {self.eaten[author_id]}", icon_url=ctx.author.avatar_url)
			e.description = f"{ctx.author.display_name} has given {user.display_name} a cookie"
			self.cd[author_id] = time.time() + 3600
			self.save()
			return await ctx.send(embed=e)
		if self.cookies[author_id] == 0:
			return await ctx.send("You have no cookies to eat :(")
		self.cookies[author_id] = self.cookies[author_id] - 1
		self.eaten[author_id] += 1
		self.save()
		e.set_author(name=f"Cookies: {self.cookies[author_id]} | Sent: {self.sent[author_id]} | Received: {self.received[author_id]} | Eaten: {self.eaten[author_id]}", icon_url=ctx.author.avatar_url)
		actions = ["chews on one of his/her cookies", "nibbles on one of his/her cookies", "eats a cookie whole"]
		e.description = f"{ctx.author.name} {random.choice(actions)}"
		await ctx.send(embed=e)

	@commands.command(name="cookies")
	async def _cookies(self, ctx, user: discord.Member=None):
		if user is None:
			user = ctx.author
		user_id = str(user.id)
		if user_id not in self.cookies:
			self.cookies[user_id] = 0
			self.sent[user_id] = 0
			self.received[user_id] = 0
			self.eaten[user_id] = 0
			self.cd[user_id] = 0
			self.save()
		e = discord.Embed(color=colors.fate())
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/507914723858186261/542465014099869697/580b57fbd9996e24bc43c103.png")
		e.set_author(name=f"Cookies: {self.cookies[user_id]} | Sent: {self.sent[user_id]} | Received: {self.received[user_id]} | Eaten: {self.eaten[user_id]}", icon_url=user.avatar_url)
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Cookies(bot))
