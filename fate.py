import json
import traceback
from time import time
from datetime import datetime
import os
import asyncio
import logging
from typing import *
import aiohttp
import aiofiles
import random

from discord.ext import commands
import discord
import aiomysql
import pymysql
from termcolor import cprint
from PIL import Image, ImageDraw, ImageFont

from utils import outh, utils, tasks, colors, checks
from utils.custom_logging import Logging


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

        self.initial_extensions = [     # Cogs to load before logging in
            'error_handler', 'config', 'menus', 'core', 'mod', 'welcome', 'farewell', 'notes', 'archive',
            'coffeeshop', 'custom', 'actions', 'reactions', 'responses', 'textart', 'fun', 'dev', 'readme',
            'reload', 'embeds', 'polis', 'apis', 'chatbridges', 'clean_rythm', 'utility', 'psutil', 'rules',
            'duel_chat', 'selfroles', 'lock', 'audit', 'cookies', 'server_list', 'emojis', 'giveaways', 'polls',
            'logger', 'autorole', 'changelog', 'restore_roles', 'chatbot', 'anti_spam', 'anti_raid', 'chatfilter',
            'nsfw', 'minecraft', 'chatlock', 'rainbow', 'system', 'user', 'limiter', 'dm_channel', 'factions',
            'secure_overwrites', 'server_setup', 'global-chat', 'ranking', 'statistics', 'toggles', 'verification'
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
            "ChatBot":      {"help": "chatbot",      "enable": "chatbot.enable",      "disable": "chatbot.disable"},
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

        self.utils = utils                   # Custom utility functions
        self.result = utils.Result           # Custom Result Object Creator
        self.memory = utils.MemoryInfo       # Class for easily accessing memory usage
        self.core_tasks = tasks.Tasks(self)  # Object to start the main tasks like `changing status`
        self.log = Logging(bot=self)         # Class to handle printing/logging

        # ContextManager for quick sql cursor access
        class Cursor:
            def __init__(cls):
                cls.conn = None
                cls.cursor = None

            async def __aenter__(cls):
                while not self.pool:
                    await asyncio.sleep(0.21)
                cls.conn = await self.pool.acquire()
                cls.cursor = await cls.conn.cursor()
                return cls.cursor

            async def __aexit__(cls, _type, _value, _tb):
                await cls.conn.commit()
                self.pool.release(cls.conn)

        self.cursor = Cursor

        # Async compatible file manager using aiofiles and asyncio.Lock
        class AsyncFileManager:
            def __init__(cls, file: str, mode: str = "r", lock: bool = True):
                cls.file = cls.temp_file = file
                if "w" in mode:
                    cls.temp_file += ".tmp"
                cls.mode = mode
                cls.fp_manager = None
                cls.lock = lock
                if lock and file not in self.locks:
                    self.locks[file] = asyncio.Lock()

            async def __aenter__(cls):
                if cls.lock:
                    await self.locks[cls.file].acquire()
                cls.fp_manager = await aiofiles.open(file=cls.temp_file, mode=cls.mode)
                return cls.fp_manager

            async def __aexit__(cls, _exc_type, _exc_value, _exc_traceback):
                await cls.fp_manager.close()
                if cls.file != cls.temp_file:
                    os.rename(cls.temp_file, cls.file)
                if cls.lock:
                    self.locks[cls.file].release()

        self.open = AsyncFileManager

        class WaitForEvent:
            def __init__(cls, event, check=None, channel=None, send_error=True, timeout=60):
                cls.event = event
                cls.channel = channel
                cls.check = check
                cls.send_error = send_error
                cls.timeout = timeout

                ctx = check if isinstance(check, commands.Context) else None
                if ctx and not cls.channel:
                    cls.channel = cls.channel
                if ctx and cls.event == 'message':
                    cls.check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            async def __aenter__(cls):
                try:
                    message = await self.wait_for(cls.event, check=cls.check, timeout=cls.timeout)
                except asyncio.TimeoutError:
                    if cls.send_error and cls.channel:
                        await cls.channel.send(f"Timed out waiting for {cls.event}")
                    raise self.ignored_exit()
                else:
                    return message

            async def __aexit__(cls, exc_type, exc_val, exc_tb):
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

        # deprecated shit
        self.get_stats = utils.get_stats()
        self.get_config = utils.get_config()

        super().__init__(
            command_prefix=utils.get_prefixes,
            activity=discord.Game(name=self.config['startup_status']), **options
        )

    async def on_error(self, event_method, *args, **kwargs):
        full_error = str(traceback.format_exc())
        ignored = ("NotFound")
        if any(Type in full_error for Type in ignored):
            return
        self.log.critical(full_error)

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
        sql = outh.MySQL()
        for _attempt in range(5):
            try:
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
            except commands.ExtensionError:
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

    # def log(self, message, level='INFO', tb=None, color=None, end=None) -> str:
    #     if level == 'DEBUG' and not self.debug_mode:
    #         return ""
    #     now = str(datetime.now().strftime("%I:%M%p"))
    #     if now.startswith('0'):
    #         now = now.replace('0', '', 1)
    #     lines = []
    #     for line in message.split('\n'):
    #         msg = f"{now} | {level} | {line}"
    #         if level == 'DEBUG' and self.config['debug_mode']:
    #             cprint(msg, color if color else 'cyan', end=end)
    #         elif level == 'INFO':
    #             cprint(msg, color if color else 'green', end=end)
    #         elif level == 'CRITICAL':
    #             cprint(msg, color if color else 'red', end=end)
    #         lines.append(msg)
    #     if tb:
    #         cprint(str(tb), color if color else 'red', end=end)
    #         lines.append(str(tb))
    #     self.logs.append('\n'.join(lines))
    #     self.logs = self.logs[:1000]
    #     return '\n'.join(lines)

    async def download(self, url: str, timeout: int = 10):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(str(url), timeout=timeout) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.read()
            except asyncio.TimeoutError:
                return None

    async def save_json(self, fp, data, mode="w+", **json_kwargs) -> None:
        # self.log(f"Saving {fp}", "DEBUG")
        # before = monotonic()
        async with aiofiles.open(fp + ".tmp", mode) as f:
            await f.write(json.dumps(data, **json_kwargs))
        # ping = str(round((monotonic() - before) * 1000))
        # self.log(f"Wrote to tmp file in {ping}ms", "DEBUG")
        # before = monotonic()
        try:
            os.rename(fp + ".tmp", fp)
        except FileNotFoundError:
            pass
            # self.log("Tmp file didn't exist, not renaming", "DEBUG")
        # ping = str(round((monotonic() - before) * 1000))
        # self.log(f"Replaced old file in {ping}ms", "DEBUG")

    async def wait_for_msg(self, ctx, timeout=60, action="Waiting for message") -> Optional[discord.Message]:
        def pred(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.wait_for('message', check=pred, timeout=timeout)
        except asyncio.TimeoutError:
            await ctx.send(f"{action} timed out!")
            return None
        else:
            return msg

    async def verify_user(self, context=None, channel=None, user=None, timeout=45, delete_after=False):
        if not user and not context:
            raise TypeError("verify_user() requires either 'context' or 'user', and neither was given")
        if not channel and not context:
            raise TypeError("verify_user() requires either 'context' or 'channel', and neither was given")
        if not user:
            user = context.author
        if not channel:
            channel = context.channel

        fp = os.path.basename(f"./static/captcha-{time()}.png")
        abcs = "abcdefghijklmnopqrstuvwxyz"
        chars = " ".join([random.choice(list(abcs)).upper() for _i in range(6)])

        def create_card():
            font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 30)
            size = font.getsize(chars)
            card = Image.new("RGBA", size=(size[0] + 20, 50), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(card)
            draw.text((10, 10), chars, fill="blue", font=font)

            lowest_range = 5
            max_range = size[0] + 15
            divide = (max_range - lowest_range) / 3
            fix_points = [random.choice(range(10, 40)) for _i in range(4)]

            for iteration in range(3):
                line_positions = (
                    # Beginning of line
                    5 + (divide * iteration), fix_points[iteration],
                    # End of line
                    max_range - ((divide * 3) - sum([divide for _i in range(iteration + 1)])), fix_points[iteration + 1]
                )
                draw.line(line_positions, fill="blue", width=5)
            card.save(fp)

        await self.loop.run_in_executor(None, create_card)

        e = discord.Embed(color=colors.fate())
        e.set_author(name=str(user), icon_url=user.avatar_url)
        e.set_image(url="attachment://" + fp)
        e.set_footer(text=f"You have {self.utils.get_time(timeout)}")
        message = await channel.send(f"{user.mention} please verify you're human", embed=e, file=discord.File(fp))

        def pred(m):
            return m.author.id == user.id and str(m.content).lower() == chars.lower().replace(" ", "")

        try:
            await self.wait_for("message", check=pred, timeout=timeout)
        except asyncio.TimeoutError:
            if delete_after:
                await message.delete()
            else:
                e.set_footer(text="Captcha Failed")
                await message.edit(embed=e)
            return False
        else:
            if delete_after:
                await message.delete()
            else:
                e.set_footer(text="Captcha Passed")
                await message.edit(content=None, embed=e)
            return True

    async def get_choice(self, ctx, *options, user, timeout=30) -> Optional[object]:
        """ Reaction based menu for users to choose between things """
        async def add_reactions(message) -> None:
            for emoji in emojis:
                if not message:
                    return
                try:
                    await message.add_reaction(emoji)
                except discord.errors.NotFound:
                    return
                if len(options) > 5:
                    await asyncio.sleep(1)
                elif len(options) > 2:
                    await asyncio.sleep(0.5)

        def predicate(r, u) -> bool:
            return u.id == user.id and str(r.emoji) in emojis

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"][:len(options)]
        if not user:
            user = ctx.author

        e = discord.Embed(color=colors.fate())
        e.set_author(name="Select which option", icon_url=ctx.author.avatar_url)
        e.description = "\n".join(f"{emojis[i]} {option}" for i, option in enumerate(options))
        e.set_footer(text=f"You have {self.utils.get_time(timeout)}")
        message = await ctx.send(embed=e)
        self.loop.create_task(add_reactions(message))

        try:
            reaction, _user = await self.wait_for("reaction_add", check=predicate, timeout=timeout)
        except asyncio.TimeoutError:
            await message.delete()
            return None
        else:
            await message.delete()
            return options[emojis.index(str(reaction.emoji))]

    async def handle_tcp(self, reader, writer, get_coro, push_coro, remove_coro):
        """ Manage an echo """
        raw_data = await reader.read(1024)
        data = json.loads(raw_data.decode())  # type: dict
        guild_id = data["target"]

        # Get a guilds data
        if data["request"] == "get":
            return_data = await get_coro(guild_id)
            if not return_data:
                return_data = {
                    "successful": False,
                    "reason": "No data"
                }

        # Update a guilds data
        elif data["request"] == "push":
            result, reason = await push_coro(guild_id, data)
            return_data = {
                "successful": result,
                "reason": reason
            }

        # Remove a guilds data
        elif data["request"] == "remove":
            result, reason = await remove_coro(guild_id)
            return_data = {
                "successful": result,
                "reason": reason
            }

        # Unknown request
        else:
            return_data = {"successful": False, "reason": "Unknown request"}

        writer.write(json.dumps(return_data).encode())
        await writer.drain()

    def run(self):
        if bot.initial_extensions:
            self.log.info("Loading initial cogs", color='yellow')
            self.load(*self.initial_extensions)
            self.log.info("Finished loading initial cogs\nLogging in..", color='yellow')
        super().run(outh.tokens('fatezero'))


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
