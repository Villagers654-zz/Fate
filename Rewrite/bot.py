import json
import traceback
from time import time
from datetime import datetime
from discord.ext import commands
import discord
import aiomysql
from pymysql.err import OperationalError
from termcolor import cprint
from utils import outh, utils, tasks


class Fate(commands.AutoShardedBot):
    def __init__(self, **options):
        with open('./data/config.json', 'r') as f:
            self.config = json.load(f)  # type: dict
        self.debug = self.config['debug_mode']
        self.login_errors = []
        self.initial_extensions = []    # Cogs to load before logging in
        self.awaited_extensions = []    # Cogs to load when the internal cache is ready
        self.utils = utils              # Custom utility functions
        self.result = utils.Result      # Custom Result Object Creator
        self.tasks = tasks.Tasks(self)  # Task Manager
        self.pool = None                # MySQL Pool initialized on_ready
        self.logs = []                  # list of str

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
            self.log("Couldn't connect to SQL server", 'CRITICAL')
            self.unload(*self.initial_extensions)
            self.log("Logging out..")
            await self.logout()
        else:
            print(f"Initialized db {sql.db} with {sql.user}@{sql.host}")

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
            lines.append(str(tb))
        self.logs.append('\n'.join(lines))
        self.logs = self.logs[:1000]

    def run(self):
        self.log("Loading cogs")
        self.load(*self.initial_extensions)
        self.log("Finished loading cogs")
        self.log("Logging in..")
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
        print(error)


bot.log("Starting Bot")
try:
    bot.run()
except discord.errors.LoginFailure:
    bot.log('Invalid Token', 'CRITICAL')
