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

from botutils import colors


defaults = {
    "rate_limit": [{
        "timespan": 5,
        "threshold": 4
    }],
    "mass_pings": {
        "per_message": 4,
        "thresholds": [{
            "timespan": 10,
            "threshold": 3
        }]
    },
    "duplicates": {
        "per_message": 10,
        "thresholds": [{
            "timespan": 25,
            "threshold": 4
        }]
    },
    "inhuman": {
        "non_abc": True,
        "tall_messages": True,
        "empty_lines": True,
        "unknown_chars": True,
        "ascii": True
    }
}


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {}
        collection = bot.mongo["AntiSpam"]
        for config in collection.find({}):
            self.config[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }

        # cache
        self.spam_cd = {}
        self.macro_cd = {}
        self.ping_cd = {}
        self.dupes = {}
        self.roles = {}
        self.mutes = {}
        self.msgs = {}
        self.index1 = {}
        self.index2 = {}
        self.cache = []

        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.stop()

    async def lock_mute(self, guild_id, user_id):
        self.cache.append([guild_id, user_id])
        await asyncio.sleep(120)
        self.cache.remove([guild_id, user_id])

    async def get_mutes(self) -> dict:
        mutes = {}
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select guild_id, channel_id, user_id, mute_role_id, end_time "
                f"from anti_spam_mutes;"
            )
            results = await cur.fetchall()
            for guild_id, channel_id, user_id, mute_role_id, end_time in results:
                if guild_id not in mutes:
                    mutes[guild_id] = {}
                mutes[guild_id][user_id] = {
                    "channel_id": channel_id,
                    "mute_role_id": mute_role_id,
                    "end_time": end_time
                }
        return mutes

    async def delete_timer(self, guild_id: int, user_id: int):
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"delete from anti_spam_mutes "
                f"where guild_id = {guild_id} "
                f"and user_id = {user_id};"
            )

    async def update_data(self, guild_id: int, data):
        collection = self.bot.aio_mongo["AntiSpam"]
        await collection.update_one(
            filter={"_id": guild_id},
            update={"$set": data},
            upsert=True
        )

    @tasks.loop(seconds=4)
    async def cleanup_task(self):
        await asyncio.sleep(1)

        # Remove guilds from blacklist if it's empty
        # for guild_id, channels in list(self.blacklist.items()):
        #     if not channels:
        #         with suppress(KeyError, ValueError):
        #             del self.blacklist[guild_id]

        # Remove guilds from prefixes if it's empty

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

    @commands.group(name="anti-spam", aliases=["antispam"])
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
                      '**Duplicates:** `copying and pasting`\n' \
                      '**Inhuman:** `abnormal, ascii, tall, etc`'
            e.add_field(name="◈ Modules", value=modules, inline=False)
            guild_id = ctx.guild.id
            if guild_id in self.config:
                conf = ""
                for key in self.config[guild_id].keys():
                    if key != "ignored":
                        conf += f"**{key.replace('_', '-')}:** `enabled`\n"
                if "ignored" in self.config[guild_id]:
                    channels = []
                    for channel_id in self.config[guild_id]["ignored"]:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            channels.append(channel)
                    if channels:
                        conf += "**Ignored:** " + ", ".join(c.mention for c in channels)
                e.add_field(name="◈ Config", value=conf, inline=False)
            await ctx.send(embed=e)

    @anti_spam.command(name="configure")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    async def _configure(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            await ctx.send("Anti spam isn't enabled")
        menu = ConfigureModules(ctx)
        await menu.setup()
        while True:
            await menu.next()

    @anti_spam.group(name='enable')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, manage_roles=True, manage_channels=True)
    async def _enable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = ctx.guild.id
            if guild_id in self.config:
                return await ctx.send("Anti spam is already enabled")
            self.config[guild_id] = {
                "rate_limit": [{
                    "timespan": 5,
                    "threshold": 4
                }],
                "mass_pings": {
                    "per_message": 4,
                    "thresholds": [{
                        "timespan": 10,
                        "threshold": 3
                    }]
                },
                "duplicates": {
                    "per_message": 10,
                    "thresholds": [{
                        "timespan": 25,
                        "threshold": 4
                    }]
                }
            }
            for key, value in self.config[guild_id].items():
                await self.bot.aio_mongo["AntiSpam"].update_one(
                    filter={"_id": guild_id},
                    update={"$set": {key: value}},
                    upsert=True
                )
            await ctx.send('Enabled the default anti-spam config')

    @_enable.command(name='rate-limit')
    @commands.has_permissions(manage_messages=True)
    async def _enable_rate_limit(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        conf = [{"timespan": 5, "threshold": 4}]
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$set": {"rate_limit": self.config[guild_id]["rate_limit"]}},
            upsert=True
        )
        self.config[guild_id] = self.config[guild_id]["rate_limit"] = conf
        await ctx.send('Enabled rate-limit module')

    @_enable.command(name='mass-pings', aliases=['mass-ping'])
    @commands.has_permissions(manage_messages=True)
    async def _enable_mass_pings(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        conf = {
            "per_message": 4,
            "thresholds": [{
                "timespan": 10,
                "threshold": 3
            }]
        }
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$set": {"mass_pings": conf}},
            upsert=True
        )
        self.config[guild_id]["mass_pings"] = conf
        await ctx.send('Enabled rate-limit module')

    @_enable.command(name='anti-macro')
    @commands.has_permissions(manage_messages=True)
    async def _enable_anti_macro(self, ctx):
        return await ctx.send("This module is currently in development and can't be used")
        # guild_id = ctx.guild.id
        # if guild_id not in self.config:
        #     self.config[guild_id] = {}
        # conf = {}
        # await self.bot.aio_mongo["AntiSpam"].update_one(
        #     filter={"_id": guild_id},
        #     update={"$set": {"anti_macro": conf}},
        #     upsert=True
        # )
        # self.config[guild_id]["anti_macro"] = conf
        # await ctx.send('Enabled anti-macro module')

    @_enable.command(name='duplicates')
    @commands.has_permissions(manage_messages=True)
    async def _enable_duplicates(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        conf = {
            "per_message": 10,
            "thresholds": [{
                "timespan": 25,
                "threshold": 4
            }]
        }
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$set": {"duplicates": conf}},
            upsert=True
        )
        self.config[guild_id]["duplicates"] = conf
        await ctx.send('Enabled duplicates module')

    @_enable.command(name='inhuman')
    @commands.has_permissions(manage_messages=True)
    async def _enable_inhuman(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        conf = {
            "non_abc": True,
            "tall_messages": True,
            "empty_lines": True,
            "unknown_chars": True,
            "ascii": True
        }
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$set": {"inhuman": conf}},
            upsert=True
        )
        self.config[guild_id]["inhuman"] = conf
        await ctx.send('Enabled duplicates module')

    @anti_spam.group(name='disable')
    @commands.has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = ctx.guild.id
            if guild_id not in self.config:
                return await ctx.send("Anti-Spam isn't enabled")
            await self.bot.aio_mongo["AntiSpam"].delete_one({"_id": guild_id})
            del self.config[guild_id]
            await ctx.send('Disabled anti-spam')

    @_disable.command(name='rate-limit', aliases=['Rate-Limit', 'ratelimit', 'RateLimit'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_rate_limit(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "rate_limit" not in self.config[guild_id]:
            return await ctx.send("Rate limit isn't enabled")
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$unset": {"rate_limit": 1}}
        )
        del self.config[guild_id]["rate_limit"]
        await ctx.send('Disabled rate-limit module')

    @_disable.command(name='anti-macro', aliases=['Anti-Macro', 'antimacro', 'AntiMacro'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_anti_macro(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "anti_macro" not in self.config[guild_id]:
            return await ctx.send("Anti Macro isn't enabled")
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$unset": {"anti_macro": 1}}
        )
        del self.config[guild_id]["anti_macro"]
        await ctx.send('Disabled anti-macro module')

    @_disable.command(name='mass-pings', aliases=['Mass-Pings', 'masspings', 'MassPings'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_mass_pings(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "mass_pings" not in self.config[guild_id]:
            return await ctx.send("Mass pings isn't enabled")
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$unset": {"mass_pings": 1}}
        )
        del self.config[guild_id]["mass_pings"]
        await ctx.send('Disabled mass-pings module')

    @_disable.command(name='duplicates', aliases=['Duplicates', 'duplicate', 'Duplicate'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_duplicates(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "duplicates" not in self.config[guild_id]:
            return await ctx.send("Duplicates isn't enabled")
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$unset": {"duplicates": 1}}
        )
        del self.config[guild_id]["duplicates"]
        await ctx.send('Disabled rate-limit module')

    @_disable.command(name='inhuman')
    @commands.has_permissions(manage_messages=True)
    async def _disable_inhuman(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "inhuman" not in self.config[guild_id]:
            return await ctx.send("Inhuman isn't enabled")
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": guild_id},
            update={"$unset": {"inhuman": 1}}
        )
        del self.config[guild_id]["rate_limit"]
        await ctx.send('Disabled inhuman module')

    @anti_spam.command(name='ignore')
    @commands.has_permissions(manage_messages=True)
    async def _ignore(self, ctx, *channel_mentions: discord.TextChannel):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "ignored" not in self.config[guild_id]:
            self.config[guild_id]["ignored"] = []
        for channel in channel_mentions[:5]:
            if "ignored" in self.config[guild_id]:
                if channel.id in self.config[guild_id]["ignored"]:
                    await ctx.send(f"{channel.mention} is already ignored")
                    continue
            if "ignored" not in self.config[guild_id]:
                self.config[guild_id]["ignored"] = []
            self.config[guild_id]["ignored"].append(channel.id)
            await self.bot.aio_mongo["AntiSpam"].update_one(
                filter={"_id": guild_id},
                update={"$set": {"ignored": self.config[guild_id]["ignored"]}}
            )
            await ctx.send(f"I'll now ignore {channel.mention}")

    @anti_spam.command(name='unignore')
    @commands.has_permissions(manage_messages=True)
    async def _unignore(self, ctx, *channel_mentions: discord.TextChannel):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "ignored" not in self.config[guild_id]:
            return await ctx.send("There aren't any ignored channels")
        for channel in channel_mentions[:5]:
            if channel.id not in self.config[guild_id]["ignored"]:
                await ctx.send(f"{channel.mention} isn't ignored")
                continue
            self.config[guild_id]["ignored"].remove(channel.id)
            if self.config[guild_id]["ignored"]:
                await self.bot.aio_mongo["AntiSpam"].update_one(
                    filter={"_id": guild_id},
                    update={"$set": {"ignored": self.config[guild_id]["ignored"]}}
                )
            else:
                await self.bot.aio_mongo["AntiSpam"].update_one(
                    filter={"_id": guild_id},
                    update={"$unset": {"ignored": 1}}
                )
            await ctx.send(f"I'll no longer ignore {channel.mention}")

    async def handle_mute(self, channel, mute_role, guild_id, user_id: int, sleep_time: int):
        if channel:
            user = channel.guild.get_member(user_id)
            with suppress(Forbidden, NotFound, HTTPException):
                await asyncio.sleep(sleep_time)
                if user and mute_role and mute_role in user.roles:
                    await user.remove_roles(mute_role)
                    mentions = discord.AllowedMentions(users=True)
                    await channel.send(f"Unmuted **{user.mention}**", allowed_mentions=mentions)

        # Clean up the tasks
        if "antispam_mutes" not in self.bot.tasks:
            self.bot.tasks["antispam_mutes"] = {}
        if guild_id in self.bot.tasks["antispam_mutes"]:
            user_id = str(user_id)
            if user_id in self.bot.tasks["antispam_mutes"][guild_id]:
                del self.bot.tasks["antispam_mutes"][guild_id][user_id]
            if not self.bot.tasks["antispam_mutes"][guild_id]:
                del self.bot.tasks["antispam_mutes"][guild_id]

        with suppress(AttributeError):
            await self.delete_timer(channel.guild.id, user_id)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not isinstance(msg.guild, discord.Guild) or msg.author.bot:
            return
        guild_id = msg.guild.id
        user_id = str(msg.author.id)
        triggered = False
        if guild_id in self.config and self.config[guild_id]:
            if "ignored" in self.config[guild_id] and msg.channel.id in self.config[guild_id]["ignored"]:
                return
            if [msg.guild.id, msg.author.id] in self.cache:
                return

            with self.bot.utils.operation_lock(key=msg.author.id):
                users = [msg.author]
                reason = "Unknown"

                # msgs to delete if triggered
                if user_id not in self.msgs:
                    self.msgs[user_id] = []
                self.msgs[user_id].append(msg)
                self.msgs[user_id] = self.msgs[user_id][-15:]

                # rate limit
                if "rate_limit" in self.config[guild_id]:
                    now = int(time() / 3)
                    if guild_id not in self.index1:
                        self.index1[guild_id] = {}
                    if user_id not in self.index1[guild_id]:
                        self.index1[guild_id][user_id] = [now, 0]
                    if self.index1[guild_id][user_id][0] == now:
                        self.index1[guild_id][user_id][1] += 1
                    else:
                        self.index1[guild_id][user_id] = [now, 0]
                    if self.index1[guild_id][user_id][1] > 4:
                        with suppress(KeyError, ValueError):
                            del self.index1[guild_id][user_id]
                            if not self.index1[guild_id]:
                                del self.index1[guild_id]
                        reason = "5 or more messages within 3 seconds"
                        triggered = True

                    now = int(time() / 10)
                    if guild_id not in self.index2:
                        self.index2[guild_id] = {}
                    if user_id not in self.index2[guild_id]:
                        self.index2[guild_id][user_id] = [now, 0]
                    if self.index2[guild_id][user_id][0] == now:
                        self.index2[guild_id][user_id][1] += 1
                    else:
                        self.index2[guild_id][user_id] = [now, 0]
                    if self.index2[guild_id][user_id][1] > 7:
                        with suppress(KeyError, ValueError):
                            del self.index2[guild_id][user_id]
                            if not self.index2[guild_id]:
                                del self.index2[guild_id]
                        reason = "8 or more messages within 10 seconds"
                        triggered = True


                # mass pings
                if "mass_pings" in self.config[guild_id]:
                    pings = [msg.mentions, msg.raw_mentions, msg.role_mentions, msg.raw_role_mentions]
                    total_pings = sum(len(group) for group in pings)
                    if total_pings > 4:
                        reason = "mass pinging"
                        triggered = True

                    pongs = lambda s: [
                        m for m in self.msgs[user_id]
                        if m and m.created_at > datetime.utcnow() - timedelta(seconds=s)
                           and sum(len(group) for group in [
                            m.mentions, m.raw_mentions, m.role_mentions, m.raw_role_mentions
                        ])
                    ]
                    if len(pongs(10)) > 2:
                        reason = "mass pinging"
                        triggered = True

                # anti macro
                # if self.toggle[guild_id]["Anti-Macro"]:
                #     if user_id not in self.macro_cd:
                #         self.macro_cd[user_id] = {}
                #         self.macro_cd[user_id]['intervals'] = []
                #     if 'last' not in self.macro_cd[user_id]:
                #         self.macro_cd[user_id]['last'] = datetime.now()
                #     else:
                #         last = self.macro_cd[user_id]['last']
                #         self.macro_cd[user_id]['intervals'].append((datetime.now() - last).seconds)
                #         intervals = self
                #         .macro_cd[user_id]['intervals']
                #         self.macro_cd[user_id]['intervals'] = intervals[-sensitivity_level + 1:]
                #         if len(intervals) > 2:
                #             if all(interval == intervals[0] and interval > 10 for interval in intervals):
                #                 reason = "macromancing"
                #                 triggered = True

                # duplicate messages
                if "duplicates" in self.config[guild_id] and msg.content:
                    if msg.channel.permissions_for(msg.guild.me).read_message_history:
                        channel_id = str(msg.channel.id)
                        if channel_id not in self.dupes:
                            self.dupes[channel_id] = []
                        self.dupes[channel_id] = [
                            msg, *[
                                msg for msg in self.dupes[channel_id]
                                if msg.created_at > datetime.utcnow() - timedelta(seconds=25)
                            ]
                        ]
                        for message in list(self.dupes[channel_id]):
                            dupes = [
                                m for m in self.dupes[channel_id]
                                if m and m.content and m.content == message.content
                            ]
                            if len(dupes) > 4:
                                await asyncio.sleep(1)
                                history = await msg.channel.history(limit=5).flatten()
                                if not any(m.author.bot for m in history):
                                    users = set(list([
                                        *[m.author for m in dupes if m], *users
                                    ]))
                                    for message in dupes:
                                        with suppress(IndexError, ValueError):
                                            self.dupes[channel_id].remove(message)
                                    with suppress(Forbidden, NotFound):
                                        await msg.channel.delete_messages([
                                            message for message in dupes if message
                                        ])
                                    reason = "duplicate messages"
                                    triggered = True
                                    break

                if "inhuman" in self.config[guild_id] and msg.content:
                    abcs = "abcdefghijklmnopqrstuvwxyzجحخهعغفقثصضشسيبلاتتمكطدظزوةىرؤءذئأإآ"
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

                if triggered and guild_id in self.config:
                    # Log that a mute is currently running for 180 seconds
                    self.bot.loop.create_task(
                        self.lock_mute(msg.guild.id, msg.author.id)
                    )

                    # Mute the relevant users
                    for iteration, user in enumerate(list(set(users))):
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
                        if user.top_role.position >= bot.top_role.position or user.guild_permissions.administrator:
                            continue
                        # Don't continue if lacking permission(s) to operate
                        if not msg.channel.permissions_for(bot).send_messages or not perms.manage_roles:
                            return

                        async with msg.channel.typing():
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
                            if mute_role.position >= msg.guild.me.top_role.position:
                                return

                            # Increase the mute timer if multiple offenses in the last hour
                            multiplier = 1
                            if guild_id not in self.mutes:
                                self.mutes[guild_id] = {}
                            if user_id not in self.mutes[guild_id]:
                                self.mutes[guild_id][user_id] = []
                            self.mutes[guild_id][user_id].append(time())
                            for mute_time in self.mutes[guild_id][user_id]:
                                if mute_time > time() - 3600:
                                    multiplier += 1
                                else:
                                    self.mutes[guild_id][user_id].remove(mute_time)

                            # Mute and purge any new messages
                            timer = 150 * multiplier
                            end_time = time() + timer
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
                            await msg.channel.send(
                                f"Temporarily muted {msg.author.mention} for spam. Reason: {reason}",
                                allowed_mentions=mentions
                            )

                        if "antispam_mutes" not in self.bot.tasks:
                            self.bot.tasks["antispam_mutes"] = {}
                        if guild_id not in self.bot.tasks["mutes"]:
                            self.bot.tasks["antispam_mutes"][guild_id] = {}

                        self.bot.tasks["antispam_mutes"][guild_id][user_id] = self.bot.loop.create_task(
                            self.handle_mute(
                                channel=msg.channel,
                                mute_role=mute_role,
                                guild_id=guild_id,
                                user_id=msg.author.id,
                                sleep_time=timer
                            )
                        )

                        async with self.bot.cursor() as cur:
                            await cur.execute(
                                f"insert into anti_spam_mutes "
                                f"values ("
                                f"{msg.guild.id}, "
                                f"{msg.channel.id}, "
                                f"{msg.author.id}, "
                                f"{mute_role.id}, "
                                f"{end_time});"
                            )

    @commands.Cog.listener()
    async def on_ready(self):
        if "mutes" not in self.bot.tasks:
            self.bot.tasks["mutes"] = {}
        mutes = await self.get_mutes()
        for guild_id, mutes in list(mutes.items()):
            for user_id, data in mutes.items():
                if guild_id not in mutes:
                    self.bot.tasks["mutes"][guild_id] = {}
                if user_id not in self.bot.tasks["mutes"][guild_id]:
                    guild = self.bot.get_guild(int(guild_id))
                    try:
                        self.bot.tasks["mutes"][guild_id] = self.bot.loop.create_task(
                            self.handle_mute(
                                channel=self.bot.get_channel(data["channel_id"]),
                                mute_role=guild.get_role(int(data["mute_role_id"])),
                                guild_id=guild_id,
                                user_id=user_id,
                                sleep_time=data["end_time"] - time()
                            )
                        )
                        self.bot.log.info(f"Resumed a anti_spam mute in {guild}")
                    except AttributeError:
                        await self.delete_timer(guild_id, user_id)
                        self.bot.log.info(f"Deleted a anti_spam task in {guild} due to changes")

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
                        await self.delete_timer(before.guild.id, before.id)
            if guild_id in self.bot.tasks["mutes"]:
                if not self.bot.tasks["mutes"][guild_id]:
                    del self.bot.tasks["mutes"][guild_id]


class ConfigureModules:
    def __init__(self, ctx):
        self.super = ctx.bot.cogs["AntiSpam"]
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id

        self.cursor = self.modules
        self.row = 0
        self.config = self.key = None

        emojis = ctx.bot.utils.emotes
        self.emotes = [emojis.home, emojis.up, emojis.down, emojis.yes]

        self.msg = self.reaction = self.user = None
        self.check = lambda r, u: r.message.id == self.msg.id and u.id == ctx.author.id

    async def setup(self):
        """Initialize the reaction menu"""
        e = self.create_embed(description=self.get_description())
        self.msg = await self.ctx.send(embed=e)
        self.bot.loop.create_task(self.add_reactions())

    def reset(self):
        """Go back to the list of enabled modules"""
        self.cursor = self.modules
        self.row = 0
        self.config = None

    @property
    def modules(self):
        """Get their current AntiSpam config"""
        items = self.bot.cogs["AntiSpam"].config[self.guild_id].items()
        return {
            module: data
            for module, data in items
            if module != "ignored"
        }

    def create_embed(self, **kwargs):
        """Get default embed style"""
        return discord.Embed(
            title="Enabled Modules", color=self.bot.config["theme_color"], **kwargs
        )

    def get_description(self):
        # Format the current options
        emojis = self.bot.utils.emotes
        description = ""
        for i, key in enumerate(self.cursor.keys()):
            if i != 0:
                description += "\n"
            if i == self.row:
                description += f"{emojis.online} {key}"
            else:
                description += f"{emojis.offline} {key}"
        return description

    async def next(self):
        """Wait for the next reaction"""
        reaction, user = await self.bot.utils.get_reaction(self.check)
        if reaction:
            self.bot.loop.create_task(self.msg.remove_reaction(reaction, user))
        e = self.create_embed()
        emojis = self.bot.utils.emotes

        # Home button
        if reaction.emoji == emojis.home:
            self.reset()
        # Up button
        elif reaction.emoji == emojis.up:
            self.row -= 1
        # Down button
        elif reaction.emoji == emojis.down:
            self.row += 1
        # Enter button
        elif str(reaction.emoji) == emojis.yes:
            key = list(self.cursor.keys())[self.row]
            if not self.cursor[key]:
                e.description = self.cursor[key]
                if key in self.config and self.config[key]:
                    await self.init_config(key)
                else:
                    await self.configure(key)
            else:
                e.title = key
                await self.init_config(key)

        # Adjust row position
        if self.row < 0:
            self.row = len(self.cursor.keys()) - 1
        elif self.row > len(self.cursor.keys()) - 1:
            self.row = 0

        # Parse the message
        if not e.description:
            e.description = self.get_description()
        if self.config:
            e.title = self.key
            e.add_field(
                name="◈ Config",
                value=f"```json\n{json.dumps(self.config, indent=2)}```"
            )
        await self.msg.edit(embed=e)

    async def add_reactions(self):
        """Add the reactions in the background"""
        for i, emote in enumerate(self.emotes):
            await self.msg.add_reaction(emote)
            if i != len(self.emotes) - 1:
                await asyncio.sleep(0.21)

    async def get_reply(self, message):
        """Get new values for a config"""
        m = await self.ctx.send(message)
        reply = await self.bot.utils.get_message(self.ctx)
        await m.delete()
        content = reply.content
        await reply.delete()
        return content

    async def update_data(self):
        """Update the cache and database"""
        self.super.config[self.guild_id][self.key] = self.config
        await self.bot.aio_mongo["AntiSpam"].update_one(
            filter={"_id": self.guild_id},
            update={"$set": {
                self.key: self.config
            }}
        )

    async def init_config(self, key):
        """Change where we're working at"""
        self.config = self.cursor[key]
        self.key = key
        self.row = 0
        self.cursor = {}

        # Add in options
        if any(isinstance(v, bool) for v in dict(self.config).values()):
            self.cursor["Enable a mod"] = None
            self.cursor["Disable a mod"] = None
        if "per_message" in self.config:
            self.cursor["Per-message threshold"] = None
        if isinstance(self.config, list) or "thresholds" in self.config:
            self.cursor["Add a custom threshold"] = None
            self.cursor["Remove a custom threshold"] = None
        self.cursor["Reset to default"] = None

    async def configure(self, key):
        """Alter a configs data"""
        if key == "Reset to default":
            self.config = defaults[self.key]
            await self.update_data()
            self.reset()

        elif key == "Per-message threshold":
            # Get options to modify the per-message threshold
            self.cursor = {
                "Update": None,
                "Disable": None
            }

        elif key == "Update":
            # Change the per-message threshold
            question = "What's the new number I should set"
            reply = await self.get_reply(question)
            if not reply.isdigit():
                await self.ctx.send("Invalid format. Your reply must be a number", delete_after=5)
            else:
                self.config["per_message"] = int(reply)
                await self.update_data()
            self.reset()

        elif key == "Disable":
            # Remove the per-message threshold
            if isinstance(self.config, dict):  # To satisfy pycharms warning
                self.config["per_message"] = None
            await self.update_data()
            self.reset()

        elif key == "Enable a mod":
            # Set a toggle to True
            question = "Which mod should I enable"
            reply = await self.get_reply(question)
            if reply.lower() not in self.config:
                await self.ctx.send("That's not a toggleable mod", delete_after=5)
            else:
                self.config[reply.lower()] = True
                await self.update_data()
            self.reset()

        elif key == "Disable a mod":
            # Set a toggle to False
            question = "Which mod should I disable"
            reply = await self.get_reply(question)
            if reply.lower() not in self.config:
                await self.ctx.send("That's not a toggleable mod", delete_after=5)
            else:
                self.config[reply.lower()] = False
                await self.update_data()
            self.reset()

        elif key == "Add a custom threshold":
            # Something something something
            question = "Send the threshold and timespan to use. Format like " \
                       "`6, 10` to only allow 6 within 10 seconds"
            reply = await self.get_reply(question)
            args = reply.split(", ")
            if not all(arg.isdigit() for arg in args) or len(args) != 2:
                await self.ctx.send("Invalid format", delete_after=5)
            else:
                new_threshold = {"timespan": args[0], "threshold": args[1]}
                dict_check = new_threshold in self.config["thresholds"] if "thresholds" in self.config else False
                if new_threshold in self.config or dict_check:
                    await self.ctx.send("That threshold already exists", delete_after=5)
                    return self.reset()
                if isinstance(self.config, list):
                    self.config.append(new_threshold)
                else:
                    self.config["thresholds"].append(new_threshold)
                await self.update_data()
            self.reset()

        elif key == "Remove a custom threshold":
            # Something something something
            question = "Send the threshold and timespan to remove. Format like " \
                       "`6, 10` to remove one with a threshold of 6 and timespan of 10"
            reply = await self.get_reply(question)
            args = reply.split(", ")
            if not all(arg.isdigit() for arg in args) or len(args) != 2:
                await self.ctx.send("Invalid format", delete_after=5)
            else:
                threshold = {"timespan": args[0], "threshold": args[1]}
                dict_check = threshold not in self.config["thresholds"] if "thresholds" in self.config else False
                if threshold not in self.config and not dict_check:
                    await self.ctx.send("That threshold doesn't exist", delete_after=5)
                    return self.reset()
                if isinstance(self.config, list):
                    self.config.remove(threshold)
                else:
                    self.config["thresholds"].remove(threshold)
                await self.update_data()
            self.reset()

        else:
            # Something isn't fucking finished
            self.cursor = {"Unknown Option": None}


def setup(bot):
    bot.add_cog(AntiSpam(bot))
