# Bot utility functions

import asyncio
import json
from datetime import datetime, timedelta
import requests
from os.path import isfile
from io import BytesIO
import re
from typing import Union
from time import time
import os
import subprocess

from discord.ext import commands, tasks
import discord
from colormap import rgb2hex
from PIL import Image

from botutils.packages import resources, listeners, menus, files


class Utils(commands.Cog):
    def __init__(self, bot, _filter, memory_info, result):
        self.bot = bot

        self.colors = self.emotes = None
        self.verify_user = self.get_choice = self.configure = None
        self.listener = None
        self.tempdl = self.save_json = self.download = None

        self.packages = [
            "resources", "listeners", "menus", "files"
        ]
        for package in self.packages:
            eval(package).init(self)

        self.filter = _filter
        self.MemoryInfo = memory_info
        self.Result = result

    @staticmethod
    async def update_msg(msg, new) -> discord.Message:
        if len(msg.content) + len(new) + 2 >= 2000:
            msg = await msg.channel.send("Uploading emoji(s)")
        await msg.edit(content=f"{msg.content}\n{new}")
        return msg

    @staticmethod
    def split(text, amount=2000) -> list:
        return [text[i : i + amount] for i in range(0, len(text), amount)]

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
        config_path = bot.get_fp_for("userdata/config.json")

        if msg.author.id == bot.config["owner_id"]:
            return default_prefix

        last_updated, config = bot.prefix_cache
        if last_updated < time() - 5:
            async with bot.open(config_path, "r") as f:
                config = json.loads(await f.read())
            bot.prefix_cache = [time(), config]

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
        conf = Utils.get_config()  # type: dict
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
    def generate_rainbow_rgb(amount: int) -> list:
        fixed_colors = [
            (255, 0, 0),  # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (75, 0, 130),  # Dark Purple
            (148, 0, 211),  # Purple
        ]
        color_array = []
        for iteration, (r, g, b) in enumerate(fixed_colors):
            color_array.append((r, g, b))
            if len(fixed_colors) != iteration + 1:
                nr, ng, nb = fixed_colors[iteration + 1]
                divide_into = int(amount / len(fixed_colors)) + 2
                r_diff = (nr - r) / divide_into
                g_diff = (ng - g) / divide_into
                b_diff = (nb - b) / divide_into
                for i in range(divide_into):
                    r += r_diff
                    g += g_diff
                    b += b_diff
                    color_array.append((int(r), int(g), int(b)))
        return color_array

    def format_dict(self, data: dict, emoji=None) -> str:
        if emoji is None:
            emoji = self.emojis("arrow") + " "
        elif emoji is False:
            emoji = ""
        result = ""
        for k, v in data.items():
            if v:
                result += f"\n{emoji}**{k}:** {v}"
            else:
                result += f"\n{emoji}{k}"
        return result

    def add_field(self, embed, name: str, value: dict, inline=True):
        embed.add_field(name=f"◈ {name}", value=self.format_dict(value), inline=inline)

    def avg_color(self, url):
        """Gets an image and returns the average color"""
        if not url:
            return self.colors.fate()
        im = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
        pixels = list(im.getdata())
        r = g = b = c = 0
        for pixel in pixels:
            # brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
            if pixel[3] > 64:
                r += pixel[0]
                g += pixel[1]
                b += pixel[2]
                c += 1
        r = r / c
        g = g / c
        b = b / c
        return eval("0x" + rgb2hex(round(r), round(g), round(b)).replace("#", ""))

    @staticmethod
    def total_seconds(now, before):
        secs = str((now - before).total_seconds())
        return secs[: secs.find(".") + 2]

    @staticmethod
    def get_stats():
        if not isfile("./data/stats.json"):
            with open("./data/stats.json", "w") as f:
                json.dump({"commands": []}, f, ensure_ascii=False)
        with open("./data/stats.json", "r") as stats:
            return json.load(stats)

    @staticmethod
    def get_config():
        if not isfile("./data/userdata/config.json"):
            with open("./data/userdata/config.json", "w") as f:
                json.dump({}, f, ensure_ascii=False)
        with open("./data/userdata/config.json", "r") as f:
            return json.load(f)

    @staticmethod
    def default_cooldown():
        return [2, 5, commands.BucketType.user]

    @staticmethod
    def bytes2human(n):
        symbols = ("KB", "MB", "GB", "TB", "PB", "E", "Z", "Y")
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return "%.1f%s" % (value, s)
        return "%sB" % n

    @staticmethod
    def cleanup_msg(msg, content=None):
        if not content:
            content = msg
        if isinstance(msg, discord.Message):
            content = content if content else msg.content
            for mention in msg.role_mentions:
                content = content.replace(str(mention), mention.name)
        content = str(content).replace("@", "@ ")
        extensions = ["." + x for x in [c for c in list(content) if c != " "]]
        if len(content.split(" ")) > 1:
            content = content.split(" ")
        else:
            content = [content]
        if isinstance(content, list):
            targets = [c for c in content if any(x in c for x in extensions)]
            for target in targets:
                content[content.index(target)] = "**forbidden-link**"
        content = " ".join(content) if len(content) > 1 else content[0]
        return content

    @staticmethod
    def get_user(ctx, user: str = None):
        if not user:
            return ctx.author
        if str(user).isdigit():
            user = str(user)
            usr = None
            if ctx.guild:
                usr = ctx.guild.get_member(int(user))
            return usr if usr else ctx.bot.get_user(int(user))
        if user.startswith("<@"):
            for char in list(user):
                if char not in list("1234567890"):
                    user = user.replace(str(char), "")
            return ctx.guild.get_member(int(user))
        else:
            user = user.lower()
            for member in ctx.guild.members:
                if user == member.name.lower():
                    return member
            for member in ctx.guild.members:
                if user == member.display_name.lower():
                    return member
            for member in ctx.guild.members:
                if user in member.name.lower():
                    return member
            for member in ctx.guild.members:
                if user in member.display_name.lower():
                    return member
        return None

    @staticmethod
    async def get_user_rewrite(
        ctx, target: str = None
    ) -> Union[discord.User, discord.Member]:
        """ Grab a user by id, name, or username, and convert to Member if possible """
        if not target:
            user = ctx.author
        elif target.isdigit() or re.findall("<.@[0-9]*>", target):
            user_id = int("".join(c for c in target if c.isdigit()))
            user = await ctx.bot.fetch_user(user_id)
        elif ctx.guild is None:
            user = ctx.author
        else:
            for usr in ctx.bot.users:
                if str(usr) == target:
                    user = usr
                    break
            else:
                target = re.sub("#[0-9]{4}", "", target.lower())
                results = [
                    member
                    for member in ctx.guild.members
                    if (
                        target in member.display_name.lower()
                        if not member.nick
                        else target in member.name.lower()
                    )
                ]
                if len(results) == 1:
                    user = results[0]  # type: discord.Member
                elif len(results) > 1:
                    user = await ctx.bot.get_choice(ctx, *results, user=ctx.author)
                else:
                    user = ctx.author
        if ctx.guild is not None and not isinstance(user, discord.Member):
            if user.id in [m.id for m in ctx.guild.members]:
                user = ctx.guild.get_member(user.id)
        return user

    @staticmethod
    def get_time(seconds):
        result = ""
        if seconds < 60:
            return f"{seconds} seconds"
        total_time = str(timedelta(seconds=seconds))
        if "," in total_time:
            days = str(total_time).replace(" days,", "").split(" ")[0]
            total_time = total_time.replace(
                f'{days} day{"s" if int(days) > 1 else ""}, ', ""
            )
            result += f"{days} days"
        hours, minutes, seconds = total_time.split(":")
        hours = int(hours)
        minutes = int(minutes)
        if hours > 0:
            result += f'{", " if result else ""}{hours} hour{"s" if hours > 1 else ""}'
        if minutes > 0:
            result += f'{", and " if result else ""}{minutes} minute{"s" if minutes > 1 else ""}'
        return result

    @staticmethod
    async def get_role(ctx, name):
        if name.startswith("<@"):
            for char in list(name):
                if not char.isdigit():
                    name = name.replace(str(char), "")
            return ctx.guild.get_role(int(name))
        else:
            roles = []
            for role in ctx.guild.roles:
                if name.lower() == role.name.lower():
                    roles.append(role)
            if not roles:
                for role in ctx.guild.roles:
                    if name.lower() in role.name.lower():
                        roles.append(role)
            if roles:
                if len(roles) == 1:
                    return roles[0]
                index = 1
                role_list = ""
                for role in roles:
                    role_list += f"{index} : {role.mention}\n"
                    index += 1
                e = discord.Embed(color=ctx.bot.config["theme_color"], description=role_list)
                e.set_author(name="Multiple Roles Found")
                e.set_footer(text="Reply with the correct role number")
                embed = await ctx.send(embed=e)

                def pred(m):
                    return (
                        m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
                    )

                try:
                    msg = await ctx.bot.wait_for("message", check=pred, timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("Timeout error", delete_after=5)
                    await embed.delete()
                    return None
                else:
                    try:
                        role = int(msg.content)
                    except:
                        await ctx.send("Invalid response")
                        return None
                    if role > len(roles):
                        await ctx.send("Invalid response")
                        return None
                    await embed.delete()
                    await msg.delete()
                    return roles[role - 1]

    async def wait_for_msg(self, ctx, user=None):
        if not user:
            user = ctx.author

        def pred(m):
            return m.channel.id == ctx.channel.id and m.author.id == user.id

        try:
            msg = await self.bot.wait_for("message", check=pred, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Timeout error")
            return False
        else:
            return msg

    @staticmethod
    def extract_timer(string):
        timers = re.findall("[0-9]+[smhd]", string)
        if not timers:
            return None
        time_to_sleep = [0, []]
        for timer in timers:
            raw = "".join(x for x in list(timer) if x.isdigit())
            if "d" in timer:
                time = int(timer.replace("d", "")) * 60 * 60 * 24
                _repr = "day"
            elif "h" in timer:
                time = int(timer.replace("h", "")) * 60 * 60
                _repr = "hour"
            elif "m" in timer:
                time = int(timer.replace("m", "")) * 60
                _repr = "minute"
            else:  # 's' in timer
                time = int(timer.replace("s", ""))
                _repr = "second"
            time_to_sleep[0] += time
            time_to_sleep[1].append(f"{raw} {_repr if raw == '1' else _repr + 's'}")
        return time_to_sleep

    @staticmethod
    def get_seconds(minutes=None, hours=None, days=None):
        if minutes:
            return minutes * 60
        if hours:
            return hours * 60 * 60
        if days:
            return days * 60 * 60 * 24
        return 0

    async def get_images(self, ctx) -> list:
        """ Gets the latest image(s) in the channel """

        def scrape(msg: discord.Message) -> list:
            """ Thoroughly checks a msg for images """
            image_links = []
            if msg.attachments:
                for attachment in msg.attachments:
                    image_links.append(attachment.url)
            for embed in msg.embeds:
                if "image" in embed.to_dict():
                    image_links.append(embed.to_dict()["image"]["url"])
            args = msg.content.split()
            if not args:
                args = [msg.content]
            for arg in args:
                if "https://cdn.discordapp.com/attachments/" in arg:
                    image_links.append(arg)
            return image_links

        image_links = scrape(ctx.message)
        if image_links:
            return image_links
        async for msg in ctx.channel.history(limit=10):
            image_links = scrape(msg)
            if image_links:
                return image_links
        await ctx.send("No images found in the last 10 msgs")
        return image_links




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
        if value in super().__iter__():
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





def setup(bot):
    bot.add_cog(Utils(bot, Filter, MemoryInfo, Result))
