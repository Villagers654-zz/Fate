# detailed information on users/channels/invites/etc

from os import path
import json
from time import time
import re
from datetime import datetime
import asyncio
import os

from discord.ext import commands
import discord
from discord import *
import aiofiles
from discord.ext.commands import Greedy as g

from utils import colors


class UtilityBeta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = './data/info.json'
        self.guild_logs = {}
        self.user_logs = {}
        self.misc_logs = {
            'invites': {}
        }
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                try:
                    dat = json.load(f)  # type: dict
                except json.JSONDecodeError:
                    bot.log("Utility is retreating to a backup file. The previous is corrupt", "CRITICAL")
                    with open(self.path + '.old') as f:
                        dat = json.load(f)
                self.guild_logs = dat['guild_logs']
                self.user_logs = dat['user_logs']
                self.misc_logs = dat['misc_logs']
        self.cache = {}

    def cog_unload(self):
        self.bot.loop.create_task(self.save_data())

    async def save_data(self):
        async with aiofiles.open(self.path+'.temp', 'w+') as f:
            await f.write(
                json.dumps(
                    {'guild_logs': self.guild_logs, 'user_logs': self.user_logs, 'misc_logs': self.misc_logs},
                    indent=2, sort_keys=True, ensure_ascii=False
                )
            )
        os.rename(self.path, self.path+'.old')
        os.rename(self.path+'.temp', self.path)
        os.remove(self.path+'.old')

    def setup_if_not_exists(self, *args):
        for arg in args:
            if isinstance(arg, discord.Guild):
                guild_id = str(arg.id)
                if guild_id not in self.guild_logs:
                    self.guild_logs[guild_id] = {
                        'joins': [],
                        'names': []
                    }
            if isinstance(arg, (discord.User, discord.Member)):
                user_id = str(arg.id)
                if user_id not in self.user_logs:
                    self.user_logs[user_id] = {
                        'names': {str(arg): time()},
                        'last_msg': None,
                        'last_online': None,
                        'duration': None
                    }

    def cleanup_users(self):
        for user_id, data in self.user_logs.items():
            for name, changed_at in data['names'].items():
                if changed_at > time() - 60*60*24*60:
                    del self.user_logs[user_id]['names'][name]
        self.save_data()

    @commands.command(name='xinfo')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def xinfo(self, ctx, users: g[User], roles: g[Role], channels: g[TextChannel]):
        bot_has_audit_access = ctx.guild.me.guild_permissions.view_audit_log  # type: bool
        if users:
            user = users[0]
            if ctx.guild:
                tmp = ctx.guild.get_member(user.id)
                if isinstance(tmp, discord.Member):
                    user = tmp
            self.setup_if_not_exists(user)

            e = discord.Embed(color=colors.fate())
            e.set_author(name="Here's what I got on them..", icon_url=self.bot.user.avatar_url)
            e.set_thumbnail(url=user.avatar_url)
            e.description = ''
            emojis = self.bot.utils.emojis
            user_id = str(user.id)

            # User Information
            user_info = {
                'Profile': f'{user.mention}',
                'ID': user.id,
                'Created at': datetime.date(user.created_at).strftime("%m/%d/%Y %I%p")
            }
            nicks = []
            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.id == user.id:
                        if member.display_name != user.display_name:
                            nicks = list(set(list([member.display_name, *nicks])))
            if nicks:
                user_info['Nicks'] = ', '.join(nicks)

            # Member Information
            member_info = {}
            if isinstance(user, discord.Member):
                user_info['Profile'] = f'{user.mention} {self.bot.utils.emojis(user.status)}'
                if user.status is discord.Status.online:
                    if user.is_on_mobile():
                        user_info["Active on Mobile 📱"] = None
                    else:
                        user_info["Active on PC 🖥"] = None

                if user.name != user.display_name:
                    member_info['Display Name'] = user.display_name
                if user.activity:
                    member_info['Activity'] = user.activity.name
                member_info['Top Role'] = user.top_role.mention

                text = len([
                    c for c in ctx.guild.text_channels if c.permissions_for(user).read_messages
                ])
                voice = len([
                    c for c in ctx.guild.voice_channels if c.permissions_for(user).read_messages
                ])

                notable = ['view_audit_log', 'manage_roles', 'manage_channels', 'manage_emojis',
                           'kick_members', 'ban_members', 'manage_messages', 'mention_everyone']
                member_info['Access'] = f"{emojis('text_channel')} {text} {emojis('voice_channel')} {voice}"
                if any(k in notable and v for k, v in list(user.guild_permissions)):
                    perms = [k for k, v in user.guild_permissions if k in notable and v]
                    perms = ['administrator'] if user.guild_permissions.administrator else perms
                    member_info['Notable Perms'] = f"`{', '.join(perms)}`"

                member_info['Shared Servers'] = str(len([s for s in self.bot.guilds if user in s.members]))

                # Bot Information
                if user.bot:  # search the audit log to see who invited the bot
                    inviter = "Unknown"
                    if bot_has_audit_access:
                        async for entry in ctx.guild.audit_logs(limit=250, action=discord.AuditLogAction.bot_add):
                            if entry.target and entry.target.id == user.id:
                                 inviter = entry.user
                                 break
                    user_info['Inviter'] = inviter

            # Activity Information
            activity_info = {}
            mutual = [g for g in self.bot.guilds if user.id in [m.id for m in g.members]]
            if mutual:
                user = mutual[0].get_member(user.id)
                if user.status is discord.Status.offline:
                    if self.user_logs[user_id]['last_online']:
                        seconds = round(time() - self.user_logs[user_id]['last_online'])
                        activity_info['Last Online'] = f"{self.bot.utils.get_time(seconds)} ago"
                        seconds = round(self.user_logs[user_id]['duration'])
                        activity_info['Online For'] = f"{self.bot.utils.get_time(seconds)}"
                    else:
                        activity_info['Last Online'] = 'Unknown'
                if self.user_logs[user_id]['last_msg']:
                    seconds = round(time() - self.user_logs[user_id]['last_msg'])
                    activity_info['Last Msg'] = f"{self.bot.utils.get_time(seconds)} ago"
                else:
                    activity_info['Last Msg'] = 'Unknown'

            # username history - broken (maybe)
            names = [
                name for name, name_time in self.user_logs[user_id]['names'].items() if (
                    name_time > time() - 60*60*24*60
                ) and name != str(user)
            ]
            if names:
                user_info['Usernames'] = ','.join(names)

            e.description += f"◈ User Information{self.bot.utils.format_dict(user_info)}\n\n"
            if member_info:
                e.description += f"◈ Member Information{self.bot.utils.format_dict(member_info)}\n\n"
            if activity_info:
                e.description += f"◈ Activity Information{self.bot.utils.format_dict(activity_info)}\n\n"
            await ctx.send(embed=e)

        elif channels:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Alright, here's what I got..", icon_url=self.bot.user.avatar_url)

            channel = channels[0]  # type: discord.TextChannel
            channel_info = {}

            channel_info["Name"] = channel.name
            channel_info["ID"] = channel.id
            channel_info["Members"] = str(len(channel.members))
            if channel.category:
                channel_info["Category"] = f"`{channel.category}`"
            if channel.is_nsfw():
                channel_info["Marked as NSFW"] = None
            if channel.is_news():
                channel_info["Is the servers news channel"] = None
            channel_info["Created at"] = datetime.date(channel.created_at).strftime("%m/%d/%Y %I%p")

            e.add_field(name="◈ Channel Information", value=self.bot.utils.format_dict(channel_info), inline=False)
            e.set_footer(text="🖥 Topic | ♻ History")

            msg = await ctx.send(embed=e)
            emojis = ["🖥", "♻"]
            for emoji in emojis:
                await msg.add_reaction(emoji)

            def predicate(r, u):
                return str(r.emoji) in emojis and r.message.id == msg.id and not u.bot

            while True:
                try:
                    reaction, _user = await self.bot.wait_for('reaction_add', check=predicate, timeout=60)
                except asyncio.TimeoutError:
                    if ctx.channel.permissions_for(ctx.guild.me).manage_messages and msg:
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
                        err = "Missing view_audit_log permission(s)"
                        if any(field.value == err for field in e.fields):
                            continue
                        e.add_field(name="◈ Channel History", value=err, inline=False)
                    else:
                        history = {}
                        e.add_field(name="◈ Channel History", value="Fetching..", inline=False)
                        await msg.edit(embed=e)

                        action = discord.AuditLogAction.channel_create
                        async for entry in ctx.guild.audit_logs(limit=500, action=action):
                            if channel.id == entry.target.id:
                                history["Creator"] = entry.user
                                break

                        if channel.permissions_for(ctx.guild.me).read_messages:
                            async for m in channel.history(limit=1):
                                seconds = (datetime.utcnow() - m.created_at).total_seconds()
                                total_time = self.bot.utils.get_time(seconds)
                                history["Last Message"] = f"{total_time} ago\n"

                        action = discord.AuditLogAction.channel_update
                        async for entry in ctx.guild.audit_logs(limit=500, action=action):
                            if channel.id == entry.target.id:
                                if entry.before.name != entry.after.name:
                                    minute = str(entry.created_at.minute)
                                    if len(minute) == 1:
                                        minute = "0" + minute
                                    when = datetime.date(entry.created_at).strftime(f"%m/%d/%Y %I:{minute}%p")
                                    history[f"**Name Changed on {when}**"] = None
                                    history[f"**Old Name:** `{entry.before.name}`\n"] = None

                        if not history:
                            history["None Found"] = None
                        print("finished gathering history")
                        e.set_field_at(
                            index=len(e.fields) - 1,
                            name="◈ Channel History", value=self.bot.utils.format_dict(dict(list(history.items())[:6])),
                            inline=False
                        )
                        emojis.remove("♻")
                await msg.edit(embed=e)

        elif 'discord.gg' in ctx.message.content:
            pass

        elif roles:
            pass

    def collect_invite_info(self, invite, guild=None):
        if not guild:
            guild = invite.guild
            if not isinstance(guild, (discord.Guild, discord.PartialInviteGuild)):
                tmp = self.bot.get_guild(guild.id)
                if isinstance(tmp, discord.Guild):
                    guild = tmp
        guild_name = 'Unknown'
        if isinstance(guild, (discord.Guild, discord.PartialInviteGuild)):
            guild_name = guild.name
        invite_info = {
            'deleted': False,
            'guild': {
                'name': guild_name,
                'id': guild.id
            }
        }
        if invite.inviter:
            invite_info['inviter'] = invite.inviter.id
        else:
            invite_info['inviter'] = None
        invite_info['member_count'] = invite.approximate_member_count
        invite_info['online_count'] = invite.approximate_presence_count
        invite_info['channel'] = {'name': None, 'id': invite.channel.id}
        if isinstance(invite.channel, (discord.TextChannel, discord.VoiceChannel, discord.PartialInviteChannel)):
            invite_info['channel']['name'] = invite.channel.name
        invite_info['temporary'] = invite.temporary
        invite_info['created_at'] = time()
        invite_info['uses'] = invite.uses
        invite_info['max_uses'] = invite.max_uses
        if 'inviters' not in invite_info:
            invite_info['inviters'] = []
        return invite_info

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            await asyncio.sleep(60 * 5)
            await self.save_data()

    @commands.Cog.listener()
    async def on_message(self, msg):
        # Keep track of their last message time
        self.setup_if_not_exists(msg.author)
        await asyncio.sleep(1)  # avoid getting in the way of .info @user
        self.user_logs[str(msg.author.id)]['last_msg'] = time()
        # Check for invites and log their current state
        if 'discord.gg' in msg.content:
            invites = re.findall('discord.gg/.{7}', msg.content)
            if invites:
                for invite in invites:
                    code = discord.utils.resolve_invite(invite)
                    try:
                        invite = await self.bot.fetch_invite(code)
                        invite_info = self.collect_invite_info(invite)
                        if invite.code not in self.misc_logs['invites']:
                            self.misc_logs[invite.code] = invite_info
                        for key, value in invite_info.items():
                            try:
                                if key not in self.misc_logs[invite.code]:
                                    self.misc_logs[invite.code][key] = value
                                elif value != self.misc_logs[invite.code][key] and value is not None:
                                    self.misc_logs[invite.code][key] = value
                            except KeyError:
                                return
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
                self.user_logs[user_id]['last_online'] = self.cache[user_id]
                self.user_logs[user_id]['duration'] = time() - self.cache[user_id]
                del self.cache[user_id]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_id = str(guild.id)
        self.setup_if_not_exists(guild)
        self.guild_logs[guild_id]['joins'].append([member.id, time()])

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        if not member.bot:
            self.setup_if_not_exists(member.guild)
            user_id = str(member.id)
            if user_id in self.guild_logs['joins']:
                del self.guild_logs['joins'][user_id]

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.code not in self.misc_logs['invites']:
            guild = self.bot.get_guild(invite.guild.id)
            try:
                inv = await self.bot.fetch_invite(invite.code, with_counts=True)
                invite = inv
            except discord.errors.HTTPException:
                pass
            self.misc_logs['invites'][invite.code] = self.collect_invite_info(invite, guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.code in self.misc_logs['invites']:
            self.misc_logs['invites'][invite.code]['deleted'] = True


def setup(bot):
    bot.add_cog(UtilityBeta(bot))
