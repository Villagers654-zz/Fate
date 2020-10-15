import asyncio
import os
import json
from time import time
from datetime import datetime, timedelta
from contextlib import suppress

import discord
from discord.errors import Forbidden, NotFound, HTTPException
from discord.ext import commands
from discord.ext import tasks

from utils import colors


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # cache
        self.spam_cd = {}
        self.macro_cd = {}
        self.ping_cd = {}
        self.dupes = {}
        self.roles = {}
        self.in_progress = {}
        self.mutes = {}
        self.msgs = {}

        # configs
        self.toggle = {}
        self.sensitivity = {}
        self.blacklist = {}
        self.path = './data/userdata/anti_spam.json'
        if not os.path.isdir('./data'):
            os.mkdir('data')
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                dat = json.load(f)
                self.toggle = dat['toggle']
                self.sensitivity = dat['sensitivity']
                self.blacklist = dat['blacklist']
        self.clear_old_msgs_task.start()

    async def save_data(self):
        data = {'toggle': self.toggle, 'sensitivity': self.sensitivity, 'blacklist': self.blacklist}
        await self.bot.save_json(self.path, data)

    def init(self, guild_id):
        if guild_id not in self.sensitivity:
            self.sensitivity[guild_id] = 'low'
        self.toggle[guild_id] = {
            'Rate-Limit': False,
            'Mass-Pings': False,
            'Anti-Macro': False,
            'Duplicates': False
        }

    @tasks.loop(seconds=4)
    async def clear_old_msgs_task(self):
        await asyncio.sleep(1)

        # Message Index
        for user_id, messages in list(self.msgs.items()):
            for msg in messages:
                with suppress(KeyError, IndexError, ValueError):
                    if not msg:
                        self.msgs[user_id].remove(msg)
                        continue
                    elif msg.created_at < datetime.utcnow() - timedelta(seconds=15):
                        self.msgs[user_id].remove(msg)
            with suppress(KeyError):
                if not self.msgs[user_id]:
                    del self.msgs[user_id]

        # Duplicate text index
        for channel_id, messages in list(self.dupes.items()):
            for message in messages:
                with suppress(KeyError, ValueError, IndexError):
                    if not message:
                        self.dupes[channel_id].remove(message)
                    elif message.created_at < datetime.utcnow() - timedelta(minutes=45):
                        self.dupes[channel_id].remove(message)
            with suppress(KeyError):
                if not self.dupes[channel_id]:
                    del self.dupes[channel_id]

    @commands.group(name='anti-spam', aliases=['antispam'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def anti_spam(self, ctx):
        if not ctx.invoked_subcommand and 'help' not in ctx.message.content:
            e = discord.Embed(color=colors.fate())
            e.set_author(name='AntiSpam Usage', icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = '**.anti-spam enable**\n`• enables all anti-spam modules`\n' \
                '**.anti-spam enable module**\n`• enables a single module`\n' \
                '**.anti-spam disable**\n`• disables all anti-spam modules`\n' \
                '**.anti-spam disable module**\n`• disables a single module`\n' \
                '**.anti-spam alter-sensitivity**\n`• alters anti-spam sensitivity`\n' \
                '**.anti-spam ignore #channel**\n`• ignores spam in a channel`\n' \
                '**.anti-spam unignore #channel**\n`• no longer ignores a channels spam`'
            modules = '**Rate-Limit:** `sending msgs fast`\n' \
                '**Mass-Pings:** `mass mentioning users`\n' \
                '**Anti-Macro:** `using macros for bots`\n' \
                '**Duplicates:** `copying and pasting`'
            e.add_field(name='◈ Modules', value=modules, inline=False)
            guild_id = str(ctx.guild.id)
            if guild_id in self.toggle:
                conf = ''
                for key, value in self.toggle[guild_id].items():
                    conf += f'**{key}:** `{"enabled" if value else "disabled"}`\n'
                e.add_field(name='◈ Config', value=conf, inline=False)
            await ctx.send(embed=e)

    @anti_spam.group(name='enable')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, manage_roles=True, manage_channels=True)
    async def _enable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.sensitivity:
                self.sensitivity[guild_id] = 'low'
            self.toggle[guild_id] = {
                'Rate-Limit': True,
                'Mass-Pings': True,
                'Anti-Macro': True,
                'Duplicates': True
            }
            await ctx.send('Enabled all anti-spam modules')
            await self.save_data()

    @_enable.command(name='rate-limit')
    @commands.has_permissions(manage_messages=True)
    async def _enable_rate_limit(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Rate-Limit'] = True
        await ctx.send('Enabled rate-limit module')
        await self.save_data()

    @_enable.command(name='mass-pings', aliases=['mass-ping'])
    @commands.has_permissions(manage_messages=True)
    async def _enable_mass_pings(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Mass-Pings'] = True
        await ctx.send('Enabled mass-pings module')
        await self.save_data()

    @_enable.command(name='anti-macro')
    @commands.has_permissions(manage_messages=True)
    async def _enable_anti_macro(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Anti-Macro'] = True
        await ctx.send('Enabled anti-macro module')
        await self.save_data()

    @_enable.command(name='duplicates')
    @commands.has_permissions(manage_messages=True)
    async def _enable_duplicates(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Duplicates'] = True
        await ctx.send('Enabled duplicates module')
        await self.save_data()

    @anti_spam.group(name='disable')
    @commands.has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.toggle:
                return await ctx.send('Anti-Spam is\'nt enabled')
            del self.toggle[guild_id]
            del self.sensitivity[guild_id]
            await ctx.send('Disabled anti-spam')
            await self.save_data()

    @_disable.command(name='rate-limit', aliases=['Rate-Limit', 'ratelimit', 'RateLimit'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_rate_limit(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Rate-Limit'] = False
        await ctx.send('Disabled rate-limit module')
        await self.save_data()

    @_disable.command(name='anti-macro', aliases=['Anti-Macro', 'antimacro', 'AntiMacro'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_anti_macro(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Anti-Macro'] = False
        await ctx.send('Disabled anti-macro module')
        await self.save_data()

    @_disable.command(name='mass-pings', aliases=['Mass-Pings', 'masspings', 'MassPings'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_mass_pings(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Mass-Pings'] = False
        await ctx.send('Disabled mass-pings module')
        await self.save_data()

    @_disable.command(name='duplicates', aliases=['Duplicates', 'duplicate', 'Duplicate'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_duplicates(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Duplicates'] = False
        await ctx.send('Disabled duplicates module')
        await self.save_data()

    @anti_spam.command(name='alter-sensitivity')
    @commands.has_permissions(manage_messages=True)
    async def _alter_sensitivity(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        if self.sensitivity[guild_id] == 'low':
            self.sensitivity[guild_id] = 'high'
        elif self.sensitivity[guild_id] == 'high':
            self.sensitivity[guild_id] = 'low'
        await ctx.send(f'Set the sensitivity to {self.sensitivity[guild_id]}')

    @anti_spam.command(name='ignore')
    @commands.has_permissions(manage_messages=True)
    async def _ignore(self, ctx, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.blacklist:
            self.blacklist[guild_id] = []
        if not channel:
            channel = ctx.channel
        if channel.id in self.blacklist[guild_id]:
            return await ctx.send('This channel is already ignored')
        self.blacklist[guild_id].append(channel.id)
        await ctx.send('👍')
        await self.save_data()

    @anti_spam.command(name='unignore')
    @commands.has_permissions(manage_messages=True)
    async def _unignore(self, ctx, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.blacklist:
            return await ctx.send('This server has no ignored channels')
        if not channel:
            channel = ctx.channel
        if channel.id not in self.blacklist[guild_id]:
            return await ctx.send('This channel isn\'t ignored')
        index = self.blacklist[guild_id].index(channel.id)
        self.blacklist[guild_id].pop(index)
        await ctx.send('👍')
        await self.save_data()

    async def handle_mute(self, channel, mute_role, user, sleep_time: int):
        with suppress(Forbidden, NotFound, HTTPException):
            await asyncio.sleep(sleep_time)
            if user and mute_role and mute_role in user.roles:
                await user.remove_roles(mute_role)
                mentions = discord.AllowedMentions(users=True)
                await channel.send(f"Unmuted **{user.mention}**", allowed_mentions=mentions)

        # Clean up the tasks
        guild_id = str(channel.guild.id)
        if guild_id in self.bot.tasks["mutes"]:
            user_id = str(user.id)
            if user_id in self.bot.tasks["mutes"][guild_id]:
                del self.bot.tasks[guild_id][user_id]
            if not self.bot.tasks["mutes"][guild_id]:
                del self.bot.tasks["mutes"][guild_id]

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not isinstance(msg.guild, discord.Guild) or msg.author.bot:
            return
        guild_id = str(msg.guild.id)
        user_id = str(msg.author.id)
        triggered = False
        if guild_id in self.toggle:
            users = [msg.author]
            sensitivity_level = 3 if self.sensitivity[guild_id] == 'low' else 2
            if guild_id in self.blacklist:
                if msg.channel.id in self.blacklist[guild_id]:
                    return

            # msgs to delete if triggered
            if user_id not in self.msgs:
                self.msgs[user_id] = []
            self.msgs[user_id].append(msg)
            self.msgs[user_id] = self.msgs[user_id][-15:]

            # rate limit
            now = int(time() / 5)
            if guild_id not in self.spam_cd:
                self.spam_cd[guild_id] = {}
            if user_id not in self.spam_cd[guild_id]:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][0] == now:
                self.spam_cd[guild_id][user_id][1] += 1
            else:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][1] > sensitivity_level:
                if self.toggle[guild_id]['Rate-Limit']:
                    with suppress(KeyError, ValueError):
                        del self.spam_cd[guild_id][user_id]
                        if not self.spam_cd[guild_id]:
                            del self.spam_cd[guild_id]
                    triggered = True

            # mass pings
            mentions = [*msg.mentions, *msg.role_mentions]
            if len(mentions) > sensitivity_level + 1 or msg.guild.default_role in mentions:
                if msg.guild.default_role in mentions:
                    if mentions.count(msg.guild.default_role) > 1 or len(mentions) > sensitivity_level + 1:
                        if self.toggle[guild_id]['Mass-Pings']:
                            triggered = True
                else:
                    if self.toggle[guild_id]['Mass-Pings']:
                        triggered = True

            # anti macro
            if user_id not in self.macro_cd:
                self.macro_cd[user_id] = {}
                self.macro_cd[user_id]['intervals'] = []
            if 'last' not in self.macro_cd[user_id]:
                self.macro_cd[user_id]['last'] = datetime.now()
            else:
                last = self.macro_cd[user_id]['last']
                self.macro_cd[user_id]['intervals'].append((datetime.now() - last).seconds)
                intervals = self.macro_cd[user_id]['intervals']
                self.macro_cd[user_id]['intervals'] = intervals[-sensitivity_level + 1:]
                if len(intervals) > 2:
                    if all(interval == intervals[0] for interval in intervals):
                        if self.toggle[guild_id]['Anti-Macro']:
                            triggered = True

            # duplicate messages
            if self.toggle[guild_id]['Duplicates']:
                channel_id = str(msg.channel.id)
                if channel_id not in self.dupes:
                    self.dupes[channel_id] = []
                self.dupes[channel_id] = [
                    msg, *[
                        msg for msg in self.dupes[channel_id]
                        if msg.created_at > datetime.utcnow() - timedelta(minutes=1)
                    ]
                ]
                for message in list(self.dupes[channel_id]):
                    dupes = [
                        m for m in self.dupes[channel_id]
                        if m and m.content == message.content
                    ]
                    if len(dupes) > sensitivity_level + 1:
                        await asyncio.sleep(1)
                        history = await msg.channel.history(limit=5).flatten()
                        if not any(m.author.bot for m in history):
                            users = set(list([
                                *[m.author for m in dupes if m], *users
                            ]))
                            await msg.channel.delete_messages([
                                message for message in dupes if message
                            ])
                            triggered = True
                            break

            if msg.guild.id == 397415086295089155:  # currently in testing
                abcs = "abcdefghijklmnopqrstuvwxyz"
                content = str(msg.content).lower()
                lines = content.split("\n")

                total_abcs = len([c for c in content if c in abcs])
                total_abcs = total_abcs if total_abcs else 1

                total_spaces = content.count(" ")
                total_spaces = total_spaces if total_spaces else 1

                has_abcs = any(content.count(c) for c in abcs)

                # non abc char spam
                if len(msg.content) > 256 and not has_abcs:
                    triggered = True
                # Tall msg spam
                elif len(content.split("\n")) > 8 and sum(len(line) for line in lines if line) < 21:
                    triggered = True
                elif len(content.split("\n")) > 5 and not has_abcs:
                    triggered = True
                # Empty lines spam
                elif len([l for l in lines if not l]) > len([l for l in lines if l]) and len(lines) > 8:
                    triggered = True
                # Mostly unknown chars spam
                elif len(content) > 128 and len(content) / total_abcs > 3:
                    triggered = True
                # ASCII / Spammed chars
                elif len(content) > 128 and len(content) / total_spaces > 10:
                    triggered = True

            if triggered:
                for iteration, user in enumerate(users):
                    user_id = str(user.id)
                    bot = msg.guild.me
                    perms = bot.guild_permissions
                    if not msg.channel.permissions_for(bot).manage_messages:
                        return

                    # Purge away spam
                    messages = []
                    if user_id in self.msgs:
                        messages = [
                            m for m in self.msgs[user_id]
                            if m and m.created_at > datetime.utcnow() - timedelta(seconds=15)
                        ]
                    self.msgs[user_id] = []  # Remove soon to be deleted messages from the list
                    with suppress(NotFound, Forbidden, HTTPException):
                        await msg.channel.delete_messages(messages)

                    # Don't mute users with Administrator
                    if msg.author.top_role.position >= bot.top_role.position or user.guild_permissions.administrator:
                        return
                    # Don't continue if lacking permission(s) to operate
                    if not msg.channel.permissions_for(bot).send_messages or not perms.manage_roles:
                        return

                    async with msg.channel.typing():
                        if guild_id not in self.in_progress:
                            self.in_progress[guild_id] = []
                        if user_id in self.in_progress[guild_id]:
                            return
                        self.in_progress[guild_id].append(user_id)

                        # Get, or setup the mute role
                        mute_role = None
                        mod = self.bot.cogs["Moderation"]
                        if guild_id in mod.config and mod.config[guild_id]["mute_role"]:
                            mute_role = msg.guild.get_role(mod.config[guild_id]["mute_role"])
                        if not mute_role:
                            mute_role = discord.utils.get(msg.guild.roles, name="Muted")
                        if not mute_role:
                            mute_role = discord.utils.get(msg.guild.roles, name="muted")
                        if not mute_role:
                            if not perms.manage_channels:
                                del self.toggle[guild_id]
                                del self.sensitivity[guild_id]
                                await self.save_data()
                                return

                            mute_role = await msg.guild.create_role(name="Muted", color=discord.Color(colors.black()), hoist=True)
                            if guild_id in mod.config:
                                mod.config[guild_id]["mute_role"] = mute_role.id
                            for channel in msg.guild.text_channels:
                                if channel.permissions_for(bot).manage_channels:
                                    await channel.set_permissions(mute_role, send_messages=False)
                            for channel in msg.guild.voice_channels:
                                if channel.permissions_for(bot).manage_channels:
                                    await channel.set_permissions(mute_role, speak=False)

                        # Increase the mute timer if multiple offenses in the last hour
                        multiplier = 0
                        if guild_id not in self.mutes:
                            self.mutes[guild_id] = {}
                        if user_id not in self.mutes[guild_id]:
                            self.mutes[guild_id][user_id] = []
                        self.mutes[guild_id][user_id].append(time())
                        for mute_time in self.mutes[guild_id][user_id]:
                            if mute_time > time() - 3600:
                                multiplier += 1
                            else:
                                index = self.mutes[guild_id][user_id].index(mute_time)
                                self.mutes[guild_id][user_id].pop(index)

                        # Mute and purge any new messages
                        timer = 150 * multiplier
                        timer_str = self.bot.utils.get_time(timer)
                        await user.add_roles(mute_role)
                        messages = []
                        if user_id in self.msgs:
                            messages = [m for m in self.msgs[user_id] if m]
                        with suppress(Forbidden, NotFound, HTTPException):
                            await msg.channel.delete_messages(messages)
                        self.msgs[user_id] = []

                        with suppress(NotFound, Forbidden, HTTPException):
                            await msg.author.send(f"You've been muted for spam in **{msg.guild.name}** for {timer_str}")
                        mentions = discord.AllowedMentions(users=True)
                        additional_info = ""
                        if len(users) > 1 and iteration == 0:
                            additional_info += f"\nIf this is a common mistake you can either disable duplicate " \
                                               f"checking with `.log disable duplicates` or ignore this channel " \
                                               f"with `.antispam ignore {msg.channel.mention}`"
                        await msg.channel.send(
                            f"Temporarily muted {msg.author.mention} for spam." + additional_info,
                            allowed_mentions=mentions
                        )

                    if "mutes" not in self.bot.tasks:
                        self.bot.tasks["mutes"] = {}
                    if guild_id not in self.bot.tasks["mutes"]:
                        self.bot.tasks["mutes"][guild_id] = {}
                    self.bot.tasks["mutes"][guild_id][user_id] = self.bot.loop.create_task(
                        self.handle_mute(
                            channel=msg.channel,
                            mute_role=mute_role,
                            user=msg.author,
                            sleep_time=timer
                        )
                    )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_id = str(before.guild.id)
        user_id = str(before.id)
        if "mutes" not in self.bot.tasks:
            self.bot.tasks["mutes"] = {}
        if guild_id in self.bot.tasks["mutes"]:
            if user_id in self.bot.tasks["mutes"][guild_id]:
                await asyncio.sleep(5)
                mute_role = None
                mod = self.bot.get_cog("Moderation")
                if not mod:
                    return
                if guild_id in mod.config and mod.config[guild_id]["mute_role"]:
                    mute_role = after.guild.get_role(mod.config[guild_id]["mute_role"])
                if not mute_role:
                    mute_role = discord.utils.get(after.guild.roles, name="Muted")
                if not mute_role:
                    mute_role = discord.utils.get(after.guild.roles, name="muted")
                if mute_role not in after.roles:
                    with suppress(KeyError):
                        self.bot.tasks["mutes"][guild_id][user_id].cancel()
                        del self.bot.tasks["mutes"][guild_id][user_id]
            if guild_id in self.bot.tasks["mutes"]:
                if not self.bot.tasks["mutes"][guild_id]:
                    del self.bot.tasks["mutes"][guild_id]


def setup(bot):
    bot.add_cog(AntiSpam(bot))


def teardown(bot):
    main = bot.cogs["AntiSpam"]  # type: AntiSpam
    main.clear_old_msgs_task.stop()
