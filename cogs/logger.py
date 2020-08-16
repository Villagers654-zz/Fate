"""
Discord.Py v1.3+ Action Logs Module:
+ can split up into multiple channels
+ key security features to protect the log
- logs can't be deleted or purged by anyone
- re-creates deleted log channel(s) and resends the last x logs

Super Important To-Do list:
+ recolor the embeds so there's no duplicate colors
- try to match the colors for .logger
"""

import asyncio
from os import path
import json
import os
from datetime import datetime, timedelta
from time import time
from aiohttp.client_exceptions import ClientOSError
import aiohttp
import aiofiles
import aiomysql

from discord.ext import commands
import discord
from discord import AuditLogAction as audit
from PIL import Image

from utils.colors import *
from utils import utils


def is_guild_owner():
    async def predicate(ctx):
        has_perms = ctx.author.id == ctx.guild.owner.id
        if not has_perms:
            await ctx.send("You need to be the owner of the server to use this")
        return has_perms
    return commands.check(predicate)


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.config = {}
        self.path = './data/userdata/secure-log.json'
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.config = json.load(f)  # type: dict

        self.channel_types = [
            "system+", "updates", "actions", "chat", "misc", "sudo"
        ]

        self.queue = {g_id: [] for g_id in self.config.keys()}
        self.recent_logs = {
            guild_id: {
                Type: [] for Type in self.channel_types
            } for guild_id, dat in self.config.items() if (
                dat['type'] == 'multi'
            )
        }

        self.static = {}
        self.wait_queue = {}

        self.invites = {}
        if self.bot.is_ready():
            self.bot.loop.create_task(self.init_invites())
            for guild_id in self.config.keys():
                if guild_id in bot.logger_tasks:
                    bot.logger_tasks[guild_id].cancel()
                task = self.bot.loop.create_task(self.start_queue(guild_id))
                bot.logger_tasks[guild_id] = task
            if "keep_alive_task" in bot.logger_tasks:
                if bot.logger_tasks["keep_alive_task"].done():
                    bot.log(
                        message="Loggers keep alive task came to an end",
                        level="CRITICAL",
                        tb=bot.logger_tasks["keep_alive_task"].result()
                    )
                else:
                    bot.logger_tasks["keep_alive_task"].cancel()
                    bot.log(
                        message="Canceled existing keep_alive_task in logger",
                        level="INFO"
                    )
            task = self.bot.loop.create_task(self.keep_alive_task())
            bot.logger_tasks["keep_alive_task"] = task

    @property
    def template(self):
        return {
            "channel": None,
            "channels": {},
            "type": "single",
            "secure": False,
            "ignored_channels": [],
            "ignored_bots": []
        }

    async def save_data(self) -> None:
        """ Saves local variables """
        await self.bot.save_json(self.path, self.config)

    async def handle_echo(self, reader, writer) -> None:
        """ Manage requests from the web server """
        async def get(guild_id: str):
            """ Get a guilds config, or use a template if not exists """
            if guild_id in self.config:
                return {
                    "config": self.config[guild_id],
                    "successful": True,
                    "reason": None
                }
            return None

        async def push(guild_id: str, data):
            """ Update or insert a new or updated config """
            requires_init = guild_id in self.config
            new_config = data["config"]
            self.config[guild_id] = new_config
            await self.save_data()
            if requires_init:  # Start or restart the queue for the guild
                if guild_id in self.bot.logger_tasks and not self.bot.logger_tasks[guild_id].done():
                    self.bot.logger_tasks[guild_id].cancel()
                task = self.bot.loop.create_task(self.start_queue(guild_id))
                self.bot.logger_tasks[guild_id] = task
            return {
                "successful": True,
                "reason": None
            }

        async def remove(guild_id: str):
            """ Remove a config """
            if guild_id not in self.config:
                return_data = {
                    "successful": False,
                    "reason": "No existing configuration"
                }
            else:
                if guild_id in self.bot.logger_tasks:
                    if not self.bot.logger_tasks[guild_id].done():
                        self.bot.logger_tasks[guild_id].cancel()
                    del self.bot.logger_tasks[guild_id]
                del self.config[guild_id]
                await self.save_data()
                return_data = {
                    "successful": True,
                    "reason": None
                }
            return return_data

        await self.bot.handle_tcp(
            reader, writer,
            get_coro=get,
            push_coro=push,
            remove_coro=remove
        )

    async def initiate_category(self, guild) -> discord.CategoryChannel:
        """ Sets up a new multi-log category"""
        if str(guild.id) not in self.config:
            self.config[str(guild.id)] = {
                "channels": {},
                "type": "multi"
            }
        category = await guild.create_category(name='MultiLog')
        for channelType in self.channel_types:
            channel = await guild.create_text_channel(
                name=channelType,
                category=category
            )
            self.config[str(guild.id)]['channels'][channelType] = channel.id
        guild_id = str(guild.id)
        self.config[guild_id]['channel'] = category.id
        return category

    async def keep_alive_task(self) -> None:
        self.bot.log("Loggers keep_alive_task was started")
        channel = self.bot.get_channel(541520201926311986)
        while True:
            for guild_id, task in list(self.bot.logger_tasks.items()):
                if task.done():
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        del self.bot.logger_tasks[guild_id]
                        continue
                    await channel.send(f"The queue task for {guild} unexpectedly completed, here's the result\n```python\n{str(task.result())[:1900]}```")
                    if guild_id in self.config:
                        task = self.bot.loop.create_task(self.start_queue(guild_id))
                        self.bot.logger_tasks[guild_id] = task
            self.bot.log.debug("keep_alive_task still running")
            await asyncio.sleep(60)

    async def wait_for_permission(self, guild, permission: str, channel=None) -> bool:
        """Notify the owner of missing permissions and wait until they've been granted"""

        # Keep a 'process list' of sorts to prevent multiple events using this
        # from causing a lot of API spam from the dm history searches
        parent = False
        guild_id = str(guild.id)
        if guild_id not in self.wait_queue:
            self.wait_queue[guild_id] = []
        if permission not in self.wait_queue[guild_id]:
            self.wait_queue[guild_id].append(permission)
            parent = True
        dm = None

        for _attempt in range(12 * 60):  # Timeout of 12 hours
            # Check if you have the required permission
            if channel:
                if eval(f"channel.permissions_for(guild.me).{permission}"):
                    if parent:
                        self.wait_queue[guild_id].remove(permission)
                        if not self.wait_queue[guild_id]:
                            del self.wait_queue[guild_id]
                    break
            else:
                if eval(f"guild.me.guild_permissions.{permission}"):
                    if parent:
                        self.wait_queue[guild_id].remove(permission)
                        if not self.wait_queue[guild_id]:
                            del self.wait_queue[guild_id]
                    break

            # See if the bot can send a dm notice
            # This is only used by the parent to prevent API spam
            if parent:
                try:
                    if not dm:
                        dm = guild.owner.dm_channel
                    if not dm:
                        dm = await guild.owner.create_dm()
                    async for msg in dm.history(limit=3):
                        if f"I need {permission}" in msg.content:
                            break
                    else:
                        print("a queue was missing permissions")
                        await guild.owner.send(
                            f"I need {permission} permissions in {guild} for the logger module to function. "
                            f"Until that's satisfied, i'll keep a maximum 12 hours of logs in queue"
                        )
                except (discord.errors.Forbidden, discord.errors.NotFound):
                    pass
            await asyncio.sleep(60)

        else:
            if parent:
                self.wait_queue[guild_id].remove(permission)
                if not self.wait_queue[guild_id]:
                    del self.wait_queue[guild_id]
            return False
        return True

    async def start_queue(self, guild_id: str) -> None:
        """ Loop for managing the guilds queue
        + checks guild permissions
        + checks channel permissions
        + can wait to send logs
        + archives the last 50-175 logs to
        be able to resend if deleted """
        guild = self.bot.get_guild(int(guild_id))
        index = 1
        while not guild:
            await asyncio.sleep(60)
            guild = self.bot.get_guild(int(guild_id))
            index += 1
            if index == 60*12:
                del self.config[guild_id]
                return
        if guild_id not in self.queue:
            self.queue[guild_id] = []
        if guild_id not in self.recent_logs:
            if self.config[guild_id]['type'] == 'single':
                self.recent_logs[guild_id] = []
            else:
                self.recent_logs[guild_id] = {
                    Type: [] for Type in self.channel_types
                }

        while True:
            while not self.queue[guild_id]:
                await asyncio.sleep(1.21)

            guild = self.bot.get_guild(int(guild_id))
            index = 1
            while not guild:
                await asyncio.sleep(60)
                guild = self.bot.get_guild(int(guild_id))
                index += 1
                if index == 60 * 12:
                    del self.config[guild_id]
                    return

            log_type = self.config[guild_id]['type']  # type: str

            for embed, channelType, logged_at in self.queue[guild_id][-175:]:
                list_obj = [embed, channelType, logged_at]
                file_paths = []
                files = []
                if isinstance(embed, tuple):
                    embed, file_paths = embed
                    if not isinstance(file_paths, list):
                        file_paths = [file_paths]
                    files = [discord.File(file) for file in file_paths if os.path.isfile(file)]

                for i, field in enumerate(embed.fields):
                    if not field.value or field.value is discord.Embed.Empty:
                        self.bot.log(f"A log of type {channelType} had no value", "CRITICAL")
                        for chunk in self.bot.utils.split(str(embed.to_dict()), 1900):
                            self.bot.log(chunk, "CRITICAL")
                        embed.fields[i].value = 'None'
                    if len(field.value) > 1024:
                        embed.remove_field(i)
                        for iter, chunk in enumerate(self.bot.utils.split(field.value, 1024)):
                            embed.insert_field_at(
                                index=i + iter,
                                name=field.name,
                                value=chunk,
                                inline=field.inline
                            )
                        self.bot.log(f"A log of type {channelType} had had a huge value", "CRITICAL")
                        for chunk in self.bot.utils.split(str(embed.to_dict()), 1900):
                            self.bot.log(chunk, "CRITICAL")

                embed.timestamp = datetime.fromtimestamp(logged_at)

                # Permission checks to ensure the secure features can function
                if self.config[guild_id]['secure']:
                    result = await self.wait_for_permission(guild, "administrator")
                    if not result:
                        del self.config[guild_id]
                        return await self.save_data()

                # Ensure the channel still exists
                category = self.bot.get_channel(self.config[guild_id]['channel'])
                if not category:
                    if not guild.me.guild_permissions.manage_channels:
                        result = await self.wait_for_permission(guild, "manage_channels")
                        if not result:
                            del self.config[guild_id]
                            return await self.save_data()
                    try:
                        category = await self.bot.fetch_channel(self.config[guild_id]['channel'])
                    except discord.errors.NotFound:
                        if log_type == 'multi':
                            category = await self.initiate_category(guild)
                            await self.save_data()
                        elif log_type == 'single':
                            category = await guild.create_text_channel(name='bot-logs')
                            self.config[guild_id]['channel'] = category.id
                        await self.save_data()

                # Ensure basic send-embed level permissions
                if isinstance(category, discord.TextChannel):
                    result = await self.wait_for_permission(guild, "send_messages", category)
                    if not result:
                        del self.config[guild_id]
                        return await self.save_data()
                    result = await self.wait_for_permission(guild, "embed_links", category)
                    if not result:
                        del self.config[guild_id]
                        return await self.save_data()

                # Ensure this still exists
                if guild_id not in self.recent_logs:
                    if self.config[guild_id]['type'] == 'single':
                        self.recent_logs[guild_id] = []
                    else:
                        self.recent_logs[guild_id] = {
                            Type: [] for Type in self.channel_types
                        }

                if isinstance(category, discord.TextChannel):  # single channel log
                    try:
                        await category.send(embed=embed, files=files)
                    except (discord.errors.Forbidden, discord.errors.NotFound, ConnectionResetError):
                        e = discord.Embed(title='Failed to send embed')
                        e.set_author(name=guild if guild else "Unknown Guild")
                        for text_group in self.bot.utils.split(str(json.dumps(embed.to_dict(), indent=2)), 1990):
                            e.add_field(name="Embed Data", value=text_group, inline=False)
                        e.set_footer(text=str(guild.id) if guild else "Unknown Guild")
                        try:
                            await category.send(embed=e)
                        except (discord.errors.Forbidden, discord.errors.NotFound):
                            break
                        continue
                    if file_paths:
                        for file in file_paths:
                            if os.path.isfile(file):
                                os.remove(file)
                    self.queue[guild_id].remove(list_obj)
                    if isinstance(self.recent_logs[guild_id], dict):
                        self.recent_logs[guild_id] = []
                    self.recent_logs[guild_id].append([embed, logged_at])

                for Type, channel_id in self.config[guild_id]['channels'].items():
                    if Type == channelType:
                        channel = self.bot.get_channel(channel_id)

                        # Ensure send-embed level permissions
                        if not channel:
                            if not guild.me.guild_permissions.manage_channels:
                                result = await self.wait_for_permission(guild, "manage_channels")
                                if not result:
                                    del self.config[guild_id]
                                    return await self.save_data()
                            result = await self.wait_for_permission(guild, "send_messages", channel)
                            if not result:
                                del self.config[guild_id]
                                return await self.save_data()
                            result = await self.wait_for_permission(guild, "embed_links", channel)
                            if not result:
                                del self.config[guild_id]
                                return await self.save_data()

                            channel = await guild.create_text_channel(
                                name=channelType,
                                category=category
                            )
                            self.config[guild_id]['channels'][Type] = channel.id
                            await self.save_data()
                        try:
                            await channel.send(embed=embed, files=files)
                        except (discord.errors.Forbidden, discord.errors.NotFound, ClientOSError):
                            e = discord.Embed(title='Failed to send embed')
                            e.set_author(name=guild if guild else "Unknown Guild")
                            for text_group in self.bot.utils.split(str(json.dumps(embed.to_dict(), indent=2)), 1024):
                                e.add_field(name="Embed Data", value=text_group, inline=False)
                            e.set_footer(text=str(guild.id) if guild else "Unknown Guild")
                            try:
                                await channel.send(embed=e)
                            except (discord.errors.Forbidden, discord.errors.NotFound, ClientOSError):
                                break
                            continue
                        if file_paths:
                            for file in file_paths:
                                if os.path.isfile(file):
                                    os.remove(file)
                        try:
                            self.queue[guild_id].remove(list_obj)
                        except IndexError:
                            pass
                        self.recent_logs[guild_id][channelType].append([embed, logged_at])
                        break

                if log_type == 'multi':
                    # noinspection PyUnboundLocalVariable
                    for log in self.recent_logs[guild_id][channelType]:
                        if time() - log[1] > 60*60*24:
                            self.recent_logs[guild_id][channelType].remove(log)
                elif log_type == 'single':
                    for log in self.recent_logs[guild_id]:
                        if time() - log[1] > 60*60*24:
                            self.recent_logs[guild_id].remove(log)
                await asyncio.sleep(0.21)

    async def init_invites(self) -> None:
        """ Indexes each servers invites """
        for guild_id in self.config.keys():
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
        return datetime.utcnow() - timedelta(seconds=10)

    async def search_audit(self, guild, *actions) -> dict:
        """ Returns the latest entry from a list of actions """
        dat = {
            'user': 'Unknown',
            'actual_user': None,
            'target': 'Unknown',
            'icon_url': guild.icon_url,
            'thumbnail_url': guild.icon_url,
            'reason': None,
            'extra': None,
            'changes': None,
            'before': None,
            'after': None,
            'recent': False
        }
        can_run = await self.wait_for_permission(guild, "view_audit_log")
        if can_run:
            async for entry in guild.audit_logs(limit=5):
                if entry.created_at > self.past and any(entry.action.name == action.name for action in actions):
                    dat['action'] = entry.action
                    if entry.user:
                        dat['user'] = entry.user.mention
                        dat['actual_user'] = entry.user
                        dat['thumbnail_url'] = entry.user.avatar_url
                    if entry.target and isinstance(entry.target, discord.Member):
                        dat['target'] = entry.target.mention
                        dat['icon_url'] = entry.target.avatar_url
                    elif entry.target:
                        dat['target'] = entry.target
                    else:
                        if entry.user:
                            dat['icon_url'] = entry.user.avatar_url
                    dat['reason'] = entry.reason
                    dat['extra'] = entry.extra
                    dat['changes'] = entry.changes
                    dat['before'] = entry.before
                    dat['after'] = entry.after
                    dat['recent'] = True
                    break
        return dat

    @commands.group(name='logger', aliases=['log', 'secure-log'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def logger(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=fate())
            e.set_author(name='| Action Logger', icon_url=ctx.guild.icon_url)
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = "*A more detailed audit log that logs changes to the server and more to ~~a~~ dedicated channel(s)*"
            e.add_field(
                name='◈ Security',
                value=">>> Logs can't be deleted by anyone, they aren't purge-able, and it "
                      "re-creates deleted log channels and resends the last 12 hours of logs",
                inline=False
            )
            e.add_field(
                name='◈ Multi-Log',
                value="> Sorts logs into multiple channels within a category like 'chat', 'actions', and 'updates'",
                inline=False
            )
            p = utils.get_prefix(ctx)
            e.add_field(
                name='◈ Commands',
                value=f"{p}log enable - `creates a log`"
                      f"\n{p}log disable - `deletes the log`"
                      f"\n{p}log switch - `toggles multi-log`"
                      f"\n{p}log security - `toggles security`"
                      f"\n{p}log ignore #channel - `ignore chat events`"
                      f"\n{p}log ignore @bot - `ignores bot spam`"
                      f"\n{p}log config `current setup overview`",
                inline=False
            )
            icon_url = 'https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png'
            e.set_footer(text="Security and Multi-Log are off by default", icon_url=icon_url)
            await ctx.send(embed=e)

    @logger.group(name='enable')
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx):
        """ Creates a multi-log """
        guild_id = str(ctx.guild.id)
        if guild_id in self.config:
            return await ctx.send("Logger is already enabled")
        perm_error = "I can't send messages in the channel I made\n" \
                     "If you want me to use your own, try `.logger setchannel`"
        try:
            channel = await ctx.guild.create_text_channel(name='discord-log')
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
            "type": "single",
            "secure": False,
            "ignored_channels": [],
            "ignored_bots": []
        }
        if guild_id in self.bot.logger_tasks and not self.bot.logger_tasks[guild_id].done():
            self.bot.logger_tasks[guild_id].cancel()
        task = self.bot.loop.create_task(self.start_queue(guild_id))
        self.bot.logger_tasks[guild_id] = task
        await ctx.send("Enabled Logger")
        await self.save_data()

    @logger.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        """ Deletes a multi-log """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]['secure']:
            if ctx.author.id != ctx.guild.owner.id:
                return await ctx.send("Due to security settings, only the owner of the server can use this")
        del self.config[guild_id]
        await ctx.send('Disabled Logger')
        await self.save_data()

    @logger.group(name='setchannel', aliases=["set-channel"])
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
            if self.config[guild_id]["type"] == "multi":
                return await ctx.send("You can only use this on single-channel logs")
            self.config[guild_id]["channel"] = channel.id
        else:
            self.config[guild_id] = {
                "channel": channel.id,
                "channels": {},
                "type": "single",
                "secure": False,
                "ignored_channels": [],
                "ignored_bots": []
            }
        if guild_id in self.bot.logger_tasks and not self.bot.logger_tasks[guild_id].done():
            self.bot.logger_tasks[guild_id].cancel()
        task = self.bot.loop.create_task(self.start_queue(guild_id))
        self.bot.logger_tasks[guild_id] = task
        await ctx.send(f"Enabled Logger in {channel.mention}")
        await self.save_data()

    @logger.command(name='switch')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def _switch(self, ctx):
        """ Switches a log between multi and single """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Multi-Log isn't enabled")
        if self.config[guild_id]['type'] == 'single':
            await self.initiate_category(ctx.guild)
            self.config[guild_id]['type'] = 'multi'
            self.recent_logs[guild_id] = {
                Type: [] for Type in self.channel_types
            }
            await ctx.send("Switched to Multi-Log")
        else:
            log = await ctx.guild.create_text_channel(name='bot-logs')
            self.config[guild_id]['channel'] = log.id
            self.config[guild_id]['channels'] = {}
            self.config[guild_id]['type'] = 'single'
            self.recent_logs[guild_id] = []
            await ctx.send('Switched to Single-Log')
        await self.save_data()

    @logger.command(name='security')
    @is_guild_owner()
    @commands.bot_has_permissions(administrator=True)
    async def _toggle_security(self, ctx):
        """ Toggles whether or not to keep the log secure """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("You need to enable logger to use this")
        if self.config[guild_id]['secure']:
            self.config[guild_id]['secure'] = False
            await ctx.send('Disabled secure features')
        else:
            self.config[guild_id]['secure'] = True
            await ctx.send('Enabled secure features')
        await self.save_data()

    @logger.command(name='ignore')
    @commands.has_permissions(administrator=True)
    async def _ignore(self, ctx):
        """ ignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]['secure'] and ctx.author.id != ctx.guild.owner.id:
            return await ctx.send("Due to security settings, only the owner of the server can use this")
        for member in ctx.message.mentions:
            if member.id in self.config[guild_id]['ignored_bots']:
                await ctx.send(f"{member.mention} is already ignored")
            elif not member.bot:
                await ctx.send(f"{member.mention} is not a bot")
            else:
                self.config[guild_id]['ignored_bots'].append(member.id)
                await ctx.send(f"I'll now ignore chat related events from {member.mention}")
        for channel in ctx.message.channel_mentions:
            if channel.id in self.config[guild_id]['ignored_channels']:
                await ctx.send(f"{channel.mention} is already ignored")
            else:
                self.config[guild_id]['ignored_channels'].append(channel.id)
                await ctx.send(f"I'll now ignore chat related events from {channel.mention}")
        await self.save_data()

    @logger.command(name='unignore')
    @commands.has_permissions(administrator=True)
    async def _unignore(self, ctx):
        """ unignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Logger isn't enabled")
        if self.config[guild_id]['secure'] and ctx.author.id != ctx.guild.owner.id:
            return await ctx.send("Due to security settings, only the owner of the server can use this")
        for member in ctx.message.mentions:
            if member.id not in self.config[guild_id]['ignored_bots']:
                await ctx.send(f"{member.mention} isn't ignored")
            self.config[guild_id]['ignored_bots'].remove(member.id)
            await ctx.send(f"I'll no longer ignore chat related events from {member.mention}")
        for channel in ctx.message.channel_mentions:
            if channel.id not in self.config[guild_id]['ignored_channels']:
                await ctx.send(f"{channel.mention} isn't ignored")
            else:
                self.config[guild_id]['ignored_channels'].remove(channel.id)
                await ctx.send(f"I'll no longer ignore chat related events from {channel.mention}")
        await self.save_data()

    @logger.command(name='config')
    async def _config(self, ctx):
        """ sends an overview of the servers current config """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("There's currently no config for this server")
        e = discord.Embed(color=fate())
        e.set_author(name="Logger Config", icon_url=ctx.guild.owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = f"**Log Type:** {self.config[guild_id]['type']} channel" \
                        f"\n**Security:** {self.config[guild_id]['secure']}" \
                        f"\n**Channel:** {self.bot.get_channel(self.config[guild_id]['channel'])}"
        if self.config[guild_id]['ignored_channels']:
            channels = []
            for channel_id in self.config[guild_id]['ignored_channels']:
                channel = self.bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    channels.append(channel.mention)
            if channels:
                e.add_field(name='◈ Ignored Channels', value=', '.join(channels), inline=False)
        if self.config[guild_id]['ignored_bots']:
            bots = []
            for bot_id in self.config[guild_id]['ignored_bots']:
                bot = ctx.guild.get_member(bot_id)
                if isinstance(bot, discord.Member):
                    bots.append(bot.mention)
            if bots:
                e.add_field(name='◈ Ignored Bots', value=', '.join(bots), inline=False)
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in list(self.config.keys()):
            if guild_id in self.bot.logger_tasks and not self.bot.logger_tasks[guild_id].done():
                continue
            task = self.bot.loop.create_task(self.start_queue(guild_id))
            self.bot.logger_tasks[guild_id] = task
        if "keep_alive_task" in self.bot.logger_tasks:
            if self.bot.logger_tasks["keep_alive_task"].done():
                self.bot.log(
                    message="Loggers keep alive task came to an end",
                    level="CRITICAL",
                    tb=self.bot.logger_tasks["keep_alive_tasks"].result()
                )
            task = self.bot.loop.create_task(self.keep_alive_task())
            self.bot.logger_tasks["keep_alive_task"] = task
        if not self.bot.tcp_servers["logger"]:
            self.bot.tcp_servers["logger"] = await asyncio.start_server(
                self.handle_echo,
                host="127.0.0.1",
                port=self.bot.config["logger_port"],
                loop=self.bot.loop
            )
        self.bot.loop.create_task(self.init_invites())

    @commands.Cog.listener()
    async def on_message(self, msg):
        """ @everyone and @here event """
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.config:
                mention = None
                content = str(msg.content).lower()
                if '!everyone' in content:
                    mention = '@everyone'
                if '!here' in content:
                    mention = '@here'
                if mention:
                    m = await msg.channel.fetch_message(msg.id)
                    e = discord.Embed(color=white())
                    e.title = f"~==🍸{mention} mentioned🍸==~"
                    e.set_thumbnail(url=msg.author.avatar_url)
                    is_successful = False
                    member = msg.guild.get_member(msg.author.id)
                    if not member:
                        return
                    if member.guild_permissions.administrator:
                        is_successful = True
                    elif member.guild_permissions.mention_everyone and (
                            not msg.channel.permissions_for(msg.author).mention_everyone is False):
                        is_successful = True
                    elif msg.channel.permissions_for(msg.author).mention_everyone:
                        is_successful = True
                    if is_successful:
                        e.description = self.bot.utils.format_dict({
                            "Author": msg.author.mention,
                            "Channel": msg.channel.mention,
                            f"[Jump to MSG]({msg.jump_url})": None
                        })
                        for group in self.bot.utils.split(m.content, 1024):
                            e.add_field(name='Content', value=group, inline=False)
                        self.queue[guild_id].append([e, 'system+', time()])

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.guild, discord.Guild):
            guild_id = str(before.guild.id)
            if guild_id in self.config and not after.author.bot:
                if before.content != after.content:
                    if before.author.id in self.config[guild_id]['ignored_bots']:
                        return
                    if before.channel.id in self.config[guild_id]['ignored_channels']:
                        return

                    e = discord.Embed(color=pink())
                    e.set_author(name='~==🍸Msg Edited🍸==~', icon_url=before.author.avatar_url)
                    e.set_thumbnail(url=before.author.avatar_url)
                    e.description = self.bot.utils.format_dict({
                        "author": before.author.mention,
                        "Channel": before.channel.mention,
                        f"[Jump to MSG]({before.jump_url})": None
                    })
                    for group in [before.content[i:i + 1024] for i in range(0, len(before.content), 1024)]:
                        e.add_field(name='◈ Before', value=group, inline=False)
                    for group in [after.content[i:i + 1024] for i in range(0, len(after.content), 1024)]:
                        e.add_field(name='◈ After', value=group, inline=False)
                    self.queue[guild_id].append([e, 'chat', time()])

                if before.embeds and not after.embeds:
                    if before.author.id in self.config[guild_id]['ignored_bots']:
                        return
                    if before.channel.id in self.config[guild_id]['ignored_channels']:
                        return

                    if before.channel.id == self.config[guild_id]['channel'] or (  # a message in the log was suppressed
                            before.channel.id in self.config[guild_id]['channels']):
                        await asyncio.sleep(0.5)  # prevent updating too fast and not showing on the users end
                        return await after.edit(suppress=False, embed=before.embeds[0])
                    e = discord.Embed(color=pink())
                    e.set_author(name='~==🍸Embed Hidden🍸==~', icon_url=before.author.avatar_url)
                    e.set_thumbnail(url=before.author.avatar_url)
                    e.description = self.bot.utils.format_dict({
                        "author": before.author.mention,
                        "Channel": before.channel.mention,
                        f"[Jump to MSG]({before.jump_url})": None
                    })
                    em = before.embeds[0].to_dict()
                    fp = f'./static/embed-{before.id}.json'
                    with open(fp, 'w+') as f:
                        json.dump(em, f, sort_keys=True, indent=4, separators=(',', ': '))
                    self.queue[guild_id].append([(e, fp), 'chat', time()])

                if before.pinned != after.pinned:
                    action = 'Unpinned' if before.pinned else 'Pinned'
                    audit_dat = await self.search_audit(after.guild, audit.message_pin)
                    e = discord.Embed(color=cyan())

                    e.set_author(name=f'~==🍸Msg {action}🍸==~', icon_url=after.author.avatar_url)
                    e.set_thumbnail(url=after.author.avatar_url)
                    e.description = self.bot.utils.format_dict({
                        "Author": after.author.mention,
                        "Channel": after.channel.mention,
                        "Who Pinned": audit_dat['user'],
                        f"[Jump to MSG]({after.jump_url})": None
                    })
                    for text_group in self.bot.utils.split(after.content,1000):
                        e.add_field(name="◈ Content", value=text_group, inline=False)
                    self.queue[guild_id].append([e, 'chat', time()])

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel = self.bot.get_channel(int(payload.data['channel_id']))
        if not isinstance(channel, discord.DMChannel):
            guild_id = str(channel.guild.id)
            if guild_id in self.config and not payload.cached_message:
                msg = await channel.fetch_message(payload.message_id)
                if msg.author.id in self.config[guild_id]['ignored_bots']:
                    return
                if msg.channel.id in self.config[guild_id]['ignored_channels']:
                    return
                e = discord.Embed(color=pink())
                e.set_author(name='Uncached Msg Edited', icon_url=msg.author.avatar_url)
                e.set_thumbnail(url=msg.author.avatar_url)
                e.description = self.bot.utils.format_dict({
                    "Author": msg.author.mention,
                    "Channel": channel.mention,
                    f"[Jump to MSG]({msg.jump_url})": None
                })
                for text_group in self.bot.utils.split(msg.content, 1024):
                    e.add_field(name='◈ Content', value=text_group, inline=False)
                self.queue[guild_id].append([e, 'chat', time()])

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.config:
                if self.config[guild_id]['secure']:
                    if msg.embeds and msg.channel.id == self.config[guild_id]['channel'] or (
                            msg.channel.id in self.config[guild_id]['channels'].values()):

                        await msg.channel.send("OwO what's this", embed=msg.embeds[0])
                        if msg.attachments:
                            files = []
                            for attachment in msg.attachments:
                                fp = os.path.join('static', attachment.filename)
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(attachment.proxy_url) as resp:
                                        file = await resp.read()
                                async with aiofiles.open(fp, 'wb') as f:
                                    await f.write(file)
                                files.append(fp)
                            self.queue[guild_id].append([(msg.embeds[0], files), 'sudo', time()])
                        else:
                            self.queue[guild_id].append([msg.embeds[0], 'sudo', time()])

                        return

                if msg.author.id == self.bot.user.id and 'your cooldowns up' in msg.content:
                    return  # is from work notifs within the factions module
                if msg.author.id in self.config[guild_id]['ignored_bots']:
                    return
                if msg.channel.id in self.config[guild_id]['ignored_channels']:
                    return

                e = discord.Embed(color=purple())
                dat = await self.search_audit(msg.guild, audit.message_delete)
                if dat['thumbnail_url'] == msg.guild.icon_url:
                    dat['thumbnail_url'] = msg.author.avatar_url
                e.set_author(name='~==🍸Msg Deleted🍸==~', icon_url=dat['thumbnail_url'])
                e.set_thumbnail(url=msg.author.avatar_url)
                e.description = self.bot.utils.format_dict({
                    "Author": msg.author.mention,
                    "Channel": msg.channel.mention,
                    "Deleted by": dat['user']
                })
                for text_group in self.bot.utils.split(msg.content, 1024):
                    e.add_field(name='◈ MSG Content', value=text_group, inline=False)
                if msg.embeds:
                    e.set_footer(text='⇓ Embed ⇓')
                if msg.attachments:
                    files = []
                    for attachment in msg.attachments:
                        fp = os.path.join('static', attachment.filename)
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.proxy_url) as resp:
                                file = await resp.read()
                        async with aiofiles.open(fp, 'wb') as f:
                            await f.write(file)
                        files.append(fp)
                    self.queue[guild_id].append([(e, files), 'chat', time()])
                else:
                    self.queue[guild_id].append([e, 'chat', time()])
                if msg.embeds:
                    self.queue[guild_id].append([msg.embeds[0], 'chat', time()])

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config and not payload.cached_message:
            if payload.channel_id in self.config[guild_id]['ignored_channels']:
                return
            guild = self.bot.get_guild(payload.guild_id)
            e = discord.Embed(color=purple())
            dat = await self.search_audit(guild, audit.message_delete)
            e.set_author(name='Uncached Message Deleted', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Author": dat['target'],
                "MSG ID": payload.message_id,
                "Channel": self.bot.get_channel(payload.channel_id).mention,
                "Deleted by": dat['user']
            })
            self.queue[guild_id].append([e, 'chat', time()])

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config:
            guild = self.bot.get_guild(payload.guild_id)
            channel = self.bot.get_channel(payload.channel_id)
            purged_messages = ''
            for msg in payload.cached_messages:

                if self.config[guild_id]['secure']:
                    if msg.embeds:
                        if msg.channel.id == self.config[guild_id]['channel']:
                            self.queue[guild_id].append([msg.embeds[0], 'sudo', time()])
                            continue
                        if msg.channel.id in self.config[guild_id]['channels']:
                            await msg.channel.send("OwO what's this", embed=msg.embeds[0])
                            self.queue[guild_id].append([msg.embeds[0], 'sudo', time()])
                            continue

                timestamp = msg.created_at.strftime('%I:%M%p')
                purged_messages = f"{timestamp} | {msg.author}: {msg.content}\n{purged_messages}"

            if payload.cached_messages and not purged_messages:  # only logs were purged
                return

            fp = f'./static/purged-messages-{r.randint(0, 9999)}.txt'
            with open(fp, 'w') as f:
                f.write(purged_messages)

            e = discord.Embed(color=lime_green())
            dat = await self.search_audit(guild, audit.message_bulk_delete)
            if dat['extra'] and dat['icon_url']:
                e.set_author(name=f"~==🍸{dict(dat['extra'])['count']} Msgs Purged🍸==~", icon_url=dat['icon_url'])
            else:
                e.set_author(name=f"~==🍸{len(payload.cached_messages)} Msgs Purged🍸==~")
            if dat['thumbnail_url']:
                e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Users Effected": len(list(set([msg.author for msg in payload.cached_messages]))),
                "Channel": channel.mention,
                "Purged by": dat['user']
            })
            self.queue[guild_id].append([(e, fp), 'chat', time()])

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        guild_id = str(payload.guild_id)
        if guild_id in self.config:
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            if msg.author.id in self.config[guild_id]['ignored_bots']:
                return
            if msg.channel.id in self.config[guild_id]['ignored_channels']:
                return
            e = discord.Embed(color=yellow())
            e.set_author(name='~==🍸Reactions Cleared🍸==~', icon_url=msg.author.avatar_url)
            e.set_thumbnail(url=msg.author.avatar_url)
            e.description = self.bot.utils.format_dict({
                "Author": msg.author.mention,
                "Channel": channel.mention,
                f"[Jump to MSG]({msg.jump_url})": None
            })
            self.queue[guild_id].append([e, 'chat', time()])

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):  # due for rewrite
        guild_id = str(after.id)
        if guild_id in self.config:
            dat = await self.search_audit(after, audit.guild_update)

            def create_template_embed():
                """ Creates a new embed to work with """
                em = discord.Embed(color=lime_green())
                em.set_author(name='~==🍸Server Updated🍸==~', icon_url=dat['icon_url'])
                em.set_thumbnail(url=after.icon_url)
                return em

            e = create_template_embed()
            if before.name != after.name:
                e.description = f"> 》__**Name Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                e.add_field(name='◈ Before', value=before.name, inline=False)
                e.add_field(name='◈ After', value=after.name, inline=False)
                self.queue[guild_id].append([e, 'updates', time()])
            if before.icon_url != after.icon_url:
                e = create_template_embed()
                e.description = f"> 》__**Icon Changed**__《" \
                                f"\n**Changed by:** [{dat['user']}]"
                if not before.is_icon_animated() and after.is_icon_animated():
                    e.description += f"\n__**Icons now animated**__"
                if not after.is_icon_animated() and before.is_icon_animated():
                    e.description += f'\n__**Icons no longer animated**__'
                self.queue[guild_id].append([e, 'updates', time()])
            if before.banner_url != after.banner_url:
                e = create_template_embed()
                e.description = f"> 》__**Banner Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                self.queue[guild_id].append([e, 'updates', time()])
            if before.splash_url != after.splash_url:
                e = create_template_embed()
                e.description = f"> 》__**Splash Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                self.queue[guild_id].append([e, 'updates', time()])
            if before.region != after.region:
                e = create_template_embed()
                e.description = f"> 》__**Region Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                e.add_field(name='◈ Before', value=str(before.region), inline=False)
                e.add_field(name='◈ After', value=str(after.region), inline=False)
                self.queue[guild_id].append([e, 'updates', time()])
            if before.afk_timeout != after.afk_timeout:
                e = create_template_embed()
                e.description = f"> 》__**AFK Timeout Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                e.add_field(name='◈ Before', value=str(before.afk_timeout), inline=False)
                e.add_field(name='◈ After', value=str(after.afk_timeout), inline=False)
                self.queue[guild_id].append([e, 'updates', time()])
            if before.afk_channel != after.afk_channel:
                e = create_template_embed()
                e.description = f"> 》__**AFK Channel Changed**__《" \
                                f"\n**Changed by:** {dat['user']}"
                if before.afk_channel:
                    e.add_field(
                        name='◈ Before',
                        value=f"**Name:** {before.afk_channel.name}"
                              f"\n**ID:** {before.afk_channel.id}",
                        inline=False
                    )
                if after.afk_channel:
                    e.add_field(
                        name='◈ After',
                        value=f"**Name:** {after.afk_channel.name}"
                              f"\n**ID:** {after.afk_channel.id}",
                        inline=False
                    )
                self.queue[guild_id].append([e, 'updates', time()])
            if before.owner != after.owner:
                e = create_template_embed()
                e.description = f"> 》__**Owner Changed**__《"
                e.add_field(
                    name='◈ Before',
                    value=f"**Name:** {before.owner.name}"
                          f"\n**Mention:** {before.owner.mention}"
                          f"\n**ID:** {before.owner.id}"
                )
                e.add_field(
                    name='◈ After',
                    value=f"**Name:** {after.owner.name}"
                          f"\n**Mention:** {after.owner.mention}"
                          f"\n**ID:** {after.owner.id}"
                )
                self.queue[guild_id].append([e, 'updates', time()])
            if before.features != after.features and before.features or after.features:
                e = create_template_embed()
                e.description = f"> 》__**Features Changed**__《"
                changes = ''
                for feature in before.features:
                    if feature not in after.features:
                        changes += f"❌ {feature}"
                for feature in after.features:
                    if feature not in before.features:
                        changes += f"<:plus:548465119462424595> {feature}"
                if changes:
                    e.add_field(name='◈ Changes', value=changes)
                    self.queue[guild_id].append([e, 'updates', time()])
            if before.premium_tier != after.premium_tier:
                e = discord.Embed(color=pink())
                action = "lowered" if before.premium_tier > after.premium_tier else "raised"
                e.description = f"Servers boost level {action} to {after.premium_tier}"
                self.queue[guild_id].append([e, 'updates', time()])
            if before.premium_subscription_count != after.premium_subscription_count:
                e = create_template_embed()
                if after.premium_subscription_count > before.premium_subscription_count:
                    action = 'Boosted'
                else:
                    action = 'Unboosted'
                who = 'Unknown, has another boost'
                if before.premium_subscribers != after.premium_subscribers:
                    changed = [m for m in before.premium_subscribers if m not in after.premium_subscribers]
                    if not changed:
                        changed = [m for m in after.premium_subscribers if m not in before.premium_subscribers]
                    who = changed[0].mention
                e.description = f"> **Member {action}**《" \
                                f"\n**Who:** [{who}]"
                self.queue[guild_id].append([e, 'system+', time()])
            # mfa_level, verification_level, explicit_content_filter, default_notifications
            # preferred_locale, large, system_channel, system_channel_flags
            # Union[emoji_limit, bitrate_limit, filesize_limit]

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=yellow())
            dat = await self.search_audit(channel.guild, audit.channel_create)
            e.set_author(name='~==🍸Channel Created🍸==~', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            member_count = 'Unknown'
            if not isinstance(channel, discord.CategoryChannel):
                member_count = len(channel.members)
            mention = 'None'
            if isinstance(channel, discord.TextChannel):
                mention = channel.mention
            e.description = self.bot.utils.format_dict({
                "Name": channel.name,
                "Mention": mention,
                "ID": channel.id,
                "Creator": dat['user'],
                "Members": member_count
            })
            self.queue[guild_id].append([e, 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:

            # anti log channel deletion
            if self.config[guild_id]['secure']:
                log_type = self.config[guild_id]['type']
                if channel.id == self.config[guild_id]['channel']:
                    if log_type == 'single':
                        for embed in self.recent_logs[guild_id]:
                            self.queue[guild_id].append([embed, 'actions', time()])
                        return
                    for channelType, embeds in self.recent_logs[guild_id].items():
                        for embed, logged_at in embeds:
                            self.queue[guild_id].append([embed, channelType, logged_at])
                for channelType, channel_id in self.config[guild_id]['channels'].items():
                    if channel_id == channel.id:
                        for embed, logged_at in self.recent_logs[guild_id][channelType]:
                            self.queue[guild_id].append([embed, channelType, logged_at])

            dat = await self.search_audit(channel.guild, audit.channel_delete)
            member_count = 'Unknown'
            if not isinstance(channel, discord.CategoryChannel):
                member_count = len(channel.members)
            category = 'None'
            if channel.category:
                category = channel.category.name

            e = discord.Embed(color=red())
            e.set_author(name='~==🍸Channel Deleted🍸==~', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Name": channel.name,
                "ID": channel.id,
                "Category": category,
                "Members": member_count,
                "Deleted by": dat['user']
            })

            if isinstance(channel, discord.CategoryChannel):
                self.queue[guild_id].append([e, 'actions', time()])
                return

            fp = f'./static/members-{r.randint(1, 9999)}.txt'
            members = f"{channel.name} - Member List"
            for member in channel.members:
                members += f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
            with open(fp, 'w') as f:
                f.write(members)

            self.queue[guild_id].append([(e, fp), 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):  # due for rewrite
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=orange())
            dat = await self.search_audit(after.guild, audit.channel_update)
            e.set_thumbnail(url=after.guild.icon_url)
            # category = 'None, or Changed'
            # if after.category and before.category == after.category:
            #     category = after.category.name

            if before.name != after.name:
                e.add_field(
                    name='~==🍸Channel Renamed🍸==~',
                    value=self.bot.utils.format_dict({
                        "Mention": after.mention,
                        "ID": after.id,
                        "Changed by": dat['user']
                    }),
                    inline=False
                )
                e.add_field(name='◈ Before', value=before.name)
                e.add_field(name='◈ After', value=after.name)

            if before.position != after.position:
                e.add_field(
                    name='~==🍸Channel Moved🍸==~',
                    value=self.bot.utils.format_dict({
                        "Mention": after.mention,
                        "ID": after.id,
                        "Changed by": dat['user']
                    }),
                    inline=False
                )
                e.add_field(name='Before', value=str(before.position))
                e.add_field(name='After', value=str(after.position))

            if isinstance(before, discord.TextChannel):
                if before.topic != after.topic:
                    if before.id not in self.config[guild_id]['ignored_channels']:
                        e.add_field(
                            name='~==🍸Topic Updated🍸==~',
                            value=self.bot.utils.format_dict({
                                "Name": after.name,
                                "Mention": after.mention,
                                "ID": after.id,
                                "Changed by": dat['user']
                            }),
                            inline=False
                        )
                        if before.topic:
                            for text_group in self.bot.utils.split(before.topic):
                                e.add_field(name='◈ Before', value=text_group, inline=False)
                        if after.topic:
                            for text_group in self.bot.utils.split(after.topic):
                                e.add_field(name='◈ After', value=text_group, inline=False)

            if before.category != after.category:
                e.add_field(
                    name='~==🍸Channel Re-Categorized🍸==~',
                    value=self.bot.utils.format_dict({
                        "Name": after.name,
                        "Mention": after.mention,
                        "ID": after.id,
                        "Changed by": dat['user']
                    }),
                    inline=False
                )
                name = 'None'
                if before.category:
                    name = before.category.name
                e.add_field(
                    name='◈ Before',
                    value=name
                )
                name = 'None'
                if after.category:
                    name = after.category.name
                e.add_field(
                    name='◈ After',
                    value=name
                )

            if before.overwrites != after.overwrites:
                for obj, permissions in list(before.overwrites.items()):
                    after_objects = [x[0] for x in after.overwrites.items()]
                    if obj not in after_objects:
                        dat = await self.search_audit(after.guild, audit.overwrite_delete)
                        perms = '\n'.join([f"{perm} - {value}" for perm, value in list(permissions) if value])
                        e.add_field(
                            name=f'❌ {obj.name} removed',
                            value=perms if perms else "-had no permissions",
                            inline=False
                        )
                        continue

                    after_values = list(list(after.overwrites.items())[after_objects.index(obj)][1])
                    if list(permissions) != after_values:
                        dat = await self.search_audit(after.guild, audit.overwrite_update)
                        e.add_field(
                            name=f'<:edited:550291696861315093> {obj.name}',
                            value='\n'.join([
                                f"{perm} - {after_values[i][1]}" for i, (perm, value) in enumerate(list(permissions)) if (
                                    value != after_values[i][1])
                            ]),
                            inline=False
                        )

                for obj, permissions in after.overwrites.items():
                    if obj not in [x[0] for x in before.overwrites.items()]:
                        dat = await self.search_audit(after.guild, audit.overwrite_create)
                        perms = '\n'.join([f"{perm} - {value}" for perm, value in list(permissions) if value])
                        e.add_field(
                            name=f'<:plus:548465119462424595> {obj.name}',
                            value=perms if perms else "-has no permissions",
                            inline=False
                        )

                e.description = self.bot.utils.format_dict({
                    "Name": after.name,
                    "Mention": after.name,
                    "ID": after.id,
                    "Changed by": dat['user']
                })

            if e.fields:
                self.queue[guild_id].append([e, 'updates', time()])

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild_id = str(role.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(role.guild, audit.role_create)
            e = discord.Embed(color=lime_green())
            e.set_author(name='~==🍸Role Created🍸==~', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Mention": role.mention,
                "ID": role.id,
                "Created by": dat['user']
            })
            self.queue[guild_id].append([e, 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild_id = str(role.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(role.guild, audit.role_delete)
            e = discord.Embed(color=dark_green())
            e.set_author(name='~==🍸Role Deleted🍸==~', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Name": role.name,
                "ID": role.id,
                "Members": len(role.members) if role.members else 'None',
                "Deleted by": dat['user']
            })
            card = Image.new('RGBA', (25, 25), color=role.color.to_rgb())
            fp = os.getcwd() + f'/static/color-{r.randint(1111, 9999)}.png'
            card.save(fp, format='PNG')
            e.set_footer(
                text=f"Hex {role.color} | RGB {role.color.to_rgb()}",
                icon_url="attachment://" + os.path.basename(fp)
            )
            fp1 = f'./static/role-members-{r.randint(1, 9999)}.txt'
            members = f"{role.name} - Member List"
            for member in role.members:
                members += f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
            with open(fp1, 'w') as f:
                f.write(members)
            self.queue[guild_id].append([(e, [fp1, fp]), 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            fp = None
            dat = await self.search_audit(after.guild, audit.role_update)
            e = discord.Embed(color=green())
            e.set_author(name='~==🍸Role Updated🍸==~', icon_url=dat['thumbnail_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Name": after.name,
                "Mention": after.mention,
                "ID": before.id,
                "Changed by": dat['user']
            })

            if before.name != after.name:
                e.add_field(
                    name='◈ Name Changed',
                    value=f"**Before:** {before.name}"
                          f"\n**After:** {after.name}",
                    inline=False
                )
            if before.color != after.color:
                # def font(size):
                #     return ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", size)

                card = Image.new('RGBA', (200, 30), color=after.color.to_rgb())
                # draw = ImageDraw.Draw(card)
                # draw.text((180 - 2, 5), 'After', (0, 0, 0), font=font(45))
                # draw.text((180 + 2, 5), 'After', (0, 0, 0), font=font(45))
                # draw.text((180, 5 - 2), 'After', (0, 0, 0), font=font(45))
                # draw.text((180, 5 + 2), 'After', (0, 0, 0), font=font(45))
                # draw.text((180, 5), 'After', (255, 255, 255), font=font(45))

                box = Image.new('RGBA', (100, 30), color=before.color.to_rgb())
                # draw = ImageDraw.Draw(box)
                # draw.text((10 - 2, 5), 'Before', (0, 0, 0), font=font(45))
                # draw.text((10 + 2, 5), 'Before', (0, 0, 0), font=font(45))
                # draw.text((10, 5 - 2), 'Before', (0, 0, 0), font=font(45))
                # draw.text((10, 5 + 2), 'Before', (0, 0, 0), font=font(45))
                # draw.text((10, 5), 'Before', (255, 255, 255), font=font(45))

                card.paste(box)
                fp1 = os.getcwd() + f'/static/color-{r.randint(1, 999)}.png'
                card.save(fp1)

                e.set_image(url="attachment://" + os.path.basename(fp1))
                e.set_thumbnail(url=dat['thumbnail_url'])
                e.add_field(
                    name='◈ Color Changed',
                    value=f"From **{before.color}** -> **{after.color}**"
                )
            if before.hoist != after.hoist:
                action = 'is now visible'
                if after.hoist is False:
                    action = 'is no longer visible'
                e.description += f"[{action}]"
            if before.mentionable != after.mentionable:
                action = 'is now mentionable'
                if not after.mentionable:
                    action = 'is no longer mentionable'
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
                self.queue[guild_id].append([em, 'updates', time()])

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
                changes = ''
                for i, (perm, value) in enumerate(iter(before.permissions)):
                    if value != list(after.permissions)[i][1]:
                        changes += f"\n• {perm} {'unallowed' if value else 'allowed'}"
                e.add_field(name='◈ Permissions Changed', value=changes, inline=False)
            if e.fields:
                if fp:
                    self.queue[guild_id].append([(e, fp), 'updates', time()])
                else:
                    self.queue[guild_id].append([e, 'updates', time()])

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        guild_id = str(guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=light_gray())
            e.set_author(name='~==🍸Integrations Update🍸==~', icon_url=guild.owner.avatar_url)
            e.set_thumbnail(url=guild.icon_url)
            e.description = "An integration was created, modified, or removed"
            self.queue[guild_id].append([e, 'system+', time()])

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild_id = str(channel.guild.id)
        if guild_id in self.config:
            dat = await self.search_audit(
                channel.guild,
                audit.webhook_create,
                audit.webhook_delete,
                audit.webhook_update
            )

            who = dat['actual_user']  # type: discord.Member
            if who and who.bot and who.id in self.config[guild_id]['ignored_bots']:
                return

            if dat['action'].name == 'webhook_create':
                action = 'Created'
            elif dat['action'].name == 'webhook_delete':
                action = 'Deleted'
            else:  # webhook update
                action = 'Updated'

            e = discord.Embed(color=cyan())
            e.set_author(name=f'~==🍸Webhook {action}🍸==~', icon_url=dat['icon_url'])
            e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = ''

            if action != 'Deleted':
                webhook = await self.bot.fetch_webhook(dat['target'].id)
                channel = self.bot.get_channel(webhook.channel_id)
                e.set_thumbnail(url=webhook.avatar_url)
                e.description = self.bot.utils.format_dict({
                    "Name": webhook.name,
                    "Type": webhook.type
                })

            e.description += self.bot.utils.format_dict({
                "ID": dat['target'].id,
                "Channel": channel.mention,
                f"{action} by": dat['user']
            })
            self.queue[guild_id].append([e, 'misc', time()])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if guild_id in self.config:
            if member.bot:
                dat = await self.search_audit(member.guild, audit.bot_add)
                e = discord.Embed(color=light_gray())
                e.set_author(name='~==🍸Bot Added🍸==~', icon_url=dat['icon_url'])
                e.set_thumbnail(url=dat['thumbnail_url'])
                inv = f'https://discordapp.com/oauth2/authorize?client_id={member.id}&permissions=0&scope=bot'
                e.description = self.bot.utils.format_dict({
                    "Name": member.name,
                    "Mention": member.mention,
                    "ID": member.id,
                    "Bot Invite": f'[here]({inv})',
                    "Invited by": dat['user']
                })
                self.queue[guild_id].append([e, 'system+', time()])
                return
            invites = await member.guild.invites()
            invite = None  # the invite used to join
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
            e = discord.Embed(color=lime_green())
            icon_url = member.avatar_url
            inviter = 'Unknown'
            if invite.inviter:
                icon_url = invite.inviter.avatar_url
                inviter = invite.inviter
            e.set_author(name='~==🍸Member Joined🍸==~', icon_url=icon_url)
            e.set_thumbnail(url=member.avatar_url)
            e.description = self.bot.utils.format_dict({
                "Name": member.name,
                "Mention": member.mention,
                "ID": member.id,
                "Invited by": inviter,
                "Invite": f'[{invite.code}]({invite.url})'
            })
            aliases = list(set([
                m.display_name for m in [
                    server.get_member(member.id) for server in self.bot.guilds if member in server.members
                ] if m.id == member.id and m.display_name != member.name
            ]))
            if len(aliases) > 0:
                e.add_field(
                    name='◈ Aliases',
                    value=', '.join(aliases),
                    inline=False
                )
            self.queue[guild_id].append([e, 'misc', time()])

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=red())
            e.description = self.bot.utils.format_dict({
                "Username": member,
                "Mention": member.mention,
                "ID": member.id,
                "Top Role": member.top_role.mention
            })
            e.set_thumbnail(url=member.avatar_url)
            removed = False

            can_run = await self.wait_for_permission(member.guild, "view_audit_log")
            if not can_run:
                return

            async for entry in member.guild.audit_logs(limit=1, action=audit.kick):
                if entry.target.id == member.id and entry.created_at > self.past:
                    e.set_author(name='~==🍸Member Kicked🍸==~', icon_url=entry.user.avatar_url)
                    e.description += self.bot.utils.format_dict({
                        "Kicked by": entry.user.mention
                    })
                    self.queue[guild_id].append([e, 'sudo', time()])
                    removed = True

            async for entry in member.guild.audit_logs(limit=1, action=audit.ban):
                if entry.target.id == member.id and entry.created_at > self.past:
                    e.set_author(name='~==🍸Member Banned🍸==~', icon_url=entry.user.avatar_url)
                    e.description += self.bot.utils.format_dict({
                        "Banned by": entry.user.mention
                    })
                    self.queue[guild_id].append([e, 'sudo', time()])
                    removed = True

            if not removed:
                e.set_author(name='~==🍸Member Left🍸==~', icon_url=member.avatar_url)
                self.queue[guild_id].append([e, 'misc', time()])

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_id = str(before.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=blue())
            if before.display_name != after.display_name:
                e.set_author(name="~==🍸Nick Changed🍸==~")
                e.description = self.bot.utils.format_dict({
                    "User": after,
                    "Mention": after.mention,
                    "ID": after.id
                })
                e.add_field(name="◈ Before", value=before.display_name)
                e.add_field(name="◈ After", value=after.display_name)
                self.queue[guild_id].append([e, 'updates', time()])

            if len(before.roles) != len(after.roles):
                dat = await self.search_audit(after.guild, audit.member_role_update)
                e.set_thumbnail(url=dat['thumbnail_url'])
                if len(before.roles) > len(after.roles):
                    action = "Revoked"
                    roles = [role for role in before.roles if role not in after.roles]
                    e.description = f"{roles[0].mention} was taken from {before}"
                else:
                    action = "Granted"
                    roles = [role for role in after.roles if role not in before.roles]
                    e.description = f"{roles[0].mention} was given to {before}"
                e.set_author(name=f"~==🍸Role {action}🍸==~", icon_url=dat['icon_url'])
                info = {
                    "User": after.mention,
                    "Role": roles[0].name,
                    "Role ID": roles[0].id,
                    f"{action} by": dat['user']
                }
                e.add_field(
                    name="◈ Information",
                    value=self.bot.utils.format_dict(info),
                    inline=False
                )
                self.queue[guild_id].append([e, 'updates', time()])


def setup(bot):
    bot.add_cog(Logger(bot))


def teardown(bot):
    for task_id, task in bot.logger_tasks.items():
        if not task.done():
            task.cancel()
        del bot.logger_tasks[task_id]
