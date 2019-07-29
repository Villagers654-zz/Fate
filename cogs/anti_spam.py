from discord.ext import commands
from os.path import isfile
from utils import colors
from time import time
import discord
import asyncio
import json

class AntiSpam(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.blacklist = {}
		self.roles = {}
		self.status = {}
		self.mutes = {}
		self.cd = {}
		self.msgs = {}
		if isfile("./data/userdata/anti_spam.json"):
			with open("./data/userdata/anti_spam.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]
				if 'blacklist' in dat:
					self.blacklist = dat['blacklist']

	def save_data(self):
		with open("./data/userdata/anti_spam.json", "w") as f:
			json.dump({"toggle": self.toggle, 'blacklist': self.blacklist}, f)

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
			    ".anti_spam disable\n"
				".anti_spam blockchannel\n"
				".anti_spam unblockchannel", inline=False)
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

	@_anti_spam.command(name='blockchannel')
	@commands.has_permissions(manage_messages=True)
	async def _block_channel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.blacklist:
			self.blacklist[guild_id] = []
		if not channel:
			channel = ctx.channel
		if channel.id in self.blacklist[guild_id]:
			return await ctx.send('This channel is already blocked')
		self.blacklist[guild_id].append(channel.id)
		await ctx.send('👍')
		self.save_data()

	@_anti_spam.command(name='unblockchannel')
	@commands.has_permissions(manage_messages=True)
	async def _unblock_channel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.blacklist[guild_id]:
			return await ctx.send('This guild has no blocked channels')
		if not channel:
			channel = ctx.channel
		if channel.id not in self.blacklist[guild_id]:
			return await ctx.send('This channel isn\'t blocked')
		index = self.blacklist[guild_id].index(channel.id)
		self.blacklist[guild_id].pop(index)
		await ctx.send('👍')
		self.save_data()

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.author, discord.Member):
			if m.author.bot:
				return
			if "spam" in m.channel.name:
				return
			guild_id = str(m.guild.id)
			if guild_id in self.toggle:
				if guild_id in self.blacklist:
					if m.channel.id in self.blacklist[guild_id]:
						return
				if m.author.id == self.bot.user.id:
					return
				user_id = str(m.author.id)
				if user_id not in self.msgs:
					self.msgs[user_id] = []
				self.msgs[user_id].append([m.id, time()])
				now = int(time() / 5)
				if guild_id not in self.cd:
					self.cd[guild_id] = {}
				if user_id not in self.cd[guild_id]:
					self.cd[guild_id][user_id] = [now, 0]
				if self.cd[guild_id][user_id][0] == now:
					self.cd[guild_id][user_id][1] += 1
				else:
					self.cd[guild_id][user_id] = [now, 0]
				if self.cd[guild_id][user_id][1] > 3:
					bot = m.guild.get_member(self.bot.user.id)
					perms = [perm for perm, value in bot.guild_permissions]
					if "manage_roles" not in perms or "manage_messages" not in perms:
						if m.channel.permissions_for(bot).send_messages:
							del self.toggle[guild_id]
							await m.channel.send("Disabled anti spam, missing required permissions")
							self.save_data()
						return
					async def delete_recent():
						self.msgs[user_id] = self.msgs[user_id][-10:]
						for msg_id, msg_time in self.msgs[user_id]:
							if msg_time > time() - 10:
								try:
									msg = await m.channel.fetch_message(msg_id)
									await msg.delete()
								except:
									pass
					if m.author.top_role.position >= bot.top_role.position:
						return await delete_recent()
					await delete_recent()
					if "send_messages" not in perms:
						return
					async with m.channel.typing():
						with open("./data/userdata/mod.json", "r") as f:
							dat = json.load(f)  # type: dict
							if "timers" in dat:
								if user_id in dat['timers']:
									return
						if guild_id not in self.status:
							self.status[guild_id] = {}
						if user_id in self.status[guild_id]:
							return
						self.status[guild_id][user_id] = "working"
						mute_role = discord.utils.get(m.guild.roles, name="Muted")
						if not mute_role:
							mute_role = discord.utils.get(m.guild.roles, name="muted")
						if not mute_role:
							if "manage_channels" not in perms:
								if m.channel.permissions_for(bot).send_messages:
									del self.toggle[guild_id]
									await m.channel.send("Disabled anti spam, missing required permissions")
									self.save_data()
								return
							mute_role = await m.guild.create_role(name="Muted", color=discord.Color(colors.black()), hoist=True)
							for channel in m.guild.text_channels:
								await channel.set_permissions(mute_role, send_messages=False)
							for channel in m.guild.voice_channels:
								await channel.set_permissions(mute_role, speak=False)
						roles = []
						for role in m.author.roles:
							try:
								await m.author.remove_roles(role)
								roles.append(role)
								await asyncio.sleep(1)
							except:
								pass
						multiplier = 0
						if guild_id not in self.mutes:
							self.mutes[guild_id] = {}
						if user_id not in self.mutes[guild_id]:
							self.mutes[guild_id][user_id] = []
						self.mutes[guild_id][user_id].append(time())
						for mute_time in self.mutes[guild_id][user_id]:
							if mute_time > time() - 3600:
								multiplier += 1
							else:
								index = self.mutes[guild_id][user_id].index(mute_time)
								self.mutes[guild_id][user_id].pop(index)
						timer = 150 * multiplier
						timer_str = '2 minutes and 30 seconds'
						if multiplier == 2:
							timer_str = '3 minutes'
						if multiplier > 2:
							timer_str = '3+ minutes'
						await m.author.add_roles(mute_role)
						try:
							await m.author.send(f"You've been muted for spam in **{m.guild.name}** for {timer_str}")
						except:
							pass
						await m.channel.send(f"Temporarily muted `{m.author.display_name}` for spam")
					await asyncio.sleep(timer)
					user = self.bot.get_user(int(user_id))
					if isinstance(user, discord.User):
						with open("./data/userdata/mod.json", "r") as f:
							dat = json.load(f)  # type: dict
							if "timers" in dat:
								if user_id in dat['timers']:
									return
						if mute_role in m.author.roles:
							async with m.channel.typing():
								try:
									await m.author.remove_roles(mute_role)
								except:
									pass
						for role in roles:
							if role not in m.author.roles:
								await asyncio.sleep(1)
								try:
									await m.author.add_roles(role)
								except:
									pass
						await m.channel.send(f"Unmuted {m.author.display_name}")
					del self.status[guild_id][user_id]

def setup(bot):
	bot.add_cog(AntiSpam(bot))
