from utils import bytes2human as p, config
from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import psutil
import json
import time
import os

class Menus(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="help")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def _help(self, ctx, command=None):
		if command:
			for cmd in self.bot.commands:
				if command == str(cmd):
					return await ctx.send(cmd.description)
			return await ctx.send("Either the command wasn't found or it has no help message")
		e = discord.Embed(title="~~~====🥂🍸🍷Help🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="◈ Core ◈", value="`leaderboard` `gleaderboard` `ggleaderboard` `mleaderboard` `gmleaderboard` `vcleaderboard` `gvcleaderboard` `changelog` `partners` `discords` `servers` `config` `prefix` `realms` `links` `ping` `info` `say`", inline=False)
		e.add_field(name="◈ Responses ◈", value="**`disableresponses` `enableresponses`:** `@Fate` `hello` `ree` `kys` `gm` `gn`", inline=False)
		e.add_field(name="◈ Music ◈", value="`join` `summon` `play` `stop` `skip` `pause` `resume` `volume` `queue` `thumbnail` `remove` `shuffle` `dc` `np`", inline=False)
		e.add_field(name="◈ Utility ◈", value="`channelinfo` `servericon` `serverinfo` `userinfo` `test_color` `makepoll` `welcome` `farewell` `logger` `emoji` `addemoji` `stealemoji` `rename_emoji` `delemoji` `owner` `avatar` `topic` `timer` `note` `quicknote` `notes` `wiki` `find` `ud` `id`", inline=False)
		e.add_field(name="◈ Reactions ◈", value="`tenor` `intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `psycho` `thonk` `shrug` `bite` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`", inline=False)
		e.add_field(name="◈ Mod ◈", value="`mute` `unmute` `vcmute` `vcunmute` `warn` `clearwarns` `addrole` `removerole` `restore_roles` `selfroles` `autorole` `limit` `audit` `lock` `lockb` `delete` `purge` `purge_user` `purge_images` `purge_embeds` `purge_bots` `nick` `massnick` `kick` `mute` `ban` `pin`", inline=False)
		e.add_field(name="◈ Fun ◈", value="`personality` `liedetector` `chatbot` `fancify` `coffee` `encode` `decode` `choose` `notice` `quote` `mock` `meme` `rate` `roll` `soul` `gay` `sue` `fap` `ask` `rps` `rr` `cookie` `shoot` `inject` `slice` `boop` `stab` `kill`", inline=False)
		try:
			await ctx.author.send(embed=e)
			await ctx.send("Help menu sent to your dm ✅")
		except:
			await ctx.send("Failed to send help menu to dm ❎", embed=e)
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=25)
			except asyncio.TimeoutError:
				pass
			else:
				if msg.content.lower() == "k":
					await ctx.message.delete()
					await asyncio.sleep(0.5)
					await msg.delete()
					async for msg in ctx.channel.history(limit=10):
						if msg.author.id == self.bot.user.id:
							if len(msg.embeds) > 0:
								await msg.delete()
							break

	@commands.command(name='info', description="Provides information relevant to the bots stats")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def info(self, ctx):
		m, s = divmod(time.time() - self.bot.START_TIME, 60)
		h, m = divmod(m, 60)
		guilds = len(list(self.bot.guilds))
		users = len(list(self.bot.users))
		path = os.getcwd() + "/data/images/banners/" + random.choice(os.listdir(os.getcwd() + "/data/images/banners/"))
		bot_pid = psutil.Process(os.getpid())
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name="Fate [Zerø]: Core Info", icon_url=self.bot.get_user(config.owner_id()).avatar_url)
		if isfile('./data/stats.json'):
			with open('./data/stats.json', 'r') as f:
				e.description = f'Commands Used: {json.load(f)["commands"]}'
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		e.add_field(name="◈ Summary ◈", value="Fate is a ~~multipurpose~~ hybrid bot created for ~~sexual assault~~ fun", inline=False)
		e.add_field(name="◈ Credits ◈", value="• Tothy ~ `rival`\n• Cortex ~ `teacher`", inline=False)
		e.add_field(name="◈ Statistics ◈", value=f'Commands: [{len(self.bot.commands)}]\nModules: [{len(self.bot.extensions)}]\nServers: [{guilds}]\nUsers: [{users}]', inline=False)
		e.add_field(name="◈ Memory ◈", value=
		f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
		f"__**RAM**__: [{p.bytes2human(psutil.virtual_memory().used)}/{p.bytes2human(psutil.virtual_memory().total)}] ({psutil.virtual_memory().percent}%)\n"
		f"__**Bot RAM**__: {p.bytes2human(bot_pid.memory_full_info().rss)} ({round(bot_pid.memory_percent())}%)\n"
		f"__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {bot_pid.cpu_percent(interval=1)}%\n")
		e.set_footer(text="Uptime: {} Hours {} Minutes {} seconds".format(int(h), int(m), int(s)))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			if msg.content.lower() == "k":
				await ctx.message.delete()
				await asyncio.sleep(0.5)
				await msg.delete()
				async for msg in ctx.channel.history(limit=10):
					if msg.author.id == self.bot.user.id:
						if len(msg.embeds) > 0:
							await msg.delete()
							break

	@commands.command(name="discords")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def discords(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Discords🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy Community", value="[Bridge of Anarchism](https://discord.gg/WN9F82d)\n[2p2e - 2pocket2edition](https://discord.gg/y4V4T84)\n[4B4T (Official)](https://discord.gg/BQ23Z2E)\n[4b4t §pawn Patrol](https://discord.gg/5hn4K8E)", inline=False)
		e.add_field(name="• Games", value="[PUBG Mobile](https://discord.gg/gVe27r4)", inline=False)
		e.add_field(name="• Misc", value="[Memes (Tothers Hotel)](https://discord.gg/TzGNyRg)\n[Threadys Alpha server](https://discord.gg/6tcqMUt)", inline=False)
		await ctx.send(embed=e)
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			if msg.content.lower() == "k":
				await ctx.message.delete()
				await asyncio.sleep(0.5)
				await msg.delete()
				async for msg in ctx.channel.history(limit=10):
					if msg.author.id == self.bot.user.id:
						if len(msg.embeds) > 0:
							await msg.delete()
							break

	@commands.command(name="servers")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def servers(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Servers🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy", value="• 4b4t.net : 19132", inline=False)
		await ctx.send(embed=e)
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			if msg.content.lower() == "k":
				await ctx.message.delete()
				await asyncio.sleep(0.5)
				await msg.delete()
				async for msg in ctx.channel.history(limit=10):
					if msg.author.id == self.bot.user.id:
						if len(msg.embeds) > 0:
							await msg.delete()
							break

	@commands.command(name="realms")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def realms(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Realms🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy Realms", value="Jappie Anarchy\n• https://realms.gg/pmElWWx5xMk\nAnarchy Realm\n• https://realms.gg/GyxzF5xWnPc\n2c2b Anarchy\n• https://realms.gg/TwbBfe0jGDc\nFraughtian Anarchy\n• https://realms.gg/rdK57KvnA8o\nChaotic Realm\n• https://realms.gg/nzDX1drovu4", inline=False)
		e.add_field(name="• Misc", value=".", inline=False)
		await ctx.send(embed=e)
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			if msg.content.lower() == "k":
				await ctx.message.delete()
				await asyncio.sleep(0.5)
				await msg.delete()
				async for msg in ctx.channel.history(limit=10):
					if msg.author.id == self.bot.user.id:
						if len(msg.embeds) > 0:
							await msg.delete()
							break

	@commands.command(name="partners")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
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
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			if msg.content.lower() == "k":
				await ctx.message.delete()
				await asyncio.sleep(0.5)
				await msg.delete()
				async for msg in ctx.channel.history(limit=10):
					if msg.author.id == self.bot.user.id:
						if len(msg.embeds) > 0:
							await msg.delete()
							break

def setup(bot):
	bot.add_cog(Menus(bot))
