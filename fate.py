"""
Luck#1574's Discord Bot
- Supports v1.5
"""

import asyncio
import random
from os.path import isfile
import json
import traceback
from datetime import datetime
import os
import subprocess

import discord
from discord.ext import commands
from termcolor import cprint

from utils import config, outh, colors

# //~== Core ==~\\

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
	if 'blocked' in config:
		if msg.author.id in config['blocked']:
			return 'lsimhbiwfefmtalol'
	if not msg.guild:
		return commands.when_mentioned_or(".")(bot, msg)
	guild_id = str(msg.guild.id)
	if 'restricted' not in config:
		config['restricted'] = {}
	if guild_id in config['restricted']:
		if msg.channel.id in config['restricted'][guild_id]['channels'] and (
				not msg.author.guild_permissions.administrator):
			return 'lsimhbiwfefmtalol'
	if 'personal_prefix' not in config:
		config['personal_prefix'] = {}
	user_id = str(msg.author.id)
	if user_id in config['personal_prefix']:
		return commands.when_mentioned_or(config['personal_prefix'][user_id])(bot, msg)
	if 'prefix' not in config:
		config['prefix'] = {}
	prefixes = config['prefix']
	if guild_id not in prefixes:
		return commands.when_mentioned_or('.')(bot, msg)
	return commands.when_mentioned_or(prefixes[guild_id])(bot, msg)

def total_seconds(now, before):
	total_seconds = str((now - before).total_seconds())
	return total_seconds[:total_seconds.find('.') + 2]

initial_extensions = [
	'error_handler', 'config', 'menus', 'core', 'music', 'mod', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop',
	'custom', 'actions', 'reactions', 'responses', 'textart', 'fun', 'dev', '4b4t', 'readme', 'reload', 'embeds',
	'polis', 'mha', 'apis', 'chatbridges', 'clean_rythm', 'utility', 'psutil', 'rules', 'duel_chat', 'selfroles',
	'lock', 'audit', 'cookies', 'backup', 'stats', 'server_list', 'emojis', 'logger', 'autorole', 'changelog',
	'restore_roles', 'chatbot', 'anti_spam', 'anti_raid', 'chatfilter', 'nsfw', 'minecraft', 'chatlock', 'rainbow',
	'system', 'user', 'limiter', 'dm_channel', 'factions', 'secure_overwrites', 'server_setup', 'secure-log', 'ranking'
]

bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True, max_messages=16000)
bot.remove_command('help')
bot.files = initial_extensions
bot.get_stats = get_stats()
bot.get_config = get_config()
login_errors = []

async def status_task():
	while True:
		motds = [
			'FBI OPEN UP', 'YEET to DELETE', 'Pole-Man', '♡Juice wrld♡', 'Mad cuz Bad', 'Quest for Cake', 'Gone Sexual',
			'@EPFFORCE#1337 wuz here'
		]
		stages = ['Serendipity', 'Euphoria', 'Singularity', 'Epiphany']
		for i in range(len(stages)):
			try:
				await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'Seeking For The Clock'))
				await asyncio.sleep(45)
				await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'{stages[i]} | use .help'))
				await asyncio.sleep(15)
				await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name=f'SVR: {len(bot.guilds)} USR: {len(bot.users)}'))
				await asyncio.sleep(15)
				await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=f'{stages[i]} | {random.choice(motds)}'))
			except:
				pass
			await asyncio.sleep(15)

# //~== Events ==~\

@bot.event
async def on_ready():
	login_time = total_seconds(datetime.now(), login_start_time)
	total_start_time = total_seconds(datetime.now(), bot.start_time)
	cprint('--------------------------', 'cyan')
	info = f'Logged in as {bot.user}\n'
	info += f"{bot.user.id}\n"
	info += f'Version: {discord.__version__}\n'
	info += f'commands: {len(bot.commands)}\n'
	info += f'User Count: {len(bot.users)}\n'
	info += f'Errors: {len(login_errors)}'
	print(info)
	cprint('--------------------------', 'cyan')
	print(' ζξ Welcome back Mikey :)\n'
	      '┌──┬┐ The best way to start\n'
	      '│  ├┘ your day is with the\n'
	      '└──┘ blood of your enemys')
	cprint('--------------------------', 'cyan')
	bot.loop.create_task(status_task())
	cprint(datetime.now().strftime("%m-%d-%Y %I:%M%p"), 'yellow')
	# notify myself on discord that the bots logged in
	channel = bot.get_channel(config.server("log"))
	p = subprocess.Popen("last | head -1", stdout=subprocess.PIPE, shell=True)
	(output, err) = p.communicate()
	output = str(output).replace("b'", "'")
	info = f'```\n--------------------------\n{info}\n--------------------------```'
	load_times = f'```Time to load files: {load_time} seconds\n' \
		f'Time to login: {login_time} seconds\n' \
	    f'Total time taken: {total_start_time} seconds```'
	e = discord.Embed(color=colors.green())
	e.set_author(name='Login Notice', icon_url=bot.user.avatar_url)
	load_msgs = [f'```{load_msg[i:i + 1000]}```' for i in range(0, len(load_msg), 1000)]
	for i in range(len(load_msgs)):
		if i == 0:
			e.description = load_msgs[i]; continue
		e.add_field(name='~', value=load_msgs[i])
	e.add_field(name="Loading Info", value=load_times, inline=False)
	e.add_field(name='Security Check', value=f'```{output}```')
	e.add_field(name="Welcome", value=info, inline=False)
	await channel.send(embed=e)
	if login_errors:
		for error in login_errors:
			await channel.send(f'```{str(error)[:1990]}```')

@bot.event
async def on_shard_ready(shard_id):
	print(f'Shard Loaded: {shard_id}')

@bot.event
async def on_disconnect():
	print('NOTICE: Disconnected from discord')

@bot.event
async def on_message(msg):
	if '@everyone' in msg.content or '@here' in msg.content:
		msg.content = msg.content.replace('@', '!')
	await bot.process_commands(msg)

@bot.event
async def on_guild_join(guild):
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
	conf = get_config()  # type: dict
	if guild.owner.id in conf['blocked']:
		await guild.leave()

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
	with open('members.txt', 'w') as f:
		f.write('\n'.join([f'{m.id}, {m}, {m.mention}' for m in guild.members]))
	await channel.send(embed=e, file=discord.File('members.txt'))
	os.remove('members.txt')

@bot.event
async def on_command(ctx):
	stats = bot.get_stats  # type: dict
	stats['commands'].append(str(datetime.now()))
	with open('./data/stats.json', 'w') as f:
		json.dump(stats, f, ensure_ascii=False)

# //~== Startup ==~\\

bot.start_time = datetime.now()
if __name__ == '__main__':
	cprint("Loading cogs..", "blue")
	unloaded_cogs = []; index = 1
	load_msg = ''
	for cog in initial_extensions:
		start_time = datetime.now()
		try:
			bot.load_extension("cogs." + cog)
			seconds = str((datetime.now() - start_time).total_seconds())
			seconds = seconds[:seconds.find('.') + 2]
			cprint(f"{index}. Cog: {cog} - operational - [{seconds}s]", "green")
			load_msg += f"{index}. Cog: {cog} - operational - [{seconds}s]\n"
			index += 1
		except Exception as e:
			cprint(f"{index}. Cog: {cog} - errored", "red")
			load_msg += f"{index}. Cog: {cog} - errored\n"
			login_errors.append(traceback.format_exc())
	reaction = ':)' if index - 1 == len(initial_extensions) else ':('
	cprint(f'Loaded {index - 1}/{len(initial_extensions)} cogs {reaction}', "magenta")
	cprint(f"Logging into discord..", "blue")
load_time = total_seconds(datetime.now(), bot.start_time)
login_start_time = datetime.now()
bot.run(outh.tokens('fatezero'))
