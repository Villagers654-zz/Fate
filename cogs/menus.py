from data.utils import converter as c
from data.misc import menus as m
from discord.ext import commands
import discord
import random
import psutil
import time
import os

class Menus:
	def __init__(self, bot):
		self.bot = bot

	@commands.group(name='help')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _help(self, ctx):
		if ctx.invoked_subcommand is None:
			e = discord.Embed(title="~~~====🥂🍸🍷Help🍷🍸🥂====~~~", color=0x80b0ff)
			e.add_field(name="◈ Information ◈", value=
			"**Dev:** Luck#1574\n"
			"**Version:** 1.0.0a\n"
			"**Prefix:** `.`", inline=False)
			e.add_field(name="◈ Commands ◈", value=
			"• core ~ `main bot usage`\n"
			"• utility ~ `helpful commands`\n"
			"• react ~ `reaction gifs / images`\n"
			"• mod ~ `moderation commands`\n"
			"• fun ~ `entertaining stuff`\n"
			"• art ~ `subpar textart ヽ(ﾟｰﾟ)ﾉ`", inline=False)
			await ctx.send(embed=e)

	@_help.command(name='core')
	async def _core(self, ctx):
		await ctx.send(embed=m.core)

	@_help.command(name='utility')
	async def _utility(self, ctx):
		await ctx.send(embed=m.utility)

	@_help.command(name='react')
	async def _react(self, ctx):
		await ctx.send(embed=m.react)

	@_help.command(name='mod')
	async def _mod(self, ctx):
		await ctx.send(embed=m.mod)

	@_help.command(name='fun')
	async def _fun(self, ctx):
		await ctx.send(embed=m.fun)

	@_help.command(name='art')
	async def _art(self, ctx):
		await ctx.send(embed=m.art)

	@_help.command(name='m')
	async def _m(self, ctx):
		await ctx.send(embed=m.m)

	@_help.command(name='e')
	async def _e(self, ctx):
		await ctx.send(embed=m.e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def core(self, ctx):
		await ctx.send(embed=m.core)

	@commands.command()
	async def utility(self, ctx):
		await ctx.send(embed=m.utility)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def react(self, ctx):
		await ctx.send(embed=m.react)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def mod(self, ctx):
		await ctx.send(embed=m.mod)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def fun(self, ctx):
		await ctx.send(embed=m.fun)

	@commands.command()
	async def art(self, ctx):
		await ctx.send(embed=m.art)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def m(self, ctx):
		await ctx.send(embed=m.m)

	@commands.command()
	async def e(self, ctx):
		await ctx.send(embed=m.e)

	@commands.command(name='info')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def info(self, ctx):
		m, s = divmod(time.time() - self.bot.START_TIME, 60)
		h, m = divmod(m, 60)
		p = psutil.Process(os.getpid())
		guilds = len(list(self.bot.guilds))
		users = len(list(self.bot.users))
		fate = self.bot.get_user(506735111543193601)
		luck = self.bot.get_user(264838866480005122)
		botram = p.memory_full_info().rss
		ramused = psutil.virtual_memory().used
		rampercent = psutil.virtual_memory().percent
		storageused = psutil.disk_usage('/').used
		storagetotal = psutil.disk_usage('/').total
		path = os.getcwd() + "/data/images/banners/" + random.choice(os.listdir(os.getcwd() + "/data/images/banners/"))
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name="Fate [Zerø]: Core Info", icon_url=luck.avatar_url)
		e.description = f'https://discord.gg/BQ23Z2E'
		e.set_thumbnail(url=fate.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		e.add_field(name="◈ Summary ◈", value="Fate is a ~~multipurpose~~ hybrid bot created for fun", inline=False)
		e.add_field(name="◈ Credits ◈", value="• Tothy ~ `inspiration & rival`\n• Cortex ~ `teacher & reee`", inline=False)
		e.add_field(name="◈ Statistics ◈", value=f'Servers: [{guilds}]\nUsers: [{users}]', inline=False)
		e.add_field(name="◈ Memory ◈", value=
		f'__**Storage**__: [{c.bytes2human(storageused)}/{c.bytes2human(storagetotal)}]\n'
		f'__**RAM**__: **Global**: {c.bytes2human(ramused)} **Bot**: {c.bytes2human(botram)} ({rampercent}%)\n'
		f'__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%')
		e.set_footer(text="Uptime: {} Hours {} Minutes {} seconds".format(int(h), int(m), int(s)))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

# ~== Ads ==~

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def discords(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Discords🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy Community", value="[Bridge of Anarchism](https://discord.gg/WN9F82d)\n[2p2e - 2pocket2edition](https://discord.gg/y4V4T84)\n[4B4T (Official)](https://discord.gg/BQ23Z2E)\n[4b4t §pawn Patrol](https://discord.gg/5hn4K8E)", inline=False)
		e.add_field(name="• Games", value="[PUBG Mobile](https://discord.gg/gVe27r4)", inline=False)
		e.add_field(name="• Misc", value="[Memes (Tothers Hotel)](https://discord.gg/TzGNyRg)\n[Threadys Alpha server](https://discord.gg/6tcqMUt)", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def servers(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Servers🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy", value="• 4b4t.net : 19132", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def realms(self, ctx):
		e = discord.Embed()
		embed=discord.Embed(title="~~~====🥂🍸🍷Realms🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="• Anarchy Realms", value="Jappie Anarchy\n• https://realms.gg/pmElWWx5xMk\nAnarchy Realm\n• https://realms.gg/GyxzF5xWnPc\n2c2b Anarchy\n• https://realms.gg/TwbBfe0jGDc\nFraughtian Anarchy\n• https://realms.gg/rdK57KvnA8o\nChaotic Realm\n• https://realms.gg/nzDX1drovu4", inline=False)
		embed.add_field(name="• Misc", value=".", inline=False)
		await ctx.send(embed=embed)

# ~== 4B4T ==~

	async def on_message(self, message: discord.Message):
		if not message.author.bot:
			if message.content.startswith(".4b4t"):
				guild = self.bot.get_guild(470961230362837002)
				e=discord.Embed(title=guild.name, color=0x0000ff)
				e.set_thumbnail(url=guild.icon_url)
				e.add_field(name="◈ Main Info ◈", value="• be sure to mention a mod\nhouse keeper or higher to\nget the player role if you\nplay on the mc server", inline=False)
				e.add_field(name="◈ Server Info ◈", value="**ip:** 4b4t.net : 19132\n**Version:** 1.7.0", inline=False)
				e.add_field(name="◈ Commands ◈", value="• submitmotd ~ `submits a MOTD`\n• reportbug ~ `report a bug`\n• rules ~ `4b4t's discord rules`\n• vote ~ `vote for 4b4t`", inline=False)
				await message.channel.send(embed=e)

	@commands.command()
	async def specs(self, ctx):
		m, s = divmod(time.time() - self.bot.START_TIME, 60)
		h, m = divmod(m, 60)
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
		guilds = len(list(self.bot.guilds))
		users = len(list(self.bot.users))
		guild = self.bot.get_guild(470961230362837002)
		fate = self.bot.get_user(506735111543193601)
		luck = self.bot.get_user(264838866480005122)
		botram = p.memory_full_info().rss
		ramused = psutil.virtual_memory().used
		ramtotal = psutil.virtual_memory().total
		rampercent = psutil.virtual_memory().percent
		cpupercent = psutil.cpu_percent(interval=1)
		cpucount = psutil.cpu_count()
		storageused = psutil.disk_usage('/').used
		storagetotal = psutil.disk_usage('/').total
		await ctx.send(f'Storage [{bytes2human(storagetotal)}]\nRAM: [{bytes2human(ramtotal)}]\nCPU Count [{cpucount}]')

# ~== Misc ==~

	@commands.command()
	async def partners(self, ctx):
		luck = self.bot.get_user(264838866480005122)
		bottest = self.bot.get_guild(501868216147247104)
		fourbfourt = "https://discord.gg/BQ23Z2E"
		totherbot = "https://discordapp.com/api/oauth2/authorize?client_id=452289354296197120&permissions=0&scope=bot"
		spookiehotel = "https://discord.gg/DVcF6Yn"
		threadysserver = "https://discord.gg/6tcqMUt"
		e=discord.Embed(color=0xffffff)
		e.set_author(name=f'🥃🥂🍸🍷Partners🍷🍸🥂🥃', icon_url=luck.avatar_url)
		e.description = "Wanna partner? dm Luck#1574"
		e.set_thumbnail(url=bottest.icon_url)
		e.add_field(name="◈ Servers ◈", value=f'• [Threadys Server]({threadysserver})\n• [Spookie Hotel]({spookiehotel})\n• [4b4t]({fourbfourt})', inline=False)
		e.add_field(name="◈ Bots ◈", value=f'• [TotherBot]({totherbot})', inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def credits(self, ctx, content='repeating'):
		e = discord.Embed()
		embed=discord.Embed(title="~~~====🥂🍸🍷Credits🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="CortexPE#8680", value="• Tought me litterally 99.9% of fates code (and dealt with my storms of questions)", inline=False)
		embed.add_field(name="Tothy", value="• existed", inline=False)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Menus(bot))
