# Luck#1574's Discord Bot
# Supports v1.3

import json
import traceback
from datetime import datetime
import os
import subprocess
import logging

import discord
from discord.ext import commands
from termcolor import cprint

from utils import config, outh, colors, utils, tasks, checks


class Fate(commands.Bot):
	def __init__(self, **options):
		self.utils = utils
		self.tasks = tasks.Tasks(self)

		# deprecated
		self.get_stats = self.utils.get_stats()
		self.get_config = self.utils.get_config()

		super().__init__(self.utils.get_prefixes, **options)


bot = Fate(case_insensitive=True, max_messages=16000)
bot.remove_command('help')
bot.add_check(checks.command_is_enabled)
initial_extensions = [
	'error_handler', 'config', 'menus', 'core', 'music', 'mod', 'welcome', 'farewell', 'notes', 'archive', 'coffeeshop',
	'custom', 'actions', 'reactions', 'responses', 'textart', 'fun', 'dev', '4b4t', 'readme', 'reload', 'embeds',
	'polis', 'apis', 'chatbridges', 'clean_rythm', 'utility', 'psutil', 'rules', 'duel_chat', 'selfroles',
	'lock', 'audit', 'cookies', 'backup', 'stats', 'server_list', 'emojis', 'logger', 'autorole', 'changelog',
	'restore_roles', 'chatbot', 'anti_spam', 'anti_raid', 'chatfilter', 'nsfw', 'minecraft', 'chatlock', 'rainbow',
	'system', 'user', 'limiter', 'dm_channel', 'factions', 'secure_overwrites', 'server_setup', 'secure-log', 'ranking',
	'global-chat', 'beta'
]
login_errors = []

# this is for the debug_task log
if os.path.isfile('discord.log'):  # reset the file on startup so the debug_log task doesn't resend logs
	os.remove('discord.log')       # also keeps the file size down and speeds things up
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


#async def handle_echo(reader, writer):
#	data = await reader.read(100)
#	message = data.decode()
#	# addr = writer.get_extra_info('peername')
#	await bot.get_channel(633866664252801024).send(discord.utils.escape_mentions(message))
#	for i in range(5):
#		writer.write(b'Received your Msg')
#		await writer.drain()


@bot.event
async def on_ready():
	# await asyncio.start_server(handle_echo, '5.189.131.176', port=31337, loop=bot.loop)
	login_time = bot.utils.total_seconds(datetime.now(), login_start_time)
	total_start_time = bot.utils.total_seconds(datetime.now(), bot.start_time)
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
	e.add_field(name="Loading Info", value=load_times, inline=False)
	e.add_field(name='Security Check', value=f'```{output}```')
	e.add_field(name="Welcome", value=info, inline=False)
	await channel.send(embed=e)

	# send the full traceback of any login errors to a dedicated channel
	for error in login_errors:
		await channel.send(f'```{str(error)[:1990]}```')

	bot.tasks.ensure_all()


@bot.event
async def on_message(msg):
	if '@everyone' in msg.content or '@here' in msg.content:
		msg.content = msg.content.replace('@', '!')
	blacklist = [
		'trap', 'dan', 'gel', 'yaoi'
	]
	if '--dm' in msg.content and not any(x in msg.content for x in blacklist):
		msg.content = msg.content.replace(' --dm', '')
		channel = await msg.author.create_dm()
		msg.channel = channel
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
	conf = bot.utils.get_config()  # type: dict
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
	stats = bot.utils.get_stats()  # type: dict
	stats['commands'].append(str(datetime.now()))
	with open('./data/stats.json', 'w') as f:
		json.dump(stats, f, ensure_ascii=False)


bot.start_time = datetime.now()
if __name__ == '__main__':
	cprint("Loading cogs..", "blue")
	unloaded_cogs = []
	index = 1
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
load_time = bot.utils.total_seconds(datetime.now(), bot.start_time)
login_start_time = datetime.now()
bot.run(outh.tokens('fatezero'))
