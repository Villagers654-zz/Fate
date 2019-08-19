from utils import bytes2human as p, config, colors
from discord.ext import commands
from datetime import datetime
import platform
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

	async def wait_for_dismissal(self, ctx, msg):
		def pred(m):
			return m.channel.id == ctx.channel.id and m.content.lower().startswith('k')
		try:
			reply = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			await asyncio.sleep(0.21)
			await ctx.message.delete()
			await asyncio.sleep(0.21)
			await msg.delete()
			await asyncio.sleep(0.21)
			await reply.delete()

	@commands.command(name='help')
	@commands.cooldown(1, 60, commands.BucketType.user)
	@commands.cooldown(1, 3, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
	async def help(self, ctx):
		async def wait_for_reaction()->list:
			def check(reaction, user):
				return user == ctx.author
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except asyncio.TimeoutError:
				return [None, None]
			else:
				return [reaction, str(reaction.emoji)]
		def default():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Help🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			usage = '• using a cmd with no args will usually send its help menu\n' \
			    '• try using `.module enable` instead of `.enable module`'
			e.add_field(name='◈ Basic Bot Usage', value=usage)
			categories = '• **Core** - `main bot commands`\n' \
				'• **Mod** - `moderation commands`\n' \
			    '• **Utility** - `helpful commands`\n' \
			    '• **Fun** - `fun games/commands`\n' \
			    '• **Music** - `play music in vc :D`'
			e.add_field(name='◈ Categories', value=categories)
			return e
		def core():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Core🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = '• **info** `depending on your args it provides information for users/roles/channels & invites`\n' \
				'• **sinfo** - `sends server info`\n' \
			    '• **leaderboard** - `servers lvl/xp ranking`\n' \
			    '• **gleaderboard** - `global lvl/xp ranking`\n' \
			    '• **ggleaderboard** - `global server ranking`\n' \
			    '• **mleaderboard** - `monthly server ranking`\n' \
			    '• **gmleaderboard** - `global monthly ranking`\n' \
			    '• **vcleaderboard** - `voicecall leaderboard`\n' \
			    '• **gvcleaderboard** - `global vc leaderboard`\n' \
			    '• **partners** - `fates partnered bots/servers`\n' \
			    '• **servers** - `featured server list`\n' \
			    '• **restrict** - `block ppl/channels from using cmds`\n' \
			    '• **unrestrict** - `undoes the following^`\n' \
			    '• **restricted** - `lists restricted channels/users`\n' \
			    '• **config** - `sends toggles for core modules`\n' \
			    '• **prefix** - `lets you change the bots prefix`\n' \
			    '• **links** - `sends invite/support links`\n' \
			    '• **ping** - `checks the bots latency`\n' \
			    '• **say** - `says stuff through the bot`'
			return e
		def mod():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Mod🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = '• **modlogs** - `shows active mutes/temp-bans`\n' \
			    '• **unmute** - `unmutes users so they can talk`\n' \
			    '• **warn** - `warns users and punishes`\n' \
			    '• **delwarn** - `removes warns with the provided reason`\n' \
			    '• **clearwarns** - `resets a users warns`\n' \
			    '• **config warns** - `set punishments for warn`\n' \
			    '• **mute** - `mutes users so they can\'t talk`\n' \
			    '• **kick** - `kicks a user from the server`\n' \
			    '• **softban** - `bans and unbans a user deleting 7 days of their msg history`\n' \
			    '• **tempban** - `bans a user for x amount of time`\n' \
			    '• **ban** `bans a user from the server`\n' \
			    '• **role** - `adds/removes roles from a user`\n' \
			    '• **restore_roles** - `gives roles back on re-join`\n' \
			    '• **selfroles** - `gives roles via reaction menus`\n' \
				'• **autorole** - `gives users roles on-join`\n' \
			    '• **limit** - `limit channels to only allow messages with things like images`\n' \
			    '• **audit** - `tools for searching through the audit log`\n' \
			    '• **lock** - `kicks users on-join`\n' \
			    '• **lockb** - `bans users on-join`\n' \
			    '• **unlock** - `disables any active locks`\n' \
			    '• **pin** - `pings the msg above`\n' \
			    '• **purge** - `mass delete messages`\n' \
			    '• **nick** - `sets a users nickname`\n' \
			    '• **massnick - `sets every users nickname`\n' \
			    '• **massrole - `gives everyone a specific role`'
			return e
		def utility():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Utility🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = '• **members** - `sends the servers member count`\n' \
			    '• **icon** - `sends the servers icon`\n' \
			    '• **sinfo** - `sends server info`\n' \
			    '• **poll** - `makes a reaction poll via embed`\n' \
			    '• **welcome** - `welcomes users on-join`\n' \
			    '• **farewell** - `gives users a farewell on-leave`\n' \
			    '• **logger** - `logs actions to a channel`\n' \
			    '• **color** - `tests a hex or changes a roles color`\n' \
			    '• **emoji** - `sends an emojis full image`\n' \
			    '• **addemoji** - `adds emojis from links or files`\n' \
			    '• **stealemoji** - `steals an emoji from another server`\n' \
			    '• **delemoji** - `deletes an emoji`\n' \
			    '• **owner** - `sends the servers owner mention`\n' \
			    '• **avatar** - `sends your profile picture`\n' \
			    '• **topic** - `sends the channel topic`\n' \
			    '• **note** - `saves a note`\n' \
			    '• **quicknote** - `notes something without the gif`\n' \
			    '• **notes** - `sends your last 5 notes`\n' \
			    '• **wiki** - `sends information on words/phrases`\n' \
			    '• **ud** - `sends a definition from urban dictionary`\n' \
			    '• **find** - `searches msg history for a word/phase`\n' \
			    '• **afk** - `tells users your\'re afk when mentioned`\n' \
			    '• **id** - `sends your id & the channels id`'
			return e
		def fun():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Fun🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = '• **ld** - `detects if a users lying`\n' \
			    '• **chatbot** - `bots are ppl too`\n' \
			    '• **fancify** - `makes text fancy`\n' \
			    '• **factions** - `work/claim/raid/grow`\n' \
			    '• **encode** - `encodes a msg in base64`\n' \
			    '• **decode** - `decodes a msg in base64`\n' \
			    '• **notice** - `aknowledges depression`\n' \
				'• **snipe** - `sends the last deleted msg`\n' \
			    '• **mock** - `mOcKs tExT fOr yOu`\n' \
			    '• **rate** - `rates the above msg`\n' \
			    '• **roll** - `sends a number bwteen 1 & 6`\n' \
			    '• **sue** - `sues the mentioned user`\n' \
			    '• **ask** - `ask meh stuff ¯\_(ツ)_/¯`\n' \
			    '• **rps** - `play rock paper scissors`\n' \
			    '• **cookie** - `giv and eat cookies 🤤`\n' \
			    '• **shoot** - `shoots a user`\n' \
			    '• **inject** - `injects a user with \'someth\'`\n' \
			    '• **slice** - `slices anything up`\n' \
			    '• **stab** - `stabs a user`\n' \
			    '• **boop** - `very kinky shit`\n' \
			    '• **rr** - `play russion roulette`'
			return e
		def music():
			e = discord.Embed(color=colors.fate())
			owner = self.bot.get_user(config.owner_id())
			e.set_author(name='~==🥂🍸🍷Music🍷🍸🥂==~', icon_url=owner.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = '• **play** - `searches or plays from url`\n' \
			    '• **playnow** - `plays immediately ignoring queue`\n' \
			    '• **playat** - `skips to a position in queue`\n' \
			    '• **find** - `finds a vid from youtube`\n' \
			    '• **stop** - `stops playing music`\n' \
			    '• **skip** - `skips a song`\n' \
			    '• **previous** - `plays the previous song`\n' \
			    '• **repeat** - `plays a song on a loop while enabled`\n' \
			    '• **shuffle** - `shuffles the queue`\n' \
			    '• **pause** - `pauses the current song`\n' \
			    '• **resume** - `unpauses the current song`\n' \
			    '• **volume** - `set the playing volume`\n' \
			    '• **queue** - `shows upcoming songs`\n' \
			    '• **remove** - `remove a song from queue`\n' \
			    '• **dc** - `disconnects from vc`\n' \
			    '• **np** - `info on the current song`'
			return e

		msg = await ctx.send(embed=default())
		emojis = ['🏡', '⏮', '⏪', '⏩', '⏭']
		index = 0; sub_index = None
		embeds = [default(), core(), mod(), utility(), fun(), music()]
		def index_check(index):
			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0
			return index

		for emoji in emojis:
			await msg.add_reaction(emoji)
			await asyncio.sleep(0.5)
		while True:
			reaction, emoji = await wait_for_reaction()
			if not reaction:
				return await msg.clear_reactions()
			if emoji == emojis[0]:  # home
				index = 0; sub_index = None
			if emoji == emojis[1]:
				index -= 2; sub_index = None
				if isinstance(embeds[index], list):
					sub_index = 0
			if emoji == emojis[2]:
				if isinstance(embeds[index], list):
					if not isinstance(sub_index, int):
						sub_index = len(embeds[index]) - 1
					else:
						if sub_index == 0:
							index -= 1; sub_index = None
							index = index_check(index)
							if isinstance(embeds[index], list):
								sub_index = len(embeds[index]) - 1
						else:
							sub_index -= 1
				else:
					index -= 1
					if isinstance(embeds[index], list):
						sub_index = len(embeds[index]) - 1
			if emoji == emojis[3]:
				if isinstance(embeds[index], list):
					if not isinstance(sub_index, int):
						sub_index = 0
					else:
						if sub_index == len(embeds[index]) - 1:
							index += 1; sub_index = None
							index = index_check(index)
							if isinstance(embeds[index], list):
								sub_index = 0
						else:
							sub_index += 1
				else:
					index += 1
					index = index_check(index)
					if isinstance(embeds[index], list):
						sub_index = 0
			if emoji == emojis[4]:
				index += 2; sub_index = None
				index = index_check(index)
				if isinstance(embeds[index], list):
					sub_index = 0
			if index > len(embeds) - 1:
				index = len(embeds) - 1
			if index < 0:
				index = 0
			if isinstance(embeds[index], list):
				if index == len(embeds) - 1:
					embeds[index][sub_index].set_footer(text='Last Page! You\'ve reached the end')
				await msg.edit(embed=embeds[index][sub_index])
			else:
				if index == len(embeds) - 1:
					embeds[index].set_footer(text='Last Page! You\'ve reached the end')
				await msg.edit(embed=embeds[index])
			await msg.remove_reaction(reaction, ctx.author)

	@commands.group(name="xhelp")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def _help(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(title="~~~====🥂🍸🍷Help🍷🍸🥂====~~~", color=0x80b0ff)
			e.add_field(name="◈ Core ◈", value="`leaderboard` `gleaderboard` `ggleaderboard` `mleaderboard` `gmleaderboard` `vcleaderboard` `gvcleaderboard` `changelog` `partners` `servers` `restrict` `unrestrict` `restricted` `config` `prefix` `invite` `realms` `ping` `info` `say`", inline=False)
			e.add_field(name="◈ Responses ◈", value="`@Fate` `hello` `ree` `kys` `gm` `gn`", inline=False)
			e.add_field(name="◈ Music ◈", value="`play` `playnow` `playat` `find` `stop` `skip` `previous` `repeat` `pause` `resume` `volume` `queue` `remove` `shuffle` `dc` `np`", inline=False)
			e.add_field(name="◈ Utility ◈", value="`membercount` `channelinfo` `servericon` `serverinfo` `userinfo` `makepoll` `welcome` `farewell` `logger` `color` `emoji` `addemoji` `stealemoji` `rename_emoji` `delemoji` `owner` `avatar` `topic` `timer` `note` `quicknote` `notes` `wiki` `find` `afk` `ud` `id`", inline=False)
			e.add_field(name="◈ Reactions ◈", value="`tenor` `intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `thonk` `shrug` `bite` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`", inline=False)
			e.add_field(name="◈ Mod ◈", value="`modlogs` `addmod` `delmod` `mods` `mute` `unmute` `vcmute` `vcunmute` `warn` `removewarn` `clearwarns` `addrole` `removerole` `restore_roles` `selfroles` `autorole` `limit` `audit` `lock` `lockb` `delete` `purge` `nick` `massnick` `kick` `mute` `ban` `pin`", inline=False)
			e.add_field(name="◈ Fun ◈", value="`personality` `liedetector` `chatbot` `fancify` `factions` `coffee` `encode` `decode` `choose` `notice` `snipe` `mock` `rate` `roll` `soul` `gay` `sue` `ask` `rps` `rr` `cookie` `shoot` `inject` `slice` `boop` `stab`", inline=False)
			try:
				await ctx.author.send(embed=e)
				await ctx.send("Help menu sent to dm ✅")
			except:
				msg = await ctx.send("Failed to send help menu to dm ❎", embed=e)
				await self.wait_for_dismissal(ctx, msg)

	@_help.command(name='archive')
	async def _archive(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.description = 'Saves chat history to a file\n' \
		    '**Usage:** .archive {amount}'
		await ctx.send(embed=e)

	@_help.command(name='antispam')
	async def _antispam(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.description = 'Saves chat history to a file\n' \
		    '**Usage:** .archive {amount}'
		await ctx.send(embed=e)

	@commands.command(name='stats', description="Provides information relevant to the bots stats")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def stats(self, ctx):
		m, s = divmod(time.time() - self.bot.START_TIME, 60)
		h, m = divmod(m, 60)
		guilds = len(list(self.bot.guilds))
		users = len(list(self.bot.users))
		path = os.getcwd() + "/data/images/banners/" + random.choice(os.listdir(os.getcwd() + "/data/images/banners/"))
		bot_pid = psutil.Process(os.getpid())
		e=discord.Embed(color=colors.fate())
		e.set_author(name="Fate [Zerø]: Core Info", icon_url=self.bot.get_user(config.owner_id()).avatar_url)
		stats = self.bot.get_stats  # type: dict
		commands = 0; lines = 0
		for command_date in stats['commands']:
			date = datetime.strptime(command_date, '%Y-%m-%d %H:%M:%S.%f')
			if (datetime.now() - date).days < 7:
				commands += 1
			else:
				index = stats['commands'].index(command_date)
				stats['commands'].pop(index)
				with open('./data/stats.json', 'w') as f:
					json.dump(stats, f, ensure_ascii=False)
		with open('fate.py', 'r') as f:
			lines += len(f.readlines())
		for file in os.listdir('cogs'):
			if file.endswith('.py'):
				with open(f'./cogs/{file}', 'r') as f:
					lines += len(f.readlines())
		e.description = f'Weekly Commands Used: {commands}\n' \
			f'Total lines of code: {lines}'
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		e.add_field(name="◈ Summary ◈", value="Fate is a ~~multipurpose~~ hybrid bot created for ~~sexual assault~~ fun", inline=False)
		e.add_field(name="◈ Statistics ◈", value=f'Commands: [{len(self.bot.commands)}]\nModules: [{len(self.bot.extensions)}]\nServers: [{guilds}]\nUsers: [{users}]')
		e.add_field(name="◈ Credits ◈", value="• Tothy ~ `rival`\n• Cortex ~ `teacher`\n• Discord.py ~ `existing`")
		e.add_field(name="◈ Memory ◈", value=
			f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
			f"__**RAM**__: [{p.bytes2human(psutil.virtual_memory().used)}/{p.bytes2human(psutil.virtual_memory().total)}] ({psutil.virtual_memory().percent}%)\n"
			f"__**Bot RAM**__: {p.bytes2human(bot_pid.memory_full_info().rss)} ({round(bot_pid.memory_percent())}%)\n"
			f"__**CPU**__: **Global**: {psutil.cpu_percent()}% **Bot**: {bot_pid.cpu_percent()}%\n")
		e.add_field(name="◈ Uptime ◈", value="Uptime: {} Hours {} Minutes {} seconds".format(int(h), int(m), int(s)))
		e.set_footer(text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}", icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png")
		msg = await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await self.wait_for_dismissal(ctx, msg)

	@commands.command(name="realms")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def realms(self, ctx):
		e=discord.Embed(title="~~~====🥂🍸🍷Realms🍷🍸🥂====~~~", color=0x80b0ff)
		e.add_field(name="• Anarchy Realms", value="Jappie Anarchy\n• https://realms.gg/pmElWWx5xMk\nAnarchy Realm\n• https://realms.gg/GyxzF5xWnPc\n2c2b Anarchy\n• https://realms.gg/TwbBfe0jGDc\nFraughtian Anarchy\n• https://realms.gg/rdK57KvnA8o\nChaotic Realm\n• https://realms.gg/nzDX1drovu4", inline=False)
		e.add_field(name="• Misc", value=".", inline=False)
		msg = await ctx.send(embed=e)
		await self.wait_for_dismissal(ctx, msg)

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
		msg = await ctx.send(embed=e)
		await self.wait_for_dismissal(ctx, msg)

def setup(bot):
	bot.add_cog(Menus(bot))
