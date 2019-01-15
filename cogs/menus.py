from discord.ext import commands
import discord
import random
import psutil
import time
import os

class Menus:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Core ==~

	@commands.command()
	@commands.check(luck)
	async def test_menus(self, ctx):
		await ctx.send('working')

# ~== Help Menus ==~

	@commands.group(name='help')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _help(self, ctx):
		if ctx.invoked_subcommand is None:
			e = discord.Embed(title="~~~====🥂🍸🍷Help🍷🍸🥂====~~~", color=0x80b0ff)
			e.add_field(name="◈ Information ◈", value="**Dev:** Luck#1574\n**Version:** 1.0.0a\n**Prefix:** `.`", inline=False)
			e.add_field(name="◈ Commands ◈", value="• core ~ `main bot usage`\n• react ~ `reaction gifs / images`\n• mod ~ `moderation commands`\n• fun ~ `entertaining stuff`\n• art ~ `subpar textart ヽ(ﾟｰﾟ)ﾉ`\n• e ~ `embed usage help`", inline=False)
			await ctx.send(embed=e)

	@_help.command(name='core')
	async def _core(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Core🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="◈ Main ◈", value="`ggleaderboard` `gleaderboard` `leaderboard` `repeat` `stalk` `links` `ping` `info`", inline=False)
		e.add_field(name="◈ Utility ◈", value="`channelinfo` `servericon` `serverinfo` `userinfo` `makepoll` `welcome` `owner` `avatar` `topic` `timer` `note` `wiki` `ud` `id`", inline=False)
		e.add_field(name="◈ Responses ◈", value="`hello` `ree` `gm` `gn`", inline=False)
		e.add_field(name="◈ Music ◈", value="`join` `summon` `play` `stop` `skip` `pause` `resume` `volume` `queue` `remove` `shuffle` `dc` `np`", inline=False)
		e.add_field(name="◈ Ads ◈", value="`discords` `servers` `realms`", inline=False)
		await ctx.send(embed=e)

	@_help.command(name='react')
	async def _react(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Reactions🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• FAQ", value="• Some commands may require you to add\ncontent after. For example: `.hug @person`", inline=False)
		e.add_field(name="• Commands", value="`intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `psycho` `thonk` `shrug` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`", inline=False)
		await ctx.send(embed=e)

	@_help.command(name='mod')
	async def _mod(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Mod🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Commands", value="`mute` `unmute` `vcmute` `vcunmute` `warn` `clearwarns` `delete` `purge` `nick` `massnick` `kick` `mute` `ban` `pin`", inline=False)
		await ctx.send(embed=e)

	@_help.command(name='fun')
	async def _fun(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Fun🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Core", value="`fancify` `coffee` `encode` `decode` `choose` `notice` `meme` `quote` `rate` `roll` `gay` `sue` `fap` `ask` `rps` `rr`", inline=False)
		e.add_field(name="• Actions", value="`crucify` `cookie` `shoot` `inject` `slice` `boop` `stab` `kill`", inline=False)
		e.add_field(name="• Responses", value="`@Fate` `Kys`", inline=False)
		await ctx.send(embed=e)

	@_help.command(name='art')
	async def _art(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷TextArt🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Commands", value="• chill ~ `wavey (~˘▾˘)~`\n• fuckit ~ `fuck itヽ(ﾟｰﾟ)ﾉ`\n• cross ~ `yield (╬ Ò ‸ Ó)`\n• angry ~ `(ノಠ益ಠ)ノ彡┻━┻`\n• yes ~ `thumbs up 👍`", inline=True)
		await ctx.send(embed=e)

	@_help.command(name='m')
	async def _m(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Misc🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Math", value="`add` `subtract` `multiply` `divide`", inline=False)
		await ctx.send(embed=e)

	@_help.command(name='e')
	async def _e(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Embeds🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="FAQ", value="• Field = {name} {value}\n• Color = {hex}", inline=False)
		e.add_field(name="• Usage", value="• embeda ~ `simple content embed {content}`\n• embedb ~ `{title} {name} {value}`\n• embedc ~ `{title} {url} {name} {value}`\n• embedu `{title} {url} {color} + 2 fields`\n• embedx ~ `{title} {url} {color} {name}\n{value} {name} {value} {name} {value}`", inline=True)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def core(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Core🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="◈ Main ◈", value="`ggleaderboard` `gleaderboard` `leaderboard` `repeat` `stalk` `links` `ping` `info`", inline=False)
		e.add_field(name="◈ Utility ◈", value="`channelinfo` `servericon` `serverinfo` `userinfo` `makepoll` `welcome` `owner` `avatar` `topic` `timer` `note` `wiki` `ud` `id`", inline=False)
		e.add_field(name="◈ Responses ◈", value="`hello` `ree` `gm` `gn`", inline=False)
		e.add_field(name="◈ Music ◈", value="`join` `summon` `play` `stop` `skip` `pause` `resume` `volume` `queue` `remove` `shuffle` `dc` `np`", inline=False)
		e.add_field(name="◈ Ads ◈", value="`discords` `servers` `realms`", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def react(self, ctx):
		e = discord.Embed(title="~~~====🥂🍸🍷Reactions🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• FAQ", value="• Some commands may require you to add\ncontent after. For example: `.hug @person`", inline=False)
		e.add_field(name="• Commands", value="`intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `psycho` `thonk` `shrug` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def mod(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Mod🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Commands", value="`mute` `unmute` `vcmute` `vcunmute` `warn` `clearwarns` `delete` `purge` `nick` `massnick` `kick` `mute` `ban` `pin`", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def fun(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Fun🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Core", value="`fancify` `coffee` `encode` `decode` `choose` `notice` `meme` `quote` `rate` `roll` `gay` `sue` `fap` `ask` `rps` `rr`", inline=False)
		e.add_field(name="• Actions", value="`crucify` `cookie` `shoot` `inject` `slice` `boop` `stab` `kill`", inline=False)
		e.add_field(name="• Responses", value="`@Fate` `Kys`", inline=False)
		await ctx.send(embed=e)

	@commands.command()
	async def art(self, ctx):
		embed=discord.Embed(title="~~~====🥂🍸🍷TextArt🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="• Commands", value="• chill ~ `wavey (~˘▾˘)~`\n• fuckit ~ `fuck itヽ(ﾟｰﾟ)ﾉ`\n• cross ~ `yield (╬ Ò ‸ Ó)`\n• angry ~ `(ノಠ益ಠ)ノ彡┻━┻`\n• yes ~ `thumbs up 👍`", inline=True)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def m(self, ctx):
		e = discord.Embed()
		embed=discord.Embed(title="~~~====🥂🍸🍷Misc🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="• Math", value="`add` `subtract` `multiply` `divide`", inline=False)
		await ctx.send(embed=embed)

	@commands.command()
	async def e(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Embeds🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="FAQ", value="• Field = {name} {value}\n• Color = {hex}", inline=False)
		e.add_field(name="• Usage", value="• embeda ~ `simple content embed {content}`\n• embedb ~ `{title} {name} {value}`\n• embedc ~ `{title} {url} {name} {value}`\n• embedu `{title} {url} {color} + 2 fields`\n• embedx ~ `{title} {url} {color} {name}\n{value} {name} {value} {name} {value}`", inline=True)
		await ctx.send(embed=e)

# ~== Bot ==~

	@commands.command(name='info')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def info(self, ctx):
		try:
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
			storageused = psutil.disk_usage('/').used
			storagetotal = psutil.disk_usage('/').total
			path = os.getcwd() + "/data/images/banners/" + random.choice(os.listdir(os.getcwd() + "/data/images/banners/"))
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name="Fate [Zerø]: Core Info", icon_url=luck.avatar_url)
			e.description = f'https://discord.gg/BQ23Z2E'
			e.set_thumbnail(url=fate.avatar_url)
			e.set_image(url="attachment://" + os.path.basename(path))
			e.add_field(name="◈ Summary ◈", value="Fate is a ~~multipurpose~~ hybrid bot created for fun, tuned to work how I personally want it to, and great for passing time", inline=False)
			e.add_field(name="◈ Credits ◈", value="• Tothy ~ `inspiration & rival`\n• Cortex ~ `teacher & reee`", inline=False)
			e.add_field(name="◈ Statistics ◈", value=f'Servers: [{guilds}]\nUsers: [{users}]', inline=False)
			e.add_field(name="◈ Memory ◈", value=f'__**Storage**__: [{bytes2human(storageused)}/{bytes2human(storagetotal)}]\n__**RAM**__: **Global**: {bytes2human(ramused)} **Bot**: {bytes2human(botram)} ({rampercent}%)\n__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%')
			e.set_footer(text="Uptime: {} Hours {} Minutes {} seconds".format(int(h), int(m), int(s)))
			await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

# ~== Ads ==~

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def discords(self, ctx):
		e = discord.Embed()
		embed=discord.Embed(title="~~~====🥂🍸🍷Discords🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="• Anarchy Community", value="[Bridge of Anarchism](https://discord.gg/WN9F82d)\n[2p2e - 2pocket2edition](https://discord.gg/y4V4T84)\n[4B4T (Official)](https://discord.gg/BQ23Z2E)\n[4b4t §pawn Patrol](https://discord.gg/5hn4K8E)", inline=False)
		embed.add_field(name="• Games", value="[PUBG Mobile](https://discord.gg/gVe27r4)", inline=False)
		embed.add_field(name="• Misc", value="[Memes (Tothers Hotel)](https://discord.gg/TzGNyRg)\n[Threadys Alpha server](https://discord.gg/6tcqMUt)", inline=False)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def servers(self, ctx):
		e = discord.Embed()
		embed=discord.Embed(title="~~~====🥂🍸🍷Servers🍷🍸🥂====~~~", color=0x80b0ff)
		embed.add_field(name="• Anarchy", value="• 4b4t.net : 19132", inline=False)
		await ctx.send(embed=embed)

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
		try:
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
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

# ~== Misc ==~

	@commands.command(name='links', aliases=['invite', 'support'])
	async def links(self, ctx):
		try:
			fate = self.bot.get_user(506735111543193601)
			luck = self.bot.get_user(264838866480005122)
			e=discord.Embed(color=0x80b0ff)
			e.set_author(name=f'| Links | 📚', icon_url=luck.avatar_url)
			e.set_thumbnail(url=random.choice(["https://cdn.discordapp.com/attachments/501871950260469790/513636718835007488/kisspng-computer-icons-message-icon-design-download-invite-5abf1e6f0905a2.045504771522474607037.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636728733433857/mail-open-outline.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636736492896271/mail-open-solid.png"]))
			e.description = f'[Invite](https://discordapp.com/oauth2/authorize?client_id=506735111543193601&permissions=485878886&scope=bot) 📥\n[Support](https://discord.gg/HkeCzSw) 📧\n[Discord](https://discord.gg/BQ23Z2E) <:discord:513634338487795732>'
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def partners(self, ctx):
		try:
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
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

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
