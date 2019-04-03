from discord.ext import commands
from os.path import isfile
import discord
import json

class Toggles(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.responses = {}
		self.mod = {}
		if isfile("./data/userdata/config/toggles.json"):
			with open("./data/userdata/config/toggles.json", "r") as infile:
				dat = json.load(infile)
				if "responses" in dat and "mod" in dat:
					self.responses = dat["responses"]
					self.mod = dat["mod"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.group(name='toggle', aliases=['t'])
	@commands.has_permissions(manage_guild=True)
	async def _toggle(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("**Toggleable modules:**\n"
			               "~ responses\n"
			               "~ mod")

	@_toggle.command(name='responses')
	async def _responses(self, ctx):
		if self.responses[str(ctx.guild.id)] == 'enabled':
			self.responses[str(ctx.guild.id)] = 'disabled'
			await ctx.send('Disabled `responses` 👍')
			self.bot.unload_extension('cogs.responses')
			self.bot.load_extension('cogs.responses')
		else:
			self.responses[str(ctx.guild.id)] = 'enabled'
			await ctx.send('Enabled `responses` 👍')
			self.bot.unload_extension('cogs.responses')
			self.bot.load_extension('cogs.responses')
		with open("./data/userdata/config/toggles.json", "w") as outfile:
			json.dump({"responses": self.responses, "mod": self.mod}, outfile, ensure_ascii=False)

	@_toggle.command(name='mod')
	async def _mod(self, ctx):
		if self.mod[str(ctx.guild.id)] == 'enabled':
			self.mod[str(ctx.guild.id)] = 'disabled'
			await ctx.send('Disabled `mod` 👍')
			self.bot.unload_extension('cogs.mod')
			self.bot.load_extension('cogs.mod')
		else:
			self.mod[str(ctx.guild.id)] = 'enabled'
			await ctx.send('Enabled `mod` 👍')
			self.bot.unload_extension('cogs.mod')
			self.bot.load_extension('cogs.mod')
		with open("./data/userdata/config/toggles.json", "w") as outfile:
			json.dump({"responses": self.responses, "mod": self.mod}, outfile, ensure_ascii=False)

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		if str(message.guild.id) not in self.responses:
			self.responses[str(message.guild.id)] = 'enabled'
			self.bot.unload_extension('cogs.responses')
			self.bot.load_extension('cogs.responses')
		if str(message.guild.id) not in self.mod:
			self.mod[str(message.guild.id)] = 'enabled'
			self.bot.unload_extension('cogs.mod')
			self.bot.load_extension('cogs.mod')
		with open("./data/userdata/config/toggles.json", "w") as outfile:
			json.dump({"responses": self.responses, "mod": self.mod}, outfile, ensure_ascii=False)

def setup(bot):
	bot.add_cog(Toggles(bot))
