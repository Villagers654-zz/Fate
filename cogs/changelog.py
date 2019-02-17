from utils import colors, config
from discord.ext import commands
from os.path import isfile
import datetime
import discord
import asyncio
import json

class Changelog:
	def __init__(self, bot):
		self.bot = bot
		self.changelogs = []
		if isfile("./data/changelog.json"):
			with open("./data/changelog.json", "r") as f:
				dat = json.load(f)
				if "changelogs" in dat:
					self.changelogs = dat["changelogs"]
					self.last_updated = dat["last_updated"]

	def save_changelog(self):
		with open("./data/changelog.json", "w") as f:
			json.dump({"changelogs": self.changelogs, "last_updated": self.last_updated}, f, sort_keys=True, indent=4, separators=(',', ': '))

	@commands.group(name="changelog")
	async def _changelog(self, ctx, *, changelog=""):
		if not changelog:
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Bot Changelog", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = ""
			changelog_count = len(self.changelogs) - 1
			for i in self.changelogs:
				e.description += f"• {self.changelogs[changelog_count]}\n"
				changelog_count -= 1
			e.set_footer(text=f"Last Updated: {self.last_updated}")
			await ctx.send(embed=e)
		if changelog:
			if config.bot.owner:
				if changelog.startswith("remove"):
					del self.changelogs[int(changelog.split(" ")[1]) - 1]
					self.save_changelog()
					await asyncio.sleep(0.5)
					return await ctx.message.delete()
				self.changelogs.append(changelog)
				if len(self.changelogs) > 6:
					del self.changelogs[0]
				self.last_updated = datetime.datetime.now().strftime("%m-%d-%Y %I:%M%p")
				self.save_changelog()
				await asyncio.sleep(0.5)
				await ctx.message.delete()

def setup(bot):
	bot.add_cog(Changelog(bot))
