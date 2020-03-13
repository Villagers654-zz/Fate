import json
import traceback
from time import time
from datetime import datetime
import os
from discord.ext import commands
import discord
import aiomysql
from pymysql.err import OperationalError
from termcolor import cprint
from utils import outh, utils, tasks, colors


class Fate(commands.AutoShardedBot):
    def __init__(self, **options):
        with open('Rewrite/data/config.json', 'r') as f:
            self.config = json.load(f)  # type: dict
        self.debug = self.config['debug_mode']
        self.pool = None                # MySQL Pool initialized on_ready

        self.login_errors = []          # Exceptions ignored during startup
        self.logs = []                  # Logs to send to discord, empties out quickly
        self.initial_extensions = []    # Cogs to load before logging in
        self.awaited_extensions = []    # Cogs to load when the internal cache is ready

        self.utils = utils              # Custom utility functions
        self.result = utils.Result      # Custom Result Object Creator
        self.memory = utils.MemoryInfo  # Class for easily accessing memory usage
        self.tasks = tasks.Tasks(self)  # Task Manager

        super().__init__(
            command_prefix=utils.get_prefixes,
            activity=discord.Game(name=self.config['startup_status']), **options
        )

    async def create_pool(self):
        sql = outh.MySQL()
        try:
            self.pool = await aiomysql.create_pool(
                host=sql.host,
                port=sql.port,
                user=sql.user,
                password=sql.password,
                db=sql.db,
                loop=self.loop
            )
        except OperationalError:
            print(traceback.format_exc())
            self.log("Couldn't connect to SQL server", 'CRITICAL')
            self.unload(*self.initial_extensions)
            self.log("Logging out..")
            await self.logout()
        else:
            self.log(f"Initialized db {sql.db} with {sql.user}@{sql.host}")

    def load(self, *extensions):
        for cog in extensions:
            try:
                self.load_extension(f"cogs.{cog}")
                self.log(f"Loaded {cog}")
            except commands.ExtensionNotFound:
                self.log(f"Couldn't find {cog}")
            except commands.ExtensionError:
                self.log(f"Couldn't load {cog}", tb=traceback.format_exc())

    def unload(self, *extensions):
        for cog in extensions:
            try:
                self.unload_extension(f"cogs.{cog}")
                self.log(f"Unloaded {cog}")
            except commands.ExtensionNotLoaded:
                self.log(f"Failed to load {cog}")

    def reload(self, *extensions):
        for cog in extensions:
            try:
                self.reload_extension(f"cogs.{cog}")
                self.log(f"Reloaded {cog}")
            except commands.ExtensionNotFound:
                self.log(f"Reloaded {cog}")
            except commands.ExtensionNotLoaded:
                self.log(f"{cog} isn't loaded")
            except commands.ExtensionError:
                self.log(f"Ignoring exception in Cog: {cog}", tb=traceback.format_exc())

    def log(self, message, level='INFO', tb=None):
        if level == 'DEBUG' and not self.debug:
            return
        now = str(datetime.now().strftime("%I:%M%p"))
        if now.startswith('0'):
            now = now.replace('0', '', 1)
        lines = []
        for line in message.split('\n'):
            msg = f"{now} | {level} | {line}"
            if level == 'DEBUG' and self.config['debug_mode']:
                cprint(msg, 'cyan')
            elif level == 'INFO':
                cprint(msg, 'green')
            elif level == 'CRITICAL':
                cprint(msg, 'red')
            lines.append(msg)
        if tb:
            cprint(str(tb), 'red')
            lines.append(str(tb))
        self.logs.append('\n'.join(lines))
        self.logs = self.logs[:1000]

    def run(self):
        self.log("Loading cogs")
        self.load(*self.initial_extensions)
        self.log("Finished loading cogs\nLogging in..")
        super().run(outh.tokens('fatezero'))


start_time = time()
bot = Fate(max_messages=16000)
if not bot.config['use_default_help']:
    bot.remove_command('help')


@bot.event
async def on_shard_ready(shard_id):
    bot.log(f"Shard {shard_id} connected")


@bot.event
async def on_ready():
    bot.log(
        '------------'
        '\nLogged in as'
        f'\n{bot.user}'
        f'\n{bot.user.id}'
        '\n------------'
    )
    await bot.create_pool()
    bot.tasks.ensure_all()
    seconds = round(time() - start_time)
    bot.log(f"Startup took {seconds} seconds")
    for error in bot.login_errors:
        bot.log("Error ignored during startup", level='CRITICAL', tb=error)


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
    if msg.guild and not msg.channel.permissions_for(msg.guild.me).send_messages:
        return
    await bot.process_commands(msg)


@bot.event
async def on_guild_join(guild):
    channel = bot.get_channel(bot.config['log_channel'])
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
    channel = bot.get_channel(bot.config['log_channel'])
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
async def on_command(_ctx):
    stats = bot.utils.get_stats()  # type: dict
    stats['commands'].append(str(datetime.now()))
    with open('./data/stats.json', 'w') as f:
        json.dump(stats, f, ensure_ascii=False)


bot.log("Starting Bot")
try:
    bot.run()
except RuntimeError:
    print("RuntimeError, exiting..")
except discord.errors.LoginFailure:
    print("Invalid Token")
