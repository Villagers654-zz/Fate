from discord.ext import commands
from utils import config, colors
from termcolor import cprint
from datetime import datetime
from os.path import isfile
import traceback
import discord
import asyncio
import random
import json
import time

# ~== Core ==~

def get_stats():
	if not isfile('./data/stats.json'):
		with open('./data/stats.json', 'w') as f:
			json.dump({'commands': []}, f, ensure_ascii=False)
	with open('./data/stats.json', 'r') as stats:
		return json.load(stats)

def get_config():
	if not isfile('./data/config.json'):
		with open('./data/config.json', 'w') as f:
			json.dump({}, f, ensure_ascii=False)
	with open('./data/config.json', 'r') as config:
		return json.load(config)

def get_prefix(bot, msg):
	config = get_config()  # type: dict
	if 'blocked' not in config:
		config['blocked'] = {}
	if msg.author.id in config['blocked']:
		return 'lsimhbiwfefmtalol'
	if isinstance(msg.author, discord.Member):
		guild_id = str(msg.guild.id)
		if 'restricted' not in config:
			config['restricted'] = {}
		if guild_id in config['restricted']:
			if msg.channel.id in config['restricted'][guild_id]['channels']:
				perms = msg.author.guild_permissions
				if not perms.administrator and not perms.manage_guild:
					return 'lsimhbiwfefmtalol'
	if not msg.guild:
		return commands.when_mentioned_or(".")(bot, msg)
	guild_id = str(msg.guild.id)
	if 'prefix' not in config:
		config['prefix']= {}
	prefixes = config['prefix']
	if guild_id not in prefixes:
		return "."
	return prefixes[guild_id]

files = ['error_handler', 'config', 'menus', 'core', 'music', 'mod', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop', 'custom',
         'actions', 'reactions', 'responses', 'textart', 'fun', 'dev', '4b4t', 'readme', 'reload', 'embeds', 'warning', 'profiles',
         'clean_rythm', 'utility', 'psutil', 'rules', 'duel_chat', 'selfroles', 'lock', 'audit', 'cookies', 'backup', 'stats', 'server_list',
         'emojis', 'logger', 'autorole', 'changelog', 'restore_roles', 'chatbot', 'anti_spam', 'anti_raid', 'chatfilter', 'nsfw', 'leaderboards',
         'chatlock', 'rainbow', 'vc_log', 'system', 'user', 'limiter', 'dm_channel', 'factions', 'secure_overwrites']

description = '''Fate[Zero]: Personal Bot'''
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, max_messages=16000)
bot.START_TIME = time.time()
bot.remove_command('help')
bot.errorcount = 0; bot.files = files
bot.get_stats = get_stats()
bot.get_config = get_config()
bot.voice_calls = []
error = False

async def status_task():
	while True:
		motds = ['FBI OPEN UP', 'YEET to DELETE', 'Pole-Man', '♡Juice wrld♡', 'Mad cuz Bad', 'Quest for Cake', 'Gone Sexual']
		stages = ['Serendipity', 'Euphoria', 'Singularity', 'Epiphany']
		for i in range(len(stages)):
			await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'{stages[i]} | use .help'))
			await asyncio.sleep(15)
			await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name=f'{stages[i]} | {len(bot.users)} users'))
			await asyncio.sleep(15)
			await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=f'{stages[i]} | {len(bot.guilds)} servers'))
			await asyncio.sleep(15)
			await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'{stages[i]} | {random.choice(motds)}'))
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
	cprint(datetime.now().strftime("%m-%d-%Y %I:%M%p"), 'yellow')
	if error:
		await bot.get_channel(503902845741957131).send(f"```{error}```")

@bot.event
async def on_guild_join(guild: discord.Guild):
	channel = bot.get_channel(config.server("log"))
	e = discord.Embed(color=colors.pink())
	e.set_author(name="Bot Added to Guild", icon_url=bot.user.avatar_url)
	if guild.icon_url:
		e.set_thumbnail(url=guild.icon_url)
	e.description = f"**Name:** {guild.name}\n" \
		f"**ID:** {guild.id}\n" \
		f"**Owner:** {guild.owner}\n" \
		f"**Members:** [`{len(guild.members)}`]"
	await channel.send(embed=e)

@bot.event
async def on_guild_remove(guild: discord.Guild):
	channel = bot.get_channel(config.server("log"))
	e = discord.Embed(color=colors.pink())
	e.set_author(name="Bot Left or Was Removed", icon_url=bot.user.avatar_url)
	if guild.icon_url:
		e.set_thumbnail(url=guild.icon_url)
	e.description = f"**Name:** {guild.name}\n" \
		f"**ID:** {guild.id}\n" \
		f"**Owner:** {guild.owner}\n" \
		f"**Members:** [`{len(guild.members)}`]"
	await channel.send(embed=e)

@bot.event
async def on_command(ctx):
	stats = bot.get_stats  # type: dict
	stats['commands'].append(str(datetime.now()))
	with open('./data/stats.json', 'w') as f:
		json.dump(stats, f, ensure_ascii=False)

# ~== Startup ==~

if __name__ == '__main__':
	cprint("Loading cogs..", "blue")
	bot.info = ""
	previous_load_time = 0
	cog_count = 0
	loaded_cogs = 0
	f = None
	for cog in files:
		cog_count += 1
		try:
			bot.load_extension("cogs." + cog)
			loaded_cogs += 1
			m, s = divmod(time.time() - bot.START_TIME, 60)
			h, m = divmod(m, 60)
			cprint(f"{cog_count}. Cog: {cog} - operational - [{str(s - previous_load_time)[:3]}]", "green")
			bot.info += f"{cog_count}. Cog: {cog} - operational - [{str(s - previous_load_time)[:3]}]\n"
			previous = float(str(s)[:3])
		except Exception as e:
			bot.errorcount += 1
			m, s = divmod(time.time() - bot.START_TIME, 60)
			h, m = divmod(m, 60)
			cprint(f"{cog_count}. Cog: {cog} - error - [{str(s - previous_load_time)[:3]}]", "red")
			bot.info += f"{cog_count}. Cog: {cog} - error - [{str(s - previous_load_time)[:3]}]\n"
			error = traceback.format_exc()
			print(traceback.format_exc())
			previous = float(str(s)[:3])
	if loaded_cogs == cog_count:
		cprint(f"Loaded {loaded_cogs}/{cog_count} cogs :)", "magenta")
	else:
		cprint(f"Loaded {loaded_cogs}/{cog_count} cogs :(", "magenta")
	cprint(f"Logging into discord..", "blue")
m, s = divmod(time.time() - bot.START_TIME, 60)
bot.LOAD_TIME = s
bot.run(config.tokens('fatezero'))
