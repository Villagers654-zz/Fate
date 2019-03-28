from discord.ext import commands
from os.path import isfile
import discord
import json

class Mod:
	def __init__(self, bot):
		self.bot = bot
		self.rules = {}
		if isfile("./data/userdata/rules.json"):
			with open("./data/userdata/rules.json", "r") as infile:
				dat = json.load(infile)
				if "rules" in dat:
					self.rules = dat["rules"]

	def save_data(self):
		with open("./data/userdata/rules.json", "w") as outfile:
			json.dump({"rules": self.rules}, outfile, ensure_ascii=False)

	@commands.group(name="rules")
	async def _rules(self, ctx):
		if ctx.invoked_subcommand is None:
			if str(ctx.guild.id) not in self.rules:
				await ctx.send("This server doesnt have any rules set, try using .rules help")
			else:
				e = discord.Embed(color=0xff0000)
				e.description = self.rules[str(ctx.guild.id)]
				await ctx.send(embed=e)

	@_rules.command(name="help")
	async def _help(self, ctx):
		await ctx.send("**Rules Usage:**\n"
		               ".rules set {rules}")

	@_rules.command(name="set")
	@commands.has_permissions(manage_guild=True)
	async def _set(self, ctx, *, rules):
		self.rules[str(ctx.guild.id)] = rules
		await ctx.send("Successfully set the rules 👍")
		self.save_data()

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.rules:
			del self.rules[guild_id]

def setup(bot):
	bot.add_cog(Mod(bot))
