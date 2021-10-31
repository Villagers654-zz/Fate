"""
cogs.moderation.logger
~~~~~~~~~~~~~~~~~~~~~~~

A cog for logging event related actions to a text channel(s)

:copyright: (C) 2020-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import asyncio
from io import BytesIO
from os import path
import json
from datetime import datetime, timezone, timedelta
from time import time
from aiohttp.client_exceptions import ClientOSError
from contextlib import suppress
import traceback
from typing import *

from discord.ext import commands
import discord
from discord import AuditLogAction as audit, File
from discord.errors import NotFound, Forbidden, HTTPException
from PIL import Image

from botutils.colors import *
from botutils import get_prefix, split, get_time
from classes import IgnoredExit


def is_guild_owner():
    async def predicate(ctx):
        has_perms = ctx.author.id == ctx.guild.owner.id
        if not has_perms:
            await ctx.send("You need to be the owner of the server to use this")
        return has_perms

    return commands.check(predicate)


already_checked: Dict[int, bool] = {}


async def remove_after(message_id: int) -> None:
    await asyncio.sleep(3600)
    already_checked.pop(message_id, None)


async def belongs_to_module(bot, message) -> bool:
    """ Checks if a message belongs to a module """
    if message.id in already_checked:
        return already_checked[message.id]
    # Remove from cache after an hour
    bot.loop.create_task(remove_after(message.id))
    # Check if it's a giveaway message
    for data in bot.cogs["giveaways"].values():
        if message.id == data["message"]:
            already_checked[message.id] = True
            return True
    # Default to not belonging to a module
    already_checked[message.id] = False
    return False


class Log(object):
    """ A dataclass-like object for sorting information """
    def __init__(self, ltype, embed, files=(), created_at=None):
        """
        :param str ltype: The category the log goes into
        :param discord.Embed embed: The embed to send to the log channel
        :param List[File] files: Optional list of files to send alongside the embed
        :param float created_at: When the log event occured
        """
        self.type = ltype
        self.embed = embed
        self.files = files
        self.created_at = created_at
        if not self.created_at:
            self.created_at = time()


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_types = [
            "everyone_mention",
            "message_edit",
            "message_delete",
            "attachment_delete",
            "embed_hidden",
            "message_pin",
            "message_purge",
            "reactions_clear",
            "server_rename",
            "new_server_icon",
            "new_server_banner",
            "new_server_splash",
            "region_change",
            "afk_timeout_change",
            "afk_channel_change",
            "new_owner",
            "features_change",
            "new_boost_tier",
            "boost",
            "channel_create",
            "channel_delete",
            "channel_update",
            "role_create",
            "role_delete",
            "role_move"
            "role_update",
            "integrations_update",
            "webhook_update",
            "member_join",
            "member_leave",
            "member_kick",
            "member_ban",
            "bot_add",
            "nick_change",
            "member_roles_update",
            "emoji_create",
            "emoji_delete",
            "emoji_rename"
        ]

        if "logger" not in bot.tasks:
            bot.tasks["logger"] = {}

        self.config = {}
        self.path = "./data/userdata/secure-log.json"
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)  # type: dict

        self.queue = {g_id: asyncio.Queue(maxsize=64) for g_id in self.config.keys()}
        self.recent_logs = {
            guild_id: [] for guild_id in self.config.keys()
        }

        self.static = {}
        self.wait_queue = {}

        self.invites = {}
        if self.bot.is_ready():
            self.bot.loop.create_task(self.init_invites())
            for guild_id in self.config.keys():
                if guild_id in bot.tasks["logger"]:
                    bot.tasks["logger"][guild_id].cancel()
                task = self.bot.loop.create_task(self.start_queue(guild_id))
                bot.tasks["logger"][guild_id] = task

        self.pool = {}

    def cog_unload(self):
        for task_id, task in self.bot.tasks["logger"].items():
            if not task.done():
                task.cancel()
            del self.bot.tasks["logger"][task_id]

    def is_enabled(self, guild_id):
        return str(guild_id) in self.config

    @property
    def template(self):
        return {
            "channel": None,
            "channels": {},
            "secure": False,
            "ignored_channels": [],
            "ignored_bots": [],
            "disabled_logs": []
        }

    def put_nowait(self, guild_id, log):
        if guild_id not in self.queue:
            return
        with suppress(asyncio.QueueFull):
            self.queue[guild_id].put_nowait(log)

    async def save_data(self) -> None:
        """ Saves local variables """
        await self.bot.utils.save_json(self.path, self.config)

    async def ensure_channels(self, guild):
        """Sets up channels in instances of them missing"""
        guild_id = str(guild.id)
        channel = self.bot.get_channel(self.config[guild_id]["channel"])

        if not channel:
            if not self.config[guild_id]["secure"]:
                return await self.destruct(guild_id)
            if not guild or not guild.me:
                return await self.destruct(guild_id)
            if not guild.me.guild_permissions.manage_channels:
                result = await self.wait_for_permissions(
                    guild, "manage_channels"
                )
                if not result:
                    return await self.destruct(guild_id)
            try:
                channel = await self.bot.fetch_channel(
                    self.config[guild_id]["channel"]
                )
            except NotFound as err:
                channel = await guild.create_text_channel(name="bot-logs")
                await channel.send(f"Couldn't get the old channel with ID: {self.config[guild_id]['channel']}\n{err}")
            self.config[guild_id]["channel"] = channel.id

        # Remove channels that redirect logs if they're missing
        for ltype, channel_id in list(self.config[guild_id]["channels"].items()):
            if not self.bot.get_channel(channel_id):
                del self.config[guild_id]["channels"][ltype]

    async def destruct(self, guild_id):
        if guild_id in self.queue:
            del self.queue[guild_id]
        if guild_id in self.recent_logs:
            del self.recent_logs[guild_id]
        if guild_id in self.bot.tasks["logger"]:
            self.bot.tasks["logger"][guild_id].cancel()
            del self.bot.tasks["logger"][guild_id]
        await self.save_data()

    async def wait_for_permissions(self, guild, permission, channel=None, host=False):
        def perms():
            return channel.permissions_for(guild.me) if channel else guild.me.guild_permissions

        if not guild or not guild.me:
            raise IgnoredExit
        if getattr(perms(), permission):
            return True

        guild_id = str(guild.id)
        if guild_id not in self.pool or not host:
            if guild_id not in self.pool:
                coro = self.wait_for_permissions(guild, permission, channel, host=True)
                task = self.bot.loop.create_task(coro)
                self.pool[guild_id] = task
            return await self.pool[guild_id]

        owner = guild.owner  # type: discord.Member
        lmt = datetime.now(tz=timezone.utc) - timedelta(days=1)
        if owner.dm_channel:
            msgs = await owner.dm_channel.history(limit=1, after=lmt).flatten()
            if not msgs or "I'm missing" in msgs[0].content:
                with suppress(Forbidden, NotFound, AttributeError):
                    await owner.send(
                        f"I need {permission} permissions in {guild} for the logger module to function. "
                        f"Until that's satisfied, i'll keep a maximum 12 hours of logs in queue"
                    )

        for _attempt in range(12 * 60):  # Timeout of 12 hours
            if not guild or not guild.me:
                await self.destruct(guild_id)
                raise IgnoredExit
            if getattr(perms(), permission):
                del self.pool[guild_id]
                return True
            await asyncio.sleep(60)
        else:
            await self.destruct(guild_id)
            raise IgnoredExit

    async def start_queue(self, guild_id: str) -> None:
        guild = self.bot.get_guild(int(guild_id))
        for _ in range(60):
            if guild:
                break
            await asyncio.sleep(60)
            guild = self.bot.get_guild(int(guild_id))
        else:
            return await self.destruct(guild_id)

        while True:  # Listen for new logs
            if guild_id not in self.queue:
                return
            log = await self.queue[guild_id].get()  # type: Log
            if log.type in self.config[guild_id]["disabled"]:
                self.queue[guild_id].task_done()
                continue

            if isinstance(log.embed, discord.Embed):
                log.embed.timestamp = datetime.fromtimestamp(log.created_at)
                for i, field in enumerate(log.embed.fields):
                    await asyncio.sleep(0)
                    if not field.value or field.value is discord.Embed.Empty:
                        self.bot.log(
                            f"A log of type {log.type} had no value", "CRITICAL"
                        )
                        for chunk in split(str(log.embed.to_dict()), 1900):
                            self.bot.log(chunk, "CRITICAL")
                        log.embed.fields[i].value = "None"
                    if len(field.value) > 1024:
                        log.embed.remove_field(i)
                        for it, chunk in enumerate(split(field.value, 1024)):
                            log.embed.insert_field_at(
                                index=i + it,
                                name=field.name,
                                value=chunk,
                                inline=field.inline,
                            )
                        self.bot.log(
                            f"A log of type {log.type} had had a huge value",
                            "CRITICAL",
                        )
                        for chunk in split(str(log.embed.to_dict()), 1900):
                            self.bot.log(chunk, "CRITICAL")

            # Permission checks to ensure the secure features can function
            if self.config[guild_id]["secure"]:
                await self.wait_for_permissions(guild, "administrator")

            # Get the channel this log will be sent to
            await self.ensure_channels(guild)
            channel = self.bot.get_channel(self.config[guild_id]["channel"])
            if log.type in self.config[guild_id]["channels"]:
                channel = self.bot.get_channel(self.config[guild_id]["channels"][log.type])

            # Ensure basic send-embed level permissions
            await self.wait_for_permissions(guild, "send_messages", channel)
            await self.wait_for_permissions(guild, "embed_links", channel)

            # Ensure this still exists
            if guild_id not in self.recent_logs:
                self.recent_logs[guild_id] = []

            ignored_exceptions = (
                discord.errors.Forbidden,
                discord.errors.NotFound,
                discord.errors.HTTPException,
                ConnectionResetError,
                ClientOSError
            )

            try:
                await channel.send(embed=log.embed, files=log.files)
            except ignored_exceptions:
                e = discord.Embed(title="Failed to send embed")
                e.set_author(name=guild if guild else "Unknown Guild")
                e.description = traceback.format_exc()

                embed_data = str(json.dumps(log.embed.to_dict(), indent=2))
                for text_group in split(embed_data, 1024):
                    e.add_field(name="Embed Data", value=text_group, inline=False)

                e.set_footer(text=str(guild.id) if guild else "Unknown Guild")

                debug = self.bot.get_channel(self.bot.config["debug_channel"])
                try:
                    await debug.send(embed=e)
                except ignored_exceptions:
                    self.queue[guild_id].task_done()
                continue

            self.recent_logs[guild_id].append([log.embed, log.created_at])
            for log in list(self.recent_logs[guild_id]):
                await asyncio.sleep(0)
                if time() - log[1] > 60 * 60 * 24:
                    self.recent_logs[guild_id].remove(log)

            self.queue[guild_id].task_done()
            await asyncio.sleep(1)

    async def init_invites(self) -> None:
        """ Indexes each servers invites """
        for guild_id in list(self.config.keys()):
            guild = self.bot.get_guild(int(guild_id))
            if isinstance(guild, discord.Guild):
                if guild_id not in self.invites:
                    self.invites[guild_id] = {}
                try:
                    invites = await guild.invites()
                    for invite in invites:
                        self.invites[guild_id][invite.url] = invite.uses
                except discord.errors.Forbidden:
                    pass

    @property
    def past(self):
        """ gets the time 2 seconds ago in utc for audit searching """
        return datetime.now(tz=timezone.utc) - timedelta(seconds=10)

    async def search_audit(self, guild, *actions) -> dict:
        """ Returns the latest entry from a list of actions """
        dat = {
            "action": None,
            "user": "Unknown",
            "actual_user": None,
            "target": "Unknown",
            "icon_url": guild.icon.url if guild.icon else None,
            "thumbnail_url": guild.icon.url if guild and guild.icon else None,
            "reason": None,
            "extra": None,
            "changes": None,
            "before": None,
            "after": None,
            "recent": False,
        }
        await self.wait_for_permissions(guild, "view_audit_log")
        with suppress(Exception):
            async for entry in guild.audit_logs(limit=5):
                with suppress(Exception):
                    if entry.created_at > self.past and any(
                        entry.action.name == action.name
                        for action in actions
                          if hasattr(entry.action, "name")
                    ):
                        dat["action"] = entry.action
                        if entry.user:
                            dat["user"] = entry.user.mention
                            dat["actual_user"] = entry.user
                            dat["thumbnail_url"] = entry.user.display_avatar.url
                        if entry.target and isinstance(entry.target, discord.Member):
                            dat["target"] = entry.target.mention
                            dat["icon_url"] = entry.target.display_avatar.url
                        elif entry.target:
                            dat["target"] = entry.target
                        else:
                            if entry.user:
                                dat["icon_url"] = entry.user.display_avatar.url
                        dat["reason"] = entry.reason
                        dat["extra"] = entry.extra
                        dat["before"] = entry.before
                        dat["after"] = entry.after
                        dat["recent"] = True
                        break
        return dat

    @commands.group(name="logger", aliases=["log", "logging"], description="Shows how to use the module")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def logger(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=fate)
            e.set_author(name="| Action Logger", icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.display_avatar.url)
            e.set_thumbnail(url=self.bot.user.display_avatar.url)
            e.description = "*A more detailed audit log that logs changes to the server and more to ~~a~~ dedicated channel(s)*"
            e.add_field(
                name="◈ Security - Optional",
                value=">>> Logs can't be deleted by anyone, they aren't purge-able, and it "
                      "re-creates deleted log channels and resends the last 12 hours of logs",
                inline=False,
            )
            p = get_prefix(ctx)
            e.add_field(
                name="◈ Commands",
                value=f"{p}log enable - `creates a log`"
                      f"\n{p}log disable - `disables the log`"
                      f"\n{p}log events - `list event names`"
                      f"\n{p}log enable [event]"
                      f"\n{p}log disable [event]"
                      f"\n{p}log move [event] #channel"
                      f"\n{p}log security - `toggles security`"
                      f"\n{p}log ignore #channel - `ignore chat logs`"
                      f"\n{p}log ignore @bot - `ignores bot spam`"
                      f"\n{p}log config `current setup overview`",
                inline=False,
            )
            icon_url = "https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png"
            e.set_footer(
                text="Security and Multi-Log are off by default", icon_url=icon_url
            )
            await ctx.send(embed=e)

    @logger.group(name="enable", description="Enables the module and creates a log channel")
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx, event=None):
        """ Creates a multi-log """
        guild_id = str(ctx.guild.id)
        if event:
            if guild_id not in self.config:
                return await ctx.send("Logger isn't enabled")
            if event not in self.log_types:
                return await ctx.send("That's not a valid event. Use `.events` to view the available log types")
            if event not in self.config[guild_id]["disabled"]:
                return await ctx.send("That event isn't disabled")
            self.config[guild_id]["disabled"].remove(event)
            await ctx.send(f"Enabled {event}")
            return await self.save_data()
        if guild_id in self.config:
            return await ctx.send("Logger is already enabled")
        perm_error = (
            "I can't send messages in the channel I made\n"
            "If you want me to use your own, try `.logger setchannel`"
        )
        try:
            channel = await ctx.guild.create_text_channel(name="discord-log")
        except discord.errors.Forbidden:
            return await ctx.send(perm_error)
        if not channel.permissions_for(ctx.guild.me).send_messages:
            try:
                await ctx.send(perm_error)
            except discord.errors.Forbidden:
                pass
            return
        if not channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.send("I need embed_links permission(s) in that channel")
        if not channel.permissions_for(ctx.guild.me).attach_files:
            return await ctx.send("I need attach_files permission(s) in that channel")
        self.config[guild_id] = {
            "channel": channel.id,
            "channels": {},
            "secure": False,
            "ignored_channels": [],
            "ignored_bots": [],
            "disabled": [],
            "themes": {}
        }
        if guild_id not in self.queue:
            self.queue[guild_id] = asyncio.Queue(maxsize=64)
        if guild_id in self.bot.tasks["logger"] and not self.bot.tasks["logger"][guild_id].done():
            self.bot.tasks["logger"][guild_id].cancel()
        task = self.bot.loop.create_task(self.start_queue(guild_id))
        self.bot.tasks["logger"][guild_id] = task
        await ctx.send("Enabled Logger")
        await self.save_data()

    @logger.command(name="disable", description="Disables the module")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx, event=None):
        """Disables the log"""
        guild_id = str(ctx.guild.id)
        if event:
            if guild_id not in self.config:
                return await ctx.send("Logger isn't enabled")
            if event not in self.log_types:
                return await ctx.send("That's not a valid event. Use `.events` to view the available log types")
            if event in self.config[guild_id]["disabled"]:
                return await ctx.send("That event is already disabled")
            self.config[guild_id]["disabled"].append(event)
            await ctx.send(f"Disabled {event}")
            return await self.save_data()
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]["secure"]:
            if ctx.author.id != ctx.guild.owner.id:
                return await ctx.send(
                    "Due to security settings, only the owner of the server can use this"
                )
        del self.config[guild_id]
        if guild_id in self.queue:
            del self.queue[guild_id]
        await ctx.send("Disabled Logger")
        await self.save_data()

    @logger.group(name="setchannel", aliases=["set-channel"], description="Enables the module in a specific channel")
    @commands.has_permissions(administrator=True)
    async def _set_channel(self, ctx, channel: discord.TextChannel = None):
        """ Creates a multi-log """
        if not channel:
            channel = ctx.channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            try:
                await ctx.send("I can't send messages in that channel")
            except discord.errors.Forbidden:
                pass
            return
        if not channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.send("I need embed_links permission(s) in that channel")
        if not channel.permissions_for(ctx.guild.me).attach_files:
            return await ctx.send("I need attach_files permission(s) in that channel")
        guild_id = str(ctx.guild.id)
        if guild_id in self.config:
            self.config[guild_id]["channel"] = channel.id
        else:
            self.config[guild_id] = {
                "channel": channel.id,
                "channels": {},
                "secure": False,
                "ignored_channels": [],
                "ignored_bots": [],
                "disabled": [],
                "themes": {}
            }
        if guild_id not in self.queue:
            self.queue[guild_id] = asyncio.Queue(maxsize=64)
        if guild_id in self.bot.tasks["logger"] and not self.bot.tasks["logger"][guild_id].done():
            self.bot.tasks["logger"][guild_id].cancel()
        task = self.bot.loop.create_task(self.start_queue(guild_id))
        self.bot.tasks["logger"][guild_id] = task
        await ctx.send(f"Enabled Logger in {channel.mention}")
        await self.save_data()

    @logger.command(name="move", description="Sets a log type to send to a diff channel")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def _move(self, ctx, log_type=None, channel: discord.TextChannel = None):
        """ Switches a log between multi and single """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if not log_type or not channel:
            return await ctx.send("Usage: `.log move event_name #channel`\n"
                                  "the event name can be found with `.log events`")
        if log_type not in self.log_types:
            return await ctx.send(
                f"That isn't a valid log type. Here's a list of the accepted types: "
                f"{', '.join(f'`{ltype}`' for ltype in self.log_types)}"
            )
        await self.ensure_channels(ctx.guild)
        if channel.id == self.config[guild_id]["channel"]:
            if log_type not in self.config[guild_id]["channels"]:
                return await ctx.send(f"{log_type} is already in {channel.mention}")
            del self.config[guild_id]["channels"][log_type]
        else:
            self.config[guild_id]["channels"][log_type] = channel.id
        await ctx.send(f"Moved the {log_type} log to {channel.mention}")
        await self.save_data()

    @logger.command(name="events", description="Lists all the names of logs")
    @commands.cooldown(1, 25, commands.BucketType.channel)
    async def events(self, ctx):
        await ctx.send(
            f"Log types: {', '.join(f'`{ltype}`' for ltype in self.log_types)}"
        )

    @logger.command(name="security", description="Toggles resending deleted logs")
    @is_guild_owner()
    @commands.bot_has_permissions(administrator=True)
    async def _toggle_security(self, ctx):
        """ Toggles whether or not to keep the log secure """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("You need to enable logger to use this")
        if self.config[guild_id]["secure"]:
            self.config[guild_id]["secure"] = False
            await ctx.send("Disabled secure features")
        else:
            self.config[guild_id]["secure"] = True
            await ctx.send("Enabled secure features")
        await self.save_data()

    @logger.command(name="ignore", description="Ignores chat events from a channel")
    @commands.has_permissions(administrator=True)
    async def _ignore(self, ctx):
        """ ignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]["secure"] and ctx.author.id != ctx.guild.owner.id:
            return await ctx.send(
                "Due to security settings, only the owner of the server can use this"
            )
        for member in ctx.message.mentions:
            if member.id in self.config[guild_id]["ignored_bots"]:
                await ctx.send(f"{member.mention} is already ignored")
            elif not member.bot:
                await ctx.send(f"{member.mention} is not a bot")
            else:
                self.config[guild_id]["ignored_bots"].append(member.id)
                await ctx.send(
                    f"I'll now ignore chat related events from {member.mention}"
                )
        for channel in ctx.message.channel_mentions:
            if channel.id in self.config[guild_id]["ignored_channels"]:
                await ctx.send(f"{channel.mention} is already ignored")
            else:
                self.config[guild_id]["ignored_channels"].append(channel.id)
                await ctx.send(
                    f"I'll now ignore chat related events from {channel.mention}"
                )
        await self.save_data()

    @logger.command(name="unignore", description="Unignores chat events from a channel")
    @commands.has_permissions(administrator=True)
    async def _unignore(self, ctx):
        """ unignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]["secure"] and ctx.author.id != ctx.guild.owner.id:
            return await ctx.send(
                "Due to security settings, only the owner of the server can use this"
            )
        for member in ctx.message.mentions:
            if member.id not in self.config[guild_id]["ignored_bots"]:
                await ctx.send(f"{member.mention} isn't ignored")
            self.config[guild_id]["ignored_bots"].remove(member.id)
            await ctx.send(
                f"I'll no longer ignore chat related events from {member.mention}"
            )
        for channel in ctx.message.channel_mentions:
            if channel.id not in self.config[guild_id]["ignored_channels"]:
                await ctx.send(f"{channel.mention} isn't ignored")
            else:
                self.config[guild_id]["ignored_channels"].remove(channel.id)
                await ctx.send(
                    f"I'll no longer ignore chat related events from {channel.mention}"
                )
        await self.save_data()

    @logger.command(name="config", description="Shows the current module config")
    async def _config(self, ctx):
        """ sends an overview of the servers current config """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("There's currently no config for this server")
        e = discord.Embed(color=fate)
        e.set_author(name="Logger Config", icon_url=ctx.guild.owner.display_avatar.url)
        e.set_thumbnail(url=self.bot.user.display_avatar.url)
        e.description = (
            f"**Security:** {self.config[guild_id]['secure']}"
            f"\n**Channel:** {self.bot.get_channel(self.config[guild_id]['channel'])}"
        )
        if self.config[guild_id]["ignored_channels"]:
            channels = []
            for channel_id in self.config[guild_id]["ignored_channels"]:
                channel = self.bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    channels.append(channel.mention)
            if channels:
                for chunk in split("\n".join(channels), 1024):
                    e.add_field(name="◈ Ignored channels", value=chunk, inline=False)
        if self.config[guild_id]["ignored_bots"]:
            bots = []
            for bot_id in self.config[guild_id]["ignored_bots"]:
                bot = ctx.guild.get_member(bot_id)
                if isinstance(bot, discord.Member):
                    bots.append(bot.mention)
            if bots:
                e.add_field(name="◈ Ignored Bots", value=", ".join(bots), inline=False)
        if self.config[guild_id]["disabled"]:
            disabled = self.config[guild_id]["disabled"]
            e.add_field(name="◈ Log Redirects", value=", ".join(disabled), inline=False)
        if self.config[guild_id]["channels"]:
            channels = []
            for log_type, channel_id in list(self.config[guild_id]["channels"].items()):
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    channels.append(f"{channel.mention} - {log_type}")
            if channels:
                for chunk in split("\n".join(channels), 1024):
                    e.add_field(name="◈ Log Redirects", value=chunk, inline=False)
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in list(self.config.keys()):
            if (
                guild_id in self.bot.tasks["logger"]
                and not self.bot.tasks["logger"][guild_id].done()
            ):
                continue
            task = self.bot.loop.create_task(self.start_queue(guild_id))
            self.bot.tasks["logger"][guild_id] = task
        self.bot.loop.create_task(self.init_invites())

    @commands.Cog.listener()
    async def on_message(self, msg):
        """ @everyone and @here event """
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.config:
                mention = None
                content = str(msg.content).lower()
                if "!everyone" in content:
                    mention = "@everyone"
                if "!here" in content:
                    mention = "@here"
                if mention:
                    e = discord.Embed(color=white)
                    e.title = f"~==🍸{mention} mentioned🍸==~"
                    e.set_thumbnail(url=msg.author.display_avatar.url)
                    is_successful = False
                    member = msg.guild.get_member(msg.author.id)
                    if not member:
                        return
                    if member.guild_permissions.administrator:
                        is_successful = True
                    elif member.guild_permissions.mention_everyone and (
                        not msg.channel.permissions_for(msg.author).mention_everyone
                        is False
                    ):
                        is_successful = True
                    elif msg.channel.permissions_for(msg.author).mention_everyone:
                        is_successful = True
                    if is_successful:
                        e.description = self.bot.utils.format_dict({
                            "Author": msg.author.mention,
                            "Channel": f"<#{msg.channel.id}>",
                            f"[Jump to MSG]({msg.jump_url})": None,
                        })
                        for group in split(msg.content, 1024):
                            e.add_field(name="◈ Content", value=group, inline=False)
                        log = Log("everyone_mention", embed=e)
                        self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.guild, discord.Guild):
            guild_id = str(before.guild.id)
            if guild_id in self.config and not after.author.bot:
                if before.content != after.content:
                    if before.author.id in self.config[guild_id]["ignored_bots"]:
                        return
                    if before.channel.id in self.config[guild_id]["ignored_channels"]:
                        return

                    e = discord.Embed(color=pink)
                    e.set_author(
                        name="~==🍸Msg Edited🍸==~", icon_url=before.author.display_avatar.url
                    )
                    e.set_thumbnail(url=before.author.display_avatar.url)
                    e.description = self.bot.utils.format_dict({
                        "author": before.author.mention,
                        "Channel": f"<#{before.channel.id}>",
                        f"[Jump to MSG]({before.jump_url})": None,
                    })
                    for group in split(before.content, 1024):
                        e.add_field(name="◈ Before", value=group, inline=False)
                    for group in split(after.content, 1024):
                        e.add_field(name="◈ After", value=group, inline=False)
                    log = Log("message_edit", embed=e)
                    self.put_nowait(guild_id, log)

                if before.embeds and not after.embeds:
                    if before.author.id in self.config[guild_id]["ignored_bots"]:
                        return
                    if before.channel.id in self.config[guild_id]["ignored_channels"]:
                        return

                    if before.channel.id == self.config[guild_id]["channel"] or (
                        before.channel.id in self.config[guild_id]["channels"]
                    ):
                        await asyncio.sleep(0.5)  # prevent updating too fast and not showing on the users end
                        return await after.edit(suppress=False, embed=before.embeds[0])
                    e = discord.Embed(color=pink)
                    e.set_author(name="~==🍸Embed Hidden🍸==~", icon_url=before.author.display_avatar.url)
                    e.set_thumbnail(url=before.author.display_avatar.url)
                    e.description = self.bot.utils.format_dict({
                        "author": before.author.mention,
                        "Channel": f"<#{before.channel.id}>",
                        f"[Jump to MSG]({before.jump_url})": None,
                    })
                    em = before.embeds[0].to_dict()
                    f = BytesIO(json.dumps(em, sort_keys=True, indent=4).encode())
                    log = Log("embed_hidden", embed=e, files=[File(f, filename="embed.json")])
                    self.put_nowait(guild_id, log)

                if before.pinned != after.pinned:
                    action = "Unpinned" if before.pinned else "Pinned"
                    audit_dat = await self.search_audit(after.guild, audit.message_pin)
                    e = discord.Embed(color=cyan)

                    e.set_author(
                        name=f"~==🍸Msg {action}🍸==~", icon_url=after.author.display_avatar.url
                    )
                    e.set_thumbnail(url=after.author.display_avatar.url)
                    e.description = self.bot.utils.format_dict({
                        "Author": after.author.mention,
                        "Channel": f"<#{after.channel.id}>",
                        "Who Pinned": audit_dat["user"],
                        f"[Jump to MSG]({after.jump_url})": None,
                    })
                    for text_group in split(after.content, 1000):
                        e.add_field(name="◈ Content", value=text_group, inline=False)
                    log = Log("message_pin", embed=e)
                    self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel = self.bot.get_channel(int(payload.data["channel_id"]))
        if isinstance(channel, discord.TextChannel) and channel.guild:
            guild_id = str(channel.guild.id)
            if guild_id in self.config and not payload.cached_message:
                try:
                    msg = await channel.fetch_message(payload.message_id)
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    return
                if msg.author.id in self.config[guild_id]["ignored_bots"]:
                    return
                if msg.channel.id in self.config[guild_id]["ignored_channels"]:
                    return
                if msg.author.id == self.bot.user.id:
                    return
                e = discord.Embed(color=pink)
                e.set_author(name="Uncached Msg Edited", icon_url=msg.author.display_avatar.url)
                e.set_thumbnail(url=msg.author.display_avatar.url)
                e.description = self.bot.utils.format_dict({
                    "Author": msg.author.mention,
                    "Channel": channel.mention,
                    f"[Jump to MSG]({msg.jump_url})": None,
                })
                for text_group in split(msg.content, 1024):
                    e.add_field(name="◈ Content", value=text_group, inline=False)
                log = Log("message_edit", embed=e)
                self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.config:
                if self.config[guild_id]["secure"]:
                    if msg.embeds and msg.channel.id == self.config[guild_id]["channel"] or (
                            msg.channel.id in self.config[guild_id]["channels"].values()
                    ):
                        if msg.embeds:
                            await msg.channel.send("OwO what's this", embed=msg.embeds[0])
                        if msg.attachments:
                            files = []
                            for attachment in msg.attachments:
                                with suppress(HTTPException, NotFound, Forbidden):
                                    files.append(await attachment.to_file(use_cached=True))
                            log = Log("message_delete", embed=msg.embeds[0] if msg.embeds else None, files=files)
                            self.put_nowait(guild_id, log)
                        return

                if (
                    msg.author.id == self.bot.user.id
                    and "your cooldowns up" in msg.content
                ):
                    return  # is from work notifs within the factions module
                if msg.author.id in self.config[guild_id]["ignored_bots"]:
                    return
                if msg.channel.id in self.config[guild_id]["ignored_channels"]:
                    return
                if (
                    msg.channel.id == self.config[guild_id]["channel"]
                    and not self.config[guild_id]["secure"]
                ):
                    return

                e = discord.Embed(color=purple)
                dat = await self.search_audit(msg.guild, audit.message_delete)
                if dat["thumbnail_url"] == msg.guild.icon.url if msg.guild.icon else None:
                    dat["thumbnail_url"] = msg.author.display_avatar.url
                e.set_author(name="~==🍸Msg Deleted🍸==~", icon_url=dat["thumbnail_url"])
                e.set_thumbnail(url=msg.author.display_avatar.url)
                kwargs = {}
                if dat["user"] != "Unknown":
                    kwargs["Deleted by"] = dat["user"]
                e.description = self.bot.utils.format_dict({
                    "Author": msg.author.mention,
                    "Channel": f"<#{msg.channel.id}>",
                    **kwargs
                })
                for text_group in split(msg.content, 1024):
                    e.add_field(name="◈ MSG Content", value=text_group, inline=False)
                if msg.embeds:
                    e.set_footer(text="⇓ Embed ⇓")
                files = []
                log_type = "message_delete"
                if msg.attachments:
                    for attachment in msg.attachments:
                        if attachment.size > 8000000:
                            continue
                        with suppress(HTTPException, NotFound, Forbidden):
                            files.append(await attachment.to_file(use_cached=True))
                    if files and "attachment_delete" in self.config[guild_id]["channels"]:
                        log_type = "attachment_delete"
                log = Log(log_type, embed=e, files=files)
                self.put_nowait(guild_id, log)
                if msg.embeds:
                    log = Log("message_delete", embed=msg.embeds[0])
                    self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config and not payload.cached_message:
            if payload.channel_id in self.config[guild_id]["ignored_channels"]:
                return
            guild = self.bot.get_guild(payload.guild_id)
            e = discord.Embed(color=purple)
            dat = await self.search_audit(guild, audit.message_delete)
            e.set_author(name="Uncached Message Deleted", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            kwargs = {}
            if dat["user"] != "Unknown":
                kwargs["Deleted by"] = dat["user"]
            e.description = self.bot.utils.format_dict({
                "Author": dat["target"],
                "MSG ID": payload.message_id,
                "Channel": f"<#{payload.channel_id}>",
                **kwargs
            })
            log = Log("message_delete", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config:
            guild = self.bot.get_guild(payload.guild_id)
            channel = self.bot.get_channel(payload.channel_id)
            purged_messages = ""
            for msg in payload.cached_messages:
                await asyncio.sleep(0)
                if self.config[guild_id]["secure"]:
                    if msg.embeds:
                        log = Log("message_delete", embed=msg.embeds[0])
                        if msg.channel.id == self.config[guild_id]["channel"]:
                            self.put_nowait(guild_id, log)
                            continue
                        if msg.channel.id in self.config[guild_id]["channels"]:
                            await msg.channel.send(
                                "OwO what's this", embed=msg.embeds[0]
                            )
                            self.put_nowait(guild_id, log)
                            continue

                timestamp = msg.created_at.strftime("%I:%M:%S%p")
                purged_messages = (
                    f"{timestamp} | {msg.author}: {msg.content}\n{purged_messages}"
                )

            if payload.cached_messages and not purged_messages:  # only logs were purged
                return
            buffer = File(BytesIO(purged_messages.encode()), filename="messages.txt")

            e = discord.Embed(color=lime_green)
            dat = await self.search_audit(guild, audit.message_bulk_delete)
            if dat["extra"] and dat["icon_url"]:
                e.set_author(
                    name=f"~==🍸{dict(dat['extra'])['count']} Msgs Purged🍸==~",
                    icon_url=dat["icon_url"],
                )
            else:
                amount = len(payload.cached_messages)
                e.set_author(name=f"~==🍸{amount if amount else 'Uncached'} Msgs Purged🍸==~")
            if dat["thumbnail_url"]:
                e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = self.bot.utils.format_dict({
                "Users Effected": len(
                    list(set([msg.author for msg in payload.cached_messages]))
                ),
                "Channel": channel.mention,
                "Purged by": dat["user"],
            })
            log = Log("message_purge", embed=e, files=[buffer])
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config:
            channel = self.bot.get_channel(payload.channel_id)
            try:
                msg = await channel.fetch_message(payload.message_id)
            except (discord.errors.NotFound, discord.errors.Forbidden):
                return
            if msg.author.id in self.config[guild_id]["ignored_bots"]:
                return
            if msg.channel.id in self.config[guild_id]["ignored_channels"]:
                return
            e = discord.Embed(color=yellow)
            e.set_author(
                name="~==🍸Reactions Cleared🍸==~", icon_url=msg.author.display_avatar.url
            )
            e.set_thumbnail(url=msg.author.display_avatar.url)
            e.description = self.bot.utils.format_dict({
                "Author": msg.author.mention,
                "Channel": channel.mention,
                f"[Jump to MSG]({msg.jump_url})": None,
            })
            log = Log("reactions_clear", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):  # due for rewrite
        guild_id = str(after.id)
        if guild_id in self.config:
            dat = await self.search_audit(after, audit.guild_update)

            def create_template_embed():
                """ Creates a new embed to work with """
                em = discord.Embed(color=lime_green)
                em.set_author(name="~==🍸Server Updated🍸==~", icon_url=dat["icon_url"])
                if after.icon:
                    em.set_thumbnail(url=after.icon.url)
                return em

            e = create_template_embed()
            if before.name != after.name:
                e.description = (
                    f"> 》__**Name Changed**__《" f"\n**Changed by:** {dat['user']}"
                )
                e.add_field(name="◈ Before", value=before.name, inline=False)
                e.add_field(name="◈ After", value=after.name, inline=False)
                log = Log("server_rename", embed=e)
                self.put_nowait(guild_id, log)
            before_url = before.icon.url if before.icon else None
            after_url = after.icon.url if after.icon else None
            if before_url != after_url:
                e = create_template_embed()
                e.description = (
                    f"> 》__**Icon Changed**__《" f"\n**Changed by:** [{dat['user']}]"
                )
                log = Log("new_server_icon", embed=e)
                self.put_nowait(guild_id, log)
            before_url = before.banner.url if before.banner else None
            after_url = after.banner.url if after.banner else None
            if before_url != after_url:
                e = create_template_embed()
                e.description = (
                    f"> 》__**Banner Changed**__《" f"\n**Changed by:** {dat['user']}"
                )
                log = Log("new_server_banner", embed=e)
                self.put_nowait(guild_id, log)
            before_url = before.splash.url if before.splash else None
            after_url = before.splash.url if before.splash else None
            if before_url != after_url:
                e = create_template_embed()
                e.description = (
                    f"> 》__**Splash Changed**__《" f"\n**Changed by:** {dat['user']}"
                )
                log = Log("new_server_splash", embed=e)
                self.put_nowait(guild_id, log)
            if before.region != after.region:
                e = create_template_embed()
                e.description = (
                    f"> 》__**Region Changed**__《" f"\n**Changed by:** {dat['user']}"
                )
                e.add_field(name="◈ Before", value=str(before.region), inline=False)
                e.add_field(name="◈ After", value=str(after.region), inline=False)
                log = Log("region_change", embed=e)
                self.put_nowait(guild_id, log)
            if before.afk_timeout != after.afk_timeout:
                e = create_template_embed()
                e.description = (
                    f"> 》__**AFK Timeout Changed**__《"
                    f"\n**Changed by:** {dat['user']}"
                )
                e.add_field(
                    name="◈ Before", value=str(before.afk_timeout), inline=False
                )
                e.add_field(name="◈ After", value=str(after.afk_timeout), inline=False)
                log = Log("afk_timeout_change", embed=e)
                self.put_nowait(guild_id, log)
            if before.afk_channel != after.afk_channel:
                e = create_template_embed()
                e.description = (
                    f"> 》__**AFK Channel Changed**__《"
                    f"\n**Changed by:** {dat['user']}"
                )
                if before.afk_channel:
                    e.add_field(
                        name="◈ Before",
                        value=f"**Name:** {before.afk_channel.name}"
                        f"\n**ID:** {before.afk_channel.id}",
                        inline=False,
                    )
                if after.afk_channel:
                    e.add_field(
                        name="◈ After",
                        value=f"**Name:** {after.afk_channel.name}"
                        f"\n**ID:** {after.afk_channel.id}",
                        inline=False,
                    )
                log = Log("afk_channel_change", embed=e)
                self.put_nowait(guild_id, log)
            if before.owner != after.owner:
                e = create_template_embed()
                e.description = f"> 》__**Owner Changed**__《"
                e.add_field(
                    name="◈ Before",
                    value=f"**Name:** {before.owner.name}"
                    f"\n**Mention:** {before.owner.mention}"
                    f"\n**ID:** {before.owner.id}",
                )
                e.add_field(
                    name="◈ After",
                    value=f"**Name:** {after.owner.name}"
                    f"\n**Mention:** {after.owner.mention}"
                    f"\n**ID:** {after.owner.id}",
                )
                log = Log("new_owner", embed=e)
                self.put_nowait(guild_id, log)
            if before.features != after.features and before.features or after.features:
                e = create_template_embed()
                e.description = f"> 》__**Features Changed**__《"
                changes = ""
                for feature in before.features:
                    if feature not in after.features:
                        changes += f"❌ {feature}"
                for feature in after.features:
                    if feature not in before.features:
                        changes += f"<:plus:548465119462424595> {feature}"
                if changes:
                    e.add_field(name="◈ Changes", value=changes)
                    log = Log("features_change", embed=e)
                    self.put_nowait(guild_id, log)
            if before.premium_tier != after.premium_tier:
                e = discord.Embed(color=pink)
                action = (
                    "lowered" if before.premium_tier > after.premium_tier else "raised"
                )
                e.description = f"Servers boost level {action} to {after.premium_tier}"
                log = Log("new_boost_tier", embed=e)
                self.put_nowait(guild_id, log)
            if before.premium_subscription_count != after.premium_subscription_count:
                e = create_template_embed()
                if after.premium_subscription_count > before.premium_subscription_count:
                    action = "Boosted"
                else:
                    action = "Unboosted"
                who = "Unknown, has another boost"
                if before.premium_subscribers != after.premium_subscribers:
                    changed = [
                        m
                        for m in before.premium_subscribers
                        if m not in after.premium_subscribers
                    ]
                    if not changed:
                        changed = [
                            m
                            for m in after.premium_subscribers
                            if m not in before.premium_subscribers
                        ]
                    who = changed[0].mention
                e.description = f"> **Member {action}**《" f"\n**Who:** [{who}]"
                log = Log("boost", embed=e)
                self.put_nowait(guild_id, log)
            # mfa_level, verification_level, explicit_content_filter, default_notifications
            # preferred_locale, large, system_channel, system_channel_flags
            # Union[emoji_limit, bitrate_limit, filesize_limit]

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=yellow)
            dat = await self.search_audit(channel.guild, audit.channel_create)
            e.set_author(name="~==🍸Channel Created🍸==~", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            member_count = "Unknown"
            if not isinstance(channel, discord.CategoryChannel):
                member_count = len(channel.members)
            mention = "None"
            if isinstance(channel, discord.TextChannel):
                mention = channel.mention
            e.description = self.bot.utils.format_dict({
                "Name": channel.name,
                "Mention": mention,
                "ID": channel.id,
                "Creator": dat["user"],
                "Members": member_count,
            })
            log = Log("channel_create", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:

            # anti log channel deletion
            if self.config[guild_id]["secure"]:
                if channel.id == self.config[guild_id]["channel"]:
                    for embed in self.recent_logs[guild_id]:
                        log = Log("message_delete", embed=embed[0])
                        await self.queue[guild_id].put(log)
                    return

            dat = await self.search_audit(channel.guild, audit.channel_delete)
            member_count = "Unknown"
            if not isinstance(channel, discord.CategoryChannel):
                member_count = len(channel.members)
            category = "None"
            if channel.category:
                category = channel.category.name

            e = discord.Embed(color=red)
            e.set_author(name="~==🍸Channel Deleted🍸==~", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = self.bot.utils.format_dict({
                "Name": channel.name,
                "ID": channel.id,
                "Category": category,
                "Members": member_count,
                "Deleted by": dat["user"],
            })

            if isinstance(channel, discord.CategoryChannel):
                log = Log("channel_delete", embed=e)
                self.put_nowait(guild_id, log)
                return

            members = f"{channel.name} - Member List"
            for member in channel.members:
                await asyncio.sleep(0)
                members += (
                    f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
                )
            buffer = File(BytesIO(members.encode()), filename="members.txt")

            log = Log("channel_delete", embed=e, files=[buffer])
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):  # due for rewrite
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=orange)
            dat = await self.search_audit(after.guild, audit.channel_update)
            if after.guild.icon:
                e.set_thumbnail(url=after.guild.icon.url)
            # category = 'None, or Changed'
            # if after.category and before.category == after.category:
            #     category = after.category.name

            if before.name != after.name:
                e.add_field(
                    name="~==🍸Channel Renamed🍸==~",
                    value=self.bot.utils.format_dict({
                        "Mention": after.mention,
                        "ID": after.id,
                        "Changed by": dat["user"],
                    }),
                    inline=False,
                )
                e.add_field(name="◈ Before", value=before.name)
                e.add_field(name="◈ After", value=after.name)

            if before.position != after.position:
                e.add_field(
                    name="~==🍸Channel Moved🍸==~",
                    value=self.bot.utils.format_dict(
                        {
                            "Mention": after.mention,
                            "ID": after.id,
                            "Changed by": dat["user"],
                        }
                    ),
                    inline=False,
                )
                e.add_field(name="Before", value=str(before.position))
                e.add_field(name="After", value=str(after.position))

            if isinstance(before, discord.TextChannel):
                if before.topic != after.topic:
                    if before.id not in self.config[guild_id]["ignored_channels"]:
                        e.add_field(
                            name="~==🍸Topic Updated🍸==~",
                            value=self.bot.utils.format_dict(
                                {
                                    "Name": after.name,
                                    "Mention": after.mention,
                                    "ID": after.id,
                                    "Changed by": dat["user"],
                                }
                            ),
                            inline=False,
                        )
                        if before.topic:
                            for text_group in split(before.topic):
                                e.add_field(
                                    name="◈ Before", value=text_group, inline=False
                                )
                        if after.topic:
                            for text_group in split(after.topic):
                                e.add_field(
                                    name="◈ After", value=text_group, inline=False
                                )

            if before.category != after.category:
                e.add_field(
                    name="~==🍸Channel Re-Categorized🍸==~",
                    value=self.bot.utils.format_dict(
                        {
                            "Name": after.name,
                            "Mention": after.mention,
                            "ID": after.id,
                            "Changed by": dat["user"],
                        }
                    ),
                    inline=False,
                )
                name = "None"
                if before.category:
                    name = before.category.name
                e.add_field(name="◈ Before", value=name)
                name = "None"
                if after.category:
                    name = after.category.name
                e.add_field(name="◈ After", value=name)

            if before.overwrites != after.overwrites:
                for obj, permissions in list(before.overwrites.items()):
                    await asyncio.sleep(0)
                    after_objects = [x[0] for x in after.overwrites.items()]
                    if obj not in after_objects:
                        dat = await self.search_audit(
                            after.guild, audit.overwrite_delete
                        )
                        perms = "\n".join(
                            [
                                f"{perm} - {value}"
                                for perm, value in list(permissions)
                                if value
                            ]
                        )
                        e.add_field(
                            name=f"❌ {obj.name} removed",
                            value=perms if perms else "-had no permissions",
                            inline=False,
                        )
                        continue

                    after_values = list(
                        list(after.overwrites.items())[after_objects.index(obj)][1]
                    )
                    if list(permissions) != after_values:
                        dat = await self.search_audit(
                            after.guild, audit.overwrite_update
                        )
                        e.add_field(
                            name=f"<:edited:550291696861315093> {obj.name}",
                            value="\n".join(
                                [
                                    f"{perm} - {after_values[i][1]}"
                                    for i, (perm, value) in enumerate(list(permissions))
                                    if (value != after_values[i][1])
                                ]
                            ),
                            inline=False,
                        )

                for obj, permissions in after.overwrites.items():
                    await asyncio.sleep(0)
                    if obj not in [x[0] for x in before.overwrites.items()]:
                        dat = await self.search_audit(
                            after.guild, audit.overwrite_create
                        )
                        perms = "\n".join(
                            [
                                f"{perm} - {value}"
                                for perm, value in list(permissions)
                                if value
                            ]
                        )
                        e.add_field(
                            name=f"<:plus:548465119462424595> {obj.name}",
                            value=perms if perms else "-has no permissions",
                            inline=False,
                        )

                e.description = self.bot.utils.format_dict({
                    "Name": after.name,
                    "Mention": after.name,
                    "ID": after.id,
                    "Changed by": dat["user"],
                })

            if e.fields:
                log = Log("channel_update", embed=e)
                self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild_id = str(role.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(role.guild, audit.role_create)
            e = discord.Embed(color=lime_green)
            e.set_author(name="~==🍸Role Created🍸==~", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = self.bot.utils.format_dict({
                "Mention": role.mention, "ID": role.id, "Created by": dat["user"]
            })
            log = Log("role_create", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild_id = str(role.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(role.guild, audit.role_delete)
            e = discord.Embed(color=dark_green)
            e.set_author(name="~==🍸Role Deleted🍸==~", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = self.bot.utils.format_dict({
                "Name": role.name,
                "ID": role.id,
                "Members": len(role.members) if role.members else "None",
                "Deleted by": dat["user"],
            })
            e.set_footer(text=f"Hex {role.color} | RGB {role.color.to_rgb()}")
            members = f"{role.name} - Member List"
            for member in role.members:
                await asyncio.sleep(0)
                members += (
                    f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
                )
            buffer = File(BytesIO(members.encode()), filename="members.txt")
            log = Log("role_delete", embed=e, files=[buffer])
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            buffer = None
            dat = await self.search_audit(after.guild, audit.role_update)
            e = discord.Embed(color=green)
            e.set_author(name="~==🍸Role Updated🍸==~", icon_url=dat["thumbnail_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = self.bot.utils.format_dict({
                "Name": after.name,
                "Mention": after.mention,
                "ID": before.id,
                "Changed by": dat["user"],
            })

            if before.name != after.name:
                e.add_field(
                    name="◈ Name Changed",
                    value=f"**Before:** {before.name}" f"\n**After:** {after.name}",
                    inline=False,
                )
            if before.color != after.color:
                def generate_image():
                    card = Image.new("RGBA", (200, 30), color=after.color.to_rgb())
                    box = Image.new("RGBA", (100, 30), color=before.color.to_rgb())

                    card.paste(box)
                    _buffer = BytesIO()
                    card.save(_buffer, format="png")
                    _buffer.seek(0)

                    return File(_buffer, filename="colors.png")

                buffer = await self.bot.loop.run_in_executor(None, generate_image)
                e.set_thumbnail(url=dat["thumbnail_url"])
                e.add_field(
                    name="◈ Color Changed",
                    value=f"From **{before.color}** -> **{after.color}**",
                )
            if before.hoist != after.hoist:
                action = "is now visible"
                if after.hoist is False:
                    action = "is no longer visible"
                e.description += f"[{action}]"
            if before.mentionable != after.mentionable:
                action = "is now mentionable"
                if not after.mentionable:
                    action = "is no longer mentionable"
                e.description += f"[{action}]"

            if before.position != after.position:
                # old_roles = self.role_index[guild_id]
                # old_pos = old_roles.index(before)
                # if old_roles[old_pos+1] is after.guild.roles[after.position+1]:
                #     if old_roles[old_pos-1] is after.guild.roles[after.position-1]:
                #         return
                # self.role_index[guild_id] = [role for role in after.guild.roles]
                em = discord.Embed()
                em.description = f"Role {before.mention} was moved"
                log = Log("role_move", embed=em)
                self.put_nowait(guild_id, log)

                # before_roles = before.guild.roles
                # before_roles.pop(after.position)
                # before_roles.insert(before.position, before)
                #
                # before_above = before_roles[before.position+1].id
                # before_below = before_roles[before.position-1].id
                # after_above = after.guild.roles[after.position+1].id
                # after_below = after.guild.roles[after.position-1].id
                #
                # if before_above == after_above and before_below == after_below:
                #     print("Identical! EEEEEE")
                # else:
                #     self.queue[guild_id].append([em, 'updates', time()])

                #     e.add_field(
                #         name='◈ Position Changed',
                #         value=f"**》Before** - {before.position}"
                #               f"\n{before_above}"
                #               f"\n{before.mention}"
                #               f"\n{before_below}"
                #               f"\n\n**》After** - {after.position}"
                #               f"\n{after_above}"
                #               f"\n{after.mention}"
                #               f"\n{after_below}",
                #         inline=False
                #     )
            if before.permissions != after.permissions:
                changes = ""
                for i, (perm, value) in enumerate(iter(before.permissions)):
                    if value != list(after.permissions)[i][1]:
                        changes += f"\n• {perm} {'unallowed' if value else 'allowed'}"
                e.add_field(name="◈ Permissions Changed", value=changes, inline=False)
            if e.fields:
                log = Log("role_update", embed=e, files=[buffer] if buffer else [])
                self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        guild_id = str(guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=light_grey)
            e.set_author(
                name="~==🍸Integrations Update🍸==~", icon_url=guild.owner.display_avatar.url
            )
            if guild.icon:
                e.set_thumbnail(url=guild.icon.url)
            e.description = "An integration was created, modified, or removed"
            log = Log("integrations_update", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(
                channel.guild,
                audit.webhook_create,
                audit.webhook_delete,
                audit.webhook_update,
            )
            if not dat["action"]:
                return

            who = dat["actual_user"]  # type: discord.Member
            if who and who.bot and who.id in self.config[guild_id]["ignored_bots"]:
                return

            if dat["action"].name == "webhook_create":
                action = "Created"
            elif dat["action"].name == "webhook_delete":
                action = "Deleted"
            else:  # webhook update
                action = "Updated"

            e = discord.Embed(color=cyan)
            e.set_author(name=f"~==🍸Webhook {action}🍸==~", icon_url=dat["icon_url"])
            e.set_thumbnail(url=dat["thumbnail_url"])
            e.description = ""

            if action != "Deleted":
                try:
                    webhook = await self.bot.fetch_webhook(dat["target"].id)
                except (NotFound, Forbidden):
                    return
                channel = self.bot.get_channel(webhook.channel_id)
                e.set_thumbnail(url=webhook.avatar.url)
                e.description = self.bot.utils.format_dict(
                    {"Name": webhook.name, "Type": webhook.type}
                )

            e.description += self.bot.utils.format_dict(
                {
                    "ID": dat["target"].id,
                    "Channel": channel.mention,
                    f"{action} by": dat["user"],
                }
            )
            log = Log("webhook_update", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if guild_id in self.config:
            if member.bot:
                dat = await self.search_audit(member.guild, audit.bot_add)
                e = discord.Embed(color=light_grey)
                e.set_author(name="~==🍸Bot Added🍸==~", icon_url=dat["icon_url"])
                e.set_thumbnail(url=dat["thumbnail_url"])
                inv = f"https://discordapp.com/oauth2/authorize?client_id={member.id}&permissions=0&scope=bot"
                e.description = self.bot.utils.format_dict(
                    {
                        "Name": member.name,
                        "Mention": member.mention,
                        "ID": member.id,
                        "Bot Invite": f"[here]({inv})",
                        "Invited by": dat["user"],
                    }
                )
                log = Log("bot_add", embed=e)
                self.put_nowait(guild_id, log)
                return

            invite = None  # the invite used to join
            if member.guild.me.guild_permissions.administrator:
                invites = await member.guild.invites()
                if guild_id not in self.invites:
                    self.invites[guild_id] = {}
                for invite in invites:
                    if invite.url not in self.invites[guild_id]:
                        self.invites[guild_id][invite.url] = invite.uses
                        if invite.uses > 0:
                            invite = invite
                            break
                    elif invite.uses != self.invites[guild_id][invite.url]:
                        self.invites[guild_id][invite.url] = invite.uses
                        invite = invite
                        break

            e = discord.Embed(color=lime_green)
            icon_url = member.display_avatar.url
            inviter = "Unknown"
            if invite and invite.inviter:
                icon_url = invite.inviter.display_avatar.url
                inviter = invite.inviter
            e.set_author(name="~==🍸Member Joined🍸==~", icon_url=icon_url)
            e.set_thumbnail(url=member.display_avatar.url)
            created = get_time(round((datetime.now(tz=timezone.utc) - member.created_at).total_seconds()))
            desc = {
                "Name": member.name,
                "Mention": member.mention,
                "ID": member.id,
                "Created": f"{created} ago",
                "Invited by": inviter
            }
            if invite:
                desc["Invite"] = f"[{invite.code}]({invite.url})"
            e.description = self.bot.utils.format_dict(desc)
            aliases = list(set([
                m.display_name
                for m in [
                    server.get_member(member.id)
                    for server in self.bot.guilds
                    if member in server.members
                ]
                if m.id == member.id and m.display_name != member.name
            ]))
            if len(aliases) > 0:
                e.add_field(name="◈ Aliases", value=", ".join(aliases), inline=False)
            log = Log("member_join", embed=e)
            self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=red)
            e.description = self.bot.utils.format_dict({
                "Username": member,
                "Mention": member.mention,
                "ID": member.id,
                "Top Role": member.top_role.mention,
            })
            e.set_thumbnail(url=member.display_avatar.url)
            removed = False

            await self.wait_for_permissions(member.guild, "view_audit_log")

            async for entry in member.guild.audit_logs(limit=1, action=audit.kick):
                if entry.target.id == member.id and entry.created_at > self.past:
                    e.set_author(
                        name="~==🍸Member Kicked🍸==~", icon_url=entry.user.display_avatar.url
                    )
                    e.description += self.bot.utils.format_dict(
                        {"Kicked by": entry.user.mention}
                    )
                    log = Log("member_kick", embed=e)
                    self.put_nowait(guild_id, log)
                    removed = True

            async for entry in member.guild.audit_logs(limit=1, action=audit.ban):
                if entry.target.id == member.id and entry.created_at > self.past:
                    e.set_author(
                        name="~==🍸Member Banned🍸==~", icon_url=entry.user.display_avatar.url
                    )
                    e.description += self.bot.utils.format_dict(
                        {"Banned by": entry.user.mention}
                    )
                    log = Log("member_ban", embed=e)
                    self.put_nowait(guild_id, log)
                    removed = True

            if not removed:
                e.set_author(name="~==🍸Member Left🍸==~", icon_url=member.display_avatar.url)
                log = Log("member_leave", embed=e)
                self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_id = str(before.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=blue)
            if before.display_name != after.display_name:
                e.set_author(name="~==🍸Nick Changed🍸==~")
                e.description = self.bot.utils.format_dict(
                    {"User": after, "Mention": after.mention, "ID": after.id}
                )
                e.add_field(name="◈ Before", value=before.display_name)
                e.add_field(name="◈ After", value=after.display_name)
                log = Log("nick_change", embed=e)
                self.put_nowait(guild_id, log)

            if len(before.roles) != len(after.roles):
                dat = await self.search_audit(after.guild, audit.member_role_update)
                e.set_thumbnail(url=dat["thumbnail_url"])
                if len(before.roles) > len(after.roles):
                    action = "Revoked"
                    roles = [role for role in before.roles if role not in after.roles]
                    e.description = f"{roles[0].mention} was taken from {before}"
                elif len(before.roles) < len(after.roles):
                    action = "Granted"
                    roles = [role for role in after.roles if role not in before.roles]
                    e.description = f"{roles[0].mention} was given to {before}"
                else:
                    return
                e.set_author(name=f"~==🍸Role {action}🍸==~", icon_url=dat["icon_url"])
                info = {
                    "User": after.mention,
                    "Role": roles[0].name,
                    "Role ID": roles[0].id,
                    f"{action} by": dat["user"],
                }
                e.add_field(
                    name="◈ Information",
                    value=self.bot.utils.format_dict(info),
                    inline=False,
                )
                log = Log("member_roles_update", embed=e)
                self.put_nowait(guild_id, log)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before: list, after: list):
        guild_id = str(guild.id)
        if guild_id in self.config:

            # Emoji rename
            index = {}
            for emoji in before:
                await asyncio.sleep(0)
                index[emoji.id] = emoji
            for emoji in after:
                await asyncio.sleep(0)
                if emoji.id in index and emoji.name != index[emoji.id].name:
                    e = discord.Embed(color=orange)
                    e.set_author(name="~==🍸Emoji Renamed🍸==~")
                    if guild.icon:
                        e.set_thumbnail(url=guild.icon.url)
                    e.description = self.bot.utils.format_dict({
                        "Emoji": str(emoji),
                        "Before": index[emoji.id].name,
                        "After": emoji.name
                    })
                    log = Log("emoji_rename", embed=e)
                    self.put_nowait(guild_id, log)

            # Emoji delete
            for emoji in before:
                await asyncio.sleep(0)
                if not any(emoji.id == e.id for e in after):
                    e = discord.Embed(color=orange)
                    e.set_author(name="~==🍸Emoji Deleted🍸==~")
                    if guild.icon:
                        e.set_thumbnail(url=guild.icon.url)
                    e.description = self.bot.utils.format_dict({
                        "Emoji": emoji.name,
                        "Animated": str(emoji.animated)
                    })
                    log = Log("emoji_delete", embed=e)
                    self.put_nowait(guild_id, log)

            # Emoji create
            for emoji in after:
                await asyncio.sleep(0)
                if not any(emoji.id == e.id for e in before):
                    e = discord.Embed(color=orange)
                    e.set_author(name="~==🍸Emoji Created🍸==~")
                    if guild.icon:
                        e.set_thumbnail(url=guild.icon.url)
                    e.description = self.bot.utils.format_dict({
                        "Emoji": str(emoji)
                    })
                    log = Log("emoji_create", embed=e)
                    self.put_nowait(guild_id, log)


def setup(bot):
    bot.add_cog(Logger(bot), override=True)
