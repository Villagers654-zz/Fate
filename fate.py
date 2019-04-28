from discord.ext import commands
from utils import config, colors
from termcolor import cprint
from os.path import isfile
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

files = ['error_handler', 'config', 'menus', 'core', 'music', 'mod', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop', 'custom',
         'actions', 'reactions', 'responses', 'textart', 'fun', 'math', 'dev', '4b4t', 'readme', 'reload', 'embeds', 'warning', 'profiles',
         'save', 'clean_rythm', 'utility', 'psutil', 'rules', 'duel_chat', 'selfroles', 'lock', 'backup', 'audit', 'cookies', 'team', 'stats',
         'anti_purge', 'emojis', 'logger', 'autorole', 'changelog', 'restore_roles', 'chatbot', 'anti_spam', 'anti_raid', 'chatfilter', 'nsfw',
         'leaderboards', 'chatlock', 'rainbow', 'vc_log', 'system']

description = '''Fate[Zero]: Personal Bot'''
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, max_messages=16000)
bot.START_TIME = time.time()
bot.remove_command('help')
bot.errorcount = 0
error = False

async def status_task():
	while True:
		motds = ['FBI OPEN UP', 'YEET to DELETE', 'Pole-Man', '♡Juice wrld♡', 'ANIMOO', 'Mad cuz Bad', 'Quest for Cake', 'Gone Sexual']
		await bot.change_presence(activity=discord.Game(name=f"Arkadia | {random.choice(motds)}"))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name='Arkadia | use .help'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'Arkadia | {len(bot.users)} users'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'Arkadia | {len(bot.guilds)} servers'))
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
	m, s = divmod(time.time() - bot.START_TIME, 60)
	bot.LOGIN_TIME = s
	bot.loop.create_task(status_task())
	cprint(datetime.datetime.now().strftime("%m-%d-%Y %I:%M%p"), 'yellow')
	if error:
		await bot.get_channel(503902845741957131).send(f"```{error}```")
	with open("./data/stats.json", "w") as f:
		json.dump({"commands": 0}, f, ensure_ascii=False)

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
	with open("./data/stats.json", "r") as f:
		commands = json.load(f)["commands"]
	with open("./data/stats.json", "w") as f:
		json.dump({"commands": commands + 1}, f, ensure_ascii=False)

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
bot.run(config.tokens("fatezero"))
