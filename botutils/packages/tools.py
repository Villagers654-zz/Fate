import re
from io import BytesIO
import requests
from PIL import Image
from typing import Union
import asyncio
from datetime import timedelta
import json
from colormap import rgb2hex
import discord


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


def get_avg_color(self, url):
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


def total_seconds(now, before):
    secs = str((now - before).total_seconds())
    return secs[: secs.find(".") + 2]


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


async def update_msg(msg, new) -> discord.Message:
    if len(msg.content) + len(new) + 2 >= 2000:
        msg = await msg.channel.send("Uploading emoji(s)")
    await msg.edit(content=f"{msg.content}\n{new}")
    return msg


class Formatting:
    def __init__(self, bot):
        self.bot = bot

    def format_dict(self, data: dict, emoji=None) -> str:
        if emoji is None:
            emoji = self.bot.utils.emotes.arrow + " "
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
        dump = lambda dump: json.dumps(data)
        return await self.bot.loop.run_in_executor(None, dump)

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


def init(cls):
    """Add functions into the main utils class"""
    cls.split = split
    cls.cleanup_msg = cleanup_msg
    cls.bytes2human = bytes2human
    cls.extract_timer = extract_timer
    cls.get_seconds = get_seconds
    cls.get_images = get_images
    cls.total_seconds = total_seconds
    cls.get_user = get_user
    cls.get_user_rewrite = get_user_rewrite
    cls.get_role = get_role
    cls.get_time = get_time
    cls.update_msg = update_msg

    formatting = Formatting(cls.bot)
    cls.format_dict = formatting.format_dict
    cls.add_field = formatting.add_field
    cls.dump_json = formatting.dump_json
    OperationLock.bot = cls.bot
    cls.operation_lock = OperationLock

