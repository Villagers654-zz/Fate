"""
cogs.moderation.mod
~~~~~~~~~~~~~~~~~~~~

A cog for general moderation commands

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from os import path
import json
from typing import *
from datetime import datetime, timedelta
import asyncio
import re
from time import time as now
from contextlib import suppress
from string import printable
from unicodedata import normalize

from discord.ext import commands
import discord
from discord import Member, Role, TextChannel, User, ButtonStyle, ui, Interaction, SelectOption
from discord.ext.commands import Greedy
from discord import NotFound, Forbidden, HTTPException

from botutils import colors, get_prefix, get_time, split, CancelButton, format_date, GetConfirmation, extract_time
from classes import IgnoredExit
from fate import Fate
from .case_manager import CaseManager


cache = {}  # Keep track of what commands are still being ran
# This should empty out as quickly as it's filled


def check_if_running():
    """ Checks if the command is already in progress """

    async def predicate(ctx):
        # with open(fp, 'r') as f:
        #     cache = json.load(f)  # type: dict
        cmd = ctx.command.name
        if cmd not in cache:
            cache[cmd] = []
        check_result = ctx.guild.id not in cache[cmd]
        if not check_result:
            with suppress(Forbidden):
                await ctx.send("That command is already running >:(")
        return check_result

    return commands.check(predicate)


def has_required_permissions(**kwargs):
    """ Permission check with support for usermod, rolemod, and role specific cmd access """
    async def predicate(ctx):
        cls = globals()["cls"]  # type: Moderation
        config = cls.config
        if str(ctx.guild.id) not in config:
            cls.config[str(ctx.guild.id)] = cls.template
        config = config[str(ctx.guild.id)]  # type: dict
        cmd = ctx.command.name
        for command, dat in config["commands"].items():
            await asyncio.sleep(0)
            for c, subs in cls.subs.items():
                if cmd in subs:
                    cmd = command
                    break
        if cmd in config["commands"]:
            allowed = config["commands"][cmd]  # type: dict
            if ctx.author.id in allowed["users"]:
                return True
            if any(role.id in allowed["roles"] for role in ctx.author.roles):
                return True
        if ctx.author.id in config["usermod"]:
            return True
        if any(r.id in config["rolemod"] for r in ctx.author.roles):
            return True
        perms = ctx.author.guild_permissions
        return all((perm, value) in list(perms) for perm, value in kwargs.items())

    return commands.check(predicate)


def has_warn_permission():
    async def predicate(ctx):
        cls = globals()["cls"]  # type: Moderation
        config = cls.template
        if not ctx.guild:
            return False
        guild_id = str(ctx.guild.id)
        if guild_id in cls.config:
            config = cls.config[guild_id]
        if ctx.author.id in config["commands"]["warn"]:
            return True
        elif ctx.author.id in config["usermod"]:
            return True
        elif any(r.id in config["rolemod"] for r in ctx.author.roles):
            return True
        elif ctx.author.guild_permissions.administrator:
            return True
        raise commands.CheckFailure("You lack administrator or usermod permissions to use this command")

    return commands.check(predicate)


class DiscordMember(commands.Converter):
    async def convert(self, ctx, argument):
        if not any(c.isdigit() for c in argument) and "#" not in argument:
            raise commands.BadArgument(f"Couldn't convert '{argument}' into member")
        converter = commands.UserConverter()
        return await converter.convert(ctx, argument)


class Moderation(commands.Cog):
    config: Dict[str, Dict[str, Any]]
    tasks: Dict[str, Dict[str, Any]]
    subs: Dict[str, List[str]]

    def __init__(self, bot: Fate):
        self.bot = bot
        self.fp: str = "./static/mod-cache.json"
        self.path: str = "./data/userdata/moderation.json"
        self.config = {}
        self.tasks = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)  # type: dict
        self.timers = bot.utils.persistent_tasks(
            database="role_timers",
            callback=self.handle_timer,
            identifier="user_id"
        )

        # Add or remove any missing/unused key/values
        # this is for ease of updating json as it's developed
        for guild_id, config in self.config.items():
            for key, values in self.template.items():
                if key not in config:
                    config[key] = values
            for key, values in config.items():
                if key not in self.template:
                    del config[key]
            self.config[guild_id] = config

        self.subs = {"warn": ["delwarn", "clearwarns"], "mute": ["unmute"]}

        self.import_bans_usage: str = "Transfer bans from one server to another. Usage is just `.import-bans 1234` " \
                                 "with 1234 being the ID of the server you're importing from"
        self.roles_usage: str = "Formats the role list to show how many members each role has. Usage is just `.roles`"

    @property
    def template(self):
        return {
            "usermod": [],  # Users with access to all mod commands
            "rolemod": [],  # Roles with access to all mod commands
            "commands": {
                "warn": {"users": [], "roles": []},
                "purge": {"users": [], "roles": []},
                "mute": {"users": [], "roles": []},
                "kick": {"users": [], "roles": []},
                "ban": {"users": [], "roles": []},
            },
            "warns": {},
            "warns_config": {},
            "mute_role": None,  # type: Optional[None, discord.Role.id]
            "timers": {},
            "mute_timers": {},
        }

    @property
    def cases(self) -> CaseManager:
        return self.bot.cogs["CaseManager"]  # type: ignore

    async def save_data(self):
        async with self.bot.utils.open(self.path, "w+") as f:
            await f.write(await self.bot.dump(self.config))

    async def cog_before_invoke(self, ctx):
        """ Index commands that are running """
        if not ctx.guild:
            raise commands.errors.NoPrivateMessage("This command can't be ran in a DM")
        cmd = ctx.command.name
        if cmd not in cache:
            cache[cmd] = []
        if ctx.guild.id not in cache[cmd]:
            cache[cmd].append(ctx.guild.id)
        if str(ctx.guild.id) not in self.config:
            self.config[str(ctx.guild.id)] = self.template
            await self.save_data()
        ctx.cls = self

    async def cog_after_invoke(self, ctx):
        """ Index commands that are running """
        for cmd, guild_ids in list(cache.items()):
            for guild_id in guild_ids:
                await asyncio.sleep(0)
                if not self.bot.get_guild(guild_id):
                    if cmd in cache and guild_id in cache[cmd]:
                        cache[cmd].remove(guild_id)
        if not ctx.guild:
            return
        cmd = ctx.command.name
        if cmd in cache and ctx.guild.id in cache[cmd]:
            cache[cmd].remove(ctx.guild.id)

    async def save_config(self, config):
        """ Save things like channel restrictions """
        self.bot.restricted = config
        async with self.bot.utils.open("./data/userdata/config.json", "w") as f:
            await f.write(await self.bot.dump(config))

    @commands.command(
        name="mute-role",
        aliases=["muterole", "set-mute-role", "setmuterole", "set-mute", "setmute"],
        description="Sets the mute role to a specific role"
    )
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(manage_roles=True)
    async def mute_role(self, ctx, *, role):
        role = await self.bot.utils.get_role(ctx, role)
        if not role:
            return await ctx.send("Role not found")
        if (
            role.position >= ctx.author.top_role.position
            and not ctx.author.id == ctx.guild.owner.id
        ):
            return await ctx.send("That role's above your paygrade, take a seat.")
        self.config[str(ctx.guild.id)]["mute_role"] = role.id
        await ctx.send(f"Set the mute role to {role.name}")
        await self.save_data()

    @commands.command(name="addmod", description="Gives a user or role access to mod commands")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    async def addmod(self, ctx, target: Union[discord.Member, discord.Role] = None):
        if not target:
            return await ctx.send("User or role not found")
        if isinstance(target, discord.Member):
            if target.top_role.position >= ctx.author.top_role.position:
                return await ctx.send("That user is above your paygrade, take a seat")
        elif target.position >= ctx.author.top_role.position:
            return await ctx.send("That role is above your paygrade, take a seat")
        guild_id = str(ctx.guild.id)
        if isinstance(target, discord.Member):
            if target.id in self.config[guild_id]["usermod"]:
                return await ctx.send("That users already a mod")
            self.config[guild_id]["usermod"].append(target.id)
        else:
            if target.id in self.config[guild_id]["rolemod"]:
                return await ctx.send("That role's already a mod role")
            self.config[guild_id]["rolemod"].append(target.id)
        e = discord.Embed(color=colors.fate)
        e.description = f"Made {target.mention} a mod"
        await ctx.send(embed=e)
        await self.save_data()

    @commands.command(
        name="delmod",
        aliases=["removemod", "del-mod", "remove-mod"],
        description="Removes a user or roles special mod command access"
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    async def delmod(self, ctx, target: Union[discord.Member, discord.Role] = None):
        if not target:
            return await ctx.send("User or role not found")
        if isinstance(target, discord.Member):
            if target.top_role.position >= ctx.author.top_role.position:
                return await ctx.send("That user is above your paygrade, take a seat")
        elif target.position >= ctx.author.top_role.position:
            return await ctx.send("That role is above your paygrade, take a seat")
        guild_id = str(ctx.guild.id)
        if isinstance(target, discord.Member):
            if target.id not in self.config[guild_id]["usermod"]:
                return await ctx.send("That user isn't a mod")
            self.config[guild_id]["usermod"].remove(target.id)
        else:
            if target.id not in self.config[guild_id]["rolemod"]:
                return await ctx.send("That role's isn't a mod role")
            self.config[guild_id]["rolemod"].remove(target.id)
        e = discord.Embed(color=colors.fate)
        e.description = f"Removed {target.mention} mod"
        await ctx.send(embed=e)
        await self.save_data()

    @commands.command(
        name="mods",
        aliases=["usermods", "rolemods"],
        description="Lists everything that has user/role mod"
    )
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def mods(self, ctx):
        config = self.config[str(ctx.guild.id)]
        if not config["usermod"] and not config["rolemod"]:
            return await ctx.send("There are no mod users or mod roles")
        e = discord.Embed(color=colors.fate)
        users = [self.bot.get_user(uid) for uid in config["usermod"]]
        users = [u for u in users if u]
        roles = [ctx.guild.get_role(rid) for rid in config["rolemod"]]
        roles = [r for r in roles if r]
        if not users and not roles:
            return await ctx.send(
                "There are no mod users or mod roles, the existing ones were removed"
            )
        if users:
            e.add_field(
                name="UserMods", value="\n".join(u.mention for u in users), inline=False
            )
        if roles:
            e.add_field(
                name="RoleMods", value="\n".join(r.mention for r in roles), inline=False
            )
        await ctx.send(embed=e)

    @commands.command(name="purge", aliases=["prune", "nuke"], description="Bulk deletes messages")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge(self, ctx, *args):
        _help = discord.Embed(color=colors.fate)
        _help.description = (
            ".purge amount\n"
            ".purge @user amount\n"
            ".purge images amount\n"
            ".purge embeds amount\n"
            ".purge stickers amount\n"
            ".purge mentions amount\n"
            ".purge users amount\n"
            ".purge bots amount\n"
            ".purge word/phrase amount"
        )
        if (not args or not args[len(args) - 1].isdigit()) and not ctx.message.reference:
            return await ctx.send(embed=_help)

        args = [str(arg).lower() for arg in args]
        if ctx.message.reference:
            amount_to_purge = "1000"
            if args:
                amount_to_purge = args[len(args) - 1]
        else:
            amount_to_purge = args[len(args) - 1]
        if not amount_to_purge.isdigit():
            return await ctx.send(f"{amount_to_purge} isn't a number")
        amount_to_purge = int(amount_to_purge)
        ctx.counter = 0
        if amount_to_purge > 1000:
            return await ctx.send("You can't purge more than 1000 messages")
        check = None
        msgs = []
        if len(args) > 1:
            if ctx.message.raw_mentions:
                special_check = lambda msg: msg.author.id in ctx.message.raw_mentions
            elif "image" in args or "images" in args:
                special_check = lambda msg: msg.attachments
            elif "embed" in args or "embeds" in args:
                special_check = lambda msg: msg.embeds
            elif "mentions" in args:
                special_check = lambda msg: msg.raw_mentions or (
                    msg.raw_channel_mentions or msg.raw_role_mentions
                )
            elif "user" in args or "users" in args:
                special_check = lambda msg: not msg.author.bot
            elif "bot" in args or "bots" in args:
                special_check = lambda msg: msg.author.bot
            elif "sticker" in args or "stickers" in args:
                special_check = lambda msg: msg.stickers
            else:
                phrase = " ".join(args[: len(args) - 1])
                special_check = lambda msg: phrase in str(msg.content).lower()
            old_amount = int(amount_to_purge)
            amount_to_purge = 250

            if "reaction" in args or "reactions" in args:
                deleted = 0
                async for msg in ctx.channel.history(before=ctx.message, limit=250):
                    if deleted == old_amount:
                        break
                    if msg.reactions:
                        await msg.clear_reactions()
                        msgs.append(msg)
                        deleted += 1

            def check(msg):
                if ctx.counter == old_amount:
                    return False
                if special_check(msg):
                    ctx.counter += 1
                    return True
                return False

        if "reaction" not in args and "reactions" not in args:
            async def purge_task(coro):
                try:
                    messages = await coro
                except discord.HTTPException:  # Msgs too old
                    try:
                        messages = []
                        async for msg in ctx.channel.history(before=ctx.message, limit=amount_to_purge):
                            with suppress(Forbidden, NotFound, asyncio.TimeoutError):
                                await msg.delete()
                                messages.append(msg)
                    except discord.NotFound:
                        raise IgnoredExit
                return messages

            kwargs = {}
            if check:
                kwargs["check"] = check
            if ctx.message.reference:
                ref = ctx.message.reference
                if ref.cached_message:
                    purge_after = ref.cached_message
                else:
                    purge_after = await ctx.channel.fetch_message(ref.message_id)
                coro = ctx.channel.purge(
                    limit=1000,
                    before=ctx.message,
                    after=purge_after,
                    **kwargs
                )
            else:
                coro = ctx.channel.purge(
                    limit=amount_to_purge,
                    before=ctx.message,
                    **kwargs
                )

            task = self.bot.loop.create_task(purge_task(coro))
            for _iteration in range(round(5 / 0.21)):
                await asyncio.sleep(0.21)
                if task.done():
                    break
            else:
                await ctx.send(
                    "It seems this purge is gonna take awhile..", delete_after=20
                )
            while not task.done():
                await asyncio.sleep(0.21)
            msgs = task.result()
        e = discord.Embed(
            description=f"♻ Cleared {len(msgs)} message{'s' if len(msgs) > 1 else ''}"
        )
        await ctx.send(embed=e, delete_after=5)
        await ctx.message.delete(delay=5)

    async def handle_mute_timer(self, guild_id: str, user_id: str, timer_info: dict):
        timer = timer_info["end_time"] - now()
        await asyncio.sleep(timer)  # Switch this to a task
        if user_id in self.config[guild_id]["mute_timers"]:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                del self.config[guild_id]["mute_timers"][user_id]
                return
            user = guild.get_member(int(user_id))
            if not user:
                del self.config[guild_id]["mute_timers"][user_id]
                return
            if "removed_roles" in timer_info and timer_info["removed_roles"]:
                for role_id in timer_info["removed_roles"]:
                    role = guild.get_role(role_id)
                    if not role:
                        continue
                    if role not in user.roles:
                        try:
                            await user.add_roles(role)
                        except discord.Forbidden:
                            pass
            mute_role = guild.get_role(self.config[guild_id]["mute_role"])
            if not mute_role:
                self.config[guild_id]["mute_role"] = None
                if user_id in self.config[guild_id]["mute_timers"]:
                    del self.config[guild_id]["mute_timers"][user_id]
                return
            if mute_role in user.roles:
                channel = self.bot.get_channel(timer_info["channel"])
                if channel:
                    try:
                        await user.remove_roles(mute_role)
                        await channel.send(f"**Unmuted:** {user.name}")
                    except discord.Forbidden:
                        pass
            if user_id in self.config[guild_id]["mute_timers"]:
                del self.config[guild_id]["mute_timers"][user_id]
        if guild_id in self.tasks and user_id in self.tasks[guild_id]:
            del self.tasks[guild_id][user_id]
        if guild_id in self.tasks and not self.tasks[guild_id]:
            del self.tasks[guild_id]

    @commands.command(
        name="mute",
        aliases=["shutup", "fuckoff", "shush", "shh", "shut", "oppress"],
        description="Prevents a user from being able to chat"
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(manage_roles=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mute(self, ctx, members: Greedy[discord.Member], *, reason="Unspecified"):
        if not members:
            return await ctx.send("**Format:** `.mute {@user} {timer: 2m, 2h, or 2d}`")

        guild_id = str(ctx.guild.id)
        mute_role = None
        async with ctx.channel.typing():
            if self.config[guild_id]["mute_role"]:
                mute_role = ctx.guild.get_role(self.config[guild_id]["mute_role"])
            if not mute_role:
                mute_role = await self.bot.utils.get_role(ctx, "muted")
                if not mute_role:
                    perms = ctx.guild.me.guild_permissions
                    if not perms.manage_channels or not perms.manage_roles:
                        p = get_prefix(ctx)
                        return await ctx.send(
                            "No muted role found, and I'm missing manage_role and manage_channel permissions to set "
                            f"one up. You can set a mute role manually with `{p}mute-role @role` which doesn't "
                            f"have to be a role @mention, and can just be the roles name."
                        )
                    await ctx.send("Creating mute role..")
                    mute_role = await ctx.guild.create_role(
                        name="Muted", color=discord.Color(colors.black)
                    )

                    # Set the overwrites for the mute role
                    for i, channel in enumerate(ctx.guild.text_channels):
                        with suppress(discord.Forbidden):
                            await channel.set_permissions(
                                mute_role, send_messages=False
                            )
                        if i + 1 >= len(
                            ctx.guild.text_channels
                        ):  # Prevent sleeping after the last
                            await asyncio.sleep(0.5)
                    for i, channel in enumerate(ctx.guild.voice_channels):
                        with suppress(discord.Forbidden):
                            await channel.set_permissions(mute_role, speak=False)
                        if i + 1 >= len(
                            ctx.guild.voice_channels
                        ):  # Prevent sleeping after the last
                            await asyncio.sleep(0.5)

                if mute_role.position >= ctx.guild.me.top_role.position:
                    return await ctx.send(
                        "My current role's not high enough for me to give, or remove the mute role to, or from anyone"
                    )
                self.config[guild_id]["mute_role"] = mute_role.id

            # Setup the mute role in channels it's not in
            for i, channel in enumerate(ctx.guild.text_channels):
                if (
                    not channel.permissions_for(ctx.guild.me).manage_channels
                    or mute_role in channel.overwrites
                ):
                    continue
                if mute_role not in channel.overwrites:
                    with suppress(discord.Forbidden):
                        await channel.set_permissions(mute_role, send_messages=False)
                    if i + 1 >= len(
                        ctx.guild.text_channels
                    ):  # Prevent sleeping after the last
                        await asyncio.sleep(0.5)
            for i, channel in enumerate(ctx.guild.voice_channels):
                if (
                    not channel.permissions_for(ctx.guild.me).manage_channels
                    or mute_role in channel.overwrites
                ):
                    continue
                if mute_role not in channel.overwrites:
                    with suppress(discord.Forbidden):
                        await channel.set_permissions(mute_role, speak=False)
                    if i + 1 >= len(
                        ctx.guild.voice_channels
                    ):  # Prevent sleeping after the last
                        await asyncio.sleep(0.5)

            if mute_role.position >= ctx.guild.me.top_role.position:
                return await ctx.send("The mute role's above my highest role so I can't manage it")

            timers = []
            timer = expanded_timer = None
            for timer in [re.findall("[0-9]+[smhd]", arg) for arg in reason.split()]:
                timers = [*timers, *timer]
            if timers:
                time_to_sleep = [0, []]
                for timer in timers:
                    reason = str(reason.replace(timer, "")).lstrip(" ").rstrip(" ")
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
                    time_to_sleep[1].append(
                        f"{raw} {_repr if raw == '1' else _repr + 's'}"
                    )
                timer, expanded_timer = time_to_sleep
                expanded_timer = ", ".join(expanded_timer)

        if not reason:
            reason = "Unspecified"
        for user in list(members):
            if user.top_role.position >= ctx.author.top_role.position:
                return await ctx.send("That user is above your paygrade, take a seat")
            if user.top_role.position >= ctx.guild.me.top_role.position:
                return await ctx.send("That users top role is above mine, so I can't manage them")
            updated = False
            if mute_role in user.roles:
                user_id = str(user.id)
                if guild_id in self.tasks and user_id in self.tasks[guild_id]:
                    self.tasks[guild_id][user_id].cancel()
                    del self.tasks[guild_id][user_id]
                    updated = True
            removed_roles = []

            async def ensure_muted():
                if user.guild_permissions.administrator:
                    choice = await self.bot.utils.get_choice(
                        ctx,
                        "Remove admin roles",
                        "Leave as is",
                        name=f"{user.name} can still talk",
                        user=ctx.author,
                    )
                    if choice == "Remove admin roles":
                        for role in user.roles:
                            if role.permissions.administrator:
                                await user.remove_roles(role)
                                removed_roles.append(role.id)
                return None

            case = await self.cases.add_case(ctx.guild.id, user.id, "mute", reason, ctx.message.jump_url, ctx.author.id)
            additional = ""
            usr_additional = ""
            async with self.bot.utils.cursor() as cur:
                await cur.execute(f"select channel_id from modmail where guild_id = {guild_id};")
                result = await cur.fetchone()
            if result:
                usr_additional += f" [use .appeal {case} if this was a mistake]"

            if not timers:
                try:
                    await user.send(f"You've been muted in {ctx.guild} for {reason}" + usr_additional)
                except:
                    additional += " (Unable to notify user via DM)"
                await user.add_roles(mute_role)
                await ctx.send(
                    f"Muted {user.display_name} for {reason} [Case #{case}]" + additional,
                    view=MuteView(ctx, user, case, reason.replace("Unspecified", ""), timer)
                )
                await ensure_muted()
                continue

            if timer > 15552000:  # 6 months
                return await ctx.send(
                    "No way in hell I'm waiting that long to unmute. "
                    "You'll have to do it yourself >:("
                )
            await user.add_roles(mute_role)
            await ensure_muted()
            timer_info = {
                "channel": ctx.channel.id,
                "user": user.id,
                "end_time": now() + timer,
                "mute_role": mute_role.id,
                "removed_roles": removed_roles,
            }
            try:
                await user.send(f"You've been muted in {ctx.guild} for {expanded_timer} for {reason}" + usr_additional)
            except:
                additional += " (Unable to notify user via DM)"
            if updated:
                await ctx.send(
                    f"Updated the mute for **{user.name}** to {expanded_timer} "
                    f"for {reason} [Case #{case}]" + additional
                )
            else:
                await ctx.send(
                    f"Muted **{user.name}** for {expanded_timer} "
                    f"for {reason} [Case #{case}]" + additional,
                    view=MuteView(ctx, user, case, reason.replace("Unspecified", ""), timer)
                )

            user_id = str(user.id)
            self.config[guild_id]["mute_timers"][user_id] = timer_info
            await self.save_data()
            task = self.bot.loop.create_task(
                self.handle_mute_timer(guild_id, user_id, timer_info)
            )
            if guild_id not in self.tasks:
                self.tasks[guild_id] = {}
            self.tasks[guild_id][user_id] = task

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id, tasks in list(self.tasks.items()):
            for user_id, task in tasks.items():
                if task.done() and task.result():
                    self.bot.log.critical(
                        f"A mute task errored\n```python\n{task.result()}```"
                    )
                    del self.tasks[guild_id][user_id]
        for guild_id, data in list(self.config.items()):
            for user_id, timer_info in data["mute_timers"].items():
                if guild_id not in self.tasks or user_id not in self.tasks[guild_id]:
                    task = self.bot.loop.create_task(
                        self.handle_mute_timer(guild_id, user_id, timer_info)
                    )
                    if guild_id not in self.tasks:
                        self.tasks[guild_id] = {}
                    self.tasks[guild_id][user_id] = task

    @commands.command(
        name="unmute",
        aliases=["unshutup", "unfuckoff", "unshh", "unshush", "unshut", "unoppress"],
        description="Removes the mute role from a user"
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @has_required_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, users: Greedy[discord.Member]):
        if not users:
            return await ctx.send("You need to specify who to unmute")
        for user in users:
            if not user:
                return await ctx.send("**Unmute Usage:**\n.unmute {@user}")
            if (
                user.top_role.position >= ctx.author.top_role.position
                and ctx.author.id != ctx.guild.owner.id
            ):
                return await ctx.send("That user is above your paygrade, take a seat")
            guild_id = str(ctx.guild.id)
            user_id = str(user.id)
            mute_role = None
            if self.config[guild_id]["mute_role"]:
                mute_role = ctx.guild.get_role(self.config[guild_id]["mute_role"])
                if not mute_role:
                    await ctx.send(
                        "The configured mute role was deleted, so I'll try to find another"
                    )
            if not mute_role:
                mute_role = await self.bot.utils.get_role(ctx, "muted")
            if not mute_role:
                p = get_prefix(ctx)
                return await ctx.send(
                    f"No mute role found? If it doesn't have `muted` in the name use `{p}mute-role @role` "
                    f"which doesn't need to be a role @mention, and you can just the roles name."
                )
            if mute_role not in user.roles:
                return await ctx.send(f"{user.display_name} is not muted")
            await user.remove_roles(mute_role)
            if user_id in self.config[guild_id]["mute_timers"]:
                del self.config[guild_id]["mute_timers"][user_id]
                await self.save_data()
            if guild_id in self.tasks and user_id in self.tasks[guild_id]:
                if not self.tasks[guild_id][user_id].done():
                    self.tasks[guild_id][user_id].cancel()
                del self.tasks[guild_id][user_id]
                if not self.tasks[guild_id]:
                    del self.tasks[guild_id]
            await ctx.send(f"Unmuted {user.name}")

    @commands.command(name="kick", description="Kicks a user from the server")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(kick_members=True)
    @commands.bot_has_permissions(embed_links=True, kick_members=True)
    async def kick(self, ctx, members: Greedy[Union[discord.Member, discord.User]], *, reason="Unspecified"):
        if not members:
            return await ctx.send("You need to properly specify who to kick")
        e = discord.Embed(color=colors.fate)
        e.set_author(name=f"Kicking members", icon_url=ctx.author.display_avatar.url)
        msg = await ctx.send(embed=e)
        e.description = ""
        for i, member in enumerate(members):
            if isinstance(member, discord.User):  # Was kicked already
                continue
            if member.top_role.position >= ctx.author.top_role.position:
                e.description += f"\n❌ {member} is Higher Than You"
            elif member.top_role.position >= ctx.guild.me.top_role.position:
                e.description += f"❌ {member} is Higher Than Me"
            else:
                case = await self.cases.add_case(
                    ctx.guild.id, member.id, "kick", reason, ctx.message.jump_url, ctx.author.id
                )
                content = f"You've been kicked in {ctx.guild} by {ctx.author} for {reason}"
                rows = await self.bot.rowcount(f"select * from modmail where guild_id = {ctx.guild.id};")
                if rows:
                    content += f". Use `.appeal {case}` if you feel there's a mistake"
                else:
                    content += f" [Case #{case}]"
                with suppress(NotFound, Forbidden, HTTPException):
                    await member.send(content)
                await member.kick(
                    reason=f"Kicked by {ctx.author} with ID: {ctx.author.id} for {reason}"
                )

                e.description += f"✅ {member} [Case #{case}]"
            if i % 2 == 0 and i != len(members) - 1:
                await msg.edit(embed=e)
        await msg.edit(embed=e)

    @commands.command(name="ban", aliases=["yeet"], description="Bans a user from the server")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @check_if_running()
    @commands.guild_only()
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(embed_links=True, ban_members=True)
    async def ban(self, ctx, users: Greedy[User], *, reason="Unspecified"):
        """ Ban cmd that supports more than just members """
        original_args = ctx.message.content.split()[1:]  # Remove prefix and command
        for iteration, (user, arg) in enumerate(zip(users, original_args)):
            if not arg.isdigit() and "#" not in arg and "@" not in arg:
                users = users[:iteration]
                reason = " ".join(original_args[-(len(original_args) - iteration):])

        reason = reason[:128]
        users_to_ban = len(users)
        e = discord.Embed(color=colors.fate)
        if users_to_ban == 0:
            return await ctx.send("You need to specify who to ban")
        elif users_to_ban > 1:
            e.set_author(
                name=f"Banning {users_to_ban} user{'' if users_to_ban > 1 else ''}",
                icon_url=ctx.author.display_avatar.url,
            )
        if users_to_ban > 10:
            return await ctx.send("That's too many")
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif"
        )
        msg = await ctx.send(embed=e)
        for user in users:
            member = discord.utils.get(ctx.guild.members, id=user.id)
            if member:
                if member.top_role.position >= ctx.author.top_role.position:
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="This users is above your paygrade",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="I can't ban this user",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
            case = await self.cases.add_case(
                ctx.guild.id, user.id, "ban", reason, ctx.message.jump_url, ctx.author.id
            )
            content = f"You've been banned in {ctx.guild} by {ctx.author} for {reason}"
            rows = await self.bot.rowcount(f"select * from modmail where guild_id = {ctx.guild.id};")
            if rows:
                content += f". Use `.appeal {case}` if you feel there's a mistake"
            else:
                content += f" [Case #{case}]"
            if f"@{user.id}>" in ctx.message.content:
                with suppress(NotFound, Forbidden, HTTPException):
                    await user.send(content)
            await ctx.guild.ban(
                user, reason=f"{ctx.author}: {reason}"[:512], delete_message_days=0
            )
            e.add_field(
                name=f"◈ Banned {user} [Case #{case}]", value=f"Reason: {reason}", inline=False
            )
        if not e.fields:
            e.colour = colors.red
            e.set_author(name="Couldn't ban any of the specified user(s)")
        await msg.edit(embed=e)

    @commands.command(
        name="get-ban",
        aliases=["getban", "searchban", "search-ban", "searchbans", "search-bans"],
        description="Gives extra information on a ban"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True, view_audit_log=True)
    async def get_ban(self, ctx, user: discord.User):
        bans = await ctx.guild.bans()
        for ban_entry in bans:
            await asyncio.sleep(0)
            if ban_entry.user.id == user.id:
                ban = ban_entry
                break
        else:
            return await ctx.send(f"{user} isn't banned")

        action = discord.AuditLogAction.ban
        async for entry in ctx.guild.audit_logs(limit=2500, action=action):
            if entry.target.id == user.id:
                entry: discord.AuditLogEntry = entry
                break
        else:
            return await ctx.send("Couldn't find any results in the audit log. It's probably too old")

        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name=f"Ban Entry for {user}", icon_url=user.display_avatar.url)
        e.description = f"> {ban.reason if ban.reason else 'No reason specified'}"
        e.add_field(
            name="◈ Banned by",
            value=str(entry.user)
        )
        when = entry.created_at.strftime("%b %d %Y %H:%M:%S")
        e.set_footer(text=f"At {when}")
        await ctx.send(embed=e)

    @commands.command(
        name="import-bans",
        aliases=["importbans", "transfer-bans", "transferbans"],
        description="Copies the ban-list from another server"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def import_bans(self, ctx, server_id: int):
        guild = self.bot.get_guild(server_id)
        if not guild:
            return await ctx.send("Server not found. Maybe i'm not in it?")
        user = guild.get_member(ctx.author.id)
        if not user:
            return await ctx.send("It doesn't seem you're in that server")
        if not user.guild_permissions.ban_members:
            return await ctx.send("You need ban_member permission(s) in that server to import its ban list")
        bans = await guild.bans()
        current_bans = await ctx.guild.bans()
        users_to_ban = []
        for entry in bans:
            if not any(entry.user.id == e.user.id for e in current_bans):
                if not ctx.guild.get_member(entry.user.id):
                    users_to_ban.append([entry.user, entry.reason])
        if not users_to_ban:
            return await ctx.send("No bans left to import")
        msg = await ctx.send(f"Importing bans (0/{len(users_to_ban)})")
        try:
            for i, (user, reason) in enumerate(users_to_ban):
                if i % round(len(users_to_ban) / 5) == 0:
                    await msg.edit(content=f"Importing bans ({i + 1}/{len(users_to_ban)})")
                if not reason:
                    reason = f"{ctx.author} importing bans"
                await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        except Forbidden:
            with suppress(Exception):
                await ctx.send("I no longer have permission(s) to ban. Operation cancelled")
        except HTTPException as error:
            await ctx.send(error)
        else:
            await msg.edit(content=f"Importing bans ({len(users_to_ban)}/{len(users_to_ban)})")
            await ctx.send("Finished importing bans")

    @commands.command(name="unban", description="Removes the ban for a user")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(
        embed_links=True, ban_members=True, view_audit_log=True
    )
    async def unban(self, ctx, users: Greedy[discord.User], *, reason=":author:"):
        if not users:
            async for entry in ctx.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            ):
                users = (entry.target,)
        if len(users) == 1:
            user = users[0]
            try:
                await ctx.guild.unban(
                    user, reason=reason.replace(":author:", str(ctx.author))
                )
            except discord.NotFound:
                return await ctx.send("That user isn't banned")
            case = await self.cases.add_case(
                ctx.guild.id, user.id, "unban", str(ctx.author), ctx.message.jump_url, ctx.author.id
            )
            e = discord.Embed(color=colors.red)
            e.set_author(name=f"{user} unbanned [Case #{case}]", icon_url=user.display_avatar.url)
            await ctx.send(embed=e)
        else:
            e = discord.Embed(color=colors.green)
            e.set_author(
                name=f"Unbanning {len(users)} users", icon_url=ctx.author.display_avatar.url
            )
            e.description = ""
            msg = await ctx.send(embed=e)
            index = 1
            for user in users:
                try:
                    await ctx.guild.unban(
                        user, reason=reason.replace(":author:", str(ctx.author))
                    )
                except discord.NotFound:
                    e.description += f"Couldn't unban {user}"
                    continue
                case = await self.cases.add_case(
                    ctx.guild.id, user.id, "unban", str(ctx.author), ctx.message.jump_url, ctx.author.id
                )
                e.description += f"✅ {user} [Case #{case}]"
                if index == 5:
                    await msg.edit(embed=e)
                    index = 1
                else:
                    index += 1
            await msg.edit(embed=e)

    @commands.command(name="roles", description="Shows how many people have each role")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 15, commands.BucketType.channel)
    @check_if_running()
    async def roles(self, ctx):
        """ Formats the role list to show how many members each role has """
        longest = sorted(ctx.guild.roles, key=lambda r: len(r.name), reverse=True)[0]
        length = len(longest.name) + 3
        roles = f"Name:{' ' * (length - 5)}Members:\n"
        for role in sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True):
            await asyncio.sleep(0)
            name = normalize('NFKD', role.name).encode('ascii', 'ignore').decode()
            name = "".join(c for c in name if c in printable)
            roles += f"\n{name}{' ' * (length - len(name))}{len(role.members)}"
        for chunk in split(roles, 1900):
            chunk = chunk.lstrip("\n")
            await ctx.send(f"```\n{chunk}```")

    @commands.command(name="mass-nick", aliases=["massnick"], description="Sets the nick of everyone in the server")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(manage_nicknames=True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    async def mass_nick(self, ctx, *, nick=""):
        def gen_embed(iteration):
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Mass Updating Nicknames", icon_url=ctx.author.display_avatar.url)
            e.description = (
                f"{iteration + 1}/{len(members)} complete"
                f"\n1 nick per 1.21 seconds"
                f"\nETA of {get_time(round((len(members) - (iteration + 1)) * 1.21))}"
            )
            return e

        if len(nick) > 32:
            return await ctx.send("Nicknames cannot exceed 32 characters in length")
        members = []
        for member in list(ctx.guild.members):
            await asyncio.sleep(0)
            if member.top_role.position < ctx.author.top_role.position:
                if member.top_role.position < ctx.guild.me.top_role.position:
                    if member.nick if not nick else member.display_name != nick:
                        members.append(member)
        if not members:
            return await ctx.send("There aren't any possible members I can nick")
        view = CancelButton("manage_roles")
        if len(members) > 3600:
            msg = await ctx.send(
                "Bruh.. you get ONE hour, but that's it.", embed=gen_embed(0), view=view
            )
        else:
            msg = await ctx.send(embed=gen_embed(0), view=view)
        await self.cases.add_case(
            ctx.guild.id, ctx.author.id, "massnick", nick, msg.jump_url, ctx.author.id
        )
        async with ctx.typing():
            last_updated = now()
            for i, member in enumerate(members[:3600]):
                await asyncio.sleep(1.21)
                if view.is_cancelled:
                    return await msg.edit(
                        content="Message Inactive: Operation Cancelled"
                    )
                if now() - 5 > last_updated:  # try checking the bots internal message cache instead
                    await msg.edit(embed=gen_embed(i))
                    last_updated = now()
                try:
                    await member.edit(nick=nick)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    if not ctx.guild.me.guild_permissions.manage_nicknames:
                        view.stop()
                        await msg.edit(content="Message Inactive: Missing Permissions", view=None)
                        return await ctx.send(
                            "I'm missing permissions to manage nicknames. Canceling the operation :["
                        )
            view.stop()
            await msg.edit(content="Operation Complete", embed=gen_embed(len(members) - 1), view=None)

    @commands.command(name="mass-role", aliases=["massrole"], description="Give a role to everyone in the server")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_required_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mass_role(self, ctx, *, role=None):
        def gen_embed(iteration):
            e = discord.Embed(color=colors.fate)
            e.set_author(name=f"Mass {action} Roles", icon_url=ctx.author.display_avatar.url)
            e.description = (
                f"{iteration + 1}/{len(members)} complete"
                f"\n1 role per 1.21 seconds"
                f"\nETA of {get_time(round((len(members) - (iteration + 1)) * 1.21))}"
            )

            return e

        if not role:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="MassRole Usages", icon_url=ctx.author.display_avatar.url)
            e.description = f"Add, or remove roles from members in mass"
            p = get_prefix(ctx)
            e.add_field(name=f"{p}massrole @Role", value="Mass adds roles")
            e.add_field(name=f"{p}massrole -@Role", value="Mass removes roles")
            e.add_field(
                name="Note",
                value="@Role can be replaced with role names, role mentions, or role ids",
                inline=False,
            )
            return await ctx.send(embed=e)

        role = role.lstrip("+")
        action = "Adding"
        if role.startswith("-"):
            action = "Removing"
            role = role.lstrip("-")
        role = await self.bot.utils.get_role(ctx, role)
        if not role:
            return
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's higher than I can manage")
        members = []
        for member in list(ctx.guild.members):
            await asyncio.sleep(0)
            if member.top_role.position < ctx.author.top_role.position:
                if member.top_role.position < ctx.guild.me.top_role.position:
                    if role not in member.roles if action == "Adding" else role in member.roles:
                        members.append(member)
        if not members:
            return await ctx.send("There aren't any possible members I can give give, or remove that role from")
        view = CancelButton("manage_roles")
        if len(members) > 3600:
            msg = await ctx.send(
                "Bruh.. you get ONE hour, but that's it.", embed=gen_embed(0), view=view
            )
        else:
            msg = await ctx.send(embed=gen_embed(0), view=view)
        await self.cases.add_case(
            ctx.guild.id, ctx.author.id, "massrole", role.mention, msg.jump_url, ctx.author.id
        )
        async with ctx.typing():
            last_updated = now()
            for i, member in enumerate(members[:3600]):
                await asyncio.sleep(1.21)
                if view.is_cancelled:
                    return await msg.edit(
                        content="Message Inactive: Operation Cancelled",
                        view=None
                    )
                if now() - 5 > last_updated:
                    await msg.edit(embed=gen_embed(i))
                    last_updated = now()
                try:
                    if action == "Adding":
                        await member.add_roles(role)
                    else:
                        await member.remove_roles(role)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    if not ctx.guild.me.guild_permissions.manage_roles:
                        view.stop()
                        await msg.edit(content="Message Inactive: Missing Permissions", view=None)
                        return await ctx.send(
                            "I'm missing permissions to manage roles. Canceling the operation :["
                        )
            view.stop()
            await msg.edit(content="Operation Complete", embed=gen_embed(i), view=None)

    @commands.command(name="nick", description="Shortcut command for setting a users nickname")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(self, ctx, user, *, nick=""):
        user = await self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        if ctx.author.id != ctx.guild.owner.id:
            if user.top_role.position >= ctx.author.top_role.position:
                return await ctx.send("That user is above your paygrade, take a seat")
            if user.top_role.position >= ctx.guild.me.top_role.position:
                return await ctx.send("I can't edit that users nick ;-;")
        if len(nick) > 32:
            return await ctx.send(
                "That nickname is too long! Must be `32` or fewer in length"
            )
        await user.edit(nick=nick)
        await ctx.message.add_reaction("👍")

    @commands.command(name="role", description="Shortcut command for giving a user a role")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role(self, ctx, user, *, role):
        user = await self.bot.utils.get_user(ctx, user)
        if user:
            user = ctx.guild.get_member(user.id)
        if not user:
            return await ctx.send("User not found")
        timer = None
        if " " in role and (timer := extract_time(role.split()[::-1][0])):
            role = role.split()[0]
            if timer > 60 * 60 * 24 * 7:
                return await ctx.send(f"You can't set a role timer longer than a week")
            if timer < 60:
                return await ctx.send("Role timer's can't be shorter than a minute")
        converter = commands.RoleConverter()
        try:
            result = await converter.convert(ctx, role)
            role = result  # type: discord.Role
        except:
            pass
        if not isinstance(role, discord.Role):
            role = await self.bot.utils.get_role(ctx, role)
        if not role:
            return await ctx.send("Role not found")

        if ctx.author.id != ctx.guild.owner.id:
            if user.top_role.position >= ctx.author.top_role.position:
                return await ctx.send("This user is above your paygrade, take a seat")
            if role.position >= ctx.author.top_role.position:
                return await ctx.send("This role is above your paygrade, take a seat")
        sensitive = ["kick_members", "ban_members", "manage_roles", "manage_channels"]
        if any(getattr(role.permissions, perm) for perm in sensitive):
            if not await GetConfirmation(ctx, "This role has sensitive permissions, are you sure?"):
                return
        if role in user.roles:
            await user.remove_roles(role)
            msg = f"Removed **{role.name}** from @{user.name}"
            add = True
        else:
            await user.add_roles(role)
            msg = f"Gave **{role.name}** to **@{user.name}**"
            add = False
        if timer:
            msg += f" for {get_time(timer)}"
        await ctx.send(msg)
        if timer:
            if user.id in self.timers.db:
                return await ctx.send("Each user can only have one role timer at a time")
            self.timers.run(
                channel_id=ctx.channel.id,
                message_id=ctx.message.id,
                role_id=role.id,
                user_id=user.id,
                add=add,
                sleep_for=timer
            )

    async def handle_timer(self, channel_id, message_id, role_id, user_id, add, sleep_for):
        await asyncio.sleep(sleep_for)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        guild = channel.guild
        member = guild.get_member(user_id)
        role = guild.get_role(role_id)
        if not member or not role:
            return
        reference = None
        try:
            ref = await channel.fetch_message(message_id)
            reference = ref
        except (NotFound, Forbidden):
            pass
        with suppress(Exception):
            if add:
                if role in member.roles:
                    return
                await member.add_roles(role)
                msg = f"Gave **{role.name}** to **@{member.name}**"
            else:
                if role not in member.roles:
                    return
                await member.remove_roles(role)
                msg = f"Removed **{role.name}** from @{member.name}"
            await channel.send(msg, reference=reference)

    @commands.command(name="rename", description="Renames a user, role, or channel")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def rename(self, ctx, target: Union[Member, Role, TextChannel], *, new_name=""):
        if not isinstance(target, Member) and not new_name:
            return await ctx.send("You need to specify the new name after the target you're renaming")
        old_name = str(target.display_name if hasattr(target, "display_name") else target.name)
        new_name = new_name[:28]
        try:
            if isinstance(target, Member):
                if target.top_role.position >= ctx.author.top_role.position:
                    return await ctx.send("That user's above your paygrade, take a seat")
                await target.edit(nick=new_name)
            elif isinstance(target, Role):
                if target.position >= ctx.author.top_role.position:
                    return await ctx.send("This role is above your paygrade, take a seat")
                await target.edit(name=new_name)
            elif isinstance(target, TextChannel):
                if not target.permissions_for(ctx.author).manage_channels:
                    return await ctx.send("You don't have the required permissions to edit that channel")
                await target.edit(name=new_name)
        except Forbidden:
            await ctx.send("I'm missing permissions to change that targets name")
        else:
            await ctx.send(f"Renamed {target.mention} from {old_name}")

    async def warn_user(self, channel, user, reason, context):
        guild = channel.guild
        guild_id = str(guild.id)
        user_id = str(user.id)
        if guild_id not in self.config:
            self.config[guild_id] = self.template
        warns = self.config[guild_id]["warns"]
        async with self.bot.utils.open("./data/userdata/config.json", "r") as f:
            config = await self.bot.load(await f.read())  # type: dict
        punishments = ["None", "None", "Mute", "Kick", "Softban", "Ban"]
        if guild_id in config["warns"]["punishments"]:
            punishments = config["warns"]["punishments"][guild_id]
        if user_id not in warns:
            warns[user_id] = []
        if not isinstance(warns[user_id], list):
            warns[user_id] = []

        warns[user_id].append([reason, str(datetime.now())])
        total_warns = 0
        for reason, time in warns[user_id]:
            time = datetime.strptime(time.replace("+00:00", ""), "%Y-%m-%d %H:%M:%S.%f")
            if (datetime.now() - time).days > 30:
                if guild_id in config["warns"]["expire"]:
                    warns[user_id].remove([reason, str(time)])
                    continue
            total_warns += 1
        await self.save_data()

        if total_warns > len(punishments):
            punishment = punishments[-1:][0]
        else:
            punishment = punishments[total_warns - 1]
        if total_warns >= len(punishments):
            next_punishment = punishments[-1:][0]
        else:
            next_punishment = punishments[total_warns]

        e = discord.Embed(color=colors.fate)
        url = self.bot.user.display_avatar.url
        if user.display_avatar.url:
            url = user.display_avatar.url
        e.set_author(name=f"{user.name} has been warned", icon_url=url)
        e.description = f"**Warns:** [`{total_warns}`] "
        if punishment != "None":
            e.description += f"**Punishment:** [`{punishment}`]"
        if punishment == "None" and next_punishment != "None":
            e.description += f"**Next Punishment:** [`{next_punishment}`]"
        else:
            if punishment == "None" and next_punishment == "None":
                e.description += f"**Reason:** [`{reason}`]"
            if next_punishment != "None":
                e.description += f"\n**Next Punishment:** [`{next_punishment}`]"
        case = await self.cases.add_case(
            int(guild_id), user.id, "warn", reason, context.message.jump_url, context.author.id
        )
        e.description += f" [Case #{case}]"
        if punishment != "None" and next_punishment != "None":
            e.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=e)
        try:
            await user.send(f"You've been warned in **{channel.guild}** for `{reason}`")
        except:
            pass
        if punishment == "Mute":
            mute_role = None
            for role in channel.guild.roles:
                if role.name.lower() == "muted":
                    mute_role = role
            if not mute_role:
                bot = discord.utils.get(guild.members, id=self.bot.user.id)
                perms = list(perm for perm, value in bot.guild_permissions if value)
                if "manage_channels" not in perms:
                    return await channel.send(
                        "No muted role found, and I'm missing manage_channel permissions to set one up"
                    )
                mute_role = await guild.create_role(
                    name="Muted", color=discord.Color(colors.black)
                )
                with suppress(Exception):
                    for chnl in guild.text_channels:
                        await chnl.set_permissions(mute_role, send_messages=False)
                    for chnl in guild.voice_channels:
                        await chnl.set_permissions(mute_role, speak=False)
            if mute_role in user.roles:
                return await channel.send(f"{user.display_name} is already muted")
            user_roles = []
            for role in user.roles:
                try:
                    await user.remove_roles(role)
                    user_roles.append(role.id)
                    await asyncio.sleep(0.5)
                except:
                    pass
            try:
                await user.add_roles(mute_role)
            except:
                return await channel.send(f"Couldn't find and mute {user}")
            timer_info = {
                "action": "mute",
                "channel": channel.id,
                "user": user.id,
                "end_time": str(datetime.now() + timedelta(seconds=7200)),
                "mute_role": mute_role.id,
                "roles": user_roles,
            }
            if user_id not in self.config[guild_id]["timers"]:
                self.config[guild_id]["timers"][user_id] = []
            self.config[guild_id]["timers"][user_id].append(timer_info)
            await self.save_data()
            await asyncio.sleep(7200)
            if mute_role in user.roles:
                with suppress(Forbidden, NotFound):
                    await user.remove_roles(mute_role)
                    await channel.send(f"**Unmuted:** {user.name}")
            if (
                user_id in self.config[guild_id]["timers"]
                and timer_info in self.config[guild_id]["timers"][user_id]
            ):
                self.config[guild_id]["timers"][user_id].remove(timer_info)
            if not self.config[guild_id]["timers"][user_id]:
                del self.config[guild_id]["timers"][user_id]
            await self.save_data()
        if punishment == "Kick":
            try:
                await guild.kick(user, reason="Reached Sufficient Warns")
            except:
                await channel.send("Failed to kick this user")
        if punishment == "Softban":
            try:
                await guild.kick(user, reason="Softban - Reached Sufficient Warns")
                await guild.unban(user, reason="Softban")
            except:
                await channel.send("Failed to softban this user")
        if punishment == "Ban":
            try:
                await guild.ban(user, reason="Reached Sufficient Warns")
            except:
                await channel.send("Failed to ban this user")

    @commands.command(name="warn", description="Dms and logs a warn on the user")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_warn_permission()
    async def warn(self, ctx, users: Greedy[discord.Member], *, reason="Unspecified"):
        if not users:
            return await ctx.send("You need to specify who to warn")
        if len(users) > 1 and len(ctx.message.raw_mentions) < len(users):
            users = users[:1]
        for user in list(users):
            if user.bot:
                await ctx.send(f"You can't warn {user.mention} because they're a bot")
                continue
            if ctx.author.id != ctx.guild.owner.id:
                if user.top_role.position >= ctx.author.top_role.position:
                    await ctx.send(f"{user.name} is above your paygrade, take a seat")
                    continue
            self.bot.loop.create_task(self.warn_user(ctx.channel, user, reason, ctx))

    @commands.command(name="delwarn", aliases=["del-warn"], description="Removes a users warn")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_warn_permission()
    @commands.bot_has_permissions(add_reactions=True)
    async def delwarn(self, ctx, user: Greedy[discord.Member], *, partial_reason):
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✔", "❌"]

        guild_id = str(ctx.guild.id)
        for user in list(set(user)):
            user_id = str(user.id)
            if user_id not in self.config[guild_id]["warns"]:
                await ctx.send(f"{user} has no warns")
                continue
            for reason, warn_time in self.config[guild_id]["warns"][user_id]:
                if partial_reason in reason:
                    e = discord.Embed(color=colors.fate)
                    e.set_author(name="Is this the right warn?")
                    e.description = reason
                    msg = await ctx.send(embed=e)
                    await msg.add_reaction("✔")
                    await asyncio.sleep(0.5)
                    await msg.add_reaction("❌")
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add", timeout=60.0, check=check
                        )
                    except asyncio.TimeoutError:
                        await msg.edit(
                            content="Inactive Message: timed out due to no response"
                        )
                        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                            await msg.clear_reactions()
                        return
                    else:
                        with suppress(ValueError, NotFound, Forbidden):
                            if str(reaction.emoji) == "✔":
                                self.config[guild_id]["warns"][user_id].remove(
                                    [reason, warn_time]
                                )
                                await self.save_data()
                                await ctx.message.delete()
                                await msg.delete()
                            else:
                                await msg.delete()
                        break

    @commands.command(name="clearwarns", aliases=["clear-warns"], description="Erases all of a users warns")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @check_if_running()
    @has_warn_permission()
    async def clear_warns(self, ctx, user: Greedy[discord.Member]):
        guild_id = str(ctx.guild.id)
        for user in list(set(user)):
            user_id = str(user.id)
            if user_id not in self.config[guild_id]["warns"]:
                await ctx.send(f"{user} has no warns")
                continue
            if (
                user.top_role.position >= ctx.author.top_role.position
                and ctx.author.id != ctx.guild.owner.id
            ):
                return await ctx.send(f"{user} is above your paygrade, take a seat")
            del self.config[guild_id]["warns"][user_id]
            await ctx.send(f"Cleared {user}'s warns")
            await self.save_data()

    @commands.command(name="warns", description="Shows all a users warns")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def _warns(self, ctx, *, user=None):
        if not user:
            user = ctx.author
        else:
            user = await self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        guild_id = str(ctx.guild.id)
        user_id = str(user.id)
        if user_id not in self.config[guild_id]["warns"]:
            self.config[guild_id]["warns"][user_id] = []
        warns = 0
        reasons = ""
        async with self.bot.utils.open("./data/userdata/config.json", "r") as f:
            conf = await self.bot.load(await f.read())
        for reason, time in self.config[guild_id]["warns"][user_id]:
            time = datetime.strptime(time.replace("+00:00", ""), "%Y-%m-%d %H:%M:%S.%f")
            if (datetime.now() - time).days > 30:
                if (
                    guild_id in conf
                    and "expire" in conf[guild_id]["warns"]
                    and conf[guild_id]["warns"]["expire"] == "True"
                ):
                    self.config[guild_id]["warns"][user_id].remove([reason, time])
                    continue
            warns += 1
            reasons += f"\n• `{reason}`"
        e = discord.Embed(color=colors.fate)
        url = self.bot.user.display_avatar.url
        if user.display_avatar.url:
            url = user.display_avatar.url
        e.set_author(name=f"{user.name}'s Warns", icon_url=url)
        e.description = f"**Total Warns:** [`{warns}`]" + reasons
        await ctx.send(embed=e)


class MuteView(ui.View):
    def __init__(self, ctx, user: Union[User, Member], case: int, reason: Optional[str], timer: Optional[int]):
        self.ctx = ctx
        self.user = user
        self.case = case
        self.reason = reason
        self.timer = timer
        super().__init__(timeout=45)

        if timer and reason:
            self.stop()
            return

        if not reason:
            self.reason_button = ui.Button(label="Set Reason", style=ButtonStyle.blurple)
            self.reason_button.callback = self.set_reason
            self.add_item(self.reason_button)

        if not timer:
            self.timer_button = ui.Button(label="Set Timer", style=ButtonStyle.blurple)
            self.timer_button.callback = self.set_timer
            self.add_item(self.timer_button)

    async def on_error(self, error, item, interaction):
        if not isinstance(error, NotFound):
            raise

    async def interaction_check(self, interaction):
        """ Ensure the interaction is from the user who initiated the view """
        if interaction.user.id != self.ctx.author.id:
            with suppress(Exception):
                await interaction.response.send_message(
                    "Only the user who initiated this command can interact", ephemeral=True
                )
            return False
        return True

    async def set_timer(self, interaction: Interaction):
        view = TimerView(self.ctx, self.case, self)
        self.remove_item(self.timer_button)
        await interaction.response.edit_message(view=view)

    async def set_reason(self, interaction: Interaction):
        view = ReasonView(self.ctx, self.case, self)
        self.remove_item(self.reason_button)
        await interaction.response.edit_message(view=view)


class TimerView(ui.View):
    class SelectOptions(ui.Select):
        timers: List[Tuple[Union[str, int]]] = [
            ("Cancel", 0),
            ("5 Minutes", 60 * 5),
            ("15 Minutes", 60 * 15),
            ("30 Minutes", 60 * 30),
            ("45 Minutes", 60 * 45),
            ("1 Hour", 60 * 60),
            ("2 Hours", 60 * 60 * 2),
            ("6 Hours", 60 * 60 * 6),
            ("12 Hours", 60 * 60 * 12),
            ("1 Day", 60 * 60 * 24),
            ("2 Days", 60 * 60 * 24 * 2),
            ("1 Week", 60 * 60 * 24 * 7)
        ]

        def __init__(self, ctx: commands.Context, case: int, home_view: MuteView):
            self.ctx = ctx
            self.bot = ctx.bot
            self.case = case
            self.home_view = home_view

            options = [
                SelectOption(label=label, emoji="⏰", value=str(timer))
                for label, timer in self.timers
            ]
            super().__init__(
                placeholder="Select from presets",
                options=options,
                min_values=1,
                max_values=1
            )

        async def callback(self, interaction: Interaction):
            if not await self.home_view.interaction_check(interaction):
                return
            duration = int(interaction.data["values"][0])
            if duration == 0:
                return await interaction.response.edit_message(view=self.home_view)

            mod: Moderation = self.bot.cogs["Moderation"]  # type: ignore
            guild_id = str(self.ctx.guild.id)

            user = self.home_view.user
            mute_role = await self.bot.attrs.get_mute_role(self.ctx.guild, upsert=True)
            await user.add_roles(mute_role)

            # Update the mute if one is already running
            if mute_role in user.roles:
                user_id = str(user.id)
                if guild_id in mod.tasks and user_id in mod.tasks[guild_id]:
                    mod.tasks[guild_id][user_id].cancel()
                    del mod.tasks[guild_id][user_id]

            timer_info = {
                "channel": self.ctx.channel.id,
                "user": user.id,
                "end_time": now() + duration,
                "mute_role": mute_role.id,
                "removed_roles": [],
            }
            mod.config[guild_id]["mute_timers"][str(user.id)] = timer_info
            await mod.save_data()
            task = self.bot.loop.create_task(
                mod.handle_mute_timer(guild_id, str(user.id), timer_info)
            )
            if guild_id not in mod.tasks:
                mod.tasks[guild_id] = {}
            mod.tasks[guild_id][str(user.id)] = task

            expanded_form = format_date(datetime.now() - timedelta(seconds=duration))
            await interaction.response.send_message(
                f"Updated the mute for {user.mention} to {expanded_form}",
                mentions=discord.AllowedMentions.all()
            )
            await interaction.message.edit(view=self.home_view)

    def __init__(self, ctx: commands.Context, case: int, home_view: MuteView):
        super().__init__(timeout=45)
        self.add_item(self.SelectOptions(ctx, case, home_view))

    async def on_error(self, error, item, interaction):
        if not isinstance(error, NotFound):
            raise


class ReasonView(ui.View):
    class SelectOptions(ui.Select):
        preset: List[Tuple[Union[str, str]]] = [
            ("❎", "Cancel"),
            ("🔊", "Spamming"),
            ("⚔", "Raiding"),
            ("👊", "Harassment"),
            ("👮‍♂️", "Discord TOS")
        ]

        def __init__(self, ctx: commands.Context, case: int, home_view: MuteView):
            self.ctx = ctx
            self.case = case
            self.home_view = home_view

            options = [
                SelectOption(label=reason, emoji=emoji, value=reason)
                for emoji, reason in self.preset
            ]
            super().__init__(
                placeholder="Select from presets",
                options=options,
                min_values=1,
                max_values=1
            )

        async def callback(self, interaction: Interaction):
            if not await self.home_view.interaction_check(interaction):
                return
            reason = interaction.data["values"][0]
            if reason == "Cancel":
                return await interaction.response.edit_message(view=self.home_view)

            async with self.ctx.bot.utils.cursor() as cur:
                await cur.execute(
                    f"update cases set "
                    f"reason = '{self.ctx.bot.encode(reason)}' "
                    f"where guild_id = {self.ctx.guild.id} "
                    f"and case_number = {self.case};"
                )

            await interaction.response.send_message(f"Updated the reason to {reason}", ephemeral=True)
            await interaction.message.edit(view=self.home_view)

    def __init__(self, ctx: commands.Context, case: int, home_view: MuteView):
        super().__init__(timeout=45)
        self.add_item(self.SelectOptions(ctx, case, home_view))

    async def on_error(self, error, item, interaction):
        if not isinstance(error, NotFound):
            raise


def setup(bot):
    cls = Moderation(bot)
    globals()["cls"] = cls
    bot.add_cog(cls)
