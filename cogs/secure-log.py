"""
Discord.Py v1.3+ Action Logs Module:
+ can split up into multiple channels
+ key security features to protect the log
- logs can't be deleted or purged by anyone
- re-creates deleted log channel(s) and resends the last x logs

Super Important To-Do list:
+ add time() to all the lists of args where logs are queued
- this is to keep ALL the logs from the last x hours instead
  of only keeping the last x logs regardless of timeframe
- default 6h-12h, can be adjusted to a max of 48h
- self.queue[guild_id].append([embed, type, time()])
+ add member update logs
- whence this is done the log will replace the old .logger
+ recolor the embeds so there's no duplicate colors
- try to match the colors for .logger
+ add a check in each log event which uses the audit that queues an
  embed denoting the bot lost perms and wait for perms silently
  for up to 12h as the queue will already notify the owner
"""

import asyncio
from os import path
import json
import os
from datetime import datetime, timedelta
import requests
import traceback
from time import time

from discord.ext import commands
import discord
from discord import AuditLogAction as audit
from PIL import Image, ImageDraw, ImageFont

from utils.colors import *
from utils import utils, config


def is_guild_owner():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner.id or (
            ctx.author.id == config.owner_id())  # for testing

    return commands.check(predicate)


class SecureLog(commands.Cog):
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

        self.invites = {}
        if self.bot.is_ready():
            self.bot.loop.create_task(self.init_invites())
            for guild_id in self.config.keys():
                bot.tasks.start(self.start_queue, guild_id, task_id=f'queue-{guild_id}', kill_existing=True)
        self.role_pos_cd = {}

    def save_data(self):
        """ Saves local variables """
        with open(self.path, 'w+') as f:
            json.dump(self.config, f)

    async def initiate_category(self, guild):
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

    async def start_queue(self, guild_id: str):
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

            log_type = self.config[guild_id]['type']  # type: str

            for embed, channelType, logged_at in self.queue[guild_id][-175:]:
                list_obj = [embed, channelType, logged_at]
                file_paths = []; files = []
                if isinstance(embed, tuple):
                    embed, file_paths = embed
                    if not isinstance(file_paths, list):
                        file_paths = [file_paths]
                    files = [discord.File(file) for file in file_paths if os.path.isfile(file)]

                for i, field in enumerate(embed.fields):
                    if not field.value:
                        embed.fields[i].value = 'None'

                embed.timestamp = datetime.fromtimestamp(logged_at)

                sent = False
                while not guild.me.guild_permissions.administrator:
                    if not sent:
                        try:
                            await guild.owner.send(
                                f"I need administrator permissions in {guild} for the multi-log to function securely. "
                                f"Until that's satisfied, i'll keep a maximum of 175 logs in queue"
                            )
                        except:
                            pass
                        sent = True
                    await asyncio.sleep(60)

                category = self.bot.get_channel(self.config[guild_id]['channel'])
                while not category:
                    try:
                        category = await self.bot.fetch_channel(self.config[guild_id]['channel'])
                    except (discord.errors.Forbidden, discord.errors.NotFound):
                        if log_type == 'multi':
                            category = await self.initiate_category(guild)
                            self.save_data()
                        elif log_type == 'single':
                            category = await guild.create_text_channel(name='bot-logs')
                            self.config[guild_id]['channel'] = category.id
                        self.save_data()
                        break
                    else:
                        break


                try:
                    if isinstance(category, discord.TextChannel):  # single channel log
                        try:
                            await category.send(embed=embed, files=files)
                        except:
                            e = discord.Embed(title='Failed to send embed')
                            e.description = f'```{json.dumps(embed.to_dict(), indent=2)}```'
                            await category.send(embed=e)
                        if file_paths:
                            for file in file_paths:
                                if os.path.isfile(file):
                                    os.remove(file)
                        self.queue[guild_id].remove(list_obj)
                        self.recent_logs[guild_id].append([embed, logged_at])

                    for Type, channel_id in self.config[guild_id]['channels'].items():
                        if Type == channelType:
                            channel = self.bot.get_channel(channel_id)
                            if not channel:
                                channel = await guild.create_text_channel(
                                    name=channelType,
                                    category=category
                                )
                                self.config[guild_id]['channels'][Type] = channel.id
                                self.save_data()
                            try:
                                await channel.send(embed=embed, files=files)
                            except:
                                e = discord.Embed(title='Failed to send embed')
                                e.description = f'```json\n{json.dumps(embed.to_dict(), indent=2)}```'
                                await channel.send(embed=e)
                            if file_paths:
                                for file in file_paths:
                                    if os.path.isfile(file):
                                        os.remove(file)
                            self.queue[guild_id].remove(list_obj)
                            self.recent_logs[guild_id][channelType].append([embed, logged_at])
                            break
                except:
                    err_channel = self.bot.get_channel(577661461543780382)
                    await err_channel.send(f"Secure Log Error\n{str(traceback.format_exc())[-1980:]}")
                    await err_channel.send(f'```json\n{json.dumps(embed.to_dict(), indent=2)}```')
                    self.queue[guild_id].remove([embed, channelType, logged_at])

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

    async def init_invites(self):
        """ Indexes each servers invites """
        for guild_id in self.config.keys():
            guild = self.bot.get_guild(int(guild_id))
            if isinstance(guild, discord.Guild):
                if guild_id not in self.invites:
                    self.invites[guild_id] = {}
                invites = await guild.invites()
                for invite in invites:
                    self.invites[guild_id][invite.url] = invite.uses

    def past(self):
        """ gets the time 2 seconds ago in utc for audit searching """
        return datetime.utcnow() - timedelta(seconds=10)

    async def search_audit(self, guild, *actions):
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
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=5):
                if entry.created_at > self.past() and any(entry.action.name == action.name for action in actions):
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
        else:
            await guild.owner.send(f"I'm missing audit log permissions for secure-log in {guild}\n"
                                   f"run `.secure-log disable` to stop recieving msgs")
        return dat

    def split_into_groups(self, text):
        if not text:
            return text
        return [text[i:i + 1000] for i in range(0, len(text), 1000)]

    @commands.group(name='log', aliases=['secure-log'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def secure_log(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=fate())
            e.set_author(name='| Action Logger', icon_url=ctx.guild.icon_url)
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = "*A more detailed audit log that logs changes to the server and more to ~~a~~ dedicated channel(s)*"
            e.add_field(
                name='◈ Security',
                value=">>> Logs can't be deleted by anyone, they aren't purge-able, and it "
                      "re-creates deleted log channels and resends the last x logs",
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
                value = f"{p}log enable - `creates a log`"
                        f"\n{p}log disable - `deletes the log`"
                        f"\n{p}log switch - `toggles multi-log`"
                        f"\n{p}log security - `toggles security`"
                        f"\n{p}log ignore #channel - `ignore chat events`"
                        f"\n{p}log ignore @bot - `ignores bot spam`"
                        f"\n{p}log config ` `current setup overview`",
                inline=False
            )
            icon_url = 'https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png'
            e.set_footer(text="Security and Multi-Log are off by default", icon_url=icon_url)
            await ctx.send(embed=e)

    @secure_log.group(name='enable')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def _enable(self, ctx):
        """ Creates a multi-log """
        guild_id = str(ctx.guild.id)
        if guild_id in self.config:
            return await ctx.send("Secure-Log is already enabled")
        channel = await ctx.guild.create_text_channel(name='secure-log')
        self.config[guild_id] = {
            "channel": channel.id,
            "channels": {},
            "type": "single",
            "secure": False,
            "ignored_channels": [],
            "ignored_bots": []
        }
        self.bot.loop.create_task(self.start_queue(guild_id))
        await ctx.send("Enabled Secure-Log")
        self.save_data()

    @secure_log.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        """ Deletes a multi-log """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Secure-Log isn't enabled")
        if self.config[guild_id]['secure']:
            if ctx.author.id != ctx.guild.owner.id:
                return await ctx.send("Due to security settings, only the owner of the server can use this")
        del self.config[guild_id]
        await ctx.send('Disabled Secure-Log')
        self.save_data()

    @secure_log.command(name='switch')
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
            await ctx.send("Enabled Multi-Log")
        else:
            log = await ctx.guild.create_text_channel(name='bot-logs')
            self.config[guild_id]['channel'] = log.id
            self.config[guild_id]['channels'] = {}
            self.config[guild_id]['type'] = 'single'
            self.recent_logs[guild_id] = []
            await ctx.send('Enabled Single-Log')
        self.save_data()

    @secure_log.command(name='security')
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

    @secure_log.command(name='ignore')
    @commands.has_permissions(administrator=True)
    async def _ignore(self, ctx):
        """ ignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Secure-Log isn't enabled")
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
        self.save_data()

    @secure_log.command(name='unignore')
    @commands.has_permissions(administrator=True)
    async def _unignore(self, ctx):
        """ unignore channels and/or bots """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Secure-Log isn't enabled")
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
        self.save_data()

    @secure_log.command(name='config')
    async def _config(self, ctx):
        """ sends an overview of the servers current config """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("There's currently no config for this server")
        e = discord.Embed(color=fate())
        e.set_author(name="Logger Config", icon_url=ctx.guild.owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = f"**Log Type:** {self.config[guild_id]['type']} channel" \
                        f"\n**Security:** {self.config[guild_id]['secure']}"
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
        for guild_id in self.config.keys():
            self.bot.tasks.start(self.start_queue, guild_id, task_id=f'queue-{guild_id}')
        await self.init_invites()

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
                            not msg.channel.permissions_for(msg.author).mention_everyone == False):
                        is_successful = True
                    elif msg.channel.permissions_for(msg.author).mention_everyone:
                        is_successful = True
                    if is_successful:
                        e.description = self.bot.utils.format_dict({
                            "Author": msg.author.mention,
                            "Channel": msg.channel.mention
                        })
                        e.add_field(name='Content', value=m.content, inline=False)
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
                    for group in [before.content[i:i + 1000] for i in range(0, len(before.content), 1000)]:
                        e.add_field(name='◈ Before', value=group, inline=False)
                    for group in [after.content[i:i + 1000] for i in range(0, len(after.content), 1000)]:
                        e.add_field(name='◈ After', value=group, inline=False)
                    self.queue[guild_id].append([e, 'chat', time()])

                if before.embeds and not after.embeds:
                    if before.author.id in self.config[guild_id]['ignored_bots']:
                        return
                    if before.channel.id in self.config[guild_id]['ignored_channels']:
                        return

                    if before.channel.id == self.config[guild_id]['channel'] or(  # a message in the log was suppressed
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
                    path = f'./static/embed-{before.id}.json'
                    with open(path, 'w+') as f:
                        json.dump(em, f, sort_keys=True, indent=4, separators=(',', ': '))
                    self.queue[guild_id].append([(e, path), 'chat', time()])

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
                    for text_group in self.split_into_groups(after.content):
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
                for text_group in self.split_into_groups(msg.content):
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
                                path = os.path.join('static', attachment.filename)
                                file = requests.get(attachment.proxy_url).content
                                with open(path, 'wb') as f:
                                    f.write(file)
                                files.append(path)
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
                for text_group in self.split_into_groups(msg.content):
                    e.add_field(name='◈ MSG Content', value=text_group, inline=False)
                if msg.embeds:
                    e.set_footer(text='⇓ Embed ⇓')
                if msg.attachments:
                    files = []
                    for attachment in msg.attachments:
                        path = os.path.join('static', attachment.filename)
                        file = requests.get(attachment.proxy_url).content
                        with open(path, 'wb') as f:
                            f.write(file)
                        files.append(path)
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

            path = f'./static/purged-messages-{r.randint(0, 9999)}.txt'
            with open(path, 'w') as f:
                f.write(purged_messages)

            e = discord.Embed(color=lime_green())
            dat = await self.search_audit(guild, audit.message_bulk_delete)
            if dat['extra'] and dat['icon_url']:
                e.set_author(name=f"~==🍸{dat['extra']['count']} Msgs Purged🍸==~", icon_url=dat['icon_url'])
            else:
                e.set_author(name=f"~==🍸{len(payload.cached_messages)} Msgs Purged🍸==~")
            if dat['thumbnail_url']:
                e.set_thumbnail(url=dat['thumbnail_url'])
            e.description = self.bot.utils.format_dict({
                "Users Effected": len(list(set([msg.author for msg in payload.cached_messages]))),
                "Channel": channel.mention,
                "Purged by": dat['user']
            })
            self.queue[guild_id].append([(e, path), 'chat', time()])

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
                e = discord.Embed(color=lime_green())
                e.set_author(name='~==🍸Server Updated🍸==~', icon_url=dat['icon_url'])
                e.set_thumbnail(url=after.icon_url)
                return e

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
            if before.features != after.features:
                e = create_template_embed()
                e.description = f"> 》__**Features Changed**__《"
                changes = ''
                for feature in before.features:
                    if feature not in after.features:
                        changes += f"❌ {feature}"
                for feature in after.features:
                    if feature not in before.features:
                        changes += f"<:plus:548465119462424595> {feature}"
                e.add_field(name='◈ Changes', value=changes)
                self.queue[guild_id].append([e, 'updates', time()])
            if before.premium_tier != after.premium_tier:
                e = create_template_embed()
                e.description = f"> 》__**Premium Tier Changed**__《" \
                                f"\n**Before:** [{before.premium_tier}]" \
                                f"\n**After:** [{after.premium_tier}]"
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
                type = self.config[guild_id]['type']
                if channel.id == self.config[guild_id]['channel']:
                    if type == 'single':
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

            path = f'./static/members-{r.randint(1, 9999)}.txt'
            members = f"{channel.name} - Member List"
            for member in channel.members:
                members += f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
            with open(path, 'w') as f:
                f.write(members)

            self.queue[guild_id].append([(e, path), 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):  # due for rewrite
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            e = discord.Embed(color=orange())
            dat = await self.search_audit(after.guild, audit.channel_update)
            e.set_thumbnail(url=after.guild.icon_url)
            category = 'None, or Changed'
            if after.category and before.category == after.category:
                category = after.category.name

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
                            for text_group in self.split_into_groups(before.topic):
                                e.add_field(name='◈ Before', value=text_group, inline=False)
                        if after.topic:
                            for text_group in self.split_into_groups(after.topic):
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
                                f"{perm} - {after_values[iter][1]}" for iter, (perm, value) in enumerate(list(permissions)) if (
                                    value != after_values[iter][1])
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
            path = f'./static/role-members-{r.randint(1, 9999)}.txt'
            members = f"{role.name} - Member List"
            for member in role.members:
                members += f"\n{member.id}, {member.mention}, {member}, {member.display_name}"
            with open(path, 'w') as f:
                f.write(members)
            self.queue[guild_id].append([(e, [path, fp]), 'actions', time()])

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild_id = str(after.guild.id)
        if guild_id in self.config:
            path = None
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
                def font(size):
                    return ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", size)

                card = Image.new('RGBA', (100, 100), color=after.color.to_rgb())
                draw = ImageDraw.Draw(card)
                draw.text((60 - 1, 5), 'After', (0, 0, 0), font=font(13))
                draw.text((60 + 1, 5), 'After', (0, 0, 0), font=font(13))
                draw.text((60, 5 - 1), 'After', (0, 0, 0), font=font(13))
                draw.text((60, 5 + 1), 'After', (0, 0, 0), font=font(13))
                draw.text((60, 5), 'After', (255, 255, 255), font=font(13))

                box = Image.new('RGBA', (50, 100), color=before.color.to_rgb())
                draw = ImageDraw.Draw(box)
                draw.text((5 - 1, 5), 'Before', (0, 0, 0), font=font(13))
                draw.text((5 + 1, 5), 'Before', (0, 0, 0), font=font(13))
                draw.text((5, 5 - 1), 'Before', (0, 0, 0), font=font(13))
                draw.text((5, 5 + 1), 'Before', (0, 0, 0), font=font(13))
                draw.text((5, 5), 'Before', (255, 255, 255), font=font(13))

                card.paste(box)
                path = os.getcwd() + f'/static/color-{r.randint(1, 999)}.png'
                card.save(path)

                e.set_thumbnail(url="attachment://" + os.path.basename(path))
                e.add_field(
                    name='◈ Color Changed',
                    value=f"__**Before:**__ {before.color}"
                          f"\n__**After:**__ {after.color}"
                )
            if before.hoist != after.hoist:
                action = 'is now visible'
                if after.hoist == False:
                    action = 'is no longer visible'
                e.description += f"[{action}]"
            if before.mentionable != after.mentionable:
                action = 'is now mentionable'
                if not after.mentionable:
                    action = 'is no longer mentionable'
                e.description += f"[{action}]"

            if before.position != after.position:
                em = discord.Embed()
                em.description = f"Role {before.mention} was moved"
                self.queue[guild_id].append([em, 'updates', time()])
                # before_roles = before.guild.roles
                # before_roles.pop(after.position)
                # before_roles.insert(before.position, before)

                # if guild_id not in self.role_pos_cd:
                #     self.role_pos_cd[guild_id] = 0
                # if self.role_pos_cd[guild_id] < time() - 2:
                #     self.role_pos_cd[guild_id] = time()

                #     before_above = before_roles[before.position+1].mention
                #     before_below = before_roles[before.position-1].mention
                #     after_above = after.guild.roles[after.position+1].mention
                #     after_below = after.guild.roles[after.position-1].mention

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
                        changes += f"\n• {perm} {'allowed' if value else 'unallowed'}"
                e.add_field(name='◈ Permissions Changed', value=changes, inline=False)
            if e.fields:
                if path:
                    self.queue[guild_id].append([(e, path), 'updates', time()])
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
                "Invite:": f'[{invite.code}]({invite.url})'
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

            async for entry in member.guild.audit_logs(limit=1, action=audit.kick):
                if entry.target.id == member.id and entry.created_at > self.past():
                    e.set_author(name='~==🍸Member Kicked🍸==~', icon_url=entry.user.avatar_url)
                    e.description += self.bot.utils.format_dict({
                        "Kicked by": entry.user.mention
                    })
                    self.queue[guild_id].append([e, 'sudo', time()])
                    removed = True

            async for entry in member.guild.audit_logs(limit=1, action=audit.ban):
                if entry.target.id == member.id and entry.created_at > self.past():
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
                    e.description = f"{roles[0].mention} was taken from {before.mention}"
                else:
                    action = "Granted"
                    roles = [role for role in after.roles if role not in before.roles]
                    e.description = f"{roles[0].mention} was given to {before.mention}"
                e.set_author(name=f"~==🍸Role {action}🍸==~", icon_url=dat['icon_url'])
                info = {
                    "User": after,
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
    bot.add_cog(SecureLog(bot))
