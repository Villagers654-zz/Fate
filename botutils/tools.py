
"""
Tools
~~~~~~

A collection of utility functions

Classes:
    TempConvo
    CooldownManager
    OperationLock
    Formatting

Methods:
    split
    cleanup_msg
    bytes2human
    extract_time
    get_seconds
    get_images
    get_avg_color
    total_seconds
    get_user_rewrite
    get_time
    get_role
    update_msg

Misc variables:
    operators
    formulas

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import re
from typing import Union
import asyncio
from datetime import timedelta
from time import time
import discord
from .emojis import arrow


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


class CooldownManager:
    def __init__(self, bot, limit, timeframe, raise_error=False):
        self.bot = bot
        self.limit = limit
        self.timeframe = timeframe
        self.raise_error = raise_error
        self.index = {}

    def check(self, _id) -> bool:
        now = int(time() / self.timeframe)
        if _id not in self.index:
            self.index[_id] = [now, 0]
        if self.index[_id][0] == now:
            self.index[_id][1] += 1
        else:
            self.index[_id] = [now, 0]
        if self.index[_id][1] >= self.limit:
            if self.raise_error:
                raise self.bot.ignored_exit
            return False
        return True

    def cleanup(self):
        del self.index
        self.index = {}


class OperationLock:
    bot = None
    def __init__(self, key):
        self.key = key

    def __enter__(self):
        if self.key in self.bot.operation_locks:
            raise self.bot.ignored_exit
        self.bot.operation_locks.append(self.key)

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.bot.operation_locks.remove(self.key)


class Formatting:
    def __init__(self, bot):
        self.bot = bot

    def format_dict(self, data: dict, emoji=None) -> str:
        if emoji is None:
            emoji = arrow() + " "
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

    async def dump_json(self, data):
        """Save json in a different thread to prevent freezing the loop"""
        return await self.bot.dump(data)

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


def split(text, amount=2000) -> list:
    return [text[i : i + amount] for i in range(0, len(text), amount)]


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


operators = {
    'seconds': 's',
    'minutes': 'm',
    'hours': 'h',
    'days': 'd',
    'weeks': 'w',
    'months': 'M',
    'years': 'y'
}

formulas = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
    'M': 2592000,
    'y': 31536000
}


def extract_time(string):
    string = string.replace(" ", "")[:20]
    for human_form, operator in operators.items():
        string = string.replace(human_form, operator)
        string = string.replace(human_form.rstrip('s'), operator)
    timers = re.findall("[0-9]*[smhdwMy]", string[:8])
    if not timers:
        return None
    timeframe = 0
    for timer in timers:
        operator = ''.join(c for c in timer if not c.isdigit())
        num = timer.replace(operator, '')
        if not num:
            continue
        num = int(num) * formulas[operator]
        timeframe += num
    return timeframe


def get_seconds(minutes=None, hours=None, days=None):
    if minutes:
        return minutes * 60
    if hours:
        return hours * 60 * 60
    if days:
        return days * 60 * 60 * 24
    return 0


async def get_images(ctx) -> list:
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


# def get_avg_color(url):
#     """Gets an image and returns the average color"""
#     if not url:
#         return fate
#     im = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
#     pixels = list(im.getdata())
#     r = g = b = c = 0
#     for pixel in pixels:
#         # brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
#         if pixel[3] > 64:
#             r += pixel[0]
#             g += pixel[1]
#             b += pixel[2]
#             c += 1
#     r = r / c
#     g = g / c
#     b = b / c
#     return eval("0x" + rgb2hex(round(r), round(g), round(b)).replace("#", ""))


def total_seconds(now, before):
    secs = str((now - before).total_seconds())
    return secs[: secs.find(".") + 2]


async def get_user_rewrite(ctx, target: str = None) -> Union[discord.User, discord.Member]:
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
            for role in roles[:5]:
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


async def update_msg(msg, new) -> discord.Message:
    if len(msg.content) + len(new) + 2 >= 2000:
        msg = await msg.channel.send("Uploading emoji(s)")
    await msg.edit(content=f"{msg.content}\n{new}")
    return msg



