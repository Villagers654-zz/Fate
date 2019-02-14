from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import json

class AutoRole:
	def __init__(self, bot):
		self.bot = bot
		self.roles = {}
		if isfile("./data/userdata/autorole.json"):
			with open("./data/userdata/autorole.json") as infile:
				dat = json.load(infile)
				if "roles" in dat:
					self.role = dat["roles"]

	def save_roles(self):
		with open("./data/userdata/autorole.json") as outfile:
			json.dump({"role": self.role}, outfile, ensure_ascii=False)

	@commands.group(name="autorole")
	@commands.has_permissions(manage_roles=True)
	async def _autorole(self, ctx, item: commands.clean_content=None):
		guild_id = str(ctx.guild.id)
		e = discord.Embed(color=colors.fate())
		if item is None:
			e.set_author(name="Auto-Role Help", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.add_field(name="◈ Usage ◈", value=
			".autorole {role}\n"
			".autorole list\n"
			".autorole clear", inline=False)
			return await ctx.send(embed=e)
		if item.lower() == "clear":
			if guild_id not in self.roles:
				return await ctx.send("Auto role is not active")
			del self.roles[guild_id]
			self.save_roles()
			return await ctx.send("Removed role(s) from auto-role")
		if item.lower() == "list":
			if guild_id not in self.roles:
				return await ctx.send("Auto role is not active")
			e.set_author(name="Auto Roles", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = ""
			for role_id in self.roles[guild_id]:
				role = ctx.guild.get_role(role_id)
				e.description += f"• {role.name}\n"
			return await ctx.send(embed=e)
		item = item.replace("@", "").lower()
		if guild_id not in self.roles:
			self.roles[guild_id] = []
		for role in ctx.guild.roles:
			if item == role.name.lower():
				self.roles[guild_id].append(role.id)
				self.save_roles()
				return await ctx.send(f"Added `{role.name}` to the list of auto roles")
		for role in ctx.guild.roles():
			if item in role.name.lower():
				self.roles[guild_id].append(role.id)
				self.save_roles()
				return await ctx.send(f"Added `{role.name}` to the list of auto roles")
		await ctx.send("Role not found")

	async def on_member_join(self, m: discord.Member):
		guild_id = str(m.guild.id)
		if guild_id in self.roles:
			for role_id in self.roles[guild_id]:
				await m.add_roles(m.guild.get_role(role_id))

	async def on_role_delete(self, role):
		guild_id = str(role.guild.id)
		if role.id in self.roles[guild_id]:
			self.roles[guild_id].pop(role.id)

def setup(bot):
	bot.add_cog(AutoRole(bot))
