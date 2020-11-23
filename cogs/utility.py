from datetime import datetime, timedelta
import aiohttp
import asyncio
import random
from io import BytesIO
import json
import os
import requests
import re
from typing import Optional, Union
from os import path
from time import time
import aiofiles
import platform
from contextlib import suppress

import discord
from discord import User, Role, TextChannel, Member
from PIL import Image
from colormap import rgb2hex
import psutil
from discord.ext import commands

from utils import colors, config
from cogs.utils import Utils as utils


class SatisfiableChannel(commands.Converter):
    async def convert(self, ctx, argument):
        converter = commands.TextChannelConverter()
        channel = await converter.convert(ctx, argument)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send(f'"{argument}" is not a valid channel')
            return False
        perms = [
            "read_messages",
            "read_message_history",
            "send_messages",
            "manage_webhooks",
        ]
        for perm in perms:
            if not eval(f"channel.permissions_for(ctx.guild.me).{perm}"):
                await ctx.send(f"I'm missing {perm} permissions in that channel")
                return False
        return channel


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.find = {}
        self.afk = {}
        self.timer_path = "./data/userdata/timers.json"
        self.timers = {}
        if os.path.isfile(self.timer_path):
            with open(self.timer_path, "r") as f:
                self.timers = json.load(f)
        self.path = "./data/info.json"
        self.guild_logs = {}
        self.user_logs = {}
        self.misc_logs = {"invites": {}}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                try:
                    dat = json.load(f)  # type: dict
                except json.JSONDecodeError:
                    bot.log(
                        "Utility is retreating to a backup file. The previous is corrupt",
                        "CRITICAL",
                    )
                    with open(self.path + ".old") as old:
                        dat = json.load(old)
                self.guild_logs = dat["guild_logs"]
                self.user_logs = dat["user_logs"]
                self.misc_logs = dat["misc_logs"]
        else:
            bot.log(
                "info.json is missing, and cogs.Utility was loaded without any data",
                "CRITICAL",
            )
        self.cache = {}
        if "info" not in bot.tasks:
            bot.tasks["info"] = bot.loop.create_task(self.save_data_task())
        else:
            bot.tasks["info"].cancel()
            bot.tasks["info"] = bot.loop.create_task(self.save_data_task())
        if "timers" not in bot.tasks:
            bot.tasks["timers"] = {}

    async def save_timers(self):
        await self.bot.save_json(self.timer_path, self.timers)

    @staticmethod
    def avg_color(url):
        """Gets an image and returns the average color"""
        if not url:
            return colors.fate()
        im = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
        pixels = list(im.getdata())
        r = g = b = c = 0
        for pixel in pixels:
            brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
            if pixel[3] > 64 and brightness > 80:
                r += pixel[0]
                g += pixel[1]
                b += pixel[2]
                c += 1
        r = r / c
        g = g / c
        b = b / c
        return eval("0x" + rgb2hex(round(r), round(g), round(b)).replace("#", ""))

    @staticmethod
    async def wait_for_dismissal(ctx, msg):
        def pred(m):
            return m.channel.id == ctx.channel.id and m.content.lower().startswith("k")

        try:
            reply = await ctx.bot.wait_for("message", check=pred, timeout=25)
        except asyncio.TimeoutError:
            pass
        else:
            await asyncio.sleep(0.21)
            await ctx.message.delete()
            await asyncio.sleep(0.21)
            await msg.delete()
            await asyncio.sleep(0.21)
            await reply.delete()

    # def cog_unload(self):
    # 	self.bot.loop.create_task(self.save_data())

    async def save_data_task(self):
        self.bot.log.debug("Starting save task for info.json")
        while True:
            await asyncio.sleep(60 * 5)
            async with aiofiles.open(self.path + ".temp", "w+") as f:
                await f.write(
                    json.dumps(
                        {
                            "guild_logs": self.guild_logs,
                            "user_logs": self.user_logs,
                            "misc_logs": self.misc_logs,
                        },
                        ensure_ascii=False,
                    )
                )
            if not path.exists(self.path):
                self.bot.log.critical(
                    "info.json was missing, and is being replaced with what's in memory"
                )
            if path.exists(self.path + ".old"):
                os.remove(self.path + ".old")
            os.rename(self.path, self.path + ".old")
            os.rename(self.path + ".temp", self.path)
            self.bot.log.debug("Saved info.json successfully")

    def setup_if_not_exists(self, *args):
        for arg in args:
            if isinstance(arg, discord.Guild):
                guild_id = str(arg.id)
                if guild_id not in self.guild_logs:
                    self.guild_logs[guild_id] = {"joins": [], "names": []}
            if isinstance(arg, (discord.User, discord.Member)):
                user_id = str(arg.id)
                if user_id not in self.user_logs:
                    self.user_logs[user_id] = {
                        "names": {str(arg): time()},
                        "last_msg": None,
                        "last_online": None,
                        "duration": None,
                    }

    @commands.command(name="delete-data")
    async def delete_data(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.user_logs:
            return await ctx.send("You have no user data saved")
        del self.user_logs[user_id]
        await ctx.send("Removed your data from .info")

    def cleanup_users(self):
        for user_id, data in self.user_logs.items():
            for name, changed_at in data["names"].items():
                if changed_at > time() - 60 * 60 * 24 * 60:
                    del self.user_logs[user_id]["names"][name]

    @commands.command(name="info", aliases=["xinfo"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def info(self, ctx, *, target: Union[User, Role, TextChannel, str] = None):
        bot_has_audit_access = (
            ctx.guild.me.guild_permissions.view_audit_log
        )  # type: bool
        if isinstance(target, (User, Member)):
            user = target  # type: discord.User
            if ctx.author.id == 611108193275478018 and user.id == 264838866480005122:
                await self.bot.get_channel(541520201926311986).send(
                    "<@264838866480005122> eppy tried using .info on yu"
                )
                return await ctx.send(
                    "https://cdn.discordapp.com/attachments/633866664252801024/725905903928213584/Screenshot_20181018-003209_Gallery.jpg"
                )
            if ctx.guild:
                tmp = ctx.guild.get_member(user.id)
                if isinstance(tmp, discord.Member):
                    user = tmp  # type: discord.Member
            self.setup_if_not_exists(user)

            e = discord.Embed(color=colors.fate())
            e.set_author(
                name="Here's what I got on them..", icon_url=self.bot.user.avatar_url
            )
            e.set_thumbnail(url=user.avatar_url)
            e.description = ""
            emojis = self.bot.utils.emojis
            user_id = str(user.id)

            # User Information
            user_info = {
                "Profile": f"{user.mention}",
                "ID": user.id,
                "Created at": user.created_at.strftime("%m/%d/%Y %I%p"),
                "Shared Servers": str(
                    len([s for s in self.bot.guilds if user in s.members])
                )
            }
            nicks = []
            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.id == user.id:
                        if member.display_name != user.display_name:
                            nicks = list(set(list([member.display_name, *nicks])))
            if nicks:
                user_info["Nicks"] = ", ".join(nicks[:5])

            # Member Information
            member_info = {}
            if isinstance(user, discord.Member):
                user_info[
                    "Profile"
                ] = f"{user.mention} {self.bot.utils.emojis(user.status)}"

                if user.name != user.display_name:
                    member_info["Display Name"] = user.display_name
                if user.activity:
                    member_info["Activity"] = user.activity.name
                member_info["Top Role"] = user.top_role.mention

                text = len(
                    [
                        c
                        for c in ctx.guild.text_channels
                        if c.permissions_for(user).read_messages
                    ]
                )
                voice = len(
                    [
                        c
                        for c in ctx.guild.voice_channels
                        if c.permissions_for(user).read_messages
                    ]
                )

                notable = [
                    "view_audit_log",
                    "manage_roles",
                    "manage_channels",
                    "manage_emojis",
                    "kick_members",
                    "ban_members",
                    "manage_messages",
                    "mention_everyone",
                ]
                member_info[
                    "Access"
                ] = f"{emojis('text_channel')} {text} {emojis('voice_channel')} {voice}"
                if any(k in notable and v for k, v in list(user.guild_permissions)):
                    perms = [k for k, v in user.guild_permissions if k in notable and v]
                    perms = (
                        ["administrator"]
                        if user.guild_permissions.administrator
                        else perms
                    )
                    member_info["Notable Perms"] = f"`{', '.join(perms)}`"

                # Bot Information
                if user.bot:  # search the audit log to see who invited the bot
                    inviter = "Unknown"
                    if bot_has_audit_access:
                        async for entry in ctx.guild.audit_logs(
                            limit=250, action=discord.AuditLogAction.bot_add
                        ):
                            if entry.target and entry.target.id == user.id:
                                inviter = entry.user
                                break
                    user_info["Inviter"] = inviter

            # Activity Information
            activity_info = {}
            mutual = [
                g for g in self.bot.guilds if user.id in [m.id for m in g.members]
            ]
            if mutual:
                user = mutual[0].get_member(user.id)
                if user.status is discord.Status.offline:
                    if self.user_logs[user_id]["last_online"]:
                        seconds = round(time() - self.user_logs[user_id]["last_online"])
                        activity_info[
                            "Last Online"
                        ] = f"{self.bot.utils.get_time(seconds)} ago"
                        seconds = round(self.user_logs[user_id]["duration"])
                        activity_info[
                            "Online For"
                        ] = f"{self.bot.utils.get_time(seconds)}"
                    else:
                        activity_info["Last Online"] = "Unknown"
                if self.user_logs[user_id]["last_msg"]:
                    seconds = round(time() - self.user_logs[user_id]["last_msg"])
                    activity_info[
                        "Last Msg"
                    ] = f"{self.bot.utils.get_time(seconds)} ago"
                else:
                    activity_info["Last Msg"] = "Unknown"

            if isinstance(user, discord.Member):
                if user.status is discord.Status.online:
                    if user.is_on_mobile():
                        activity_info["Active on Mobile 📱"] = None
                    else:
                        activity_info["Active on PC 🖥"] = None

            # username history - broken (maybe)
            names = [
                name
                for name, name_time in self.user_logs[user_id]["names"].items()
                if name_time > time() - 60 * 60 * 24 * 60 and name != str(user)
            ]
            if names:
                user_info["Usernames"] = ",".join(names)

            e.description += (
                f"◈ User Information{self.bot.utils.format_dict(user_info)}\n\n"
            )
            if member_info:
                e.description += (
                    f"◈ Member Information{self.bot.utils.format_dict(member_info)}\n\n"
                )
            if activity_info:
                e.description += f"◈ Activity Information{self.bot.utils.format_dict(activity_info)}\n\n"
            # e.set_footer(text="🗑 | Erase User Data")
            await ctx.send(embed=e)

        elif isinstance(target, TextChannel):
            e = discord.Embed(color=colors.fate())
            e.set_author(
                name="Alright, here's what I got..", icon_url=self.bot.user.avatar_url
            )

            channel = target  # type: discord.TextChannel
            channel_info = {
                "Name": channel.name,
                "ID": channel.id,
                "Members": str(len(channel.members)),
            }

            if channel.category:
                channel_info["Category"] = f"`{channel.category}`"
            if channel.is_nsfw():
                channel_info["Marked as NSFW"] = None
            if channel.is_news():
                channel_info["Is the servers news channel"] = None
            channel_info["Created at"] = channel.created_at.strftime("%m/%d/%Y %I%p")

            e.add_field(
                name="◈ Channel Information",
                value=self.bot.utils.format_dict(channel_info),
                inline=False,
            )
            e.set_footer(text="🖥 Topic | ♻ History")

            msg = await ctx.send(embed=e)
            emojis = ["🖥", "♻"]
            for emoji in emojis:
                await msg.add_reaction(emoji)

            def predicate(r, u):
                return str(r.emoji) in emojis and r.message.id == msg.id and not u.bot

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", check=predicate, timeout=60
                    )
                except asyncio.TimeoutError:
                    if (
                        ctx.channel.permissions_for(ctx.guild.me).manage_messages
                        and msg
                    ):
                        await msg.clear_reactions()
                    return

                if str(reaction.emoji) == "🖥":  # Requested topic information
                    topic = channel.topic
                    if not topic:
                        topic = "None set."
                    for group in self.bot.utils.split(topic, 1024):
                        e.add_field(name="◈ Channel Topic", value=group, inline=False)
                    emojis.remove("🖥")
                elif str(reaction.emoji) == "♻":  # Requested channel history
                    if not bot_has_audit_access:
                        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                            await msg.remove_reaction(reaction, user)
                        err = "Missing view_audit_log permission(s)"
                        if any(field.value == err for field in e.fields):
                            continue
                        e.add_field(name="◈ Channel History", value=err, inline=False)
                    else:
                        e.set_footer()
                        history = {}
                        e.add_field(
                            name="◈ Channel History", value="Fetching..", inline=False
                        )
                        await msg.edit(embed=e)

                        action = discord.AuditLogAction.channel_create
                        async for entry in ctx.guild.audit_logs(
                            limit=500, action=action
                        ):
                            if channel.id == entry.target.id:
                                history["Creator"] = entry.user
                                break

                        if channel.permissions_for(ctx.guild.me).read_messages:
                            async for m in channel.history(limit=1):
                                seconds = (
                                    datetime.utcnow() - m.created_at
                                ).total_seconds()
                                total_time = self.bot.utils.get_time(round(seconds))
                                history["Last Message"] = f"{total_time} ago\n"

                        action = discord.AuditLogAction.channel_update
                        async for entry in ctx.guild.audit_logs(
                            limit=750, action=action
                        ):
                            if channel.id == entry.target.id:
                                if not hasattr(entry.before, "name") or not hasattr(
                                    entry.after, "name"
                                ):
                                    continue
                                if entry.before.name != entry.after.name:
                                    minute = str(entry.created_at.minute)
                                    if len(minute) == 1:
                                        minute = "0" + minute
                                    when = entry.created_at.strftime(
                                        f"%m/%d/%Y %I:{minute}%p"
                                    )
                                    history[f"**Name Changed on {when}**"] = None
                                    history[
                                        f"**Old Name:** `{entry.before.name}`\n"
                                    ] = None

                        if not history:
                            history["None Found"] = None
                        e.set_field_at(
                            index=len(e.fields) - 1,
                            name="◈ Channel History",
                            value=self.bot.utils.format_dict(
                                dict(list(history.items())[:6])
                            ),
                            inline=False,
                        )
                        emojis.remove("♻")
                await msg.edit(embed=e)

        elif "discord.gg" in ctx.message.content:
            e = discord.Embed(color=colors.fate())
            e.set_author(
                name="Alright, here's what I got..", icon_url=self.bot.user.avatar_url
            )
            inv = [arg for arg in ctx.message.content.split() if "discord.gg" in arg][0]
            code = discord.utils.resolve_invite(inv)
            dat = None
            try:
                invite = await self.bot.fetch_invite(code)
            except (discord.errors.NotFound, discord.errors.Forbidden):
                if code in self.misc_logs["invites"]:
                    dat = self.misc_logs["invites"][code]
                    e.set_footer(text="⚠ From History ⚠")
            else:
                dat = self.collect_invite_info(invite, invite.guild)
            if not dat:
                return await ctx.send("Invite not found")

            logged = None
            if code in self.misc_logs["invites"]:
                logged = self.misc_logs["invites"][code]

            core = {
                "Guild": dat["guild"]["name"],
                "GuildID": dat["guild"]["id"],
                "Channel": dat["channel"]["name"],
                "ChannelID": dat["channel"]["id"],
            }

            inviters = []
            if logged:
                for user_id in logged["inviters"]:
                    user = self.bot.get_user(user_id)
                    if not user:
                        user = await self.bot.fetch_user(user_id)
                    inviters.append(str(user))

            e.add_field(
                name="◈ Invite Information",
                value=self.bot.utils.format_dict(core),
                inline=False,
            )
            if inviters:
                e.add_field(
                    name="◈ Inviters", value=", ".join(inviters[:16]), inline=False
                )
            await ctx.send(embed=e)

        elif isinstance(target, Role):
            e = discord.Embed(color=colors.fate())
            e.set_author(
                name="Alright, here's what I got..", icon_url=self.bot.user.avatar_url
            )
            role = target  # type: discord.Role

            core = {
                "Name": role.name,
                "Mention": role.mention,
                "ID": role.id,
                "Members": len(role.members) if role.members else "None",
                "Created at": role.created_at.strftime("%m/%d/%Y %I%p"),
            }

            extra = {
                "Mentionable": str(role.mentionable),
                "HEX Color": role.color,
                "RGB Color": role.colour.to_rgb(),
            }
            if role.hoist:
                extra["**Shows Above Other Roles**"] = None
            if role.managed:
                extra["**And Is An Integrated Role**"] = None

            e.add_field(
                name="◈ Role Information",
                value=self.bot.utils.format_dict(core),
                inline=False,
            )
            e.add_field(
                name="◈ Extra", value=self.bot.utils.format_dict(extra), inline=False
            )
            e.set_footer(text="React With ♻ For History")

            msg = await ctx.send(embed=e)
            emojis = ["♻"]

            for emoji in emojis:
                await msg.add_reaction(emoji)

            def predicate(r, u):
                return str(r.emoji) in emojis and r.message.id == msg.id and not u.bot

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", check=predicate, timeout=60
                    )
                except asyncio.TimeoutError:
                    if (
                        ctx.channel.permissions_for(ctx.guild.me).manage_messages
                        and msg
                    ):
                        await msg.clear_reactions()
                    return
                if not bot_has_audit_access:
                    if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                        await msg.remove_reaction(reaction, user)
                    err = "Missing view_audit_log permission(s)"
                    if any(field.value == err for field in e.fields):
                        continue
                    e.add_field(name="◈ Role History", value=err, inline=False)
                else:
                    e.set_footer()
                    history = {}
                    e.add_field(name="◈ Role History", value="Fetching..", inline=False)
                    await msg.edit(embed=e)

                    action = discord.AuditLogAction.role_create
                    async for entry in ctx.guild.audit_logs(limit=500, action=action):
                        if role.id == entry.target.id:
                            history["Creator"] = f"{entry.user}\n"
                            break

                    action = discord.AuditLogAction.role_update
                    async for entry in ctx.guild.audit_logs(limit=500, action=action):
                        if role.id == entry.target.id and hasattr(entry.after, "name"):
                            minute = str(entry.created_at.minute)
                            if len(minute) == 1:
                                minute = "0" + minute
                            when = datetime.date(entry.created_at).strftime(
                                f"%m/%d/%Y %I:{minute}%p"
                            )
                            if not hasattr(entry.before, "name"):
                                if entry.before.name != role.name:
                                    history[f"**Name Changed on {when}**"] = None
                                    history[f"**Changed to:** `{entry.before.name}`\n"] = None
                            elif entry.before.name != entry.after.name:
                                history[f"**Name Changed on {when}**"] = None
                                history[f"**Old Name:** `{entry.before.name}`\n"] = None

                    if not history:
                        history["None Found"] = None
                    e.set_field_at(
                        index=len(e.fields) - 1,
                        name="◈ Role History",
                        value=self.bot.utils.format_dict(
                            dict(list(history.items())[:6])
                        ),
                        inline=False,
                    )
                    emojis.remove("♻")
                    return await msg.edit(embed=e)
                await msg.edit(embed=e)

        else:
            options = ["Bot Info", "User Info", "Server Info", "Channel Info"]
            choice = await self.bot.get_choice(ctx, *options, user=ctx.author)
            if not choice:
                return
            if choice == "User Info":
                return await ctx.command.__call__(ctx, target=ctx.author)
            elif choice == "Server Info":
                return await self.bot.get_command("sinfo").__call__(ctx)
            elif choice == "Channel Info":
                return await ctx.command.__call__(ctx, target=ctx.channel)

            e = discord.Embed()
            e.set_author(
                name="Collecting Information..",
                icon_url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif",
            )
            msg = await ctx.send(embed=e)
            guilds = len(list(self.bot.guilds))
            users = len(list(self.bot.users))
            bot_pid = psutil.Process(os.getpid())
            e = discord.Embed(color=colors.fate())
            e.set_author(
                name="Fate Bot: Core Info",
                icon_url=self.bot.get_user(config.owner_id()).avatar_url,
            )
            stats = self.bot.utils.get_stats()  # type: dict
            commands = 0
            lines = 0
            for command_date in stats["commands"]:
                date = datetime.strptime(command_date, "%Y-%m-%d %H:%M:%S.%f")
                if (datetime.now() - date).days < 7:
                    commands += 1
                else:
                    stats["commands"].remove(command_date)
            async with self.bot.open("./data/stats.json", "w") as f:
                await f.write(json.dumps(stats))
            async with self.bot.open("fate.py", "r") as f:
                lines += len(await f.readlines())
            for file in os.listdir("cogs"):
                if file.endswith(".py"):
                    async with self.bot.open(f"./cogs/{file}", "r") as f:
                        lines += len(await f.readlines())
            e.description = f"Commands Used This Week: {commands}" \
                            f"\nLines of code: {lines}"
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.add_field(
                name="◈ Summary ◈",
                value="Fate is a ~~multipurpose~~ hybrid bot created for fun",
                inline=False,
            )
            e.add_field(
                name="◈ Statistics ◈",
                value=f"**Commands:** [{len(self.bot.commands)}]"
                      f"\n**Modules:** [{len(self.bot.extensions)}]"
                      f"\n**Servers:** [{guilds}]"
                      f"\n**Users:** [{users}]",
            )
            e.add_field(
                name="◈ Credits ◈",
                value="\n• **Cortex** ~ `teacher of many things..`"
                      "\n• **Discord.py** ~ `existing for me to use`"
                      "\n• **Luck** ~ `owner & main developer`"
                      "\n• **Opal, Koro, Vco** ~ `code management`"
            )

            def get_info() -> str:
                disk = psutil.disk_usage('/')
                ram = psutil.virtual_memory()
                freq = psutil.cpu_freq()
                cur = str(round(freq.current))

                if freq.current < 1000:
                    cur = f"{cur}GHz"
                else:
                    cur = f"{cur[0]}.{cur[1]}GHz"
                max = str(round(freq.max))
                max = f"{max[0]}.{max[1]}GHz"
                p = self.bot.utils
                c_temp = round(psutil.sensors_temperatures(fahrenheit=False)['coretemp'][0].current)
                f_temp = round(psutil.sensors_temperatures(fahrenheit=True)['coretemp'][0].current)
                value = f"**Storage (HDD)**: {p.bytes2human(disk.used)}/{p.bytes2human(disk.total)} - ({round(disk.percent)}%)\n" \
                        f"**RAM (DDR4)**: {p.bytes2human(ram.used)}/{p.bytes2human(ram.total)} - ({round(ram.percent)}%)\n" \
                        f"**CPU i9-10900K:** {round(psutil.cpu_percent())}% @{cur}/{max}\n" \
                        f"**CPU Temp:** {c_temp}°C {f_temp}°F\n" \
                        f"**Bot Usage:** **RAM:** {p.bytes2human(bot_pid.memory_full_info().rss)} **CPU:** {round(bot_pid.cpu_percent())}%"
                return value

            e.add_field(
                name="◈ Memory ◈",
                value=await self.bot.loop.run_in_executor(None, get_info),
                inline=False,
            )

            async with self.bot.open("./data/uptime.json", "r") as f:
                uptime_data = json.loads(await f.read())
            uptime_data = [
                datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
                for date_string in uptime_data
            ]

            # timespan = (uptime_data[len(uptime_data) - 1] - uptime_data[0]).seconds
            downtime = 0
            for iteration, date in enumerate(uptime_data):
                if iteration != len(uptime_data) - 1:
                    diff = (uptime_data[iteration + 1] - date).seconds
                    if diff > 60:
                        downtime += diff
                        continue

            if downtime == 0:
                downtime = 1
            # percentage = round((round(timespan - downtime) / round(timespan)) * 100)
            online_for = datetime.now() - self.bot.start_time
            e.add_field(
                name="◈ Uptime ◈",
                value=f"Online for {utils.get_time(round(online_for.total_seconds()))}\n",
                      # f"With {percentage}% uptime in the last 7 days\n",
                inline=False,
            )
            e.set_footer(
                text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}",
                icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png",
            )
            await msg.edit(embed=e)
            return await self.wait_for_dismissal(ctx, msg)

    def collect_invite_info(self, invite, guild=None):
        if not guild:
            guild = invite.guild
            if not isinstance(guild, (discord.Guild, discord.PartialInviteGuild)):
                tmp = self.bot.get_guild(guild.id)
                if isinstance(tmp, discord.Guild):
                    guild = tmp
        guild_name = "Unknown"
        if isinstance(guild, (discord.Guild, discord.PartialInviteGuild)):
            guild_name = guild.name
        invite_info = {"deleted": False, "guild": {"name": guild_name, "id": guild.id}}
        if invite.inviter:
            invite_info["inviter"] = invite.inviter.id
        else:
            invite_info["inviter"] = None
        invite_info["member_count"] = invite.approximate_member_count
        invite_info["online_count"] = invite.approximate_presence_count
        invite_info["channel"] = {"name": None, "id": invite.channel.id}
        if isinstance(
            invite.channel,
            (discord.TextChannel, discord.VoiceChannel, discord.PartialInviteChannel),
        ):
            invite_info["channel"]["name"] = invite.channel.name
        invite_info["temporary"] = invite.temporary
        invite_info["created_at"] = time()
        invite_info["uses"] = invite.uses
        invite_info["max_uses"] = invite.max_uses
        if "inviters" not in invite_info:
            invite_info["inviters"] = []
        return invite_info

    @commands.Cog.listener()
    async def on_message(self, msg):
        # AFK Command
        if msg.author.bot:
            return
        user_id = str(msg.author.id)
        if user_id in self.afk:
            del self.afk[user_id]
            await msg.channel.send("removed your afk", delete_after=3)
        else:
            for user in msg.mentions:
                user_id = str(user.id)
                if user_id in self.afk:
                    replies = ["shh", "shush", "shush child", "nO"]
                    choice = random.choice(replies)
                    await msg.channel.send(f"{choice} he's {self.afk[user_id]}")

        # Keep track of their last message time
        self.setup_if_not_exists(msg.author)
        await asyncio.sleep(1)  # avoid getting in the way of .info @user
        self.user_logs[str(msg.author.id)]["last_msg"] = time()
        # Check for invites and log their current state
        if "discord.gg" in msg.content:
            invites = re.findall("discord.gg/.{4,8}", msg.content)
            if invites:
                for invite in invites:
                    code = discord.utils.resolve_invite(invite)
                    try:
                        invite = await self.bot.fetch_invite(code)
                        invite_info = self.collect_invite_info(invite)
                        if invite.code not in self.misc_logs["invites"]:
                            self.misc_logs["invites"][invite.code] = invite_info
                        for key, value in invite_info.items():
                            try:
                                if key not in self.misc_logs["invites"][invite.code]:
                                    self.misc_logs["invites"][invite.code][key] = value
                                elif (
                                    value != self.misc_logs["invites"][invite.code][key]
                                    and value is not None
                                ):
                                    self.misc_logs["invites"][invite.code][key] = value
                            except KeyError:
                                return
                        if (
                            msg.author.id
                            not in self.misc_logs["invites"][invite.code]["inviters"]
                        ):
                            self.misc_logs["invites"][invite.code]["inviters"].append(
                                msg.author.id
                            )
                    except discord.errors.NotFound:
                        pass
                    except discord.errors.HTTPException:
                        pass

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        user_id = str(before.id)
        old_name = str(before)
        new_name = str(after)
        if old_name != new_name:
            self.setup_if_not_exists(before)
            if new_name not in self.user_logs[user_id]:
                self.user_logs[user_id][new_name] = time()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status != after.status:
            user_id = str(before.id)
            self.setup_if_not_exists(before)
            status = discord.Status
            if user_id not in self.cache and after.status != status.offline:
                self.cache[user_id] = time()
            elif before.status == status.offline and after.status != status.online:
                self.cache[user_id] = time()
            if before.status != status.offline and after.status == status.offline:
                if user_id not in self.cache:
                    return  # Prevents the code below from repeating
                self.user_logs[user_id]["last_online"] = self.cache[user_id]
                self.user_logs[user_id]["duration"] = time() - self.cache[user_id]
                del self.cache[user_id]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_id = str(guild.id)
        self.setup_if_not_exists(guild)
        self.guild_logs[guild_id]["joins"].append([member.id, time()])

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        if not member.bot:
            self.setup_if_not_exists(member.guild)
            user_id = str(member.id)
            if user_id in self.guild_logs["joins"]:
                del self.guild_logs["joins"][user_id]

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.code not in self.misc_logs["invites"]:
            guild = self.bot.get_guild(invite.guild.id)
            try:
                inv = await self.bot.fetch_invite(invite.code, with_counts=True)
                invite = inv
            except discord.errors.HTTPException:
                pass
            self.misc_logs["invites"][invite.code] = self.collect_invite_info(
                invite, guild
            )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.code in self.misc_logs["invites"]:
            self.misc_logs["invites"][invite.code]["deleted"] = True

    @commands.command(name="serverinfo", aliases=["sinfo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def serverinfo(self, ctx):
        try:
            e = discord.Embed(color=self.avg_color(ctx.guild.icon_url))
        except ZeroDivisionError:
            e = discord.Embed(color=colors.fate())
        e.description = f"id: {ctx.guild.id}\nOwner: {ctx.guild.owner}"
        e.set_author(name=f"{ctx.guild.name}:", icon_url=ctx.guild.owner.avatar_url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        main = (
            f"• AFK Timeout [`{ctx.guild.afk_timeout}`]\n"
            f"• Region [`{ctx.guild.region}`]\n"
            f"• Members [`{ctx.guild.member_count}`]"
        )
        e.add_field(name="◈ Main ◈", value=main, inline=False)
        security = (
            f"• Explicit Content Filter: [`{ctx.guild.explicit_content_filter}`]\n"
            f"• Verification Level: [`{ctx.guild.verification_level}`]\n"
            f"• 2FA Level: [`{ctx.guild.mfa_level}`]"
        )
        e.add_field(name="◈ Security ◈", value=security, inline=False)
        if ctx.guild.premium_tier:
            perks = (
                f"• Boost Level [`{ctx.guild.premium_tier}`]\n"
                f"• Total Boosts [`{ctx.guild.premium_subscription_count}`]\n"
                f"• Max Emoji's [`{ctx.guild.emoji_limit}`]\n"
                f'• Max Bitrate [`{utils.bytes2human(ctx.guild.bitrate_limit).replace(".0", "")}`]\n'
                f'• Max Filesize [`{utils.bytes2human(ctx.guild.filesize_limit).replace(".0", "")}`]'
            )
            e.add_field(name="◈ Perks ◈", value=perks, inline=False)
        created = datetime.date(ctx.guild.created_at)
        e.add_field(
            name="◈ Created ◈", value=created.strftime("%m/%d/%Y"), inline=False
        )
        await ctx.send(embed=e)

    @commands.command(name="servericon", aliases=["icon"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def servericon(self, ctx):
        e = discord.Embed(color=0x80B0FF)
        e.set_image(url=ctx.guild.icon_url)
        await ctx.send(embed=e)

    @commands.command(name="makepoll", aliases=["mp"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.has_permissions(add_reactions=True)
    @commands.bot_has_permissions(add_reactions=True)
    async def makepoll(self, ctx):
        async for msg in ctx.channel.history(limit=2):
            if msg.id != ctx.message.id:
                await msg.add_reaction(":approve:506020668241084416")
                await msg.add_reaction(":unapprove:506020690584010772")
                return await ctx.message.delete()

    @commands.command(name="members", aliases=["membercount"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def members(self, ctx, *, role=None):
        if role:  # returns a list of members that have the role
            if ctx.message.role_mentions:
                role = ctx.message.role_mentions[0]
            else:
                role = await utils.get_role(ctx, role)
                if not isinstance(role, discord.Role):
                    return
            if role.id == ctx.guild.default_role.id:
                return await ctx.send("biTcH nO")
            e = discord.Embed(color=role.color)
            e.set_author(name=role.name, icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = ""
            dat = [(m, m.top_role.position) for m in role.members]
            for member, position in sorted(dat, key=lambda kv: kv[1], reverse=True):
                new_line = f"• {member.mention}\n"
                if len(e.description) + len(new_line) > 2000:
                    await ctx.send(embed=e)
                    e.description = ""
                e.description += new_line
            if not e.description:
                e.description = "This role has no members"
            return await ctx.send(embed=e)
        else:  # return the servers member count
            status_list = [
                discord.Status.online,
                discord.Status.idle,
                discord.Status.dnd,
            ]
            humans = len([m for m in ctx.guild.members if not m.bot])
            bots = len([m for m in ctx.guild.members if m.bot])
            online = len([m for m in ctx.guild.members if m.status in status_list])
            e = discord.Embed(color=colors.fate())
            e.set_author(name=f"Member Count", icon_url=ctx.guild.owner.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = (
                f"**Total:** [`{ctx.guild.member_count}`]\n"
                f"**Online:** [`{online}`]\n"
                f"**Humans:** [`{humans}`]\n"
                f"**Bots:** [`{bots}`]"
            )
            await ctx.send(embed=e)

    @commands.command(name="permissions", aliases=["perms", "perm"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def permissions(self, ctx, permission=None):
        perms = [perm[0] for perm in [perm for perm in discord.Permissions()]]
        if not permission:
            return await ctx.send(f'Perms: {", ".join(perms)}')
        if permission.lower() not in perms:
            return await ctx.send("Unknown perm")
        e = discord.Embed(color=colors.fate())
        e.set_author(name=f"Things with {permission}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        members = ""
        for member in ctx.guild.members:
            if eval(f"member.guild_permissions.{permission}"):
                members += f"{member.mention}\n"
        if members:
            e.add_field(name="Members", value=members[:1000])
        roles = ""
        for role in ctx.guild.roles:
            if eval(f"role.permissions.{permission}"):
                roles += f"{role.mention}\n"
        if roles:
            e.add_field(name="Roles", value=roles[:1000])
        await ctx.send(embed=e)

    @commands.command(name="tinyurl")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def tinyurl(self, ctx, *, link: str):
        await ctx.message.delete()
        url = "http://tinyurl.com/api-create.php?url=" + link
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                r = await resp.read()
                r = str(r).replace("b'", "").replace("'", "")
        emb = discord.Embed(color=0x80B0FF)
        emb.add_field(name="Original Link", value=link, inline=False)
        emb.add_field(name="Shortened Link", value=r, inline=False)
        emb.set_footer(
            text="Powered by tinyurl.com",
            icon_url="http://cr-api.com/static/img/branding/cr-api-logo.png",
        )
        await ctx.send(embed=emb)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def avatar(self, ctx, *, user=None):
        if not user:
            user = ctx.author.mention
        if user.isdigit():
            try:
                user = await self.bot.fetch_user(int(user))
            except discord.errors.NotFound:
                return await ctx.send("User not found")
        else:
            user = self.bot.utils.get_user(ctx, user)
            if not user:
                return await ctx.send("User not found")
        e = discord.Embed(color=0x80B0FF)
        if "gif" in user.avatar_url:
            e.set_image(url=user.avatar_url)
        else:
            e.set_image(url=user.avatar_url_as(format="png"))
        await ctx.send(
            f"◈ {utils.cleanup_msg(ctx.message, user.display_name)}'s avatar ◈", embed=e
        )

    @commands.command(name="owner")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def owner(self, ctx):
        e = discord.Embed(color=colors.fate())
        e.description = f"**Server Owner:** {ctx.guild.owner.mention}"
        await ctx.send(embed=e)

    @commands.command(name="topic")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.guild_only()
    async def topic(self, ctx):
        if not ctx.channel.topic:
            return await ctx.send("This channel has no topic")
        await ctx.send(ctx.channel.topic)

    @commands.command(name="color", aliases=["setcolor", "changecolor"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def color(self, ctx, *args):
        if len(args) == 0:
            color = colors.random()
            e = discord.Embed(color=color)
            e.set_author(name=f"#{color}", icon_url=ctx.author.avatar_url)
            return await ctx.send(embed=e)
        if len(args) == 1:
            _hex = args[0].strip("#")
            try:
                color = int("0x" + _hex, 0)
            except ValueError:
                return await ctx.send("That's not a real hex")
            if color > 16777215:
                return await ctx.send("That hex value is too large")
            e = discord.Embed(color=color)
            e.description = f"#{_hex}"
            return await ctx.send(embed=e)
        if not ctx.author.guild_permissions.manage_roles:
            return await ctx.send("You need manage roles permissions to use this")
        if "<@" in args[0]:
            target = "".join(x for x in args[0] if x.isdigit())
            if not target:
                return await ctx.send("Wtf man.. wHo")
            role = ctx.guild.get_role(int(target))
        else:
            role = await utils.get_role(ctx, args[0])
        if not role:
            return await ctx.send("Unknown role")
        try:
            _hex = discord.Color(int("0x" + args[1].strip("#").strip("0x"), 0))
        except:
            return await ctx.send("Invalid Hex")
        if role.position >= ctx.author.top_role.position:
            return await ctx.send("That roles above your paygrade, take a seat")
        previous_color = role.color
        await role.edit(color=_hex)
        await ctx.send(f"Changed {role.name}'s color from {previous_color} to {_hex}")

    async def remind(self, user_id, msg, dat):
        end_time = datetime.strptime(dat["timer"], "%Y-%m-%d %H:%M:%S.%f")
        await discord.utils.sleep_until(end_time)
        channel = self.bot.get_channel(dat["channel"])
        try:
            await channel.send(
                f"{dat['mention']} remember dat thing: {discord.utils.escape_mentions(msg)}",
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
            )
        except (discord.errors.Forbidden, discord.errors.NotFound, AttributeError):
            pass
        with suppress(KeyError, ValueError):
            del self.timers[user_id][msg]
        with suppress(KeyError, ValueError):
            if not self.timers[user_id]:
                del self.timers[user_id]
        await self.save_timers()
        with suppress(KeyError, ValueError):
            del self.bot.tasks["timers"][f"timer-{dat['timer']}"]

    @commands.command(name="reminder", aliases=["timer", "remindme", "remind"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def timer(self, ctx, *args):
        p = self.bot.utils.get_prefixes(self.bot, ctx.message)[2]
        usage = (
            f">>> Usage: `{p}reminder [30s|5m|1h|2d]`"
            f"Example: `{p}reminder 1h take out da trash`"
        )
        timers = []
        for timer in [re.findall("[0-9]+[smhd]", arg) for arg in args]:
            timers = [*timers, *timer]
        args = [arg for arg in args if not any(timer in arg for timer in timers)]
        if not timers:
            return await ctx.send(usage)
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
        timer, expanded_timer = time_to_sleep

        user_id = str(ctx.author.id)
        if user_id not in self.timers:
            self.timers[user_id] = {}
        msg = " ".join(args)
        try:
            self.timers[user_id][msg] = {
                "timer": str(datetime.utcnow() + timedelta(seconds=timer)),
                "channel": ctx.channel.id,
                "mention": ctx.author.mention,
                "expanded_timer": expanded_timer,
            }
        except OverflowError:
            return await ctx.send("That's a bit.. *too far*  into the future")
        await ctx.send(
            f"I'll remind you about {' '.join(args)} in {', '.join(expanded_timer)}"
        )
        await self.save_timers()
        task = self.bot.loop.create_task(
            self.remind(user_id, msg, self.timers[user_id][msg])
        )
        self.bot.tasks["timers"][f"timer-{self.timers[user_id][msg]['timer']}"] = task

    @commands.command(name="timers", aliases=["reminders"])
    @commands.cooldown(*utils.default_cooldown())
    async def timers(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.timers:
            return await ctx.send("You currently have no timers")
        if not self.timers[user_id]:
            return await ctx.send("You currently have no timers")
        e = discord.Embed(color=colors.fate())
        for msg, dat in list(self.timers[user_id].items()):
            end_time = datetime.strptime(dat["timer"], "%Y-%m-%d %H:%M:%S.%f")
            if datetime.utcnow() > end_time:
                del self.timers[user_id][msg]
                await self.save_timers()
                continue
            expanded_time = timedelta(seconds=(end_time - datetime.utcnow()).seconds)
            channel = self.bot.get_channel(dat["channel"])
            if not channel:
                del self.timers[user_id][msg]
                await self.save_timers()
                continue
            e.add_field(
                name=f"Ending in {expanded_time}",
                value=f"{channel.mention} - `{msg}`",
                inline=False,
            )
        await ctx.send(embed=e)

    @commands.Cog.listener("on_ready")
    async def resume_timers(self):
        if "timers" not in self.bot.tasks:
            self.bot.tasks["timers"] = {}
        for user_id, timers in self.timers.items():
            for timer, dat in timers.items():
                if f"timer-{dat['timer']}" in self.bot.tasks["timers"]:
                    continue
                task = self.bot.loop.create_task(self.remind(user_id, timer, dat))
                self.bot.tasks["timers"][f"timer-{dat['timer']}"] = task

    @commands.command(name="findmsg")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def _findmsg(self, ctx, *, content=None):
        if content is None:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Error ⚠", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = (
                "Content is a required argument\n"
                "Usage: `.find {content}`\n"
                "Limit: 16,000"
            )
            e.set_footer(text="Searches for a message")
            return await ctx.send(embed=e)
        async with ctx.typing():
            channel_id = str(ctx.channel.id)
            if channel_id in self.find:
                return await ctx.send("I'm already searching")
            self.find[channel_id] = True
            async for msg in ctx.channel.history(limit=25000):
                if ctx.message.id != msg.id:
                    if content.lower() in msg.content.lower():
                        e = discord.Embed(color=colors.fate())
                        e.set_author(
                            name="Message Found 🔍", icon_url=ctx.author.avatar_url
                        )
                        e.set_thumbnail(url=ctx.guild.icon_url)
                        e.description = (
                            f"**Author:** `{msg.author}`\n"
                            f"[Jump to MSG]({msg.jump_url})"
                        )
                        if msg.content != "":
                            e.add_field(name="Full Content:", value=msg.content)
                        if len(msg.attachments) > 0:
                            for attachment in msg.attachments:
                                e.set_image(url=attachment.url)
                        await ctx.send(embed=e)
                        del self.find[channel_id]
                        return await ctx.message.delete()
        await ctx.send("Nothing found")
        del self.find[channel_id]

    @commands.command(name="last-entry")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(view_audit_log=True)
    @commands.bot_has_permissions(view_audit_log=True)
    async def last_entry(self, ctx, user: Optional[discord.User], action=None):
        """ Gets the last entry for a specific action """
        last_entry = None
        if not user and not action:
            return await ctx.send("You need to specify a user, or an audit log action")
        elif user:
            async for entry in ctx.guild.audit_logs(limit=250):
                if (
                    entry.target and entry.target.id == user.id
                ) or entry.user.id == user.id:
                    last_entry = entry
                    break
        else:
            try:
                action = eval("discord.AuditLogAction." + action)
            except SyntaxError:
                return await ctx.send(f"`{action}` isn't an audit log action")
            async for entry in ctx.guild.audit_logs(limit=1, action=action):
                last_entry = entry
        if not last_entry:
            return await ctx.send(f"I couldn't find anything")
        e = discord.Embed(color=colors.fate())
        e.description = self.bot.utils.format_dict(
            {
                "Action": last_entry.action.name,
                "User": last_entry.user,
                "Target": last_entry.target,
                "Reason": last_entry.reason if last_entry.reason else "None Specified",
                "When": last_entry.created_at,
            }
        )
        await ctx.send(embed=e)

    @commands.command(name="id")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def id(self, ctx, *, user=None):
        if user:
            user = utils.get_user(ctx, user)
            if not user:
                return await ctx.send("User not found")
            return await ctx.send(user.id)
        for user in ctx.message.mentions:
            return await ctx.send(user.id)
        for channel in ctx.message.channel_mentions:
            return await ctx.send(channel.id)
        e = discord.Embed(color=colors.fate())
        e.description = (
            f"{ctx.author.mention}: {ctx.author.id}\n"
            f"{ctx.channel.mention}: {ctx.channel.id}"
        )
        await ctx.send(embed=e)

    @commands.command(name="estimate-inactives")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    async def estimate_inactives(self, ctx, days: int):
        inactive_count = await ctx.guild.estimate_pruned_members(days=days)
        e = discord.Embed(color=colors.fate())
        e.description = f"Inactive Users: {inactive_count}"
        await ctx.send(embed=e)

    @commands.command(name="create-webhook", aliases=["createwebhook"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_webhooks=True)
    @commands.bot_has_permissions(
        manage_webhooks=True, embed_links=True, manage_messages=True
    )
    async def create_webhook(self, ctx, *, name=None):
        if not name:
            return await ctx.send(
                'Usage: "`.create-webhook name`"\nYou can attach a file for its avatar'
            )
        avatar = None
        if ctx.message.attachments:
            avatar = await ctx.message.attachments[0].read()
        webhook = await ctx.channel.create_webhook(name=name, avatar=avatar)
        e = discord.Embed(color=colors.fate())
        e.set_author(name=f"Webhook: {webhook.name}", icon_url=webhook.url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        e.description = webhook.url
        try:
            await ctx.author.send(embed=e)
            await ctx.send("Sent the webhook url to dm 👍")
        except:
            await ctx.send("Failed to dm you the webhook url", embed=e)

    @commands.command(name="webhooks")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def webhooks(self, ctx, channel: discord.TextChannel = None):
        """ Return all the servers webhooks """
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Webhooks", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        if channel:
            if not channel.permissions_for(ctx.guild.me).manage_webhooks:
                return await ctx.send(
                    "I need manage webhook(s) permissions in that channel"
                )
            webhooks = await channel.webhooks()
            e.description = "\n".join([f"• {webhook.name}" for webhook in webhooks])
            await ctx.send(embed=e)
        else:
            for channel in ctx.guild.text_channels:
                if channel.permissions_for(ctx.guild.me).manage_webhooks:
                    webhooks = await channel.webhooks()
                    if webhooks:
                        e.add_field(
                            name=f"◈ {channel}",
                            value="\n".join(
                                [f"• {webhook.name}" for webhook in webhooks]
                            ),
                            inline=False,
                        )
            await ctx.send(embed=e)

    @commands.command(name="move", aliases=["mv"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def move(self, ctx, amount: int, channel: SatisfiableChannel()):
        """ Moves a conversation to another channel """

        if ctx.channel.id == channel.id:
            return await ctx.send("Hey! that's illegal >:(")
        if amount > 250:
            return await ctx.send("That's too many :[")
        cooldown = 1
        if amount > 50:
            await ctx.send("That's a lot.. ima do this a lil slow then")
            cooldown *= cooldown

        webhook = await channel.create_webhook(name="Chat Transfer")
        msgs = await ctx.channel.history(limit=amount + 1).flatten()

        e = discord.Embed()
        e.set_author(name=f"Progress: 0/{amount}", icon_url=ctx.author.avatar_url)
        e.set_footer(text=f"Moving to #{channel.name}")
        transfer_msg = await ctx.send(embed=e)

        em = discord.Embed()
        em.set_author(name=f"Progress: 0/{amount}", icon_url=ctx.author.avatar_url)
        em.set_footer(text=f"Moving from #{channel.name}")
        channel_msg = await channel.send(embed=em)

        await ctx.message.delete()

        index = 1
        for iteration, msg in enumerate(msgs[::-1]):
            if ctx.message.id == msg.id:
                continue
            avatar = msg.author.avatar_url
            embed = None
            if msg.embeds:
                embed = msg.embeds[0]

            files = []
            file_paths = []
            for attachment in msg.attachments:
                fp = os.path.join("static", attachment.filename)
                await attachment.save(fp)
                files.append(discord.File(fp))
                file_paths.append(fp)

            await webhook.send(
                msg.content,
                username=msg.author.display_name,
                avatar_url=avatar,
                files=files,
                embed=embed,
            )
            for fp in file_paths:
                os.remove(fp)
            if index == 5:
                e.set_author(
                    name=f"Progress: {iteration+1}/{amount}",
                    icon_url=ctx.author.avatar_url,
                )
                em.set_author(
                    name=f"Progress: {iteration+1}/{amount}",
                    icon_url=ctx.author.avatar_url,
                )
                await transfer_msg.edit(embed=e)
                await channel_msg.edit(embed=em)
                index = 1
            else:
                index += 1
            await msg.delete()
            await asyncio.sleep(cooldown)

        await webhook.delete()
        result = f"Progress: {amount}/{amount}"
        e.set_author(name=result, icon_url=ctx.author.avatar_url)
        em.set_author(name=result, icon_url=ctx.author.avatar_url)
        await transfer_msg.edit(embed=e)
        await channel_msg.edit(embed=em)

    @commands.command(name="afk")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def afk(self, ctx, *, reason="afk"):
        if ctx.message.mentions or ctx.message.role_mentions:
            return await ctx.send("nO")
        e = discord.Embed(color=colors.fate())
        e.set_author(name="You are now afk", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e, delete_after=5)
        self.afk[str(ctx.author.id)] = reason
        await asyncio.sleep(5)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Utility(bot))

