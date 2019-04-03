from datetime import datetime, timedelta
from discord.ext import commands
from os.path import isfile
from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
import discord
import random
import json
import time
import os

class Leaderboards(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.cd = {}
		self.global_data = {}
		self.guilds_data = {}
		self.monthly_global_data = {}
		self.monthly_guilds_data = {}
		self.gvclb = {}
		self.vclb = {}
		self.dat = {}
		if isfile("./data/userdata/xp.json"):
			with open("./data/userdata/xp.json", "r") as infile:
				dat = json.load(infile)
				if "global" in dat and "guilded" in dat:
					self.global_data = dat["global"]
					self.guilds_data = dat["guilded"]
					self.monthly_global_data = dat["monthly_global"]
					self.monthly_guilds_data = dat["monthly_guilded"]
					self.vclb = dat["vclb"]
					self.gvclb = dat["gvclb"]

	def save_xp(self):
		with open("./data/userdata/xp.json", "w") as outfile:
			json.dump({"global": self.global_data, "guilded": self.guilds_data, "monthly_global": self.monthly_global_data,
			           "monthly_guilded": self.monthly_guilds_data, "vclb": self.vclb, "gvclb": self.gvclb},
			          outfile, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

	def msg_footer(self):
		return random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready",
		    "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme",
		                      "Powered by doritos", "Cooldown: 10 seconds"])

	def vc_footer(self):
		return random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready",
		    "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme", "Powered by tostitos"])

	@commands.command(name="leaderboard", aliases=["lb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def leaderboard(self, ctx):
		e = discord.Embed(title="Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.guilds_data[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += "‎**‎#{}.** ‎`‎{}`: ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.set_footer(text=self.msg_footer())
		await ctx.send(embed=e)

	@commands.command(name="gleaderboard", aliases=["glb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def gleaderboard(self, ctx):
		e = discord.Embed(title="Global Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			e.set_footer(text=self.msg_footer())
		await ctx.send(embed=e)

	@commands.command(name="ggleaderboard", aliases=["gglb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def ggleaderboard(self, ctx):
		e = discord.Embed(title="Guild XP Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for guild_id, xp in (sorted({i:sum(x.values()) for i, x in self.guilds_data.items()}.items(), key=lambda kv: kv[1], reverse=True))[:8]:
			name = "INVALID-GUILD"
			guild = self.bot.get_guild(int(guild_id))
			if isinstance(guild, discord.Guild):
				name = guild.name
			else:
				del self.guilds_data[guild_id]
			e.description += "**#{}.** `{}`: {}\n".format(rank, name, xp)
			rank += 1
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.set_footer(text=self.msg_footer())
		await ctx.send(embed=e)

	@commands.command(name="mleaderboard", aliases=["mlb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _mleaderboard(self, ctx):
		guild_id = str(ctx.guild.id)
		users = list(self.monthly_guilds_data[guild_id])
		xp = {}
		for user in users:
			for msg in self.monthly_guilds_data[guild_id][user]:
				xp[user] = len(self.monthly_guilds_data[guild_id][user])
		e = discord.Embed(title="Monthly Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			e.set_footer(text=self.msg_footer())
		await ctx.send(embed=e)

	@commands.command(name="gmleaderboard", aliases=["gmlb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _gmleaderboard(self, ctx):
		users = list(self.monthly_global_data)
		xp = {}
		for user in users:
			for msg in self.monthly_global_data[user]:
				xp[user] = len(self.monthly_global_data[user])
		e = discord.Embed(title="Global Monthly Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			level = str(xp / 750)
			level = level[:level.find(".")]
			e.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			e.set_footer(text=self.msg_footer())
		await ctx.send(embed=e)

	@commands.command(name="vcleaderboard", aliases=["vclb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def vcleaderboard(self, ctx):
		e = discord.Embed(title="VC Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.vclb[str(ctx.guild.id)].items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			e.description += "‎**‎#{}.** ‎`‎{}`: ‎{}\n".format(rank, name, score)
			rank += 1
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.set_footer(text=self.vc_footer())
		await ctx.send(embed=e)

	@commands.command(name="gvcleaderboard", aliases=["gvclb"])
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def gvcleaderboard(self, ctx):
		e = discord.Embed(title="Global VC Leaderboard", color=0x4A0E50)
		e.description = ""
		rank = 1
		for user_id, xp in (sorted(self.gvclb.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				name = user.name
			score = timedelta(seconds=xp)
			e.description += "‎**#‎{}.** ‎`‎{}`‎ ~ ‎{}\n".format(rank, name, score)
			rank += 1
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png")
			e.set_footer(text=self.vc_footer())
		await ctx.send(embed=e)

	@commands.command(name="card")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _card(self, ctx):
		leaderboard = ""
		rank = 1
		for user_id, xp in (sorted(self.global_data.items(), key=lambda kv: kv[1], reverse=True))[:15]:
			name = "INVALID-USER"
			user = self.bot.get_user(int(user_id))
			if isinstance(user, discord.User):
				filter = list('abcdefghijklmnopqrstuvwxyz1234567890 ')
				name = ""
				for char in list(user.name):
					if char.lower() in filter:
						name += char
				check = True
				for char in list(name):
					if char != " ":
						check = False
				if check:
					name = "Unknown"
			level = str(xp / 750)
			level = level[:level.find(".")]
			leaderboard += "‎#‎{}. ‎{}‎ ~ ‎{} | {}\n".format(rank, name, level, xp)
			rank += 1
		card = Image.new("RGBA", (1024, 1024), (255, 255, 255))
		img = Image.open('./data/images/backgrounds/galaxy.jpg').convert("RGBA")
		img = img.resize((1024, 1024), Image.BICUBIC)
		card.paste(img, (0, 0, 1024, 1024), img)
		card.save("./data/images/backgrounds/galaxy.png", format="png")
		img = Image.open('./data/images/backgrounds/galaxy.png')
		draw = ImageDraw.Draw(img)
		font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 60)
		def large(size):
			return ImageFont.truetype("./utils/fonts/Fitamint Script.ttf", size)
		draw.text((25, 25), "Global Leaderboard", (255, 255, 255), font=large(150))
		draw.text((5, 220), leaderboard, (255, 255, 255), font=font)
		img = img.convert("RGB")
		img.save('./data/images/backgrounds/results/galaxy.png')
		e = discord.Embed(color=0x4A0E50)
		e.set_image(url="attachment://" + os.path.basename('/data/images/backgrounds/results/galaxy.png'))
		await ctx.send(file=discord.File('./data/images/backgrounds/results/galaxy.png',
		    filename=os.path.basename('/data/images/backgrounds/results/galaxy.png')), embed=e)

	@commands.Cog.listener()
	async def on_message(self, m:discord.Message):
		if isinstance(m.guild, discord.Guild):
			if not m.author.bot:
				author_id = str(m.author.id)
				guild_id = str(m.guild.id)
				msg_id = str(m.id)
				if author_id not in self.cd:
					self.cd[author_id] = 0
				if self.cd[author_id] < time.time():
					if guild_id not in self.guilds_data:
						self.guilds_data[guild_id] = {}
					if author_id not in self.guilds_data[guild_id]:
						self.guilds_data[guild_id][author_id] = 0
					if author_id not in self.global_data:
						self.global_data[author_id] = 0
					if author_id not in self.monthly_global_data:
						self.monthly_global_data[author_id] = {}
					if guild_id not in self.monthly_guilds_data:
						self.monthly_guilds_data[guild_id] = {}
					if author_id not in self.monthly_guilds_data[guild_id]:
						self.monthly_guilds_data[guild_id][author_id] = {}

					self.global_data[author_id] += 1
					self.guilds_data[guild_id][author_id] += 1
					self.monthly_global_data[author_id][msg_id] = time.time()
					self.monthly_guilds_data[guild_id][author_id][msg_id] = time.time()
					self.cd[author_id] = time.time() + 10

					for msg_id, msg_time in (sorted(self.monthly_global_data[author_id].items(), key=lambda kv: kv[1], reverse=True)):
						if float(msg_time) < time.time() - 2592000:
							del self.monthly_global_data[author_id][str(msg_id)]
					for msg_id, msg_time in (sorted(self.monthly_guilds_data[guild_id][author_id].items(), key=lambda kv: kv[1], reverse=True)):
						if float(msg_time) < time.time() - 2592000:
							del self.monthly_guilds_data[guild_id][author_id][str(msg_id)]

					self.save_xp()

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		if isinstance(member.guild, discord.Guild):
			if not member.bot:
				guild_id = str(member.guild.id)
				user_id = str(member.id)
				channel_id = None
				channel = None  # type: discord.TextChannel
				if not after.channel:
					channel_id = str(before.channel.id)
					channel = before.channel
				if not before.channel:
					channel_id = str(after.channel.id)
					channel = after.channel
				if guild_id not in self.vclb:
					self.vclb[guild_id] = {}
				if user_id not in self.vclb[guild_id]:
					self.vclb[guild_id][user_id] = 0
				if user_id not in self.gvclb:
					self.gvclb[user_id] = 0
				if channel_id is None:
					return
				if channel_id not in self.dat:
					self.dat[channel_id] = {}
				if "members" not in self.dat[channel_id]:
					self.dat[channel_id]["members"] = []
				if "status" not in self.dat[channel_id]:
					self.dat[channel_id]["status"] = "inactive"
				if user_id not in self.dat[channel_id]["members"]:
					self.dat[channel_id]["members"].append(user_id)
					if len(channel.members) < 2:
						self.dat[channel_id]["status"] = "inactive"
					if self.dat[channel_id]["status"] == "inactive":
						if len(channel.members) > 1:
							if after.self_mute:
								return
							if after.mute:
								return
							self.dat[channel_id]["status"] = "active"
							for user in channel.members:
								member_id = str(user.id)
								if member_id not in self.dat[channel_id].keys():
									self.dat[channel_id][member_id] = datetime.now()
					else:
						self.dat[channel_id][user_id] = datetime.now()
				else:
					if not after.channel:
						if self.dat[channel_id]["status"] == "active":
							if len(channel.members) < 2:
								self.dat[channel_id]["status"] = "inactive"
								for id in self.dat[channel_id]["members"]:
									if id in self.dat[channel_id]:
										seconds = (datetime.now() - self.dat[channel_id][id]).seconds
										self.vclb[guild_id][id] += seconds
										self.gvclb[id] += seconds
										del self.dat[channel_id][id]
							else:
								if user_id in self.dat[channel_id]:
									seconds = (datetime.now() - self.dat[channel_id][user_id]).seconds
									self.vclb[guild_id][user_id] += seconds
									self.gvclb[user_id] += seconds
									del self.dat[channel_id][user_id]
						self.dat[channel_id]["members"].pop(self.dat[channel_id]["members"].index(str(user_id)))
				if before.self_mute is False and after.self_mute is True:
					if self.dat[channel_id]["status"] == "active":
						if len(channel.members) == 2:
							self.dat[channel_id]["status"] = "inactive"
							for id in self.dat[channel_id]["members"]:
								if id in self.dat[channel_id]:
									seconds = (datetime.now() - self.dat[channel_id][id]).seconds
									self.vclb[guild_id][id] += seconds
									self.gvclb[id] += seconds
									del self.dat[channel_id][id]
						else:
							seconds = (datetime.now() - self.dat[channel_id][user_id]).seconds
							self.vclb[guild_id][user_id] += seconds
							self.gvclb[user_id] += seconds
							del self.dat[channel_id][user_id]
				if before.self_mute is True and after.self_mute is False:
					if self.dat[channel_id]["status"] == "inactive":
						if len(channel.members) > 1:
							self.dat[channel_id]["status"] = "active"
							for user in channel.members:
								member_id = str(user.id)
								if member_id not in self.dat[channel_id].keys():
									self.dat[channel_id][member_id] = datetime.now()
					else:
						self.dat[channel_id][user_id] = datetime.now()
				self.save_xp()

def setup(bot: commands.Bot):
	bot.add_cog(Leaderboards(bot))
