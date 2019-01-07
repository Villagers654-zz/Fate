from discord.ext import commands
import traceback
import datetime
import discord
import asyncio
import random
import time
import sys
import os

# ~== Core ==~

description = '''Fate[Zero]: Personal Bot'''
bot = commands.Bot(command_prefix='.', case_insensitive=True)
initial_extensions = ['cogs.error_handler', 'cogs.menus', 'cogs.core', 'cogs.mod', 'cogs.music', 'cogs.leaderboards', 'cogs.welcome', 'cogs.farewell', 'cogs.notes', 'cogs.archive',  'cogs.coffeeshop', 'cogs.custom', 'cogs.actions', 'cogs.reactions', 'cogs.responses', 'cogs.textart', 'cogs.fun', 'cogs.math', 'cogs.dev', 'cogs.4b4t', 'cogs.readme', 'cogs.legit', 'cogs.reload', 'cogs.embeds', 'cogs.manager']
bot.START_TIME = time.time()
bot.remove_command('help')
errorcount = 0
error = False
file = False

async def status_task():
	while True:
		await bot.change_presence(activity=discord.Game(name="4b4t.net | {}".format(random.choice(["FBI OPEN UP", "YEET to DELETE", "Pole-Man", "♡Juice wrld♡", "ANIMOO", "Mad cuz Bad", "Quest for Cake", "Gone Sexual"]))))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name='4b4t.net | use .help'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'4b4t.net | {len(list(bot.users))} users'))
		await asyncio.sleep(15)
		await bot.change_presence(activity=discord.Game(name=f'4b4t.net | {len(list(bot.guilds))} servers'))
		await asyncio.sleep(15)

@bot.event
async def on_ready():
	print('--------------------------')
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print(f'Modules: {len(bot.extensions)}')
	print(f'Errors: {errorcount}')
	print('--------------------------')
	print(' ζξ Welcome back Mikey :)\n'
	      '┌──┬┐ The best way to start\n'
	      '│  ├┘ your day is with the\n'
	      '└──┘ blood of your enemys')
	print('--------------------------')
	fmt = "%m-%d-%Y %H:%M%p"
	created = datetime.datetime.now()
	print(created.strftime(fmt))
	if file is not False:
		await bot.get_channel(514213558549217330).send(f"```{file}```")
	bot.loop.create_task(status_task())

# ~== Startup ==~

if __name__ == '__main__':
	print("Loading cogs..")
	cogs = 0
	rank = 0
	f = None
	for cog in initial_extensions:
		cogs += 1
		try:
			bot.load_extension(cog)
			rank += 1
			c = cog.replace("cogs.", "")
			print(f"{cogs}. Cogs: {c} - operational")
		except Exception as e:
			errorcount += 1
			error = True
			c = cog.replace("cogs.", "")
			print(f"{cogs}. Cogs: {c} - error")
			file = traceback.format_exc()
	if rank == cogs:
		print(f"Loaded {rank}/{cogs} cogs :)")
	else:
		print(f"Loaded {rank}/{cogs} cogs :(")
	print(f"Logging into discord..")
bot.run('NTA2NzM1MTExNTQzMTkzNjAx.DttN1Q.NKRp6wgtqSYurVAKjA1ip133xZ4')
