from discord.ext import commands
from datetime import datetime
from os.path import isfile
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO
from PIL import Image
import requests
import discord
import json

class Profiles(commands.Cog):
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

	def save_profiles(self):
		with open("./data/userdata/profiles.json", "w") as outfile:
			json.dump({"info": self.info, "name": self.name, "color": self.color, "created": self.created,
			           "channel": self.channel, "discord": self.discord, "website": self.website,
			           "thumbnail": self.thumbnail, "icon": self.icon}, outfile, ensure_ascii=False)

	def get(self):
		with open("./data/userdata/xp.json", "r") as f:
			return json.load(f)

	def global_data(self):
		return self.get()["global"]

	def guilds_data(self):
		return self.get()["guilded"]

	def monthly_global_data(self):
		return self.get()["monthly_global"]

	def monthly_guilds_data(self):
		return self.get()["monthly_guilded"]

	def vclb(self):
		return self.get()["vclb"]

	def gvclb(self):
		return self.get()["gvclb"]

	@commands.command(pass_context=True)
	async def xprofile(self, ctx, user: discord.Member=None):
		if user is None:
			user = ctx.author
		user_id = str(user.id)
		if str(user.id) in self.gvclb():
			xp = self.global_data()[user_id] + self.gvclb()[user_id] / 20
		else:
			xp = self.global_data()[user_id]
		level = str(xp / 750)
		level = level[:level.find(".")]
		if user_id not in self.gvclb():
			vc_xp = 0
		else:
			vc_xp = str(self.gvclb()[user_id] / 60)[:str(self.gvclb()[user_id] / 60).find('.')]
		payload = f"Level: {level}\nXP: {str(xp)[:str(xp).find('.')]}\n" \
			f"MSG: {self.global_data()[user_id]}\nVC: {vc_xp}"
		card = Image.new("RGBA", (1024, 1024), (255, 255, 255))
		img = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert("RGBA")
		img = img.resize((1024, 1024), Image.BICUBIC)
		card.paste(img, (0, 0, 1024, 1024), img)
		card.save("background.png", format="png")
		img = Image.open('background.png')
		draw = ImageDraw.Draw(img)
		font = ImageFont.truetype("Modern_Sans_Light.otf", 75)
		fontbig = ImageFont.truetype("Fitamint Script.ttf", 200)
		draw.text((10, 30), f"{user.name}", (79, 0, 139), font=fontbig)
		draw.text((700, 30), f"{payload}", (0, 0, 255), font=ImageFont.truetype("Modern_Sans_Light.otf", 65))
		draw.text((10, 975), f"{self.info[str(user.id)]}", (255, 255, 255), font=ImageFont.truetype("Modern_Sans_Light.otf", 40))
		img = img.convert("RGB")
		img.save('background.png')
		await ctx.send(file=discord.File("background.png"))

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
		self.save_profiles()

	@_set.command(name="bio", aliases=["info"])
	async def _bio(self, ctx, *, info):
		self.info[str(ctx.author.id)] = info
		await ctx.send('success')
		self.save_profiles()

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
		self.save_profiles()

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
		self.save_profiles()

	@_set.command(name="discord")
	async def _discord(self, ctx, url=None):
		if url is None:
			self.discord[str(ctx.author.id)] = "None"
			await ctx.send("Reset your discord servers url")
		else:
			try: url = await self.bot.fetch_invite(url)
			except: return await ctx.send('Invalid invite')
			self.discord[str(ctx.author.id)] = url
			await ctx.send('Success')

	@_set.command(name="website")
	async def _website(self, ctx, url=None):
		if url is None:
			self.website[str(ctx.author.id)] = "None"
			await ctx.send("Reset your website url")
		else:
			if url.startswith("https://"):
				pass
			else:
				url = "https://" + url
			self.website[str(ctx.author.id)] = url
			await ctx.send("Success")
		self.save_profiles()

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
		self.save_profiles()

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
		self.save_profiles()

	@commands.command()
	async def profile(self, ctx, user=None):
		# get the user
		check = 0
		if user is None:
			user = ctx.author
			check += 1
		else:
			if user.startswith("<@"):
				user = user.replace("<@", "")
				user = user.replace(">", "")
				user = user.replace("!", "")
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
				user_id = str(user.id)
				links = ""
				fmt = "%m-%d-%Y %I:%M%p"
				created = datetime.now()
				if str(user.id) in self.gvclb():
					xp = self.global_data()[user_id] + self.gvclb()[user_id] / 20
				else:
					xp = self.global_data()[user_id]
				level = str(xp / 750)
				level = level[:level.find(".")]
				if str(user.id) in self.color:
					color = f"0x{self.color[user_id]}"
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
				try:
					e = discord.Embed(color=color)
				except:
					await ctx.send("There was an error with your hex")
					e = discord.Embed(color=0x9eafe3)
				try:
					e.set_thumbnail(url=thumbnail)
				except:
					await ctx.send("there was an error with your thumbnail")
					e.set_thumbnail(url=user.avatar_url)
				if str(user.id) not in self.name:
					name = user.name
				else:
					name = f"{self.name[user_id]}"
				icon = user.avatar_url
				if user_id in self.icon:
					if self.icon[user_id] != "None":
						icon = self.icon[user_id]
				try:
					e.set_author(name=name, icon_url=icon)
				except:
					await ctx.send("There was an error with your icon")
					e.set_author(name=name, icon_url=user.avatar_url)
				if user_id not in self.info:
					self.info[str(user.id)] = 'nothing to see here, try using .set'
				if user_id not in self.gvclb():
					vc_xp = 0
				else:
					vc_xp = str(self.gvclb()[user_id] / 60)[:str(self.gvclb()[user_id] / 60).find('.')]
				e.description = f"**Level:** {level} **XP:** {str(xp)[:str(xp).find('.')]}\n" \
					f"**MSG XP:** {self.global_data()[user_id]} **VC XP:** {vc_xp}"
				e.add_field(name=f"◈ Bio ◈", value=f"{self.info[str(user.id)]}")
				if user_id not in self.created:
					self.created[user_id] = created.strftime(fmt)
				if user_id in self.channel:
					if self.channel[str(user.id)] == "None":
						pass
					else:
						links += f"[Channel]({self.channel[user_id]})\n"
				if user_id in self.discord:
					if self.discord[str(user.id)] == "None":
						pass
					else:
						links += f"[Discord]({self.discord[user_id]})\n"
				if user_id in self.website:
					if self.website[user_id] == "None":
						pass
					else:
						links += f"[Website]({self.website[user_id]})\n"
				if links == "":
					pass
				else:
					e.add_field(name="◈ Links ◈", value=links, inline=False)
				e.set_footer(text=f'Profile Created: {self.created[user_id]}')
				await ctx.send(embed=e)
			self.save_profiles()

def setup(bot):
	bot.add_cog(Profiles(bot))
