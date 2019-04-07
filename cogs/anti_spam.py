from discord.ext import commands
from os.path import isfile
from utils import colors
from time import time
import discord
import asyncio
import json

class Anti_Spam(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.roles = {}
		self.working = {}
		self.cd = {}
		if isfile("./data/userdata/anti_spam.json"):
			with open("./data/userdata/anti_spam.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]

	def save_data(self):
		with open("./data/userdata/anti_spam.json", "w") as f:
			json.dump({"toggle": self.toggle}, f)

	@commands.group(name="anti_spam", aliases=["antispam"])
	@commands.bot_has_permissions(embed_links=True)
	async def _anti_spam(self, ctx):
		if not ctx.invoked_subcommand:
			toggle = "disabled"
			if str(ctx.guild.id) in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Anti Spam", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="Usage", value=
				".anti_spam enable\n"
			    ".anti_spam disable", inline=False)
			e.set_footer(text=f"Current Status: {toggle}")
			await ctx.send(embed=e)

	@_anti_spam.command(name="enable")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True,
	manage_roles=True, manage_channels=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.toggle:
			return await ctx.send("Anti spam is already enabled")
		self.toggle[guild_id] = ctx.guild.name
		await ctx.send("Enabled anti spam")
		self.save_data()

	@_anti_spam.command(name="disable")
	@commands.has_permissions(manage_messages=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("Anti spam is not enabled")
		del self.toggle[guild_id]
		await ctx.send("Disabled anti spam")
		self.save_data()

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if guild_id in self.toggle:
				if m.author.bot:
					return
				if m.author.top_role.position >= m.guild.get_member(self.bot.user.id).top_role.position:
					return
				user_id = str(m.author.id)
				now = int(time() / 5)
				if guild_id not in self.cd:
					self.cd[guild_id] = {}
				if user_id not in self.cd[guild_id]:
					self.cd[guild_id][user_id] = [now, 0]
				if self.cd[guild_id][user_id][0] == now:
					self.cd[guild_id][user_id][1] += 1
				else:
					self.cd[guild_id][user_id] = [now, 0]
				if self.cd[guild_id][user_id][1] > 2:
					if guild_id not in self.working:
						self.working[guild_id] = {}
					if user_id in self.working[guild_id]:
						return
					self.working[guild_id][user_id] = "working"
					role = discord.utils.get(m.guild.roles, name="Muted")
					if not role:
						role = discord.utils.get(m.guild.roles, name="muted")
					if not role:
						role = await m.guild.create_role(name="Muted", color=discord.Color(colors.black()), hoist=True)
						for channel in m.guild.text_channels:
							await channel.set_permissions(role, send_messages=False)
						for channel in m.guild.voice_channels:
							await channel.set_permissions(role, speak=False)
					roles = []
					for r in m.author.roles:
						try:
							await m.author.remove_roles(r)
							roles.append(r.id)
							await asyncio.sleep(0.5)
						except:
							pass
					await m.author.add_roles(role)
					try:
						await m.author.send(f"You've been muted for spam in **{m.guild.name}** for 2mins and 30secs")
					except:
						pass
					await asyncio.sleep(150)
					rs = []
					for r in m.author.roles:
						rs.append(r.name.lower())
					if "muted" not in rs:
						return
					await m.author.remove_roles(role)
					for r in roles:
						await m.author.add_roles(m.guild.get_role(r))
						await asyncio.sleep(0.5)
					del self.working[guild_id][user_id]

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.toggle:
			del self.toggle[guild_id]
			self.save_data()

def setup(bot):
	bot.add_cog(Anti_Spam(bot))
