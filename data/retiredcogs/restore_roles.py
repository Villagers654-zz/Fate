from discord.ext import commands
from os.path import isfile
import asyncio
import json

class RestoreRoles(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.data = {}
		if isfile("./data/userdata/restore_roles.json"):
			with open("./data/userdata/restore_roles.json", "r") as f:
				self.data = json.load(f)

	def save_data(self):
		with open("./data/userdata/restore_roles.json", "w") as f:
			json.dump(self.data, f, sort_keys=True, indent=4, separators=(",", ": "))

	def is_guild_owner(ctx: commands.Context):
		return ctx.author is ctx.guild.owner

	@commands.command(name="restore_roles")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	async def _restore_roles(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.data:
			del self.data[guild_id]
			await ctx.send("Disabled restore_roles")
			return self.save_data()
		self.data[guild_id] = {}
		await ctx.send("**Enabled restore_roles:**\n"
		"Adds a users roles back if they leave and rejoin")
		self.save_data()

	@commands.Cog.listener()
	async def on_member_join(self, member):
		guild_id = str(member.guild.id)
		member_id = str(member.id)
		if guild_id in self.data:
			if member_id in self.data[guild_id]:
				for role_id in self.data[guild_id][member_id]:
					try:
						role = member.guild.get_role(role_id)
						if role:
							await member.add_roles(role)
							await asyncio.sleep(1)
					except:
						pass

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		guild_id = str(member.guild.id)
		member_id = str(member.id)
		if guild_id in self.data:
			self.data[guild_id][member_id] = []
			for role in member.roles:
				self.data[guild_id][member_id].append(role.id)
			self.save_data()

def setup(bot):
	bot.add_cog(RestoreRoles(bot))
