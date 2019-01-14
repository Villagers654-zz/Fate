from PIL import Image, ImageDraw
from discord.ext import commands
import discord
import asyncio
import random
import psutil
import os

class Dev:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def tothy(ctx):
		return ctx.message.author.id == 355026215137968129

	def zerotwo(ctx):
		return ctx.message.author.id == 261569654646898688

	def puffy(ctx):
		return ctx.message.author.id == 257560165488918529

# ~== Core ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_dev(self, ctx):
		await ctx.send('working')

# ~== Main ==~)

	@commands.command()
	async def arg_test(self, ctx, ree=""):
		if len(ree) > 0:
			await ctx.send(";-;")
		else:
			await ctx.send(".-.")

	@commands.command()
	async def ltr(self, ctx):
		await ctx.send(u"\u200E")

	@commands.command()
	async def rtl(self, ctx):
		await ctx.send(u"\u200F")

	@commands.command()
	@commands.check(luck)
	async def testsend(self, *, message):
		await self.bot.get_user(264838866480005122).send(message)

	async def on_member_join(self,m:discord.Member):
		if m.guild.id ==470961230362837002:
			if m.id ==255433446220890112:
				await m.guild.ban(m, reason="faggotry")
				c = self.bot.get_channel(502236124308307968)
				await c.send("the faggot has been banned.")

	@commands.command()
	async def messagecount(self, ctx, times):
		for i in range(times):
			count = 1
			async for msg in ctx.channel.history(limit=100000):
				count += 1
		await ctx.send(count)

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
	async def members(self, ctx):
		await ctx.send(ctx.guild.members)

	@commands.command()
	async def draw(self, ctx):
		try:
			img = Image.new('RGB', (100, 30), color=(73, 109, 137))
			d = ImageDraw.Draw(img)
			d.text((10, 10), "Hello World", fill=(255, 255, 0))
			img.save('text.png')
			e = discord.Embed()
			path = os.getcwd()
			e.set_image(url="attachment:///" + path)
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(e)

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
		try:
			s = [f"{guild[0]}: - {guild[2]} members, Owner: {guild[1]}" for guild in sorted([[g.name, g.owner.name, len(g.members)] for g in self.bot.guilds], key=lambda k: k[2], reverse=True)[:100]]
			e=discord.Embed(color=0x80b0ff)
			e.description = f'```{s}```'
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

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
	async def freq(self, ctx):
		await ctx.send(psutil.cpu_freq())

	@commands.command()
	async def pids(self, ctx):
		await ctx.send(psutil.pids())

	@commands.command()
	async def temp(self, ctx):
		await ctx.send(psutil.sensors_temperatures())

	@commands.command()
	async def net(self, ctx):
		await ctx.send(psutil.net_if_stats())

	@commands.command(name='ram', aliases=['wam'])
	async def ram(self, ctx):
		try:
			def bytes2human(n):
				symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
				prefix = {}
				for i, s in enumerate(symbols):
					prefix[s] = 1 << (i + 1) * 10
				for s in reversed(symbols):
					if n >= prefix[s]:
						value = float(n) / prefix[s]
						return '%.1f%s' % (value, s)
				return "%sB" % n
			p = psutil.Process(os.getpid())
			botram = p.memory_full_info().rss
			ramused = psutil.virtual_memory().used
			ramtotal = psutil.virtual_memory().total
			await ctx.send(f'[{bytes2human(ramused)}, {bytes2human(ramtotal)}]')
		except Exception as e:
				await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	@commands.check(luck)
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
	@commands.check(luck)
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
	@commands.check(luck)
	async def retreat(self, ctx):
		await ctx.send('leaving guild')
		await ctx.guild.leave()

	@commands.command()
	@commands.check(luck)
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
	@commands.check(luck)
	async def edit(self, ctx, *, arg):
		try:
			c = 0
			async for msg in ctx.channel.history(limit=3):
				if c == 1:
					await msg.edit(content=arg)
					await ctx.message.delete()
					break;
				c += 1
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=5)
			await ctx.message.delete()

	@commands.command(name='luckydelete', aliases=['md'])
	@commands.check(luck)
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
	@commands.check(luck)
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
	@commands.check(luck)
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
	@commands.check(luck)
	async def luckyspam(self, ctx, times: int, *, content='Format: .spam numberofmessages "content"'):
		for i in range(times):
			await ctx.send(content)
			await asyncio.sleep(1)

	@commands.command()
	@commands.check(luck)
	async def antitother(self, ctx, times: int):
		for i in range(times):
			await ctx.send(random.choice(["Fagitos", "https://discord.gg/BQ23Z2E", "Reeeeeeeeeeeeeeeeeeeeeee", "<@355026215137968129>", "pUrE wHiTe pRiVelIdgEd mALe", "there's a wasp sucking out all my stick juices", "Really? That's the sperm that won?", "May the fly be with you", "You're not you when you're hungry", "I recognize that flower, see you soon :)", "FBI OPEN UP", "Sponsored by Samsung", "iLiKe NuT", "Florin joins, Yall dislocate yo joints...", "old school tricks rise again", "i can't see, my thumbs are in the way", "All Heil nut", "SARGON NEED MORE DOPAMINE", ".prune 1000", "Nani", "I’m more blind then Hitler when he had that chlorine gas up in his eye", "real art^", "2b2t.org is a copy of the middle east", "warned for advertising", "jOiN sR", "6 million juice", "The 7th SR Fag", "7th team lgbt", "DAiLy reMinDer sEx RoboTs coSt lesS thAn ReAl gRilLs", "elon's musk", "Fuck the battle cat", "9/11"]))

def setup(bot):
	bot.add_cog(Dev(bot))
