import json
import traceback
from time import time
from datetime import datetime
import os
import asyncio
import logging
from typing import *
import aiofiles

from discord.ext import commands
import discord
import aiomysql
import pymysql
from termcolor import cprint

from utils import auth, tasks, colors, checks
from utils.custom_logging import Logging
from cogs.utils import Utils


class EmptyException(Exception):
    pass


class Fate(commands.AutoShardedBot):
    def __init__(self, **options):
        with open('./data/config.json', 'r') as f:
            self.config = json.load(f)  # type: dict
        self.debug_mode = self.config['debug_mode']
        self.owner_ids = set(list([self.config["bot_owner_id"], *self.config["bot_owner_ids"]]))
        self.pool = None                # MySQL Pool initialized on_ready
        self.tcp_servers = {            # Socket servers for web panel
            "logger": None,
            "levels": None
        }
        self.lavalink = None            # Music server
        self.login_errors = []          # Exceptions ignored during startup
        self.logs = []                  # Logs to send to discord, empties out quickly
        self.locks = {}
        self.tasks = {}                 # Task object storing for easy management
        self.logger_tasks = {}          # Same as Fate.tasks except dedicated to cogs.logger
        self.last_traceback = ""        # Formatted string of the last error traceback
        self.ignored_exit = EmptyException
        self.allow_user_mentions = discord.AllowedMentions(users=True, roles=False, everyone=False)

        self.initial_extensions = [  # Cogs to load pre-login
            'actions', 'anti_raid', 'anti_spam', 'apis', 'archive', 'audit', 'autorole', 'changelog', 'chatfilter',
            'chatlock', 'clean_rythm', 'coffeeshop', 'config', 'cookies', 'core', 'custom', 'dev', 'dm_channel',
            'duel_chat', 'embeds', 'emojis', 'error_handler', 'factions', 'farewell', 'fun', 'giveaways', 'global-chat',
            'limiter', 'lock', 'logger', 'menus', 'minecraft', 'mod', 'notes', 'nsfw', 'polls', 'psutil', 'rainbow',
            'ranking', 'reactions', 'readme', 'reload', 'responses', 'restore_roles', 'rules', 'secure_overwrites',
            'selfroles', 'server_list', 'server_setup', 'statistics', 'system', 'textart', 'toggles', 'user', 'utility',
            'utils', 'verification', 'welcome'
        ]

        self.awaited_extensions = []  # Cogs to load when the internal cache is ready
        self.module_index = {
            # Cog Name      Help command             Enable Command                   Disable command
            "Welcome":      {"help": "welcome",      "enable": "welcome.enable",      "disable": "welcome.disable"},
            "Leave":        {"help": "leave",        "enable": "leave.enable",        "disable": "leave.disable"},
            "AntiRaid":     {"help": "antiraid",     "enable": "antiraid.enable",     "disable": "antiraid.disable"},
            "AntiSpam":     {"help": "antispam",     "enable": "antispam.enable",     "disable": "antispam.disable"},
            "ChatFilter":   {"help": "chatfilter",   "enable": "chatfilter.enable",   "disable": "chatfilter.disable"},
            "ChatLock":     {"help": "chatlock",     "enable": "chatlock.enable",     "disable": "chatlock.disable"},
            # "ChatBot":    {"help": "chatbot",      "enable": "chatbot.enable",      "disable": "chatbot.disable"},
            "GlobalChat":   {"help": "global-chat",  "enable": "global-chat.enable",  "disable": "global-chat.disable"},
            "Lock":         {"help": None,           "enable": "lock",                "disable": "lock"},
            "Lockb":        {"help": None,           "enable": "lockb",               "disable": "lockb"},
            "Logger":       {"help": "logger",       "enable": "logger.enable",       "disable": "logger.disable"},
            "Responses":    {"help": "responses",    "enable": "enableresponses",     "disable": "disableresponses"},
            "RestoreRoles": {"help": "restoreroles", "enable": "restoreroles.enable", "disable": "restoreroles.disable"},
            "SelfRoles":    {"help": "selfroles",    "enable": "create-menu",         "disable": None}
        }

        if not self.config["original_bot"]:
            original_only = ['polis', 'dev', 'backup']
            for ext in original_only:
                if ext in self.initial_extensions:
                    self.initial_extensions.remove(ext)

        self.core_tasks = tasks.Tasks(self)  # Object to start the main tasks like `changing status`
        self.log = Logging(bot=self)         # Class to handle printing/logging

        # ContextManager for quick sql cursor access
        class Cursor:
            def __init__(this):
                this.conn = None
                this.cursor = None

            async def __aenter__(this):
                while not self.pool:
                    await asyncio.sleep(0.21)
                this.conn = await self.pool.acquire()
                this.cursor = await this.conn.cursor()
                return this.cursor

            async def __aexit__(this, _type, _value, _tb):
                await this.conn.commit()
                self.pool.release(this.conn)

        self.cursor = Cursor

        # Async compatible file manager using aiofiles and asyncio.Lock
        class AsyncFileManager:
            def __init__(this, file: str, mode: str = "r", lock: bool = True):
                this.file = this.temp_file = file
                if "w" in mode:
                    this.temp_file += ".tmp"
                this.mode = mode
                this.fp_manager = None
                this.lock = lock
                if lock and file not in self.locks:
                    self.locks[file] = asyncio.Lock()

            async def __aenter__(this):
                if this.lock:
                    await self.locks[this.file].acquire()
                this.fp_manager = await aiofiles.open(file=this.temp_file, mode=this.mode)
                return this.fp_manager

            async def __aexit__(this, _exc_type, _exc_value, _exc_traceback):
                await this.fp_manager.close()
                if this.file != this.temp_file:
                    os.rename(this.temp_file, this.file)
                if this.lock:
                    self.locks[this.file].release()

        self.open = AsyncFileManager

        class WaitForEvent:
            def __init__(this, event, check=None, channel=None, send_error=True, timeout=60):
                this.event = event
                this.channel = channel
                this.check = check
                this.send_error = send_error
                this.timeout = timeout

                ctx = check if isinstance(check, commands.Context) else None
                if ctx and not this.channel:
                    this.channel = this.channel
                if ctx and this.event == 'message':
                    this.check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            async def __aenter__(this):
                try:
                    message = await self.wait_for(this.event, check=this.check, timeout=this.timeout)
                except asyncio.TimeoutError:
                    if this.send_error and this.channel:
                        await this.channel.send(f"Timed out waiting for {this.event}")
                    raise self.ignored_exit()
                else:
                    return message

            async def __aexit__(this, exc_type, exc_val, exc_tb):
                pass

        self.require = WaitForEvent

        # Set the oauth_url for users to invite the bot with
        perms = discord.Permissions(0)
        perms.update(
                embed_links=True, manage_messages=True,
                view_audit_log=True, manage_webhooks=True,
                manage_roles=True, manage_channels=True,
                manage_guild=True, manage_emojis=True,
                change_nickname=True, manage_nicknames=True,
                external_emojis=True, attach_files=True,
                kick_members=True, ban_members=True,
                read_message_history=True, add_reactions=True
            )
        self.invite_url = discord.utils.oauth_url(
            self.config['bot_user_id'],
            perms
        )

        super().__init__(
            command_prefix=Utils.get_prefixes,
            activity=discord.Game(name=self.config['startup_status']), **options
        )

    @property
    def utils(self) -> Utils:
        if "Utils" not in self.cogs:
            raise ModuleNotFoundError("The utils cog hasn't been loaded yet")
        return self.get_cog("Utils")

    # async def on_error(self, event_method, *args, **kwargs):
    #     full_error = str(traceback.format_exc())
    #     ignored = ("NotFound")
    #     if any(Type in full_error for Type in ignored):
    #         return
    #     self.log.critical(full_error)

    def get_message(self, message_id: int):
        """ Return a message from the internal cache if it exists """
        for message in self.cached_messages:
            if message.id == message_id:
                return message
        return None

    async def create_pool(self, force=False):
        if self.pool and not force:
            return self.log.info("bot.create_pool was called when one was already initialized")
        elif self.pool:
            self.log.critical("Closing the existing pool to start a new connection")
            self.pool.close()
            await self.pool.wait_closed()
            self.log.info("Pool was successfully closed")
        sql = auth.MySQL()
        for _attempt in range(5):
            try:
                self.log("Connecting to db")
                pool = await aiomysql.create_pool(
                    host=sql.host,
                    port=sql.port,
                    user=sql.user,
                    password=sql.password,
                    db=sql.db,
                    autocommit=True,
                    loop=self.loop,
                    maxsize=10
                )
                self.pool = pool
                break
            except (ConnectionRefusedError, pymysql.err.OperationalError):
                self.log.critical("Couldn't connect to SQL server, retrying in 25 seconds..")
                self.log.critical(traceback.format_exc())
            await asyncio.sleep(25)
        else:
            self.log.critical(f"Couldn't connect to SQL server, reached max attempts``````{traceback.format_exc()}")
            self.unload(*self.initial_extensions, log=False)
            self.log.critical("Logging out..")
            return await self.logout()
        self.log.info(f"Initialized db {sql.db} with {sql.user}@{sql.host}")

    def load(self, *extensions) -> None:
        for cog in extensions:
            try:
                self.load_extension(f"cogs.{cog}")
                self.log.info(f"Loaded {cog}", end="\r")
            except commands.ExtensionNotFound:
                self.log.critical(f"Couldn't find {cog}")
                self.log.info("Continuing..")
            except (commands.ExtensionError, commands.ExtensionFailed, Exception):
                self.log.critical(f"Couldn't load {cog}``````{traceback.format_exc()}")
                self.log.info("Continuing..")

    def unload(self, *extensions, log=True) -> None:
        for cog in extensions:
            try:
                self.unload_extension(f"cogs.{cog}")
                if log:
                    self.log.info(f"Unloaded {cog}")
            except commands.ExtensionNotLoaded:
                if log:
                    self.log.info(f"Failed to unload {cog}")

    def reload(self, *extensions) -> None:
        for cog in extensions:
            try:
                self.reload_extension(f"cogs.{cog}")
                self.log.info(f"Reloaded {cog}")
            except commands.ExtensionNotFound:
                self.log.info(f"Reloaded {cog}")
            except commands.ExtensionNotLoaded:
                self.log.info(f"{cog} isn't loaded")
            except commands.ExtensionError:
                self.log.info(f"Ignoring exception in Cog: {cog}``````{traceback.format_exc()}")

    # Scheduled for removal whence all references are removed
    async def download(self, url: str, timeout: int = 10):
        return await self.utils.download(url, timeout)

    async def save_json(self, fp, data, mode="w+", **json_kwargs) -> None:
        return await self.utils.save_json(fp, data, mode, **json_kwargs)

    async def wait_for_msg(self, ctx, timeout=60, action="Waiting for message") -> Optional[discord.Message]:
        return await self.utils.wait_for_msg(ctx, timeout, action)

    async def verify_user(self, context=None, channel=None, user=None, timeout=45, delete_after=False):
        return await self.utils.verify_user(context, channel, user, timeout, delete_after)

    async def get_choice(self, ctx, *options, user, timeout=30) -> Optional[object]:
        """ Reaction based menu for users to choose between things """
        return await self.utils.get_choice(ctx, *options, user=user, timeout=timeout)
    # -------------------------------------------------------

    def run(self):
        if bot.initial_extensions:
            self.log.info("Loading initial cogs", color='yellow')
            self.load(*self.initial_extensions)
            self.log.info("Finished loading initial cogs\nLogging in..", color='yellow')
        cipher = auth.Tokens()
        super().run(cipher.decrypt("fate"))


# Reset log files on startup so they don't fill up and cause lag
start_time = time()
# if os.path.isfile("/home/luck/.pm2/logs/fate-out.log"):
#     os.remove("/home/luck/.pm2/logs/fate-out.log")
# if os.path.isfile("/home/luck/.pm2/logs/fate-error.log"):
#     os.remove("/home/luck/.pm2/logs/fate-error.log")
if os.path.isfile('discord.log'):
    os.remove('discord.log')

# debug_task log
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Initialize the bot
bot = Fate(max_messages=250000, case_insensitive=True)
bot.allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)
bot.remove_command('help')  # Default help command
bot.add_check(checks.command_is_enabled)


@bot.event
async def on_shard_ready(shard_id):
    bot.log.info(f"Shard {shard_id} connected")


@bot.event
async def on_connect():
    bot.log.info(
        '------------'
        '\nLogged in as'
        f'\n{bot.user}'
        f'\n{bot.user.id}'
        '\n------------',
        color='green'
    )
    cprint("Initializing cache", "yellow", end="\r")
    index = 0
    chars = r"-/-\-"
    while not bot.is_ready():
        cprint(f"Initializing cache {chars[index]}", "yellow", end="\r")
        index += 1
        if index + 1 == len(chars):
            index = 0
        await asyncio.sleep(0.21)
        bot.log.debug("Iterated through cache initialization")


@bot.event
async def on_ready():
    bot.log.info("Finished initializing cache", color="yellow")
    if not bot.pool:
        await bot.create_pool()
    bot.owner_ids = set(list([bot.config["bot_owner_id"], *bot.config["bot_owner_ids"]]))
    if bot.awaited_extensions:
        bot.log.info("Loading awaited cogs", color='yellow')
        bot.load(*bot.awaited_extensions)
        bot.log.info("Finished loading awaited cogs", color='yellow')
    bot.core_tasks.ensure_all()
    seconds = round(time() - start_time)
    bot.log.info(f"Startup took {seconds} seconds")
    for error in bot.login_errors:
        bot.log.critical(f"Error ignored during startup:\n{error}")


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
    inviter = "Unknown"
    if guild.me.guild_permissions.view_audit_log:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
            inviter = str(entry.user)
    e.description = f"**Name:** {guild.name}" \
                    f"\n**ID:** {guild.id}" \
                    f"\n**Owner:** {guild.owner}" \
                    f"\n**Members:** [`{len(guild.members)}`]" \
                    f"\n**Inviter:** [`{inviter}`]"
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
    async with bot.open("./data/stats.json", "w") as f:
        await f.write(json.dumps(stats))


if __name__ == '__main__':
    bot.log.info("Starting Bot", color='yellow')
    bot.start_time = datetime.now()
    try:
        bot.run()
    except discord.errors.LoginFailure:
        print("Invalid Token")
    except asyncio.exceptions.CancelledError:
        pass
    except (RuntimeError, KeyboardInterrupt):
        pass
