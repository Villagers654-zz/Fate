from discord.ext import commands
from termcolor import cprint
from os.path import isfile
from utils import config, colors
import traceback
import datetime
import discord
import asyncio
import random
import json
import time

# ~== Core ==~

def get_prefix(bot, message):
	setup_data = {}
	if not message.guild:
		return commands.when_mentioned_or(".")(bot, message)
	if not isfile("./data/userdata/prefixes.json"):
		with open("./data/userdata/prefixes.json", "w") as f:
			json.dump(setup_data, f, sort_keys=True,
			indent=4, separators=(',', ': '))
	with open(r"./data/userdata/prefixes.json", "r") as f:
		prefixes = json.load(f)
	if str(message.guild.id) not in prefixes:
		return "."
	prefix = prefixes[str(message.guild.id)]
	return prefix

files = ['error_handler', 'config', 'menus', 'core', 'mod', 'music', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop', 'custom',
         'actions', 'reactions', 'responses', 'textart', 'fun', 'math', 'dev', '4b4t', 'readme', 'legit', 'reload', 'embeds', 'warning',
         'profiles', 'save', 'clean_rythm', 'tother', 'utility', 'psutil', 'rules', 'duel_chat', 'selfroles', 'lock', 'backup', 'audit',
         'cookies', 'team', 'anti_purge', 'emojis', 'logger', 'autorole', 'changelog', 'restore_roles', 'stats',
         'chatbot', 'anti_spam', 'anti_raid', 'chatfilter', 'nsfw', 'leaderboards', 'chatlock']

description = '''Fate[Zero]: Personal Bot'''
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, max_messages=16000)
bot.START_TIME = time.time()
bot.remove_command('help')
bot.errorcount = 0
error = False

async def status_task():
	while True:
		await bot.change_presence(activity=discord.Game(name=f"4b4t.net | {random.choice(['FBI OPEN UP', 'YEET to DELETE', 'Pole-Man', '♡Juice wrld♡', 'ANIMOO', 'Mad cuz Bad', 'Quest for Cake', 'Gone Sexual'])}"))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name='4b4t.net | use .help'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'4b4t.net | {len(list(bot.users))} users'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'4b4t.net | {len(list(bot.guilds))} servers'))
		await asyncio.sleep(15)

@bot.event
async def on_ready():
	cprint('--------------------------', 'cyan')
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print(f'Version: {discord.__version__}')
	print(f'Commands: {len(bot.commands)}')
	print(f'Errors: {bot.errorcount}')
	cprint('--------------------------', 'cyan')
	print(' ζξ Welcome back Mikey :)\n'
	      '┌──┬┐ The best way to start\n'
	      '│  ├┘ your day is with the\n'
	      '└──┘ blood of your enemys')
	cprint('--------------------------', 'cyan')
	bot.loop.create_task(status_task())
	fmt = "%m-%d-%Y %I:%M%p"
	created = datetime.datetime.now()
	cprint(created.strftime(fmt), 'yellow')
	if error:
		await bot.get_channel(503902845741957131).send(f"```{error}```")
	m, s = divmod(time.time() - bot.START_TIME, 60)
	bot.LOGIN_TIME = s

@bot.event
async def on_guild_join(guild):
	channel = bot.get_channel(config.server("log"))
	e = discord.Embed(color=colors.pink())
	e.set_author(name="Bot Added to Guild", icon_url=bot.user.avatar_url)
	e.set_thumbnail(url=guild.icon_url)
	e.description = f"**Guild:** {guild.name}\n" \
		f"**ID:** {guild.id}\n" \
		f"**Owner:** {guild.owner}\n" \
		f"**Members:** [`{len(guild.members)}`]"
	await channel.send(embed=e)

@bot.event
async def on_guild_remove(guild):
	channel = bot.get_channel(config.server("log"))
	e = discord.Embed(color=colors.pink())
	e.set_author(name="Bot Left or Was Removed", icon_url=bot.user.avatar_url)
	e.set_thumbnail(url=guild.icon_url)
	e.description = f"**Guild:** {guild.name}\n" \
		f"**ID:** {guild.id}\n" \
		f"**Owner:** {guild.owner}\n" \
		f"**Members:** [`{len(guild.members)}`]"
	await channel.send(embed=e)

# ~== Startup ==~

if __name__ == '__main__':
	cprint("Loading cogs..", "blue")
	bot.info = ""
	previous = 0
	cogs = 0
	rank = 0
	f = None
	for cog in files:
		cogs += 1
		try:
			bot.load_extension("cogs." + cog)
			rank += 1
			m, s = divmod(time.time() - bot.START_TIME, 60)
			h, m = divmod(m, 60)
			cprint(f"{cogs}. Cog: {cog} - operational - [{str(s - previous)[:3]}]", "green")
			bot.info += f"{cogs}. Cog: {cog} - operational - [{str(s - previous)[:3]}]\n"
			previous = float(str(s)[:3])
		except Exception as e:
			bot.errorcount += 1
			m, s = divmod(time.time() - bot.START_TIME, 60)
			h, m = divmod(m, 60)
			cprint(f"{cogs}. Cog: {cog} - error - [{str(s - previous)[:3]}]", "red")
			bot.info += f"{cogs}. Cog: {cog} - error - [{str(s - previous)[:3]}]\n"
			error = traceback.format_exc()
			previous = float(str(s)[:3])
	if rank == cogs:
		cprint(f"Loaded {rank}/{cogs} cogs :)", "magenta")
	else:
		cprint(f"Loaded {rank}/{cogs} cogs :(", "magenta")
	cprint(f"Logging into discord..", "blue")
m, s = divmod(time.time() - bot.START_TIME, 60)
h, m = divmod(m, 60)
bot.LOAD_TIME = s
bot.run(config.tokens("fatezero"))
