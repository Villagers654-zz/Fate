from cogs.utils import psutil as p
from discord.ext import commands
from os.path import isfile
import traceback
import datetime
import discord
import asyncio
import random
import psutil
import json
import time

class Profiles:
	def __init__(self, bot):
		self.bot = bot
		self.name = {}
		self.info = {}
		self.color = {}
		self.created = {}
		self.channel = {}
		self.discord = {}
		self.website = {}
		self.thumbnail = {}
		self.icon = {}
		if isfile("./data/userdata/profiles.json"):
			with open("./data/userdata/profiles.json", "r") as infile:
				dat = json.load(infile)
				if "name" in dat and "info" in dat and "color" in dat and "created" in dat and "channel" in dat and "discord" in dat and "website" in dat and "thumbnail" in dat and "icon" in dat:
					self.name = dat["name"]
					self.info = dat["info"]
					self.color = dat["color"]
					self.created = dat["created"]
					self.channel = dat["channel"]
					self.discord = dat["discord"]
					self.website = dat["website"]
					self.thumbnail = dat["thumbnail"]
					self.icon = dat["icon"]
		self.cd = {}
		self.global_data = {}
		self.guilds_data = {}
		if isfile("./data/userdata/xp.json"):
			with open("./data/userdata/xp.json", "r") as infile:
				dat = json.load(infile)
				if "global" in dat and "guilded" in dat:
					self.global_data = dat["global"]
					self.guilds_data = dat["guilded"]
		self.statschannel = {}
		self.statsmessage = {}
		if isfile("./data/userdata/config/stats.json"):
			with open("./data/userdata/config/stats.json", "r") as infile:
				dat = json.load(infile)
				if "statschannel" in dat and "statsmessage" in dat:
					self.statschannel = dat["statschannel"]
					self.statsmessage = dat["statsmessage"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.group(name="set")
	async def _set(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("**Profile Usage:**\n"
			               ".set name {name}\n"
			               ".set bio {bio}\n"
			               ".set color {hex}\n"
			               ".set discord {url}\n"
			               ".set channel {url}\n"
			               ".set icon {img}\n"
			               ".set thumbnail {img}\n")

	@_set.command(name="name")
	async def _name(self, ctx, *, name=None):
		if name is None:
			self.name[str(ctx.author.id)] = ctx.author.name
			await ctx.send("Your name has been reset.")
		else:
			self.name[str(ctx.author.id)] = name
			await ctx.send('success')
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="bio", aliases=["info"])
	async def _bio(self, ctx, *, info):
		self.info[str(ctx.author.id)] = info
		await ctx.send('success')
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="color")
	async def _color(self, ctx, hex=None):
		if hex is None:
			self.color[str(ctx.author.id)] = "9eafe3"
			await ctx.send("Your color has been reset")
		else:
			if hex == "red":
				hex = "ff0000"
			if hex == "orange":
				hex = "ff560d"
			if hex == "yellow":
				hex = "ffff00"
			if hex == "green":
				hex = "33CC33"
			if hex == "blue":
				hex = "0000FF"
			if hex == "purple":
				hex = "800080"
			hex = hex.replace("#", "")
			if len(list(hex)) == 6:
				self.color[str(ctx.author.id)] = f"{hex}"
				await ctx.send("Success")
			else:
				await ctx.send("that is not a hex")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="channel")
	async def _channel(self, ctx, url=None):
		if url is None:
			self.channel[str(ctx.author.id)] = "None"
			await ctx.send("Reset your channel url")
		else:
			listed = ["youtube.com", "youtu.be"]
			for i in listed:
				if i in url:
					listed = True
			if listed == True:
				self.channel[str(ctx.author.id)] = url
				await ctx.send('Success')
			else:
				await ctx.send("That's not a youtube channel")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="discord")
	async def _discord(self, ctx, url=None):
		if url is None:
			self.discord[str(ctx.author.id)] = "None"
			await ctx.send("Reset your discord servers url")
		else:
			if "discord.gg" in url:
				self.discord[str(ctx.author.id)] = url
				await ctx.send('Success')
			else:
				await ctx.send("That's not a discord link")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="website")
	async def _website(self, ctx, url=None):
		if url is None:
			self.website[str(ctx.author.id)] = "None"
			await ctx.send("Reset your website url")
		else:
			self.website[str(ctx.author.id)] = url
			await ctx.send("Success")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="thumbnail")
	async def _thumbnail(self, ctx):
		if len(ctx.message.attachments) > 0:
			if len(ctx.message.attachments) > 1:
				await ctx.send("You've provided too many attachments")
			else:
				for attachment in ctx.message.attachments:
					self.thumbnail[str(ctx.author.id)] = attachment.url
					await ctx.send("Success")
		else:
			self.thumbnail[str(ctx.author.id)] = "None"
			await ctx.send("Reset your thumbnail")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@_set.command(name="icon")
	async def _icon(self, ctx):
		if len(ctx.message.attachments) > 0:
			if len(ctx.message.attachments) > 1:
				await ctx.send("You've provided too many attachments")
			else:
				for attachment in ctx.message.attachments:
					self.icon[str(ctx.author.id)] = attachment.url
					await ctx.send("Success")
		else:
			self.icon[str(ctx.author.id)] = "None"
			await ctx.send("Reset your icon")
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@commands.command()
	async def profile(self, ctx, user=None):
		# get deh user
		check = 0
		if user is None:
			user = ctx.author
			check += 1
		else:
			if user.startswith("<@"):
				user = user.replace("<@", "")
				user = user.replace(">", "")
				user = self.bot.get_user(eval(user))
				check += 1
			else:
				for member in ctx.guild.members:
					if str(user).lower() in str(member.name).lower():
						user_id = member.id
						user = self.bot.get_user(user_id)
						check += 1
						break
		if check is not 0:
			if user.bot == True:
				await ctx.send("bots cant have profiles")
			else:
				links = ""
				fmt = "%m-%d-%Y %I:%M%p"
				created = datetime.datetime.now()
				xp = self.global_data[str(user.id)]
				level = str(xp / 750)
				level = level[:level.find(".")]
				if str(user.id) in self.color:
					color = f"0x{self.color[str(user.id)]}"
				else:
					color = "0x9eafe3"
				#piecing the embed together
				color = eval(color)
				thumbnail = user.avatar_url
				if str(user.id) in self.thumbnail:
					if self.thumbnail[str(user.id)] == "None":
						pass
					else:
						thumbnail = self.thumbnail[str(user.id)]
				e = discord.Embed(color=color)
				e.set_thumbnail(url=thumbnail)
				if str(user.id) not in self.name:
					name = user.name
				else:
					name = f"{self.name[str(user.id)]}"
				icon = user.avatar_url
				if str(user.id) in self.icon:
					if self.icon[str(user.id)] == "None":
						pass
					else:
						icon = self.icon[str(user.id)]
				e.set_author(name=name, icon_url=icon)
				if str(user.id) not in self.info:
					self.info[str(user.id)] = 'nothing to see here, try using .set'
				e.description = f"**Level:** {level} **XP:** {xp}"
				e.add_field(name=f"◈ Bio ◈", value=f"{self.info[str(user.id)]}")
				if str(user.id) not in self.created:
					self.created[str(user.id)] = created.strftime(fmt)
				if str(user.id) in self.channel:
					if self.channel[str(user.id)] == "None":
						pass
					else:
						links += f"[Channel]({self.channel[str(user.id)]})\n"
				if str(user.id) in self.discord:
					if self.discord[str(user.id)] == "None":
						pass
					else:
						links += f"[Discord]({self.discord[str(user.id)]})\n"
				if str(user.id) in self.website:
					if self.website[str(user.id)] == "None":
						pass
					else:
						links += f"[Website]({self.website[str(user.id)]})\n"
				if links == "":
					pass
				else:
					e.add_field(name="◈ Links ◈", value=links, inline=False)
				e.set_footer(text=f'Profile Created: {self.created[str(user.id)]}')
				await ctx.send(embed=e)
				if str(e) == "invalid token (<string>, line 1)":
					self.color[str(ctx.author.id)] = "0x9eafe3"
					await ctx.send("there was an error with your color, therefore its been reset")
				else:
					await ctx.send(e)
			with open("./data/userdata/profiles.json", "w") as outfile:
				json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
				           "channel": self.channel, "discord": self.discord, "website": self.website,
				           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	@commands.command(name="leaderboard", aliases=["lb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def leaderboard(self, ctx):
		embed = discord.Embed(title="Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			embed.description += "‎**‎#{}.** ‎`‎{}`: ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			embed.set_thumbnail(url=ctx.guild.icon_url)
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 10 seconds"]))
		await ctx.send(embed=embed)

	@commands.command(name="gleaderboard", aliases=["glb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def gleaderboard(self, ctx):
		embed = discord.Embed(title="Global Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			embed.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 10 seconds"]))
		await ctx.send(embed=embed)

	@commands.command(name="ggleaderboard", aliases=["gglb"])
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def ggleaderboard(self, ctx):
		embed = discord.Embed(title="Guild XP Leaderboard", color=0x4A0E50)
		embed.description = ""
		rank = 1
		for guild_id, xp in (sorted({i:sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
			name = "INVALID-GUILD"
			guild = self.bot.get_guild(int(guild_id))
			if isinstance(guild, discord.Guild):
				name = guild.name
			embed.description += "**#{}.** `{}`: {}\n".format(rank, name, xp)
			rank += 1
			embed.set_thumbnail(url=ctx.guild.icon_url)
			embed.set_footer(text=random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready", "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by doritos", "Cooldown: 10 seconds"]))
		await ctx.send(embed=embed)

	@commands.group(name='stats')
	@commands.check(luck)
	async def _stats(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	@_stats.command(name='setchannel')
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		if channel is None:
			self.statschannel = ctx.channel.id
		else:
			self.statschannel = channel
		with open("./data/config/stats.json", "w") as outfile:
			json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
		await ctx.message.delete()

	@_stats.command(name='start', aliases=['fix'])
	async def _start(self, ctx):
		self.bot.loop.create_task(self.stats())
		await ctx.message.delete()

	async def stats(self):
		while True:
			try:
				channel = self.bot.get_channel(self.statschannel)
				e = discord.Embed(title="", color=0x4A0E50)
				e.description = "💎 Official 4B4T Server 💎"
				leaderboard = ""
				rank = 1
				for user_id, xp in (sorted(self.guilds_data[str(channel.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:8]:
					name = "INVALID-USER"
					user = self.bot.get_user(int(user_id))
					if isinstance(user, discord.User):
						name = user.name
					level = str(xp / 750)
					level = level[:level.find(".")]
					leaderboard += "‎**‎#{}.** ‎`‎{}`: ‎{} | {}\n".format(rank, name, level, xp)
					rank += 1
				e.set_thumbnail(url=channel.guild.icon_url)
				e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
				e.add_field(name="◈ Discord ◈", value=f'__**Founder**__: FrequencyX4\n__**Members**__: {channel.guild.member_count}', inline=False)
				e.add_field(name="Leaderboard", value=leaderboard, inline=False)
				e.add_field(
					name="◈ Memory ◈",
					value=f"__**Storage**__: [{p.bytes2human(p.storageused)}/{p.bytes2human(p.storagetotal)}]\n"
					f"__**RAM**__: **Global**: {p.bytes2human(p.ramused)} **Bot**: {p.bytes2human(p.botram)}\n"
					f"__**CPU**__: **Global**: {p.cpu}% **Bot**: {p.botcpu}%\n"
					f"__**CPU Per Core**__: {[round(i) for i in psutil.cpu_percent(interval=1, percpu=True)]}\n"
					f"__**CPU Frequency**__: [{p.freq}/{p.freqmax}]")
				fmt = "%m-%d-%Y %I:%M%p"
				time = datetime.datetime.now()
				time = time.strftime(fmt)
				e.set_footer(text=f'Updated: {time}')
				statschannel = self.bot.get_channel(self.statschannel)
				try:
					message = await statschannel.get_message(self.statsmessage)
					await message.edit(embed=e)
				except Exception as e:
					preparing = discord.Embed()
					preparing.description = 'preparing stats..'
					msg = await statschannel.send(embed=preparing)
					self.statsmessage = msg.id
					with open("./data/userdata/config/stats.json", "w") as outfile:
						json.dump({"statschannel": self.statschannel, "statsmessage": self.statsmessage}, outfile, ensure_ascii=False)
				async for msg in statschannel.history(limit=5):
					greenid = "{}".format(self.statsmessage)
					redid = "{}".format(msg.id)
					if redid not in greenid:
						await msg.delete()
				await asyncio.sleep(25)
			except Exception as e:
				await self.bot.get_channel(534608853300412416).send(f"```{traceback.format_exc()}```{e}")

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.stats())

	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):
			if not m.author.bot:
				r = random.randint(5, 10)
				author_id = str(m.author.id)
				guild_id = str(m.guild.id)
				if author_id not in self.cd:
					self.cd[author_id] = 0
				if self.cd[author_id] < time.time():
					if guild_id not in self.guilds_data:
						self.guilds_data[guild_id] = {}
					if author_id not in self.guilds_data[guild_id]:
						self.guilds_data[guild_id][author_id] = 0
					if author_id not in self.global_data:
						self.global_data[author_id] = 0

					self.global_data[author_id] += 1
					self.guilds_data[guild_id][author_id] += 1
					self.cd[author_id] = time.time() + 10

					with open("./data/userdata/xp.json", "w") as outfile:
						json.dump({"global": self.global_data, "guilded": self.guilds_data}, outfile, ensure_ascii=False)

def setup(bot):
	bot.add_cog(Profiles(bot))
