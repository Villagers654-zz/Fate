
"""
Fate
~~~~~

Main file intended for starting the bot

:copyright: (C) 2018-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import json
import traceback
from time import time
from datetime import datetime, timezone
import os
import asyncio
import logging
from contextlib import suppress
from base64 import b64decode, b64encode
import sys
from cryptography.fernet import Fernet
from getpass import getpass
import aiohttp

from discord.ext import commands
import discord
import aiomysql
import pymysql
from termcolor import cprint
from discord.errors import NotFound, Forbidden, HTTPException
from discord_sentry_reporting import use_sentry
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from cleverbot import async_ as cleverbot

from classes import checks
from classes.exceptions import EmptyException
from botutils import colors, get_prefixes_async, Utils, FileCache
from botutils.custom_logging import Logging
from cogs.core.tasks import Tasks


class Fate(commands.AutoShardedBot):
    loop: asyncio.BaseEventLoop
    def __init__(self, **options):
        # Bot Configuration
        with open("./data/config.json", "r") as f:
            self.config = json.load(f)  # type: dict
        with open("./data/userdata/config.json", "r") as f:
            dat = json.load(f)
        self.blocked = dat["blocked"]

        # User configs
        self.restricted = {}
        with open("./data/userdata/disabled_commands.json", "r") as f:
            self.disabled_commands = json.load(f)
        if not os.path.exists(self.config["datastore_location"]):
            os.mkdir(self.config["datastore_location"])

        self.auth = {}
        self.debug_mode = self.config["debug_mode"]
        self.owner_ids = set(
            list([self.config["bot_owner_id"], *self.config["bot_owner_ids"]])
        )
        self.theme_color = self.config["theme_color"]

        self.utils = Utils(self)
        self.cache = FileCache(self)

        # Cache
        self.toggles = {}  # Mappings for `Module -> Enable Command`
        self.locks = {}
        self.operation_locks = []
        self.tasks = {}  # Task object storing for easy management
        self.logger_tasks = {}  # Same as Fate.tasks except dedicated to cogs.logger
        self.chats = {}  # CleverBot API chat objects
        self.filtered_messages = {}

        self.pool = None  # MySQL Pool initialized on_ready
        self.lavalink = None  # Music server
        self.login_errors = []  # Exceptions ignored during startup
        self.logs = []  # Logs to send to discord, empties out quickly
        self.last_traceback = ""  # Formatted string of the last error traceback
        self.ignored_exit = EmptyException
        self.allow_user_mentions = discord.AllowedMentions(
            users=True, roles=False, everyone=False
        )
        self.log = Logging(bot=self)         # Class to handle printing/logging

        self.user_config_cache = [
            0,  # Time last updated
            {}  # User data
        ]

        # Set the oauth_url for users to invite the bot with
        perms = discord.Permissions(0)
        perms.update(**self.config["bot_invite_permissions"])
        self.invite_url = discord.utils.oauth_url(self.config["bot_user_id"], permissions=perms)

        super().__init__(
            command_prefix=get_prefixes_async,
            intents=discord.Intents.all(),
            activity=discord.Game(name=self.config["startup_status"]),
            max_messages=self.config["max_cached_messages"],
            **options,
        )

    @property
    def core_tasks(self) -> Tasks:
        """Return the cog for tasks relating to bot management"""
        if "Tasks" not in self.cogs:
            raise ModuleNotFoundError("The Tasks cog hasn't been loaded yet")
        return self.get_cog("Tasks")

    def get_fp_for(self, path) -> str:
        """Return the path for the set storage location"""
        return os.path.join(self.config["datastore_location"], path)

    async def get_resource(self, url, method="get", *args, **kwargs):
        try:
            async with aiohttp.ClientSession() as session:
                operation = getattr(session, method.lower())
                async with operation(url, *args, **kwargs) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        raise self.ignored_exit
        except aiohttp.ClientPayloadError:
            raise commands.BadArgument("Failed to fetch an invalid resource")

    def get_message(self, message_id: int):
        """ Return a message from the internal cache if it exists """
        for message in self.cached_messages:
            if message.id == message_id:
                return message
        return None

    @property
    def mongo(self):
        conf = self.auth["MongoDB"]
        return pymongo.MongoClient(conf["url"])[conf["db"]]

    @property
    def aio_mongo(self):
        conf = self.auth["MongoDB"]
        client = AsyncIOMotorClient(conf["url"], **conf["connection_args"])
        db = client.get_database(conf["db"])
        return db

    async def update_mongo(self, collection, filter, data):
        pass

    async def remove_mongo(self, collection, filter):
        self.aio_mongo[collection].delete_many(filter)

    async def create_pool(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.log.critical(
                "Closed the existing pool to start a new one"
            )
        sql = self.auth["MySQL"]  # type: dict
        for _attempt in range(5):
            try:
                self.log("Connecting to db")
                pool = await aiomysql.create_pool(
                    host=sql["host"],
                    port=sql["port"],
                    user=sql["user"],
                    password=sql["password"],
                    db=sql["db"],
                    autocommit=True,
                    loop=self.loop,
                    minsize=1,
                    maxsize=16
                )
                self.pool = pool
                break
            except (ConnectionRefusedError, pymysql.err.OperationalError):
                self.log.critical(
                    "Couldn't connect to MySQL server, retrying in 25 seconds.."
                )
                self.log.critical(traceback.format_exc())
            await asyncio.sleep(25)
        else:
            self.log.critical(
                f"Couldn't connect to MySQL server, reached max attempts``````{traceback.format_exc()}"
            )
            self.unload_extensions(*self.config["extensions"], log=False)
            self.log.critical("Logging out..")
            return await self.close()
        self.log.info(f"Initialized db {sql['db']} with {sql['user']}@{sql['host']}")

    async def wait_for_pool(self) -> bool:
        if not self.pool:
            for _ in range(240):
                await asyncio.sleep(1)
                if self.pool:
                    break
            else:
                return False
        return True

    async def execute(self, sql: str) -> None:
        if await self.wait_for_pool():
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    with suppress(RuntimeError):
                        await cur.execute(sql)
        return None

    async def fetch(self, sql: str) -> tuple:
        if await self.wait_for_pool():
            async with self.utils.cursor() as cur:
                await cur.execute(sql)
                r = await cur.fetchall()
            return r
        return ()

    async def rowcount(self, sql: str) -> int:
        if await self.wait_for_pool():
            async with self.utils.cursor() as cur:
                await cur.execute(sql)
                rows = cur.rowcount
            return rows
        return 0

    def load_collection(self, collection) -> dict:
        data = {}
        for config in collection.find({}):
            data[config["_id"]] = {
                k: v for k, v in config.items() if k != "_id"
            }
        return data

    def get_asset(self, asset):
        asset = asset.lstrip("/")
        if "." not in asset or not os.path.exists(f"./assets/{asset}"):
            dir = "./assets/"
            paths = asset.split("/")
            filename = paths[-1:][0]
            if "/" in asset:
                dir += paths[0]
            for file in os.listdir(dir):
                if filename in file:
                    asset = asset.replace(filename, file)
                    break
            else:
                for root, dirs, files in os.walk(dir):
                    for file in files:
                        if filename in file:
                            asset = os.path.join(root.lstrip("./assets/"), file)
                            break
        return f"http://assets.fatebot.xyz/{asset}"

    def load_extensions(self, *extensions) -> None:
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
        self.paginate()

    def unload_extensions(self, *extensions, log=True) -> None:
        for cog in extensions:
            try:
                self.unload_extension(f"cogs.{cog}")
                if log:
                    self.log.info(f"Unloaded {cog}")
            except commands.ExtensionNotLoaded:
                if log:
                    self.log.info(f"Failed to unload {cog}")

    def reload_extensions(self, *extensions) -> None:
        for cog in extensions:
            try:
                self.reload_extension(f"cogs.{cog}")
                self.log.info(f"Reloaded {cog}")
            except commands.ExtensionNotFound:
                self.log.info(f"Reloaded {cog}")
            except commands.ExtensionNotLoaded:
                self.log.info(f"{cog} isn't loaded")
            except commands.ExtensionError:
                self.log.info(
                    f"Ignoring exception in Cog: {cog}``````{traceback.format_exc()}"
                )
        self.paginate()

    def paginate(self):
        """Map out each modules enable command for use of `.enable module`"""
        remap = not not self.toggles
        self.toggles.clear()
        for module, cls in self.cogs.items():
            if hasattr(cls, "enable_command") and hasattr(cls, "disable_command"):
                self.toggles[module] = [
                    getattr(cls, "enable_command"),
                    getattr(cls, "disable_command")
                ]
        self.log(f"{'Rem' if remap else 'M'}apped modules")

    async def load(self, data):
        load_json = lambda: json.loads(data)
        return await self.loop.run_in_executor(None, load_json)

    async def dump(self, data):
        dump_json = lambda: json.dumps(data)
        return await self.loop.run_in_executor(None, dump_json)

    def encode(self, string) -> str:
        return b64encode(string.encode()).decode()

    def decode(self, string) -> str:
        return b64decode(string.encode()).decode()

    def run(self):
        # Decrypt auth data and login
        cipher = Fernet(getpass().encode())
        fp = os.path.join(self.config["datastore_location"], "auth.json")
        with open(fp, "r") as f:
            data = cipher.decrypt(f.read().encode()).decode()
        self.auth = json.loads(data)

        # Load in guild prefixes
        self.guild_prefixes = {}
        collection = self.mongo["GuildPrefixes"]
        for config in collection.find({}):
            self.guild_prefixes[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }
#
        # Load in user prefixes
        self.user_prefixes = {}
        collection = bot.mongo["UserPrefixes"]
        for config in collection.find({}):
            self.user_prefixes[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }

        # Load additional modules/cogs
        if self.config["extensions"]:
            self.log.info("Loading initial cogs", color="yellow")
            extensions = []
            for category, cogs in self.config["extensions"].items():
                for cog in cogs:
                    extensions.append(f"{category}.{cog}")
            self.load_extensions(*extensions)
            self.log.info("Finished loading initial cogs\nAuthenticating with token..", color="yellow")
            self.paginate()

        # Load in caches
        self.restricted = self.utils.cache("restricted")
        self.attrs = self.utils.attrs

        # Initialize cleverBot
        self.cb = cleverbot.Cleverbot(
            self.auth["CleverBot"],
            cs='76nxdxIJ02AAA',
            timeout=10,
            tweak1=0,
            tweak2=100,
            tweak3=100,
            loop=self.loop
        )

        super().run(self.auth["tokens"][self.config["token_id"]])


# Reset log files on startup so they don't fill up and cause lag
start_time = time()
if os.path.isfile("discord.log"):
    os.remove("discord.log")

# debug_task log
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# Initialize the bot
bot = Fate(case_insensitive=True)
bot.allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)
bot.remove_command("help")  # Default help command
bot.add_check(checks.command_is_enabled)
bot.add_check(checks.blocked)
bot.add_check(checks.restricted)
use_sentry(
    bot,
    dsn=bot.config["sentry_dsn"]
)


@bot.event
async def on_shard_connect(shard_id):
    if shard_id == 0:
        bot.log.info(
            "------------"
            "\nLogging in as"
            f"\n{bot.user}"
            f"\n{bot.user.id}"
            "\n------------",
            color="green",
        )
    bot.log.info(f"Shard {shard_id} connected")


@bot.event
async def on_connect():
    cprint("Initializing cache", "yellow", end="\r")
    index = 0
    chars = r"-/-\-"
    while not bot.is_ready():
        cprint(f"Initializing cache {chars[index]}", "yellow", end="\r")
        index += 1
        if index + 1 == len(chars):
            index = 0
        await asyncio.sleep(0.21)


@bot.event
async def on_ready():
    bot.log.info("Finished initializing cache", color="yellow")
    # Reconnect the nodes if the bot is reconnecting
    if "Music" in bot.cogs:
        cog = bot.cogs["Music"]
        if cog.refresh:
            bot.cogs["Music"].refresh_nodes()
            bot.log.info("Refreshed nodes")
        else:
            cog.refresh = True
    if not bot.pool:
        await bot.create_pool()
    bot.owner_ids = set(
        list([bot.config["bot_owner_id"], *bot.config["bot_owner_ids"]])
    )
    bot.core_tasks.ensure_all()
    seconds = round(time() - start_time)
    bot.log.info(f"Startup took {seconds} seconds")
    for error in bot.login_errors:
        bot.log.critical(f"Error ignored during startup:\n{error}")


get_prefix_cd = bot.utils.cooldown_manager(1, 10)


@bot.event
async def on_message(msg):
    # Send the prefix if the bot's mentioned
    if not msg.author.bot and bot.user.mentioned_in(msg) and len(msg.content.split()) == 1:
        if str(bot.user.id) in msg.content:
            rate_limited = get_prefix_cd.check(msg.author.id)
            if not rate_limited:
                r = await get_prefixes_async(bot, msg)
                prefixes = "\n".join(r[1:])
                if len(prefixes.split("\n")) > 2:
                    return
                with suppress(NotFound, Forbidden, HTTPException, AttributeError):
                    await msg.channel.send(f"The prefixes you can use are:\n{prefixes}")
                return
    if msg.guild and msg.guild.me and not msg.channel.permissions_for(msg.guild.me).send_messages:
        return

    # Replace mini numbers due to them being recognized as integers
    msg.content = msg.content.encode("utf-8").decode()

    # Parse prefix, run checks, and execute
    await bot.process_commands(msg)


@bot.event
async def on_error(_event_method, *_args, **_kwargs):
    if "Unknown Interaction" in traceback.format_exc():
        return
    error = sys.exc_info()[1]
    ignored = (
        bot.ignored_exit,
        aiohttp.ClientOSError,
        asyncio.exceptions.TimeoutError,
        discord.errors.DiscordServerError,
        discord.errors.NotFound
    )
    if isinstance(error, ignored):
        return
    raise error


@bot.event
async def on_guild_join(guild):
    if not bot.is_ready() or not guild:
        return
    channel = bot.get_channel(bot.config["log_channel"])
    e = discord.Embed(color=colors.pink)
    e.set_author(name="Bot Added to Guild", icon_url=bot.user.avatar.url)
    if guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    inviter = "Unknown"
    if guild.me.guild_permissions.view_audit_log:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
            inviter = str(entry.user)
    e.description = (
        f"**Name:** {guild.name}"
        f"\n**ID:** {guild.id}"
        f"\n**Owner:** {guild.owner}"
        f"\n**Members:** [`{len(guild.members)}`]"
        f"\n**Inviter:** [`{inviter}`]"
    )
    await channel.send(embed=e)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    if not bot.is_ready():
        return
    channel = bot.get_channel(bot.config["log_channel"])
    e = discord.Embed(color=colors.pink)
    e.set_author(name="Bot Left or Was Removed", icon_url=bot.user.avatar.url)
    if guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    e.description = (
        f"**Name:** {guild.name}\n"
        f"**ID:** {guild.id}\n"
        f"**Owner:** {guild.owner}\n"
        f"**Members:** [`{len(guild.members)}`]"
    )
    async with bot.utils.open("members.txt", "w") as f:
        await f.write("\n".join([f"{m.id}, {m}, {m.mention}" for m in guild.members]))
    await channel.send(embed=e, file=discord.File("members.txt"))
    with suppress(FileNotFoundError):
        os.remove("members.txt")


if __name__ == "__main__":
    bot.log.info("Starting Bot", color="yellow")
    bot.start_time = datetime.now(tz=timezone.utc)
    try:
        bot.run()
    except discord.errors.LoginFailure:
        print("Invalid Token")
    except asyncio.exceptions.CancelledError:
        pass
    except (RuntimeError, KeyboardInterrupt):
        pass
