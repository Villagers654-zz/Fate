# Bot utility functions

import asyncio
import json
from datetime import datetime
import re
from time import time
import os
import subprocess
from importlib import reload
from contextlib import suppress

from discord.ext import commands, tasks
import discord

from botutils.packages import resources, listeners, menus, files, tools


class Utils(commands.Cog):
    def __init__(self, bot, _filter, memory_info, result):
        self.bot = bot
        self.TempConvo = TempConvo

        # Resources
        self.colors = self.emotes = self.generate_rainbow_rgb = self.get_config = self.get_stats = None
        # Menus
        self.verify_user = self.get_choice = self.configure = None
        # Listeners
        self.listener = None
        # Files
        self.tempdl = self.save_json = self.download = None
        self.split = self.cleanup_msg = self.bytes2human = self.extract_timer = self.get_seconds = None
        # Tools
        self.get_images = self.total_seconds = self.format_dict = self.add_field = self.update_msg = None
        self.get_user = self.get_role = self.get_time = None

        # Packages to import
        self.packages = [
            "resources", "tools", "listeners", "files", "menus"
        ]
        for package in self.packages:
            reload(eval(package))
            eval(package).init(self)

        self.filter = _filter
        self.MemoryInfo = memory_info
        self.Result = result

    @staticmethod
    def get_prefix(ctx):
        p = "."
        if ctx.guild:
            guild_id = str(ctx.guild.id)
            config = ctx.bot.utils.get_config()  # type: dict
            if guild_id in config["prefix"]:
                p = config["prefix"][guild_id]
        return p

    @staticmethod
    async def get_prefixes_async(bot, msg):
        default_prefix = commands.when_mentioned_or(".")(bot, msg)
        # config_path = bot.get_fp_for("userdata/config.json")

        if msg.author.id == bot.config["owner_id"]:
            return default_prefix

        config = bot.prefix_cache

        if msg.author.id in config["blocked"]:
            return None

        guild_id = str(msg.guild.id) if msg.guild else None
        if msg.guild and guild_id in config["restricted"]:
            if msg.channel.id in config["restricted"][guild_id]:
                if not msg.author.guild_permissions.administrator:
                    return None

        user_id = str(msg.author.id)
        if user_id in config["personal_prefix"]:
            return commands.when_mentioned_or(
                config["personal_prefix"][user_id]
            )(bot, msg)

        if guild_id in config["prefix"]:
            return commands.when_mentioned_or(
                config["prefix"][guild_id]
            )(bot, msg)

        return default_prefix

    @staticmethod
    def get_prefixes(bot, msg):
        conf = resources.get_config()
        config = bot.config
        if msg.author.id == config["bot_owner_id"]:
            return commands.when_mentioned_or(".")(bot, msg)
        if "blocked" in conf:
            if msg.author.id in conf["blocked"]:
                return "lsimhbiwfefmtalol"
        else:
            bot.log("Blocked key was non existant")
        if not msg.guild:
            return commands.when_mentioned_or(".")(bot, msg)
        guild_id = str(msg.guild.id)
        if "restricted" not in conf:
            conf["restricted"] = {}
        if guild_id in conf["restricted"]:
            if msg.channel.id in conf["restricted"][guild_id]["channels"] and (
                not msg.channel.permissions_for(msg.author).manage_messages
            ):
                return "lsimhbiwfefmtalol"
        if "personal_prefix" not in conf:
            conf["personal_prefix"] = {}
        user_id = str(msg.author.id)
        if user_id in conf["personal_prefix"]:
            return commands.when_mentioned_or(conf["personal_prefix"][user_id])(
                bot, msg
            )
        if "prefix" not in conf:
            conf["prefix"] = {}
        prefixes = conf["prefix"]
        if guild_id not in prefixes:
            return commands.when_mentioned_or(".")(bot, msg)
        return commands.when_mentioned_or(prefixes[guild_id])(bot, msg)

    @staticmethod
    def emojis(emoji):
        if emoji is None:
            return "‎"
        if emoji == "plus":
            return "<:plus:548465119462424595>"
        if emoji == "edited":
            return "<:edited:550291696861315093>"
        if emoji == "arrow":
            date = datetime.utcnow()
            if date.month == 1 and date.day == 26:  # Chinese New Year
                return "🐉"
            if date.month == 2 and date.day == 14:  # Valentines Day
                return "❤"
            if date.month == 6:  # Pride Month
                return "<a:arrow:679213991721173012>"
            if date.month == 7 and date.day == 4:  # July 4th
                return "🎆"
            if date.month == 10 and date.day == 31:  # Halloween
                return "🎃"
            if date.month == 11 and date.day == 26:  # Thanksgiving
                return "🦃"
            if datetime.month == 12 and date.day == 25:  # Christmas
                return "🎄"
            return "<:enter:673955417994559539>"

        if emoji == "text_channel":
            return "<:textchannel:679179620867899412>"
        if emoji == "voice_channel":
            return "<:voicechannel:679179727994617881>"

        if emoji == "invisible" or emoji is discord.Status.offline:
            return "<:status_offline:659976011651219462>"
        if emoji == "dnd" or emoji is discord.Status.dnd:
            return "<:status_dnd:659976008627388438>"
        if emoji == "idle" or emoji is discord.Status.idle:
            return "<:status_idle:659976006030983206>"
        if emoji == "online" or emoji is discord.Status.online:
            return "<:status_online:659976003334045727>"

    @staticmethod
    def default_cooldown():
        return [2, 5, commands.BucketType.user]


class Result:
    def __init__(self, result, errored=False, traceback=None):
        self.result = result
        self.errored = errored
        self.traceback = traceback


class Filter:
    def __init__(self):
        self._blacklist = []
        self.index = {
            "a": ["\\@", "4"],
            "b": [],
            "c": [],
            "d": [],
            "e": ["3"],
            "f": [],
            "g": [],
            "h": [],
            "i": ["\\!", "1"],
            "j": [],
            "k": [],
            "l": [],
            "m": [],
            "n": [],
            "o": ["0", "\\(\\)", "\\[\\]"],
            "p": [],
            "q": [],
            "r": [],
            "s": ["\\$"],
            "t": [],
            "u": [],
            "v": [],
            "w": [],
            "x": [],
            "y": [],
            "z": [],
            "0": [],
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
        }

    @property
    def blacklist(self):
        return self._blacklist

    @blacklist.setter
    def blacklist(self, value: list):
        self._blacklist = [item.lower() for item in value]

    def __call__(self, message: str):
        for phrase in self.blacklist:
            pattern = ""
            try:
                if len(phrase) > 3:
                    message = message.replace(" ", "")
                message = str(message).lower()
                chunks = message.replace(" ", "").split()
                if phrase in chunks:
                    return True, phrase
                if (
                    not len(list(filter(lambda char: char in message, list(phrase))))
                    > 1
                ):
                    continue
                if any(char not in self.index.keys() for char in phrase):
                    pattern = ""
                    for char in phrase:
                        if char in self.index and self.index[char]:
                            main_char = (
                                char if char in self.index.keys() else f"\\{char}"
                            )
                            singles = [c for c in self.index[char] if len(c) == 1]
                            multi = [c for c in self.index[char] if len(c) > 1]
                            pattern += (
                                f"([{main_char}{''.join(f'{c}' for c in singles)}]"
                            )
                            if singles and multi:
                                pattern += "|"
                            if multi:
                                pattern += "|".join(f"({c})" for c in multi)
                            pattern += ")"
                        else:
                            pattern += char
                        if char in self.index.keys():
                            pattern += "+"
                else:
                    pattern = phrase
                pattern.replace("++", "+")
                if re.search(pattern, message):
                    return True, pattern  # Flagged
            except Exception as e:
                print(f"{e}\nMsg: {message}\nPattern: {pattern}")
        return False, None


class MemoryInfo:
    @staticmethod
    async def __coro_fetch(interval=0):
        p = subprocess.Popen(
            f"python3 memory_info.py {os.getpid()} {interval}",
            stdout=subprocess.PIPE,
            shell=True,
        )
        await asyncio.sleep(1)
        (output, err) = p.communicate()
        output = output.decode()
        return json.loads(output)

    @staticmethod
    def __fetch(interval=1):
        p = subprocess.Popen(
            f"python3 memory_info.py {os.getpid()} {interval}",
            stdout=subprocess.PIPE,
            shell=True,
        )
        (output, err) = p.communicate()
        output = output.decode()
        return json.loads(output)

    @staticmethod
    async def full(interval=1):
        return await MemoryInfo.__coro_fetch(interval)

    @staticmethod
    async def cpu(interval=1):
        mem = await MemoryInfo.__coro_fetch(interval)
        return mem["PID"]["CPU"]

    @staticmethod
    def ram(interval=0):
        return MemoryInfo.__fetch(interval)["PID"]["RAM"]["RSS"]

    @staticmethod
    async def cpu_info(interval=1):
        mem = await MemoryInfo.__coro_fetch(interval)
        return {"global": mem["GLOBAL"]["CPU"], "bot": mem["PID"]["CPU"]}

    @staticmethod
    def global_cpu(interval=1):
        return MemoryInfo.__fetch(interval)["GLOBAL"]["CPU"]

    @staticmethod
    def global_ram(interval=0):
        return MemoryInfo.__fetch()["GLOBAL"]["RAM"]["USED"]

class TempList(list):
    def __init__(self, bot, keep_for: int = 10):
        self.bot = bot
        self.keep_for = keep_for
        super().__init__()

    async def remove_after(self, value):
        await asyncio.sleep(self.keep_for)
        with suppress(IndexError):
            super().remove(value)

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.bot.loop.create_task(
            self.remove_after(args[0])
        )


class CacheWriter:
    def __init__(self, cache, filepath):
        self.cache = cache
        self.filepath = filepath

    async def write(self, *args, **kwargs):
        await self.cache.write(self.filepath, *args, **kwargs)


class Cache:
    def __init__(self, bot):
        self.bot = bot
        self.data = {}  # Filepath: {"args": list, "kwargs": dict}
        self.dump_task.start()

    def __del__(self):
        self.dump_task.stop()

    @tasks.loop(minutes=15)
    async def dump_task(self):
        for filepath, data in list(self.data.items()):
            args = data["args"]
            kwargs = data["kwargs"]
            async with self.bot.open(filepath, "w+") as f:
                await f.write(*args, *kwargs)
            del self.data[filepath]
            self.bot.log.debug(f"Wrote {filepath} from cache")

    async def write(self, filepath, *args, **kwargs):
        self.data[filepath] = {
            "args": args,
            "kwargs": kwargs
        }


class TempConvo:
    def __init__(self, context):
        self.ctx = context
        self.sent = []

    def predicate(self, message):
        return message.author.id in [self.ctx.author.id, self.ctx.bot.user.id]

    async def __aenter__(self):
        return self

    async def __aexit__(self, _type, _tb, _exc):
        before = self.sent[len(self.sent) - 1]
        after = self.sent[0]
        msgs = await self.ctx.channel.history(before=before, after=after).flatten()
        await self.ctx.channel.delete_messages([
            before, after, *[
                msg for msg in msgs if self.predicate(msg)
            ]
        ])

    async def send(self, *args, **kwargs):
        msg = await self.ctx.send(*args, **kwargs)
        self.sent.append(msg)


def setup(bot):
    bot.add_cog(Utils(bot, Filter, MemoryInfo, Result))
