from discord.ext import commands
from utils import colors
import discord
import json

class Config(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def prefix(self, id):
		with open("./data/userdata/prefixes.json", "r") as f:
			dat = json.load(f)
			if id in dat:
				return dat[id]
			return "."

	def restore_roles(self, id):
		with open("./data/userdata/restore_roles.json", "r") as f:
			if id in json.load(f):
				return "active"
			return "inactive"

	def chatfilter(self, id):
		with open("./data/userdata/chatfilter.json", "r") as f:
			if int(id) in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def anti_spam(self, id):
		with open("./data/userdata/anti_spam.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def anti_raid(self, id):
		with open("./data/userdata/anti_spam.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def anti_purge(self, id):
		with open("./data/userdata/anti_spam.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def selfroles(self, id):
		with open("./data/userdata/selfroles.json", "r") as f:
			if id in json.load(f)["message"]:
				return "active"
			return "inactive"

	def autorole(self, id):
		with open("./data/userdata/autorole.json", "r") as f:
			if id in json.load(f)["roles"]:
				return "active"
			return "inactive"

	def welcome(self, id):
		with open("./data/userdata/welcome.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def farewell(self, id):
		with open("./data/userdata/farewell.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def chatbot(self, id):
		with open("./data/userdata/chatbot.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def logger(self, id):
		with open("./data/userdata/logger.json", "r") as f:
			if id in json.load(f)["channel"]:
				return "active"
			return "inactive"

	def lock(self, id):
		with open("./data/userdata/lock.json", "r") as f:
			if id in json.load(f)["lock"]:
				return "active"
			return "inactive"

	@commands.command(name="config")
	@commands.bot_has_permissions(embed_links=True)
	async def _config(self, ctx):
		guild_id = str(ctx.guild.id)
		e = discord.Embed(color=colors.fate())
		e.set_author(name="| 💎 Server Config 💎", icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"**Prefix:** [`{self.prefix(guild_id)}`]\n"
		module_config =  f"**Restore Roles:** [`{self.restore_roles(guild_id)}`]\n" \
			f"**Chat Filter:** [`{self.chatfilter(guild_id)}`]\n" \
			f"**Anti Spam:** [`{self.anti_spam(guild_id)}`]\n" \
			f"**Anti Raid:** [`{self.anti_raid(guild_id)}`]\n" \
			f"**Anti Purge:** [`{self.anti_purge(guild_id)}`]\n" \
			f"**Self Roles:** [`{self.selfroles(guild_id)}`]\n" \
			f"**Auto Role:** [`{self.autorole(guild_id)}`]\n" \
			f"**Welcome:** [`{self.welcome(guild_id)}`]\n" \
			f"**Farewell:** [`{self.farewell(guild_id)}`]\n" \
			f"**Chatbot:** [`{self.chatbot(guild_id)}`]\n" \
			f"**Logger:** [`{self.logger(guild_id)}`]\n" \
			f"**Lock:** [`{self.lock(guild_id)}`]"
		e.add_field(name="◈ Modules ◈", value=module_config)
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Config(bot))
