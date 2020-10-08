import asyncio
import os
import random
import sys
import traceback

import discord
import psutil
from discord.ext import commands

# ~== Core ==~

description = '''Fate [Zerø]: personal bot'''
bot = commands.Bot(command_prefix='~', case_insensitive=True)
initial_extensions = ['cogs.core']
bot.remove_command('help')




async def status_task():
	while True:
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
		cpupercent = psutil.cpu_percent(interval=1)
		await bot.change_presence(activity=discord.Game(name='4b4t.net | CPU: [{}%]'.format(cpupercent)))
		await asyncio.sleep(15)

async def motd_task():
	while True:
		guild = bot.get_guild(470961230362837002)
		await guild.edit(name="4B4T - {}".format(random.choice(["When the Stars Fall", "Fuck the battle cat", "Woah. . .", "MrBoom10 is Online!", "Heil Sharp 5!", "Sponsored by Samsung", "FBI OPEN UP", "Gapple up", "iLiKe NuT", "All heil nut", "The 7 SR Fags", "ToTheR iS goD", "Fly on Fly off", "Ripperoni pepperoni", "Mayfly!", "Legit Anarchy!", "TotherIsTostitos", "Legit has been muted", "#Free Legit", "Now better than 2p2e!", "6 million juice", "Maps are the best", "7th team lgbt", "elon's musk", "Virtual Daycare", "Time Ticks On", "HeckaGuide was here", "fite me", "fortnut sucks", "7tm Surpreme", "ZR", "Half Life 3", "HI MOM", "no u", "HeckuvaGuide", "NANI?!?", "HA BEAT YA TO IT", "a war in motd", "Hawhatalooser", "obliviscancer", "YEET to DELETE", "You have aids", "ifyoucantbeatitYEETit", "Let’s grab our paint sets", "Communism", "T O T H E R", "FishyBear", "baccacito", "Why so serious?", "disabled due to a exploit", "mikey big gay", "juice wrld", "Huggably rapably fresh", "♡Juice wrld♡", "0/10 meme", "xJuice Wrld", "PURGE THE INFIDELS", "Niggatry", "This shit is not secure", "The Security is Shit", "They need the sack", "Tomato juice!", "Thready = bae", "Send Luck Loli Hentai", "Pole-Man", "Disbanded", "Privileged", "Threadys Republic", "Homiesexual", "Digital Daycare", "IM BACK!!!", "u got food?", "Thready = god 3xpl01ter", "poleman is bae", "The Fuckening", "ANIMOO", "MrBoom10 had the closest base to 0,0", "isthismotdgood", "where's the food", "bettter Believe it's not butter", "Lmao", "Illuminati confirmed", "Cool Story Bro", "It's a dirty liar", "Fate is a hoe", "4B4T", "Fate=Garden tool", "<Gay", "Fate is a slut", "Abuse", "Kool Kidz Klub", "Ewwww", "FREE CANDY", "SeNd NuDeS", "SeNd CoRdS", "It's a block game", "it's a small world", "Beat the Meat", "Hey that's mine", "VFD", "D A B", "ChairyChairChair", "I will beat luck", "MotdKing", "I'll be here all day", "Wait I'm busy", "Sorry Luck", "Over 9000!", "You would not believe your eyes", "Despaciti", "Despacito", "All hail plankton", "Pubg", "Plus Ultra!", "The Cake is a lie", "Half Life 3 confirmed", "OG", "Hi Mom!", "WektWabbitPlayz", "Mad cuz Bad", "Mincecraft"  "Memes", "Sky Banana", "Reee?", "The community isn't the same", "Mother of the devil", "Do your homework", "The base dropped harder than my grades", "All the other kids", "According to all known laws of aviation", "Fate want sucky sucky?", "It's not a phase mom", "Aliens.", "CookieToast", "Fortnite is gay", "Madness?", "This is madness", "This is Sparta!", "This is Anarchy!", "2+2 is... 10", "Quest for Cake", "the big lesbian is coming", "Powered by Beddys ego", "Art", "A MAJESTIC FUCKING EAGLE", "WhyAmIStillGettingHate", "Fateisemo", "FateisBait", "Brickr Ban Book", "Emo", "Burn it with fire", "2 Steves 1 block", "red pancakes", "2 letters E Z", "PG-13", "Beat Your Meat 2", "EVERYONE IS HERE", "Sponsored by Walmart", "5b5t", "7B7T", "I didn't do it", "Bye have a great tiem", "OwO", "Jake from State farm", "Capitalism", "Sorry Fam", "Trust No One", "It only takes one player", "4b4t java fags found us", "I'm back", "depresso expresso", "Heck=motd king", "Poleman is back Mikey", "ISAWEDTHISBOSTINHALF", "Triiiiiipaloski", "#gaslegit", "This is Patrick", "FD", "Kill Yourself Wait Please Don't", "Faggotry", "Waffles", "Blue Waffles", "red pancakes", "moooore", "With a Portuguese Breakfast", "The Motd King has arrived", "Bow down faggots", "NO U", "Oh Snap", "Shits going down", "Gone Sexual", "we are burning this town", "Gone Wrong"])))
		await asyncio.sleep(7200)

async def message_task():
	while True:
		def bytes2human(n):
			symbols = ('GHz', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
			prefix = {}
			for i, s in enumerate(symbols):
				prefix[s] = 1 << (i + 1) * 10
			for s in reversed(symbols):
				if n >= prefix[s]:
					value = float(n) / prefix[s]
					return '%.1f%s' % (value, s)
			return "%sB" % n
		p = psutil.Process(os.getpid())
		freq = psutil.cpu_freq().current
		botram = p.memory_full_info().rss
		ramused = psutil.virtual_memory().used
		ramtotal = psutil.virtual_memory().total
		rampercent = psutil.virtual_memory().percent
		cpupercent = psutil.cpu_percent(interval=1)
		storageused = psutil.disk_usage('/').used
		storagetotal = psutil.disk_usage('/').total
		channel = bot.get_channel(510410941809033216)
		guild = bot.get_guild(470961230362837002)
		luck = bot.get_user(264838866480005122)
		msg = await channel.get_message(511174525103243264)
		e=discord.Embed(color=0x0000ff)
		e.description = f'💎 Official 4B4T Server 💎'
		e.set_thumbnail(url=guild.icon_url)
		e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
		e.add_field(name="◈ Discord ◈", value=f'__**Owner**__: FrequencyX4\n__**Members**__: {guild.member_count}', inline=False)
		e.add_field(name="◈ Memory ◈", value=f'__**Storage**__: [{bytes2human(storageused)}/{bytes2human(storagetotal)}]\n__**RAM**__: **Global**: {bytes2human(ramused)} **Bot**: {bytes2human(botram)}\n__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%\n__**CPU Frequency**__: {bytes2human(freq)}')
		e.set_footer(text=psutil.cpu_percent(interval=1, percpu=True))
		await msg.edit(embed=e)
		await asyncio.sleep(10)

@bot.event
async def on_ready():
	bot.loop.create_task(status_task())
	bot.loop.create_task(message_task())
	print('--------------------')
	print('Logged in as')
	print('Fate [Zero] (Personal Bot)')
	print(bot.user.id)
	print('--------------------')

# ~== Startup ==~

if __name__ == '__main__':
	for cog in initial_extensions:
		try:
			bot.load_extension(cog)
		except Exception as e:
			print('Failed to load extension' + cog, file=sys.stderr)
			traceback.print_exc()
bot.run('NTExMTQxMzM1ODY1MjI5MzMz.DsnCTA.88EZp46nBljzk9YYdr4WUtzw9mE')
