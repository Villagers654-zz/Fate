import asyncio
import json
from time import time
from datetime import datetime, timezone, timedelta, timezone
from contextlib import suppress
import traceback
import pytz

import discord
from discord.errors import Forbidden, NotFound, HTTPException
from discord.ext import commands
from discord.ext import tasks

from botutils import colors, get_time, emojis


utc = pytz.UTC
defaults = {
    "rate_limit": [
        {
            "timespan": 3,
            "threshold": 4
        },
        {
            "timespan": 10,
            "threshold": 6
        }
    ],
    "mass_pings": {
        "per_message": 4,
        "thresholds": [{
            "timespan": 10,
            "threshold": 3
        },
        {
            "timespan": 30,
            "threshold": 6
        }
        ]
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
        "ascii": True,
        "copy_paste": True
    }
}


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.utils.cache("AntiSpam")

        # cache
        self.spam_cd = {}   # Cooldown cache for rate limiting
        self.macro_cd = {}  # Per-user message interval cache to look for patterns
        self.dupes = {}     # Per-channel index to keep track of duplicate messages
        self.msgs = {}      # Limited message cache
        self.mutes = {}     # Keep track of mutes to increment the timer per-mute
        self.typing = {}

        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.stop()

    def is_enabled(self, guild_id):
        return guild_id in self.config

    async def get_mutes(self) -> dict:
        mutes = {}
        async with self.bot.utils.cursor() as cur:
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
        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"delete from anti_spam_mutes "
                f"where guild_id = {guild_id} "
                f"and user_id = {user_id};"
            )

    @tasks.loop(seconds=10)
    async def cleanup_task(self):
        # Message Index
        for user_id, messages in list(self.msgs.items()):
            await asyncio.sleep(0)
            for msg in messages:
                with suppress(KeyError, IndexError, ValueError):
                    if not msg:
                        self.msgs[user_id].remove(msg)
                        continue
                    elif msg.created_at < datetime.now(tz=timezone.utc) - timedelta(seconds=15):
                        self.msgs[user_id].remove(msg)
            with suppress(KeyError):
                if not self.msgs[user_id]:
                    del self.msgs[user_id]

        # Duplicate text index
        for channel_id, messages in list(self.dupes.items()):
            await asyncio.sleep(0)
            for message in messages:
                with suppress(KeyError, ValueError, IndexError):
                    if not message:
                        self.dupes[channel_id].remove(message)
                    elif message.created_at < datetime.now(tz=timezone.utc) - timedelta(minutes=45):
                        self.dupes[channel_id].remove(message)
            with suppress(KeyError):
                if not self.dupes[channel_id]:
                    del self.dupes[channel_id]

        # Typing timestamps
        for user_id, timestamps in list(self.typing.items()):
            await asyncio.sleep(0)
            if not any((datetime.now(tz=timezone.utc) - date).seconds < 60 for date in self.typing[user_id]):
                if user_id in self.typing:
                    del self.typing[user_id]

    @commands.group(name="anti-spam", aliases=["antispam"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def anti_spam(self, ctx):
        if not ctx.invoked_subcommand and 'help' not in ctx.message.content:
            e = discord.Embed(color=colors.fate)
            e.set_author(name='AntiSpam Usage', icon_url=ctx.author.avatar.url)
            e.set_thumbnail(url=ctx.guild.icon.url)
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
                if conf:
                    e.add_field(name="◈ Config", value=conf, inline=False)
            await ctx.send(embed=e)

    @anti_spam.command(name="configure", aliases=["config"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    async def _configure(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
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
            self.config[guild_id] = defaults
            await self.config.flush()
            await ctx.send('Enabled the default anti-spam config')

    @_enable.command(name='rate-limit')
    @commands.has_permissions(manage_messages=True)
    async def _enable_rate_limit(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        conf = [{"timespan": 5, "threshold": 4}]
        self.config[guild_id]["rate_limit"] = conf
        await self.config.flush()
        await ctx.send('Enabled rate-limit module')

    @_enable.command(name='mass-pings', aliases=['mass-ping'])
    @commands.has_permissions(manage_messages=True)
    async def _enable_mass_pings(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]["mass_pings"] = {
            "per_message": 4,
            "thresholds": [{
                "timespan": 10,
                "threshold": 3
            }]
        }
        await self.config.flush()
        await ctx.send('Enabled rate-limit module')

    @_enable.command(name='anti-macro')
    @commands.has_permissions(manage_messages=True)
    async def _enable_anti_macro(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if "anti_macro" in self.config[guild_id]:
            return await ctx.send("Anti macro is already enabled")
        self.config[guild_id]["anti_macro"] = {}
        await self.config.flush()
        await ctx.send('Enabled anti-macro module')

    @_enable.command(name='duplicates')
    @commands.has_permissions(manage_messages=True)
    async def _enable_duplicates(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]["duplicates"] = {
            "per_message": 10,
            "thresholds": [{
                "timespan": 25,
                "threshold": 4
            }]
        }
        await self.config.flush()
        await ctx.send('Enabled duplicates module')

    @_enable.command(name='inhuman')
    @commands.has_permissions(manage_messages=True)
    async def _enable_inhuman(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]["inhuman"] = {
            "non_abc": True,
            "tall_messages": True,
            "empty_lines": True,
            "unknown_chars": True,
            "ascii": True,
            "copy_paste": True
        }
        await self.config.flush()
        await ctx.send('Enabled duplicates module')

    @anti_spam.group(name='disable')
    @commands.has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = ctx.guild.id
            if guild_id not in self.config:
                return await ctx.send("Anti-Spam isn't enabled")
            self.config.remove(guild_id)
            await ctx.send('Disabled anti-spam')

    @_disable.command(name='rate-limit', aliases=['Rate-Limit', 'ratelimit', 'RateLimit'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_rate_limit(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "rate_limit" not in self.config[guild_id]:
            return await ctx.send("Rate limit isn't enabled")
        self.config.remove_sub(guild_id, "rate_limit")
        await ctx.send('Disabled rate-limit module')

    @_disable.command(name='anti-macro', aliases=['Anti-Macro', 'antimacro', 'AntiMacro'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_anti_macro(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "anti_macro" not in self.config[guild_id]:
            return await ctx.send("Anti Macro isn't enabled")
        self.config.remove_sub(guild_id, "anti_macro")
        await ctx.send('Disabled anti-macro module')

    @_disable.command(name='mass-pings', aliases=['Mass-Pings', 'masspings', 'MassPings'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_mass_pings(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "mass_pings" not in self.config[guild_id]:
            return await ctx.send("Mass pings isn't enabled")
        self.config.remove_sub(guild_id, "mass_pings")
        await ctx.send('Disabled mass-pings module')

    @_disable.command(name='duplicates', aliases=['Duplicates', 'duplicate', 'Duplicate'])
    @commands.has_permissions(manage_messages=True)
    async def _disable_duplicates(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "duplicates" not in self.config[guild_id]:
            return await ctx.send("Duplicates isn't enabled")
        self.config.remove_sub(guild_id, "rate_limit")
        await ctx.send('Disabled rate-limit module')

    @_disable.command(name='inhuman')
    @commands.has_permissions(manage_messages=True)
    async def _disable_inhuman(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Anti spam isn't enabled")
        if "inhuman" not in self.config[guild_id]:
            return await ctx.send("Inhuman isn't enabled")
        self.config.remove_sub(guild_id, "inhuman")
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
            await ctx.send(f"I'll now ignore {channel.mention}")
        await self.config.flush()

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
            if not self.config[guild_id]["ignored"]:
                self.config.remove_sub(guild_id, "ignored")
            await ctx.send(f"I'll no longer ignore {channel.mention}")
        await self.config.flush()

    @anti_spam.command(name="stats")
    @commands.is_owner()
    async def stats(self, ctx):
        running = 0
        muted = 0
        done = []
        for guild_id, timers in self.bot.tasks["antispam_mutes"].items():
            for user_id, task in timers.items():
                if task.done():
                    done.append(task)
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        mute_role = await self.bot.attrs.get_mute_role(guild)
                        user = guild.get_member(int(user_id))
                        if user and mute_role and mute_role in user.roles:
                            muted += 1
                else:
                    running += 1
        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name="AntiSpam Stats", icon_url=self.bot.user.avatar.url)
        emotes = emojis
        errored = []
        try:
            errored = [task for task in done if task.exception() or task.result()]
        except:
            e.add_field(
                name="◈ Error",
                value=traceback.format_exc(),
                inline=False
            )
        e.description = f"{emotes.online} {running} tasks running\n" \
                        f"{emotes.idle} {len(done) - len(errored)} tasks done\n" \
                        f"{emotes.dnd} {len(errored)} tasks errored\n" \
                        f"{emotes.offline} {muted} still muted"
        await ctx.send(embed=e)

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

    async def destroy_task(self, guild_id, user_id):
        """Clean up the cache before ending the task"""
        guild_id = int(guild_id)
        user_id = int(user_id)
        if guild_id in self.bot.tasks["antispam_mutes"]:
            if user_id in self.bot.tasks["antispam_mutes"][guild_id]:
                del self.bot.tasks["antispam_mutes"][guild_id][user_id]
            if not self.bot.tasks["antispam_mutes"][guild_id]:
                del self.bot.tasks["antispam_mutes"][guild_id]
        with suppress(AttributeError):
            await self.delete_timer(guild_id, user_id)

    async def cleanup_from_message(self, msg):
        """Remove duplicate messages if duplicate msg spam was detected"""
        async for m in msg.channel.history(limit=10):
            if m.content == msg.content:
                with suppress(NotFound, Forbidden):
                    await m.delete()

    async def process_mute(self, guild_id, user_id, msg, reason="", resume=False, timer=0):
        """Handle the entire muting process separately"""
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return await self.destroy_task(guild_id, user_id)
        user = guild.get_member(int(user_id))
        if not user:
            return await self.destroy_task(guild_id, user_id)

        mute_role = await self.bot.attrs.get_mute_role(guild, upsert=True)
        if not mute_role or mute_role.position >= guild.me.top_role.position:
            return await self.destroy_task(guild_id, user_id)

        with self.bot.utils.operation_lock(key=int(user_id)):
            if not resume:
                bot_user = msg.guild.me
                perms = msg.channel.permissions_for(bot_user)
                if not perms.manage_messages or not perms.manage_roles:
                    return await self.destroy_task(guild_id, user_id)

                # Don't mute users with Administrator
                if user.top_role.position >= bot_user.top_role.position or user.guild_permissions.administrator:
                    return await self.destroy_task(guild_id, user_id)

                # Don't continue if lacking permission(s) to operate
                if not msg.channel.permissions_for(bot_user).send_messages or not perms.manage_roles:
                    return await self.destroy_task(guild_id, user_id)

                async with msg.channel.typing():
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
                    if mute_role in user.roles:
                        return await self.destroy_task(guild_id, user_id)

                    timer = 150
                    timer *= multiplier
                    end_time = time() + timer
                    timer_str = get_time(timer)

                    try:
                        await user.add_roles(mute_role)
                    except (NotFound, HTTPException) as e:
                        with suppress(Exception):
                            await msg.channel.send(f"Failed to mute {msg.author}. {e}")
                        return await self.destroy_task(guild_id, user_id)
                    except Forbidden:
                        with suppress(Exception):
                            await msg.channel.send(f"Failed to mute {msg.author}. Missing permissions")
                        return await self.destroy_task(guild_id, user_id)

                    messages = []
                    if user_id in self.msgs:
                        messages = [m for m in self.msgs[user_id] if m]
                    with suppress(Forbidden, NotFound, HTTPException):
                        await msg.channel.delete_messages(messages)
                    self.msgs[user_id] = []

                    with suppress(NotFound, Forbidden, HTTPException):
                        await user.send(f"You've been muted for spam in **{msg.guild.name}** for {timer_str}")
                    mentions = discord.AllowedMentions(users=True)
                    with suppress(NotFound, Forbidden, HTTPException):
                        await msg.channel.send(
                            f"Temporarily muted {user.mention} for spam. Reason: {reason}",
                            allowed_mentions=mentions
                        )

                    if "duplicate" in reason:
                        if msg.channel.permissions_for(msg.guild.me).manage_messages:
                            if msg.channel.permissions_for(msg.guild.me).read_message_history:
                                self.bot.loop.create_task(self.cleanup_from_message(msg))

                    with suppress(Exception):
                        async with self.bot.utils.cursor() as cur:
                            await cur.execute(
                                f"insert into anti_spam_mutes "
                                f"values ("
                                f"{msg.guild.id}, "
                                f"{msg.channel.id}, "
                                f"{msg.author.id}, "
                                f"{mute_role.id}, "
                                f"'{end_time}')"
                                f"on duplicate key update "
                                f"end_time = '{end_time}';"
                            )

            if timer > 3600:
                self.bot.log.critical(f"An antispam task is sleeping for {timer} seconds")

            await asyncio.sleep(timer)
            if user and mute_role and mute_role in user.roles:
                if not msg:
                    with suppress(NotFound, Forbidden, HTTPException):
                        await user.remove_roles(mute_role)
                else:
                    try:
                        await user.remove_roles(mute_role)
                    except Forbidden:
                        await msg.channel.send(f"Missing permissions to unmute {user.mention}")
                    except NotFound:
                        await msg.channel.send(f"Couldn't find and unmute **{user}**")
                    except HTTPException:
                        await msg.channel.send(f"Unknown error while unmuting {user.mention}")
                    else:
                        await msg.channel.send(
                            f"Unmuted **{user.mention}**",
                            allowed_mentions=discord.AllowedMentions(users=True)
                        )

            return await self.destroy_task(guild_id, user_id)

    @commands.Cog.listener("on_typing")
    async def log_typing_timestamps(self, channel, user, when):
        if hasattr(channel, "guild") and channel.guild and channel.guild.id in self.config:
            guild_id = channel.guild.id
            if "inhuman" in self.config[guild_id] and self.config[guild_id]["inhuman"]["copy_paste"]:
                user_id = user.id
                if user_id not in self.typing:
                    self.typing[user_id] = []
                self.typing[user_id].append(when)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not isinstance(msg.guild, discord.Guild) or msg.author.bot:
            return
        guild_id = msg.guild.id
        user_id = msg.author.id
        triggered = False
        if guild_id in self.config and self.config[guild_id]:
            if "ignored" in self.config[guild_id] and msg.channel.id in self.config[guild_id]["ignored"]:
                return

            perms = msg.channel.permissions_for(msg.guild.me)
            if not perms.manage_messages or not perms.manage_roles:
                return

            users = [msg.author]
            reason = "Unknown"

            # msgs to delete if triggered
            if user_id not in self.msgs:
                self.msgs[user_id] = []
            self.msgs[user_id].append(msg)
            self.msgs[user_id] = self.msgs[user_id][-15:]

            # Inhuman checks
            if "inhuman" in self.config[guild_id] and msg.content:
                conf = self.config[guild_id]["inhuman"]  # type: dict
                abcs = "abcdefghijklmnopqrstuvwxyzجحخهعغفقثصضشسيبلاتتمكطدظزوةىرؤءذئأإآ"

                content = str(msg.content).lower()
                lines = content.split("\n")

                total_abcs = len([c for c in content if c in abcs])
                total_abcs = total_abcs if total_abcs else 1

                total_spaces = content.count(" ")
                total_spaces = total_spaces if total_spaces else 1

                has_abcs = any(content.count(c) for c in abcs)

                # non abc char spam
                if conf["non_abc"]:
                    if len(msg.content) > 256 and not has_abcs:
                        reason = "Inhuman: non abc"
                        triggered = True

                # Tall msg spam
                if conf["tall_messages"]:
                    if len(content.split("\n")) > 8 and sum(len(line) for line in lines if line) < 21:
                        reason = "Inhuman: tall message"
                        triggered = True
                    elif len(content.split("\n")) > 5 and not has_abcs:
                        reason = "Inhuman: tall message"
                        triggered = True

                # Empty lines spam
                if conf["empty_lines"]:
                    small_lines = len([l for l in lines if not l or len(l) < 3])
                    large_lines = len([l for l in lines if l and len(l) > 2])
                    if small_lines > large_lines and len(lines) > 8:
                        reason = "Inhuman: too many empty lines"
                        triggered = True

                # Mostly unknown chars spam
                if conf["unknown_chars"]:
                    if len(content) > 128 and len(content) / total_abcs > 3:
                        if not ("http" in content and len(content) < 512):
                            reason = "Inhuman: mostly non abc characters"
                            triggered = True

                # ASCII / Spammed chars
                if conf["ascii"]:
                    if len(content) > 256 and len(content) / total_spaces > 10:
                        reason = "Inhuman: ascii"
                        triggered = True

                # Pasting large messages without typing much, or at all
                lmt = 250 if "http" in msg.content else 100
                check = msg.channel.permissions_for(msg.author).manage_messages
                if not check and conf["copy_paste"] and len(msg.content) > lmt:
                    if user_id not in self.typing:
                        reason = "pasting bulky message (check #1)"
                        triggered = None
                    elif len(msg.content) > 150:
                        typed_recently = any(
                            (datetime.now(tz=timezone.utc) - date).seconds < 25 for date in self.typing[user_id]
                        )
                        if not typed_recently:
                            reason = "pasting bulky message (check #2)"
                            triggered = None
                        if len(msg.content) > 250:
                            count = len([
                                ts for ts in self.typing[user_id]
                                if (datetime.now(tz=timezone.utc) - ts).seconds < 60
                            ])
                            if count < 3:
                                reason = "pasting bulky message (check #3)"
                                triggered = None
                    if user_id in self.typing:
                        del self.typing[user_id]

            # Rate limit
            if "rate_limit" in self.config[guild_id] and self.config[guild_id]["rate_limit"] and not triggered:
                if guild_id not in self.spam_cd:
                    self.spam_cd[guild_id] = {}
                for rate_limit in list(self.config[guild_id]["rate_limit"]):
                    await asyncio.sleep(0)
                    dat = [
                        *list(rate_limit.values()),
                        ",".join(str(v) for v in rate_limit.values())
                    ]
                    timespan, threshold, uid = dat
                    if uid not in self.spam_cd[guild_id]:
                        self.spam_cd[guild_id][uid] = {}
                for rl_id in list(self.spam_cd[guild_id].keys()):
                    await asyncio.sleep(0)
                    raw = rl_id.split(",")
                    dat = {
                        "timespan": int(raw[0]),
                        "threshold": int(raw[1])
                    }
                    if dat not in self.config[guild_id]["rate_limit"]:
                        del self.spam_cd[guild_id][rl_id]

                for rl_id in list(self.spam_cd[guild_id].keys()):
                    await asyncio.sleep(0)
                    timeframe, threshold = rl_id.split(",")
                    now = int(time() / int(timeframe))
                    if user_id not in self.spam_cd[guild_id][rl_id]:
                        self.spam_cd[guild_id][rl_id][user_id] = [now, 0]
                    if self.spam_cd[guild_id][rl_id][user_id][0] == now:
                        self.spam_cd[guild_id][rl_id][user_id][1] += 1
                    else:
                        self.spam_cd[guild_id][rl_id][user_id] = [now, 0]
                    if self.spam_cd[guild_id][rl_id][user_id][1] >= int(threshold):
                        reason = f"{threshold} messages within {timeframe} seconds"
                        triggered = True

            # mass pings
            if "mass_pings" in self.config[guild_id] and not triggered:
                await asyncio.sleep(0)
                pings = [msg.raw_mentions, msg.raw_role_mentions]
                total_pings = sum(len(group) for group in pings)
                if total_pings > self.config[guild_id]["mass_pings"]["per_message"]:
                    reason = "mass pinging"
                    triggered = True

                if user_id not in self.msgs:
                    self.msgs[user_id] = []
                pongs = lambda s: [
                    m for m in self.msgs[user_id]
                    if m and m.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=s)
                       and sum(len(group) for group in [
                        m.mentions, m.raw_mentions, m.role_mentions, m.raw_role_mentions
                    ])
                ]

                for threshold in self.config[guild_id]["mass_pings"]["thresholds"]:
                    await asyncio.sleep(0)
                    if user_id not in self.msgs:
                        self.msgs[user_id] = []
                    if len(pongs(threshold["timespan"])) > threshold["threshold"]:
                        reason = "mass pinging"
                        triggered = True

            # anti macro
            if "anti_macro" in self.config[guild_id] and not triggered:
                async def has_pattern(intervals):
                    total = []
                    for index in range(len(intervals)):
                        for i in range(5):
                            await asyncio.sleep(0)
                            total.append(intervals[index:index + i])

                    total = [p for p in total if len(p) > 2]
                    top = []
                    for lst in sorted(total, key=lambda v: total.count(v), reverse=True):
                        await asyncio.sleep(0)
                        dat = [lst, total.count(lst)]
                        if dat not in top:
                            top.append(dat)

                    for lst, count in top[:5]:
                        await asyncio.sleep(0)
                        div = round(len(intervals) / len(lst))
                        if all(i < 3 for i in lst):
                            return False
                        elif count >= div - 1:
                            return True
                        else:
                            return False

                ts = datetime.timestamp
                if user_id not in self.macro_cd:
                    self.macro_cd[user_id] = [ts(msg.created_at), []]
                else:
                    self.macro_cd[user_id][1] = [
                        *self.macro_cd[user_id][1][-20:],
                        ts(msg.created_at) - self.macro_cd[user_id][0]
                    ]
                    self.macro_cd[user_id][0] = ts(msg.created_at)
                    intervals = [int(i) for i in self.macro_cd[user_id][1]]
                    if len(intervals) > 12:
                        if all(round(cd) == round(intervals[0]) for cd in intervals):
                            if intervals[0] > 3 and intervals[0] < 3:
                                triggered = True
                                reason = "Repeated messages at the same interval"
                        elif await has_pattern(intervals):
                            triggered = True
                            reason = "Using a bot/macro"

            # duplicate messages
            if "duplicates" in self.config[guild_id] and msg.content and not triggered:
                await asyncio.sleep(0)
                if msg.channel.permissions_for(msg.guild.me).read_message_history:
                    with self.bot.utils.operation_lock(key=msg.id):
                        channel_id = str(msg.channel.id)
                        if channel_id not in self.dupes:
                            self.dupes[channel_id] = []
                        self.dupes[channel_id] = [
                            msg, *[
                                msg for msg in self.dupes[channel_id]
                                if msg.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=60)
                            ]
                        ]
                        for threshold in self.config[guild_id]["duplicates"]["thresholds"]:
                            lmt = threshold["threshold"]
                            timeframe = threshold["timespan"]
                            for message in list(self.dupes[channel_id]):
                                await asyncio.sleep(0)
                                if channel_id not in self.dupes:
                                    break
                                dupes = [
                                    m for m in self.dupes[channel_id]
                                    if m and m.content and m.content == message.content
                                       and m.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=timeframe)
                                       and len(m.content) > 5
                                ]
                                all_are_single_use = all(
                                    len([m for m in dupes if m.author.id == dupes[i].author.id]) == 1
                                    for i in range(len(dupes))
                                )
                                if len(dupes) > 1 and not all_are_single_use:
                                    if len([d for d in dupes if d.author.id == dupes[0].author.id]) == 1:
                                        dupes.pop(0)
                                if len(dupes) > lmt:
                                    history = await msg.channel.history(limit=2).flatten()
                                    if not any(m.author.bot for m in history):
                                        users = set(list([
                                            *[m.author for m in dupes if m], *users
                                        ]))
                                        for message in dupes:
                                            with suppress(IndexError, ValueError, KeyError):
                                                self.dupes[channel_id].remove(message)
                                        with suppress(Forbidden, NotFound):
                                            await msg.channel.delete_messages([
                                                message for message in dupes if message
                                            ])
                                        reason = "duplicate messages"
                                        triggered = True
                                        break
                            if triggered:
                                break

            if triggered is None or "ascii" in reason and not msg.author.guild_permissions.administrator:
                with suppress(HTTPException, NotFound, Forbidden):
                    await msg.delete()
                    await msg.channel.send(f"No {reason}")
                return

            if triggered and guild_id in self.config:
                # Mute the relevant users
                for iteration, user in enumerate(list(set(users))):
                    with self.bot.utils.operation_lock(key=user.id):
                        guild_id = msg.guild.id
                        user_id = user.id
                        bot_user = msg.guild.me
                        perms = msg.channel.permissions_for(bot_user)
                        if not perms.manage_messages:
                            return

                        # Purge away spam
                        messages = []
                        if user_id in self.msgs:
                            messages = [
                                m for m in self.msgs[user_id]
                                if m and m.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=15)
                            ]
                        self.msgs[user_id] = []  # Remove soon to be deleted messages from the list
                        with suppress(NotFound, Forbidden, HTTPException):
                            await msg.channel.delete_messages(messages)

                        # Don't mute users with Administrator
                        if user.top_role.position >= bot_user.top_role.position or user.guild_permissions.administrator:
                            return
                        # Don't continue if lacking permission(s) to operate
                        if not msg.channel.permissions_for(bot_user).send_messages or not perms.manage_roles:
                            return

                        async with msg.channel.typing():
                            mute_role = await self.bot.attrs.get_mute_role(msg.guild, upsert=True)
                            if not mute_role or mute_role.position >= msg.guild.me.top_role.position:
                                return

                    if "antispam_mutes" not in self.bot.tasks:
                        self.bot.tasks["antispam_mutes"] = {}
                    if guild_id not in self.bot.tasks["antispam_mutes"]:
                        self.bot.tasks["antispam_mutes"][guild_id] = {}
                    if user_id in self.bot.tasks["antispam_mutes"][guild_id]:
                        task = self.bot.tasks["antispam_mutes"][guild_id][user_id]
                        if task.done():
                            if task.result():
                                self.bot.log.critical(f"An antispam task errored.\n{task.result()}")
                            else:
                                self.bot.log.critical(f"An antispam task errored with no result")
                        else:
                            return

                    self.bot.tasks["antispam_mutes"][guild_id][user_id] = self.bot.loop.create_task(
                        self.process_mute(
                            user_id=user.id,
                            guild_id=guild_id,
                            msg=msg,
                            reason=reason
                        )
                    )

    @commands.Cog.listener()
    async def on_ready(self):
        if "antispam_mutes" not in self.bot.tasks:
            self.bot.tasks["antispam_mutes"] = {}
        mutes = await self.get_mutes()
        for guild_id, mutes in list(mutes.items()):
            for user_id, data in mutes.items():
                if guild_id not in self.bot.tasks["antispam_mutes"]:
                    self.bot.tasks["antispam_mutes"][guild_id] = {}
                if user_id not in self.bot.tasks["antispam_mutes"][guild_id]:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        await self.destroy_task(guild_id, user_id)
                        continue
                    try:
                        self.bot.tasks["antispam_mutes"][guild_id][user_id] = self.bot.loop.create_task(
                            self.process_mute(
                                guild_id=guild_id,
                                user_id=user_id,
                                msg=None,
                                reason="",
                                timer=round(float(data["end_time"]) - time()),
                                resume=True
                            )
                        )
                        self.bot.log.info(f"Resumed a anti_spam mute in {guild}")
                    except AttributeError:
                        await self.destroy_task(guild_id, user_id)
                        self.bot.log.info(f"Deleted a anti_spam task in {guild} due to changes")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_id = str(before.guild.id)
        user_id = str(before.id)
        if "antispam_mutes" not in self.bot.tasks:
            self.bot.tasks["antispam_mutes"] = {}
        if guild_id in self.bot.tasks["antispam_mutes"]:
            if user_id in self.bot.tasks["antispam_mutes"][guild_id]:
                await asyncio.sleep(5)
                mute_role = await self.bot.attrs.get_mute_role(before.guild, upsert=False)
                if not mute_role:
                    return
                if mute_role not in after.roles:
                    await self.destroy_task(guild_id, user_id)
            if guild_id in self.bot.tasks["antispam_mutes"]:
                if not self.bot.tasks["antispam_mutes"][guild_id]:
                    del self.bot.tasks["antispam_mutes"][guild_id]


class ConfigureModules:
    def __init__(self, ctx):
        self.super = ctx.bot.cogs["AntiSpam"]
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id

        self.cursor = self.modules
        self.row = 0
        self.config = self.key = None

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
        ignored = ('ignored', 'anti_macro')
        return {
            module: data
            for module, data in items
            if module not in ignored
        }

    def create_embed(self, **kwargs):
        """Get default embed style"""
        return discord.Embed(
            title="Enabled Modules", color=self.bot.config["theme_color"], **kwargs
        )

    def get_description(self):
        # Format the current options
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
            if not self.cursor[key] and not isinstance(self.cursor[key], list):
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
            if isinstance(self.config, list):
                conf = []
                for item in self.config:
                    dat = {}
                    for k, v in sorted(item.items(), key=lambda kv: kv[0]):
                        dat[k] = v
                    conf.append(dat)
            else:
                conf = {}
                for k, v in sorted(self.config.items(), key=lambda kv: kv[0]):
                    conf[k] = v
            e.add_field(
                name="◈ Config",
                value=f"```json\n{json.dumps(conf, indent=2)}```"
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
                if int(reply) > 16:
                    await self.ctx.send("At the moment you can't go above 16")
                    return self.reset()
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
            if len(self.config) == 3 if isinstance(self.config, list) else len(self.config["thresholds"]) == 3:
                await self.ctx.send("You can't have more than 3 thresholds", delete_after=5)
                return self.reset()
            question = "Send the threshold and timespan to use. Format like " \
                       "`6, 10` to only allow 6 msgs within 10 seconds"
            reply = await self.get_reply(question)
            args = reply.split(", ")
            if not all(arg.isdigit() for arg in args) or len(args) != 2:
                await self.ctx.send("Invalid format", delete_after=5)
            else:
                if int(args[0]) > 60:
                    await self.ctx.send("You can't go above 60s for the timespan")
                    return self.reset()
                if int(args[1]) > 30:
                    await self.ctx.send("You can't go above 30 for the threshold")
                    return self.reset()
                new_threshold = {"timespan": int(args[1]), "threshold": int(args[0])}
                list_check = new_threshold in self.config if isinstance(self.config, list) else False
                dict_check = new_threshold in self.config["thresholds"] if isinstance(self.config, dict) else False
                if list_check or dict_check:
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
                threshold = {"timespan": int(args[1]), "threshold": int(args[0])}
                list_check = threshold in self.config if isinstance(self.config, list) else False
                dict_check = threshold in self.config["thresholds"] if isinstance(self.config, dict) else False
                if not list_check and not dict_check:
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
    bot.add_cog(AntiSpam(bot), override=True)
