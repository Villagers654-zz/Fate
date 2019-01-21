from discord.ext import commands
from data.config import token
from termcolor import cprint
import traceback
import datetime
import discord
import asyncio
import random
import time

# ~== Core ==~

files = ['error_handler', 'owner', 'menus', 'core', 'mod', 'music', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop', 'custom',
         'actions', 'reactions', 'responses', 'textart', 'fun', 'math', 'dev', '4b4t', 'readme', 'legit', 'reload', 'embeds', 'manager',
         'profiles', 'save', 'clean_rythm', 'anti_magik', 'tother', 'utility', 'psutil', 'rules', 'duel_chat']

description = '''Fate[Zero]: Personal Bot'''
bot = commands.Bot(command_prefix=['.', '<@506735111543193601>'], case_insensitive=True)
bot.START_TIME = time.time()
bot.remove_command('help')
bot.LOAD_TIME = None
bot.LOGIN_TIME = None
bot.errorcount = 0
error = False
bot.info = ""

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
	print(f'Modules: {len(bot.commands)}')
	print(f'Errors: {bot.errorcount}')
	cprint('--------------------------', 'cyan')
	print(' ζξ Welcome back Mikey :)\n'
	      '┌──┬┐ The best way to start\n'
	      '│  ├┘ your day is with the\n'
	      '└──┘ blood of your enemys')
	cprint('--------------------------', 'cyan')
	fmt = "%m-%d-%Y %I:%M%p"
	created = datetime.datetime.now()
	cprint(created.strftime(fmt), 'yellow')
	if error is not False:
		await bot.get_channel(534608853300412416).send(f"```{error}```")
	bot.loop.create_task(status_task())
	m, s = divmod(time.time() - bot.START_TIME, 60)
	h, m = divmod(m, 60)
	bot.LOGIN_TIME = s

# ~== Startup ==~

if __name__ == '__main__':
	cprint("Loading cogs..", "blue")
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
			cprint(f"{cogs}. Cog: {cog} - operational - [{str(s)[:3]}]", "green")
			bot.info += f"{cogs}. Cog: {cog} - operational - [{str(s)[:3]}]\n"
		except Exception as e:
			bot.errorcount += 1
			m, s = divmod(time.time() - bot.START_TIME, 60)
			h, m = divmod(m, 60)
			cprint(f"{cogs}. Cog: {cog} - error - [{str(s)[:3]}]", "red")
			bot.info += f"{cogs}. Cog: {cog} - error - [{str(s)[:3]}]\n"
			error = traceback.format_exc()
	if rank == cogs:
		cprint(f"Loaded {rank}/{cogs} cogs :)", "magenta")
	else:
		cprint(f"Loaded {rank}/{cogs} cogs :(", "magenta")
	cprint(f"Logging into discord..", "blue")
m, s = divmod(time.time() - bot.START_TIME, 60)
h, m = divmod(m, 60)
bot.LOAD_TIME = s
bot.run(token.fatezero)
