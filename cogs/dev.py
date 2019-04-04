from utils import colors, config, checks
from discord.ext import commands
from os.path import isfile
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from io import BytesIO
from datetime import datetime
import subprocess
import requests
import difflib
import discord
import asyncio
import random
import psutil
import sqlite3
import json
import time
import os

class Dev(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last = {}

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(name="xinfo")
	async def _info(self, ctx, user: discord.Member = None):
		if user is None:
			user = ctx.author
		card = Image.new("RGBA", (1024, 1024), (255, 255, 255))
		img = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert("RGBA")
		img = img.resize((1024, 1024), Image.BICUBIC)
		card.paste(img, (0, 0, 1024, 1024), img)
		card.save("background.png", format="png")
		img = Image.open('background.png')
		draw = ImageDraw.Draw(img)
		font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 75)  # Make sure you insert a valid font from your folder.
		fontbig = ImageFont.truetype("./utils/fonts/Fitamint Script.ttf", 200)  # Make sure you insert a valid font from your folder.
		#    (x,y)::↓ ↓ ↓ (text)::↓ ↓     (r,g,b)::↓ ↓ ↓
		draw.text((10, 40), "Information:", (255, 255, 255), font=fontbig)
		draw.text((10, 300), "Username: {}".format(user.name), (255, 255, 255), font=font)
		draw.text((10, 400), "ID: {}".format(user.id), (255, 255, 255), font=font)
		draw.text((10, 500), "Status: {}".format(user.status), (255, 255, 255), font=font)
		draw.text((10, 600), "Created: {}".format(datetime.date(user.created_at).strftime("%m/%d/%Y")), (255, 255, 255), font=font)
		draw.text((10, 700), "Nickname: {}".format(user.display_name), (255, 255, 255), font=font)
		draw.text((10, 800), "Top Role: {}".format(user.top_role), (255, 255, 255), font=font)
		draw.text((10, 900), "Joined: {}".format(datetime.date(user.joined_at).strftime("%m/%d/%Y")), (255, 255, 255), font=font)
		img = img.convert("RGB")
		img.save('infoimg2.png')  # Change infoimg2.png if needed.
		await ctx.send(file=discord.File("infoimg2.png"))

	@commands.command(name="scrapeimages")
	@commands.check(checks.luck)
	async def _scrapeimages(self, ctx, filename, limit = 1000):
		if not isfile(f"./data/images/urls/{filename}"):
			with open(f"./data/images/urls/{filename}", "w") as f:
				image_urls = ""
				async for msg in ctx.channel.history(limit=limit):
					if msg.attachments:
						for attachment in msg.attachments:
							if not image_urls:
								image_urls += attachment.url
							else:
								image_urls += f"\n{attachment.url}"
				f.write(image_urls)
		else:
			f = open(f"./data/images/urls/{filename}", "r")
			urls = f.readlines()
			f.close()
			async for msg in ctx.channel.history(limit=limit):
				if msg.attachments:
					for attachment in msg.attachments:
						urls.append(f"{attachment.url}")
			clean_content = ""
			for url in urls:
				if url not in clean_content:
					clean_content += f"\n{url}"
			f = open(f"./data/images/urls/{filename}", "w")
			f.write(clean_content.replace("\n\n", "\n"))
			f.close()
		await ctx.send("Done")

	@commands.command(name="changepresence", aliases=["cp"])
	@commands.check(checks.luck)
	async def changepresence(self, ctx, *, arg):
		async with ctx.typing():
			await self.bot.change_presence(activity=discord.Game(name=arg))
			await ctx.send('done', delete_after=5)
			await asyncio.sleep(5)
			await ctx.message.delete()

	@commands.command()
	@commands.check(checks.luck)
	async def sendfile(self, ctx, directory):
		if "fate/" in directory:
			directory = directory.replace("fate/", "/home/luck/FateZero/")
		await ctx.send(file=discord.File(directory))

	@commands.command(name='console', aliases=['c'])
	@commands.check(checks.luck)
	async def console(self, ctx, *, command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		await ctx.send(f"```{msg[:1994]}```")

	@commands.command()
	@commands.check(checks.luck)
	async def logout(self, ctx):
		await ctx.send('logging out')
		await self.bot.logout()

	@commands.command()
	@commands.check(checks.luck)
	async def error(self, ctx):
		p = subprocess.Popen("cat  /home/luck/.pm2/logs/bot-error.log", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").replace("`", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		msg = msg[::-1]
		msg = msg[:msg.find("Ignoring"[::-1])]
		await ctx.send(f"```Ignoring{msg[::-1]}```")

	@commands.command()
	@commands.check(checks.luck)
	async def dbbbb(self, ctx, arg):
		dat = sqlite3.connect('notes.db')
		c = dat.cursor()
		c.execute("""CREATE TABLE notes (
					id integer,
					note text
					)""")
		c.execute("INSERT INTO notes VALUES (:id, :note)", {'id': ctx.author.id, 'note': arg})
		c.execute("SELECT note FROM notes WHERE id={}".format(ctx.author.id))
		dat.commit()
		await ctx.send(c.fetchone())
		dat.close()

	@commands.command(description="yeet")
	@commands.check(checks.luck)
	async def chs(self, ctx, channel: discord.TextChannel, *, content):
		await channel.send(content)
		await ctx.message.delete()

	@commands.command()
	async def reverse(self, ctx, *, content):
		await ctx.send(content[::-1])

	@commands.command()
	async def chars(self, ctx, *, content):
		await ctx.send(len(content))

	@commands.command()
	@commands.check(checks.luck)
	async def run(self, ctx, *, code):
		await ctx.send(eval(code))

	@commands.command()
	async def ltr(self, ctx):
		await ctx.send(u"\u200E")

	@commands.command()
	async def rtl(self, ctx):
		await ctx.send(u"\u200F")

	async def on_member_join(self,m:discord.Member):
		if m.guild.id ==470961230362837002:
			if m.id ==255433446220890112:
				await m.guild.ban(m, reason="faggotry")
				await self.bot.get_channel(502236124308307968).send("the faggot has been banned.")

	@commands.command()
	async def modules(self, ctx):
		e = discord.Embed()
		modules = ""
		for module in self.bot.extensions:
			modules += "{},".format(module)
			modules = modules.replace("cogs.", " ")
			e.description = f"**Active Modules:** {modules}"
		await ctx.send(embed=e)

	@commands.command()
	async def reee(self, ctx):
		e = discord.Embed()
		e.description = ""
		for member in ctx.guild.members[:100]:
			e.description += "{}, ".format(member.name)
		await ctx.send(embed=e)

	@commands.command()
	async def lmgtfy(self, ctx, *, query: str):
		msg = query.replace(" ", "+")
		msg = "http://lmgtfy.com/?q={}".format(msg)
		await ctx.send(msg)

	@commands.command()
	async def robohash(self, ctx, user: discord.User):
		"""
		RIP.
		"""
		user = user.name
		await ctx.send("https://robohash.org/{}.png".format(user.replace(" ", "%20")))

	@commands.command()
	async def battery(self, ctx):
		e = discord.Embed()
		luck = self.bot.get_user(264838866480005122)
		percent = psutil.sensors_battery().percent
		charging = psutil.sensors_battery().power_plugged
		e.set_author(name=f'{percent}% Charging = {charging}', icon_url=luck.avatar_url)
		await ctx.send(embed=e)

	@commands.command()
	async def linkie(self, ctx):
		try:
			url = "https://discord.gg/BQ23Z2E"
			e=discord.Embed()
			e.description = f'[4b4t]({url})'
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def guilds(self, ctx):
		s = [f"{guild[0]}: - {guild[2]} members, Owner: {guild[1]}" for guild in sorted([[g.name, g.owner.name, len(g.members)] for g in self.bot.guilds], key=lambda k: k[2], reverse=True)[:100]]
		e=discord.Embed(color=0x80b0ff)
		e.description = f'```{s}```'
		await ctx.send(embed=e)

	@commands.command()
	async def mh(self, ctx):
		def pred(ctx):
			return ctx.author == ctx.author and ctx.channel == ctx.channel
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
		except asyncio.TimeoutError:
			await ctx.send(f'you faggot, you took too long')
		except Exception as e:
			await ctx.send(e)
		else:
			await ctx.send('hmmm {0.content}'.format(msg))

	@commands.command()
	@commands.check(checks.luck)
	async def print(self, ctx, *, arg):
		async with ctx.typing():
			try:
				print("{}: {}".format(ctx.author.name, arg))
				e=discord.Embed(color=0x80b0ff)
				e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				e.description = f'Successfully printed `{arg}` to the console'
				await ctx.message.delete()
				await ctx.send(embed=e, delete_after=5)
			except Exception as e:
				await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	@commands.check(checks.luck)
	async def r(self, ctx, *, arg):
		try:
			await ctx.send(arg)
			await ctx.message.delete()
			e=discord.Embed(description="`{0}`".format(arg), color=0x7030a0)
			e.set_author(name="{0} had me repeat:".format(ctx.author.name), icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			channel = self.bot.get_channel(503902845741957131)
			await channel.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=10)

	@commands.command()
	@commands.check(checks.luck)
	async def leave(self, ctx, guild_id: int=None):
		if guild_id:
			await ctx.send('leaving guild')
			await self.bot.get_guild(guild_id).leave()
		await ctx.send('leaving guild')
		await ctx.guild.leave()

	@commands.command()
	@commands.check(checks.luck)
	async def twist(self, ctx, arg):
		async with ctx.typing():
			await ctx.message.delete()
			await ctx.send("Initiating dick twist ceremony")
			await asyncio.sleep(1)
			await ctx.send("*twists {}'s dick off*".format(arg))
			await asyncio.sleep(0.5)
			await ctx.send("*places {}'s dick inside of ceremonial chalice & grinds it up*".format(arg))
			await asyncio.sleep(0.5)
			await ctx.send("gives {} coffee in which his dick was the coffee grinds".format(arg))

	@commands.command()
	@commands.check(checks.luck)
	async def edit(self, ctx, *, arg):
		try:
			c = 0
			async for msg in ctx.channel.history(limit=3):
				if msg.author.id == self.bot.user.id:
					await msg.edit(content=arg)
					await ctx.message.delete()
					break;
				c += 1
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=5)
			await ctx.message.delete()

	@commands.command(name='luckydelete', aliases=['md'])
	@commands.check(checks.luck)
	async def luckydelete(self, ctx):
		try:
			c = 0
			async for msg in ctx.channel.history(limit=3):
				if c == 1:
					await msg.delete()
					await ctx.message.delete()
					break;
				c += 1
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=5)
			await ctx.message.delete()

# ~== Mod ==~

	@commands.command()
	@commands.check(checks.luck)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def luckykick(self, ctx, user:discord.Member, *, reason:str=None):
		await ctx.guild.kick(user)
		path = os.getcwd() + "/images/bean/" + random.choice(os.listdir(os.getcwd() + "/images/bean/"))	
		e = discord.Embed(color=0x80b0ff)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ {} kicked {} ◈'.format(ctx.message.author.name, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()
		log=discord.Embed(description="`kicked {0}`".format(user), color=0xff0000)
		log.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		log.set_thumbnail(url=ctx.guild.icon_url)
		channel = self.bot.get_channel(503902845741957131)
		await channel.send(embed=log)

	@commands.command()
	@commands.check(checks.luck)
	@commands.cooldown(1, 25, commands.BucketType.user)
	async def luckyban(self, ctx, user:discord.Member, *, reason=None):
		await ctx.guild.ban(user)
		path = os.getcwd() + "/images/bean/" + random.choice(os.listdir(os.getcwd() + "/images/bean/"))	
		e = discord.Embed(color=0x80b0ff)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ {} banned {} ◈'.format(ctx.message.author.name, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()
		log=discord.Embed(description="`kicked {}`".format(user), color=0xAA0114)
		log.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		log.set_thumbnail(url=ctx.guild.icon_url)
		channel = self.bot.get_channel(503902845741957131)
		await channel.send(embed=log)

# ~== Fun ==~

	@commands.command()
	@commands.check(checks.luck)
	async def luckyspam(self, ctx, times: int, *, content='Format: .spam numberofmessages "content"'):
		for i in range(times):
			await ctx.send(content)
			await asyncio.sleep(1)

	@commands.command()
	@commands.check(checks.luck)
	async def antitother(self, ctx, times: int):
		for i in range(times):
			await ctx.send(random.choice(["Fagitos", "https://discord.gg/BQ23Z2E", "Reeeeeeeeeeeeeeeeeeeeeee", "<@355026215137968129>", "pUrE wHiTe pRiVelIdgEd mALe", "there's a wasp sucking out all my stick juices", "Really? That's the sperm that won?", "May the fly be with you", "You're not you when you're hungry", "I recognize that flower, see you soon :)", "FBI OPEN UP", "Sponsored by Samsung", "iLiKe NuT", "Florin joins, Yall dislocate yo joints...", "old school tricks rise again", "i can't see, my thumbs are in the way", "All Heil nut", "SARGON NEED MORE DOPAMINE", ".prune 1000", "Nani", "I’m more blind then Hitler when he had that chlorine gas up in his eye", "real art^", "2b2t.org is a copy of the middle east", "warned for advertising", "jOiN sR", "6 million juice", "The 7th SR Fag", "7th team lgbt", "DAiLy reMinDer sEx RoboTs coSt lesS thAn ReAl gRilLs", "elon's musk", "Fuck the battle cat", "9/11"]))

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if "4B4T" in m.guild.name:
				if m.author.name == "Legit":
					if "purchase" in m.content or "$" in m.content:
						await m.delete()
			if m.content.lower().startswith("pls magik <@264838866480005122>"):
				def pred(m):
					return m.author.id == 270904126974590976 and m.channel == m.channel

				try:
					msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
				except asyncio.TimeoutError:
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
				else:
					await asyncio.sleep(0.5)
					await msg.delete()
					await m.channel.send("next time i ban you")
			commands = ["t!avatar <@264838866480005122>", ".avatar <@264838866480005122>",
			            "./avatar <@264838866480005122>", "t.avatar <@264838866480005122>"]
			bots = [506735111543193601, 418412306981191680, 172002275412279296, 452289354296197120]
			if m.content.lower() in commands:
				def pred(m):
					return m.author.id in bots and m.channel == m.channel

				try:
					msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
				except asyncio.TimeoutError:
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
				else:
					await asyncio.sleep(0.5)
					await msg.delete()
					await m.channel.send("next time i ban you")

def setup(bot):
	bot.add_cog(Dev(bot))
