"""
cogs.core.ranking
~~~~~~~~~~~~~~~~~~

A customizable xp ranking cog

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import json
from time import time, monotonic
from random import *
import asyncio
from io import BytesIO
from datetime import datetime, timezone, timedelta
import aiohttp
from pymysql.err import DataError, InternalError
from contextlib import suppress

from discord.ext import commands, tasks
import discord
from discord import NotFound, Forbidden
from PIL import Image, ImageFont, ImageDraw, ImageSequence, UnidentifiedImageError

from botutils import colors, get_prefix, url_from, Menu, cache_rewrite
from botutils.pillow import add_corners
from classes import IgnoredExit


def profile_help():
    e = discord.Embed(color=colors.purple)
    e.add_field(
        name=".set title your_new_title",
        value="Changes the title field in your profile card",
        inline=False,
    )
    e.add_field(
        name=".set background [optional-url]",
        value="You can attach a file while using the cmd, or put a link where it says optional-url. "
        "If you don't do either, i'll reset your background to default (transparent)",
    )
    return e


cleanup_interval = 3600
leaderboard_icon = "https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png"


class Ranking(commands.Cog):
    path = "./data/userdata/xp.json"  # filepath: Per-guild xp configs
    profile_path = "./data/userdata/profiles.json"  # filepath: Profile data
    clb_path = "./data/userdata/cmd-lb.json"  # filepath: Commands used
    default_config = {
        "min_xp_per_msg": 1,
        "max_xp_per_msg": 1,
        "first_lvl_xp_req": 250,
        "timeframe": 10,
        "msgs_within_timeframe": 1,
    }

    msg_cooldown = 3600
    cd = {}
    global_cd = {}
    spam_cd = {}
    macro_cd = {}
    cmd_cd = {}

    def __init__(self, bot):
        self.bot = bot
        self.channels: bot.utils.cache = bot.cogs["Messages"].config
        self.levels = {}

        # Configs
        self.config = cache_rewrite.Cache(bot, "ranking", default=self.default_config)
        self.profile = cache_rewrite.Cache(bot, "profiles")

        # Help menus
        self.set_usage = self.set
        self.role_rewards_usage = self.role_rewards
        self.profile_usage = f"`.profile` your global rank\n" \
                             f"`.rank` your rank in the server"
        self.leaderboard_usage = "`.lb` server leaderboard\n" \
                                 "`.glb` global leaderboard\n" \
                                 "`.mlb` monthly server leaderboard\n" \
                                 "`.gmlb` global monthly server leaderboard"
        self.clb_usage = "`.clb` displays the top used commands on the bot"
        self.top_help = "shows the top 10 ranked users in the server"

        self.cmd_cleanup_task.start()
        self.monthly_cleanup_task.start()
        self.cooldown_cleanup_task.start()

    def cog_unload(self):
        self.cmd_cleanup_task.cancel()
        self.monthly_cleanup_task.cancel()
        self.cooldown_cleanup_task.cancel()

    @tasks.loop(hours=1)
    async def cmd_cleanup_task(self):
        async with self.bot.utils.cursor() as cur:
            lmt = int(datetime.timestamp(
                datetime.now(tz=timezone.utc) + timedelta(days=30)
            ))
            await cur.execute(
                f"delete from commands where ran_at > {lmt};"
            )

    @tasks.loop(minutes=1)
    async def cooldown_cleanup_task(self):
        before = monotonic()
        total = 0
        for user_id, timestamp in list(self.global_cd.items()):
            await asyncio.sleep(0)
            if timestamp < time():
                del self.global_cd[user_id]
                total += 1
        ping = str(round((monotonic() - before) * 1000)) + "ms"
        self.bot.log.debug(f"Removed {total} cooldowns in {ping}")
        self.spam_cd = {}
        self.macro_cd = {}

    @tasks.loop(hours=1)
    async def monthly_cleanup_task(self):
        await asyncio.sleep(1)
        self.bot.log.debug("Started xp cleanup task")
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        while self.bot.pool is None:
            await asyncio.sleep(5)
        async with self.bot.utils.cursor() as cur:
            limit = time() - 60 * 60 * 24 * 30  # One month
            await cur.execute(f"delete from monthly_msg where msg_time < {limit};")
            await cur.execute(
                f"delete from global_monthly where msg_time < {limit};"
            )
            self.bot.log.debug("Removed expired messages from monthly leaderboards")

    @staticmethod
    async def get_multiplier_for(level):
        multiplier = 1
        increase_by = 0.125
        reduce_at = 3

        for i in range(level):
            await asyncio.sleep(0)
            if multiplier >= reduce_at:
                increase_by /= 2
                reduce_at += 3
            multiplier += increase_by

        return multiplier

    async def calc_lvl_info(self, xp, config):
        level = 0
        remaining_xp = xp
        base_requirement = config["first_lvl_xp_req"]

        while True:
            await asyncio.sleep(0)
            multiplier = await self.get_multiplier_for(level)
            current_req = base_requirement * multiplier
            if remaining_xp < current_req:
                break
            remaining_xp -= current_req
            level += 1
            if level >= 500:
                break

        data = {
            "level": level,
            "xp": xp,
            "level_start": (xp + (current_req - remaining_xp)) - current_req,
            "level_end": xp + (current_req - remaining_xp),
            "start_to_end": current_req,
            "progress": remaining_xp
        }
        return {
            key: round(value) for key, value in data.items()
        }

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild and not msg.author.bot and self.bot.pool:
            await asyncio.sleep(0.21)
            guild_id = msg.guild.id
            user_id = msg.author.id

            async def punish():
                self.global_cd[user_id] = time() + 60

            # anti spam
            now = int(time() / 5)
            if guild_id not in self.spam_cd:
                self.spam_cd[guild_id] = {}
            if user_id not in self.spam_cd[guild_id]:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][0] == now:
                self.spam_cd[guild_id][user_id][1] += 1
            else:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][1] > 3:
                return await punish()
            await asyncio.sleep(0)

            # anti macro
            if user_id not in self.macro_cd:
                self.macro_cd[user_id] = {}
                self.macro_cd[user_id]["intervals"] = []
            if "last" not in self.macro_cd[user_id]:
                self.macro_cd[user_id]["last"] = datetime.now(tz=timezone.utc)
            else:
                last = self.macro_cd[user_id]["last"]
                self.macro_cd[user_id]["intervals"].append(
                    (datetime.now(tz=timezone.utc) - last).seconds
                )
                intervals = self.macro_cd[user_id]["intervals"]
                self.macro_cd[user_id]["intervals"] = intervals[-3:]
                if len(intervals) > 2:
                    if all(interval == intervals[0] for interval in intervals):
                        return await punish()

            set_time = datetime.timestamp(
                datetime.now(tz=timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0)
            )
            if user_id not in self.global_cd:
                self.global_cd[user_id] = 0
            if self.global_cd[user_id] < time():
                self.global_cd[user_id] = time() + 10
                try:
                    async with self.bot.utils.cursor() as cur:
                        await cur.execute(
                            f"insert into global_msg "
                            f"values ({user_id}, 1) "
                            f"on duplicate key update xp = xp + 1;"
                        )

                        # global monthly msg xp
                        await cur.execute(
                            f"INSERT INTO global_monthly "
                            f"VALUES ({user_id}, {set_time}, 1) "
                            f"ON DUPLICATE KEY UPDATE xp = xp + 1;"
                        )
                except DataError as error:
                    self.bot.log(f"Error updating global xp\n{error}")
                except InternalError:
                    pass
                except RuntimeError:
                    return

            # per-server leveling
            conf = await self.config[guild_id] or self.default_config
            if conf["min_xp_per_msg"] >= conf["max_xp_per_msg"]:
                new_xp = conf["min_xp_per_msg"]
            else:
                new_xp = randint(conf["min_xp_per_msg"], conf["max_xp_per_msg"])
            if guild_id not in self.cd:
                self.cd[guild_id] = {}
            if user_id not in self.cd[guild_id]:
                self.cd[guild_id][user_id] = []
            msgs = [
                x for x in self.cd[guild_id][user_id] if x > time() - conf["timeframe"]
            ]
            self.cd[guild_id][user_id] = msgs
            if len(msgs) < conf["msgs_within_timeframe"]:
                self.cd[guild_id][user_id].append(time())
                try:
                    async with self.bot.utils.cursor() as cur:
                        # Guilded xp
                        await cur.execute(
                            f"insert into msg "
                            f"values ({guild_id}, {user_id}, {new_xp}) "
                            f"on duplicate key update xp = xp + {new_xp};"
                        )

                        # Monthly guilded msg xp
                        await cur.execute(
                            f"INSERT INTO monthly_msg "
                            f"VALUES ({guild_id}, {user_id}, {set_time}, {new_xp}) "
                            f"ON DUPLICATE KEY UPDATE xp = xp + {new_xp};"
                        )

                        # Fetch current xp for level roles
                        await cur.execute(
                            f"select xp from msg "
                            f"where guild_id = {guild_id} "
                            f"and user_id = {user_id} "
                            f"limit 1;"
                        )
                        if not cur.rowcount:
                            return
                        xp, = await cur.fetchone()

                    # Fetch the level information
                    dat = await self.calc_lvl_info(xp, conf)

                    # Check if the user leveled up
                    queued_message = None
                    if config := self.channels.get(guild_id, None):
                        if location := config.get("level_up_messages", None):
                            if guild_id not in self.levels:
                                self.levels[guild_id] = {}
                            if user_id not in self.levels[guild_id]:
                                self.levels[guild_id][user_id] = [dat["level"], time()]
                            else:
                                if dat["level"] > self.levels[guild_id][user_id][0]:
                                    channel = self.bot.get_channel(location) or msg.channel
                                    if channel and channel.permissions_for(msg.guild.me).send_messages:
                                        queued_message = channel.send(
                                            content=f"{msg.author.mention}, **you're now level {dat['level']}**",
                                            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                                        )
                                self.levels[guild_id][user_id] = [dat["level"], time()]

                    # Fetch available level roles
                    async with self.bot.utils.cursor() as cur:
                        await cur.execute(
                            f"select role_id, lvl, stack from role_rewards "
                            f"where guild_id = {guild_id} "
                            f"and lvl <= {dat['level']} "
                            f"order by lvl asc;"
                        )
                        if not cur.rowcount:
                            if queued_message:
                                await queued_message
                            return
                        results = await cur.fetchall()

                    # Check if the user's missing any of the roles
                    results = sorted(results, key=lambda v: v[1], reverse=True)
                    for role_id, lvl, stack, *_args in results:
                        role = msg.guild.get_role(role_id)
                        if role not in msg.author.roles:
                            try:
                                await msg.author.add_roles(role)
                                e = discord.Embed(color=role.color)
                                e.description = f"You leveled up and earned {role.mention}"
                                with suppress(Forbidden):
                                    await msg.channel.send(embed=e)
                                if not stack:
                                    await cur.execute(
                                        f"select role_id from role_rewards "
                                        f"where guild_id = {guild_id};"
                                    )
                                    results = await cur.fetchall()
                                    for _role_id, in results:
                                        if _role_id != role_id:
                                            role = msg.guild.get_role(_role_id)
                                            if role in msg.author.roles:
                                                await msg.author.remove_roles(role)
                                    return
                            except (NotFound, Forbidden, AttributeError):
                                await self.bot.execute(
                                    f"delete from role_rewards "
                                    f"where role_id = {role_id} limit 1;"
                                )
                            except Exception:
                                pass
                        if not stack:
                            return

                except DataError as error:
                    self.bot.log(f"Error updating guild xp\n{error}")
                except InternalError:
                    pass

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await asyncio.sleep(0.5)
        if ctx.command.name == "sexuality":
            ctx.command.name = "gay"
        cmd = ctx.command.name
        set_time = int(datetime.timestamp(
            datetime.now(tz=timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0)
        ))
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from commands where command = '{cmd}' and ran_at = {(set_time)};")
            if cur.rowcount:
                await cur.execute(
                    f"update commands "
                    f"set total = total + 1 "
                    f"where command = '{cmd}' and ran_at = {set_time};"
                )
            else:
                await cur.execute(f"insert into commands values ('{cmd}', 1, {set_time});")

    @commands.group(
        name="role-rewards",
        aliases=["level-rewards", "level-roles", "lr"],
        description="Grant roles for leveling up"
    )
    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def role_rewards(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Level Roles", icon_url=self.bot.user.display_avatar.url)
            e.set_thumbnail(url=url_from(ctx.guild.icon))
            e.description = self.role_rewards.description
            p = get_prefix(ctx)  # type: str
            cmd = ctx.invoked_with
            e.add_field(
                name="◈ Usage",
                value=f"{p}{cmd} add [level] @role\n"
                      f"`adds a level reward`\n"
                      f"{p}{cmd} remove @role\n"
                      f"`removes a level reward`\n"
                      f"{p}{cmd} limit-all\n"
                      f"`only lets users keep the highest role reward`\n"
                      f"{p}{cmd} unlimit-all\n"
                      f"`lets users maintain every role reward they earn`",
                inline=False
            )
            e.add_field(
                name="◈ Note",
                value="Replace `@role` with the mention for the role you want to give, "
                      "and replace `[level]` with the level you want the role to be given at",
                inline=False
            )
            async with self.bot.utils.cursor() as cur:
                await cur.execute(
                    f"select role_id, lvl from role_rewards "
                    f"where guild_id = {ctx.guild.id} "
                    f"order by lvl desc;"
                )
                results = await cur.fetchall()
            if results:
                value = ""
                for role_id, level in results:
                    value += f"\nLvl {level} - {ctx.guild.get_role(int(role_id)).mention}"
                e.add_field(
                    name="◈ Active Roles",
                    value=value,
                    inline=False
                )
            await ctx.send(embed=e)

    @role_rewards.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def _add(self, ctx, level: int, *, role: discord.Role = None):
        if level <= 0:
            return await ctx.send("The level requirement can't be less than 1")
        if not role:
            role = await self.bot.utils.get_role(ctx, role)
            if not role:
                return await ctx.send("I wasn't able to find that role")
        if role.position >= ctx.author.top_role.position:
            return await ctx.send("That role's above your paygrade. Take a seat")
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's too high for me to manage")

        # Check the number of role rewards
        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select * from role_rewards "
                f"where guild_id = {ctx.guild.id};"
            )
            entries = cur.rowcount
        if entries >= 10:
            return await ctx.send("You can't have more than 10 level rewards")

        stack = True
        await ctx.send(
            "Should I remove this role when the user gets a higher role reward? "
            "Reply with `yes` or `no`"
        )
        reply = await self.bot.utils.get_message(ctx)
        if "yes" in reply.content.lower():
            stack = False

        await self.bot.execute(
            f"insert into role_rewards "
            f"values ({ctx.guild.id}, {role.id}, {level}, {stack}) "
            f"on duplicate key update lvl = {level} and stack = {stack};"
        )
        await ctx.send(f"Added {role.mention}")

    @role_rewards.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def _remove(self, ctx, role: discord.Role = None):
        if not role:
            role = await self.bot.utils.get_role(ctx, role)
            if not role:
                return await ctx.send("I wasn't able to find that role")
        await self.bot.execute(f"delete from role_rewards where role_id = {role.id};")
        await ctx.send(f"Removed the level-role for {role.mention} if it existed")

    @role_rewards.command(name="limit-all")
    @commands.has_permissions(manage_roles=True)
    async def _limit_all(self, ctx):
        await self.bot.execute(f"update role_rewards set stack = False where guild_id = {ctx.guild.id};")
        await ctx.send("Set the limit to only keep the top role reward")

    @role_rewards.command(name="unlimit-all")
    @commands.has_permissions(manage_roles=True)
    async def _unlimit_all(self, ctx):
        await self.bot.execute(f"update role_rewards set stack = True where guild_id = {ctx.guild.id};")
        await ctx.send("Set the limit to allow keeping all role rewards")

    @commands.command(name="xp-config", description="Shows the current xp configuration")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def xp_config(self, ctx):
        """ Sends an overview for the current config """
        e = discord.Embed(color=0x4A0E50)
        e.set_author(name="XP Configuration", icon_url=ctx.guild.owner.display_avatar.url)
        e.set_thumbnail(url=self.bot.user.display_avatar.url)
        conf = await self.config[ctx.guild.id]
        e.description = (
            f"• Min XP Per Msg: {conf['min_xp_per_msg']}"
            f"\n• Max XP Per Msg: {conf['max_xp_per_msg']}"
            f"\n• Timeframe: {conf['timeframe']}"
            f"\n• Msgs Within Timeframe: {conf['msgs_within_timeframe']}"
            f"\n• First Lvl XP Req: {conf['first_lvl_xp_req']}"
        )
        p = get_prefix(ctx)
        e.set_footer(text=f"Use {p}set to adjust these settings")
        await ctx.send(embed=e)

    @commands.group(name="set", description="Shows usage on how to use the set command")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    async def set(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Set Usage", icon_url=ctx.author.display_avatar.url)
            e.set_thumbnail(url=self.bot.user.display_avatar.url)
            p: str = ctx.prefix
            e.description = "`[]` = your arguments / setting"
            e.add_field(
                name="◈ Profile Stuff",
                value=f"{p}set title [new title]"
                f"\n• `sets the title in your profile`"
                f"\n{p}set background [optional_url]"
                f"\n• `sets your profiles background img`",
                inline=False,
            )
            e.add_field(
                name="◈ XP Stuff",
                value=f"{p}set min-xp-per-msg [amount]"
                f"\n• `sets the minimum gained xp per msg`"
                f"\n{p}set max-xp-per-msg [amount]"
                f"\n• `sets the maximum gained xp per msg`"
                f"\n{p}set timeframe [amount]"
                f"\n• `sets the timeframe to allow x messages`"
                f"\n{p}set msgs-within-timeframe [amount]"
                f"\n• `sets the limit of msgs within the timeframe`"
                f"\n{p}set first-lvl-xp-req [amount]"
                f"\n• `required xp to level up your first time`",
                inline=False,
            )
            e.set_footer(text=f"Use {p}xp-config to see xp settings")
            await ctx.send(embed=e)

    @set.command(name="title", description="Sets the title in your profile card")
    async def _set_title(self, ctx, *, title):
        if len(title) > 32:
            return await ctx.send("Titles can't be greater than 22 characters")
        await self.profile[ctx.author.id].set("title", title)
        await ctx.send("Set your title")

    @set.command(name="background", description="Sets the background in your profile card")
    async def _set_background(self, ctx, url=None):
        profile = await self.profile[ctx.author.id]
        if not url and not ctx.message.attachments:
            if "background" not in profile:
                return await ctx.send("You don't have a custom background")
            del profile["background"]
            await ctx.send("Reset your background")
            return await profile.save()
        if not url:
            url = ctx.message.attachments[0].url
        profile["background"] = url
        await ctx.send("Set your background image")
        await profile.save()

    @set.command(name="min-xp-per-msg", description="Sets the minimum xp users get from a message")
    @commands.has_permissions(administrator=True)
    async def _min_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        conf = await self.config[ctx.guild.id]
        conf["min_xp_per_msg"] = amount
        msg = f"Set the minimum xp gained per msg to {amount}"
        if amount > conf["max_xp_per_msg"]:
            conf["max_xp_per_msg"] = amount
            msg += f". I also upped the maximum xp per msg to {amount}"
        await ctx.send(msg)
        await conf.save()

    @set.command(name="max-xp-per-msg", description="Sets the maximum xp users get from a message")
    @commands.has_permissions(administrator=True)
    async def _max_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        conf = await self.config[ctx.guild.id]
        conf["max_xp_per_msg"] = amount
        msg = f"Set the maximum xp gained per msg to {amount}"
        if amount < conf["min_xp_per_msg"]:
            conf["min_xp_per_msg"] = amount
            msg += f". I also lowered the minimum xp per msg to {amount}"
        await ctx.send(msg)
        await conf.save()

    @set.command(name="timeframe", description="Sets the timeframe to allow x messages")
    @commands.has_permissions(administrator=True)
    async def _timeframe(self, ctx, amount: int):
        """ sets the timeframe to allow x messages """
        if amount > 3600:
            return await ctx.send("The timeframe can't be longer than an hour")
        await self.config[ctx.guild.id].set("timeframe", amount)
        await ctx.send(f"Set the timeframe that allows x messages to {amount}")

    @set.command(name="msgs-within-timeframe", description="the limit of msgs within the timeframe")
    @commands.has_permissions(administrator=True)
    async def _msgs_within_timeframe(self, ctx, amount: int):
        """ sets the limit of msgs within the timeframe """
        if amount > 3600:
            return await ctx.send("That number's too high")
        await self.config[ctx.guild.id].set("msgs_within_timeframe", amount)
        await ctx.send(f"Set msgs within timeframe limit to {amount}")

    @set.command(name="first-lvl-xp-req", description="Sets the required xp to level up your first time")
    @commands.has_permissions(administrator=True)
    async def _first_level_xp_req(self, ctx, amount: int):
        """ sets the required xp to level up your first time """
        if amount > 2500:
            return await ctx.send("You can't set an amount greater than 2,500")
        elif amount < 100:
            return await ctx.send("You can't set an amount smaller than 100")
        await self.config[ctx.guild.id].set("first_lvl_xp_req", amount)
        await ctx.send(f"Set the required xp to level up your first time to {amount}")

    @commands.command(name="give-xp", description="Gives a user additional xp")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.cooldown(2, 10, commands.BucketType.channel)
    @commands.guild_only()
    async def give_xp(self, ctx, users: commands.Greedy[discord.Member], amount: int):
        if len(users) > 3:
            return await ctx.send("You can't alter the xp of more than 3 users at a time")
        if amount <= 0:
            return await ctx.send("The amount must be greater than 0")
        async with self.bot.utils.cursor() as cur:
            for user in users:
                await cur.execute(
                    f"insert into msg values ({ctx.guild.id}, {user.id}, {amount}) "
                    f"on duplicate key update xp = xp + {amount};"
                )
        await ctx.send(
            f"Gave {', '.join(u.mention for u in users)} {amount} xp",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )

    @commands.command(name="give-xp", description="Gives a user additional xp")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.cooldown(2, 10, commands.BucketType.channel)
    @commands.guild_only()
    async def give_xp(self, ctx, users: commands.Greedy[discord.Member], amount: int):
        if ctx.author.id != ctx.guild.owner.id:
            return await ctx.send("Only the server owner can run this")
        if len(users) > 3:
            return await ctx.send("You can't alter the xp of more than 3 users at a time")
        if amount <= 0:
            return await ctx.send("The amount must be greater than 0")
        async with self.bot.utils.cursor() as cur:
            for user in users:
                await cur.execute(
                    f"insert into msg values ({ctx.guild.id}, {user.id}, {amount}) "
                    f"on duplicate key update xp = xp + {amount};"
                )
        await ctx.send(
            f"Gave {', '.join(u.mention for u in users)} {amount} xp",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )

    @commands.command(name="remove-xp", description="Removes some of a users xp")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.cooldown(2, 10, commands.BucketType.channel)
    @commands.guild_only()
    async def remove_xp(self, ctx, users: commands.Greedy[discord.Member], amount: int):
        if ctx.author.id != ctx.guild.owner.id:
            return await ctx.send("Only the server owner can run this")
        if len(users) > 3:
            return await ctx.send("You can't alter the xp of more than 3 users at a time")
        if amount <= 0:
            return await ctx.send("The amount must be greater than 0")
        async with self.bot.utils.cursor() as cur:
            for user in users:
                await cur.execute(
                    f"select * from msg "
                    f"where guild_id = {ctx.guild.id} "
                    f"and user_id = {user.id} "
                    f"and xp >= {amount};"
                )
                if cur.rowcount:
                    await cur.execute(
                        f"update msg "
                        f"set xp = xp - {amount} "
                        f"where guild_id = {ctx.guild.id} "
                        f"and user_id = {user.id};"
                    )
                else:
                    await cur.execute(
                        f"delete from msg "
                        f"where guild_id = {ctx.guild.id} "
                        f"and user_id = {user.id};"
                    )
        await ctx.send(
            f"Removed {amount} xp from {', '.join(u.mention for u in users)}",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )

    @commands.command(
        name="profile",
        aliases=["rank"],
        description="Shows your profile or rank card",
        usage=profile_help()
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    async def profile(self, ctx):
        """ Profile / Rank Image Card """
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        user_id = user.id
        guild_id = ctx.guild.id
        conf = await self.config[guild_id]

        # config
        title = "Use .help profile"
        backgrounds = [
            "https://cdn.discordapp.com/attachments/632084935506788385/670258618750337024/unknown.png",  # gold
            "https://media.giphy.com/media/26n6FdRZBIjOCHpJK/giphy.gif",  # spinning blade effect
        ]
        background_url = choice(backgrounds)
        if ctx.guild.splash:
            background_url = str(ctx.guild.splash.url)
        if ctx.guild.banner:
            background_url = str(ctx.guild.banner.url)
        profile = await self.profile[user_id]
        if "title" in profile:
            title = profile["title"]
        if "background" in profile:
            background_url = profile["background"]

        # xp variables
        guild_rank = "unranked"  # this is required, remember to get this here
        who = 'You' if user.id == ctx.author.id else 'They'
        async with self.bot.utils.cursor() as cur:
            if "global" in ctx.message.content or "profile" in ctx.message.content.lower():
                await cur.execute(f"select xp from global_msg where user_id = {user_id} limit 1;")
                results = await cur.fetchone()  # type: tuple
                if not results:
                    return await ctx.send(
                        f"{who} currently have no global xp, try rerunning this command now"
                    )
                dat = await self.calc_lvl_info(results[0], self.default_config)
            else:
                await cur.execute(
                    f"select xp from msg "
                    f"where guild_id = {guild_id} "
                    f"and user_id = {user_id} "
                    f"limit 1;"
                )
                results = await cur.fetchone()  # type: tuple
                if not results:
                    return await ctx.send(
                        f"{who} currently have no xp in this server, try rerunning this command now"
                    )
                dat = await self.calc_lvl_info(results[0], conf)

        base_req = conf["first_lvl_xp_req"]
        level = dat["level"]
        xp = dat["progress"]
        max_xp = base_req if level == 0 else dat["start_to_end"]
        length = ((100 * (xp / max_xp)) * 1000) / 100
        required = f"Required: {max_xp - xp}"
        progress = f"{xp} / {max_xp} xp"
        misc = f"{progress} | {required}"

        # pick status icon
        statuses = {
            discord.Status.online: "https://cdn.discordapp.com/emojis/659976003334045727.png?v=1",
            discord.Status.idle: "https://cdn.discordapp.com/emojis/659976006030983206.png?v=1",
            discord.Status.dnd: "https://cdn.discordapp.com/emojis/659976008627388438.png?v=1",
            discord.Status.offline: "https://cdn.discordapp.com/emojis/659976011651219462.png?v=1",
        }
        status = statuses[user.status]
        if user.is_on_mobile():
            status = "https://cdn.discordapp.com/attachments/541520201926311986/666182794665263124/1578900748602.png"

        # Prepare the profile card
        url = "https://cdn.discordapp.com/attachments/632084935506788385/666158201867075585/rank-card.png"
        raw_card = await self.bot.get_resource(url)
        raw_avatar = await self.bot.get_resource(str(user.display_avatar.url))
        raw_status = await self.bot.get_resource(status)
        try:
            raw_background = await self.bot.get_resource(background_url, label="background")
        except (aiohttp.InvalidURL, UnidentifiedImageError):
            return await ctx.send(
                "Sorry, but I seem to be having issues using your current background"
                "\nYou can use `.set background` to reset it, or attach a file while "
                "using that command to change it"
            )

        def create_card():
            def process_frame(card, frame):
                frame = frame.convert("RGBA")
                frame = frame.resize((1000, 500), Image.BICUBIC)
                frame.paste(card, (0, 0), card)
                return frame

            def font(size):
                return ImageFont.truetype("./botutils/fonts/Modern_Sans_Light.otf", size)

            file = BytesIO()
            card = Image.open(BytesIO(raw_card))
            draw = ImageDraw.Draw(card)
            data = []
            for r, g, b, c in card.getdata():
                if c == 0:
                    data.append((r, g, b, c))
                elif r == 0 and g == 174 and b == 239:  # blue
                    data.append((r, g, b, 100))
                elif r == 48 and g == 48 and b == 48:  # dark gray
                    data.append((r, g, b, 225))
                elif r == 218 and g == 218 and b == 218:  # light gray
                    data.append((r, g, b, 150))
                else:
                    data.append((r, g, b, c))
            card.putdata(data)

            # user vanity
            avatar = Image.open(BytesIO(raw_avatar)).convert("RGBA")
            avatar = add_corners(avatar.resize((175, 175), Image.BICUBIC), 87)
            card.paste(avatar, (75, 85), avatar)
            draw.ellipse((75, 85, 251, 261), outline="black", width=6)
            status = Image.open(BytesIO(raw_status)).convert("RGBA")
            status = status.resize((75, 75), Image.BICUBIC)
            card.paste(status, (190, 190), status)

            # leveling / ranking
            rank_pos = [865, 85]
            rank_font = 30
            for i in range(len(str(guild_rank))):
                if i > 1:
                    rank_pos[1] += 1
                    rank_font -= 5
            draw.text(
                tuple(rank_pos),
                f"Rank #{guild_rank}",
                (255, 255, 255),
                font=font(rank_font),
            )

            level_pos = [640, 145]
            text = f"Level {level}"
            for i in range(len(str(level))):
                if i == 1:
                    text = f"Lvl. {level}"
                    level_pos[0] += 15
                if i == 2:
                    level_pos[0] -= 5
                if i == 3:
                    level_pos[0] -= 5
            draw.text(tuple(level_pos), text, (0, 0, 0), font=font(100))

            draw.text((10, 320), title, (0, 0, 0), font=font(50))
            draw.text((25, 415), misc, (255, 255, 255), font=font(50))
            draw.line((0, 500, length, 500), fill=user.color.to_rgb(), width=10)

            # backgrounds and saving
            if not background_url:
                card.save(file, format="PNG")
                return file, "png"

            try:
                background = Image.open(BytesIO(raw_background)).convert("RGBA")
            except UnidentifiedImageError:
                self.bot.loop.create_task(ctx.send("Invalid background. Change it via .set background"))
                raise IgnoredExit

            # Ordinary image
            if "gif" not in background_url:
                background = background.convert("RGBA")
                background = background.resize((1000, 500), Image.BICUBIC)
                background.paste(card, (0, 0), card)
                background.save(file, format="PNG")
                return file, "png"

            # Keep the size of gifs low
            dur = background.info["duration"]
            skip = False
            frames = []
            for frame in ImageSequence.Iterator(background):
                frames.append(process_frame(card, frame))
            while True:
                if len(frames) < 75:
                    break
                for frame in frames:
                    if skip:
                        frames.remove(frame)
                    skip = not skip

            frames[0].save(
                fp=file,
                save_all=True,
                append_images=frames[1:],
                loop=0,
                duration=dur,
                optimize=False,
                format="GIF"
            )
            return file, "gif"

        file, ext = await self.bot.loop.run_in_executor(None, create_card)
        file.seek(0)
        ty = "Profile" if "profile" in ctx.message.content.lower() else "Rank"
        await ctx.send(f"> **{ty} card for {user}**", file=discord.File(file, filename=f"card.{ext.lower()}"))

    @commands.command(name="top", description="Shows the top 9 ranking users in the server", aliases=["levels"])
    @commands.cooldown(1, 25, commands.BucketType.user)
    @commands.cooldown(1, 25, commands.BucketType.guild)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def top(self, ctx):
        if hasattr(ctx, "channel"):
            await ctx.channel.trigger_typing()

        async def get_av_task(url):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(url)) as resp:
                        result = BytesIO(await resp.read())
                        return result
            except:
                await ctx.send(f"can't get {url}")

        def font(size):
            return ImageFont.truetype("./botutils/fonts/Roboto-Bold.ttf", size=size)

        r = await self.bot.fetch(
            f"select user_id, xp from msg where guild_id = {ctx.guild.id} order by xp desc limit 20;"
        )
        members = []
        for user_id, xp in r:
            await asyncio.sleep(0)
            member = ctx.guild.get_member(user_id)
            if member:
                members.append([member, xp])

        conf = await self.config[ctx.guild.id]

        tasks = [
            [
                m, xp,
                await self.calc_lvl_info(xp, conf),
                self.bot.loop.create_task(get_av_task(m.display_avatar.url))
            ] for m, xp in members[:9]
        ]
        for i in range(50):
            await asyncio.sleep(0.21)
            if all(task.done() for _m, _xp, _lvl_dat, task in tasks):
                break
        else:
            return await ctx.send("Couldn't get all of the avatars for the top 9 users")
        assets = []
        for member, xp, lvl_dat, task in tasks:
            with suppress(Exception):
                assets.append([member, xp, lvl_dat, task.result()])

        def create_card():
            card = Image.new("RGBA", (750, 900), color=(0, 0, 0, 0))
            for i, (member, xp, lvl_dat, asset) in enumerate(assets):
                av = Image.open(asset).convert("RGBA")
                av = av.resize((90, 90), Image.BICUBIC)
                im = Image.new(mode="RGBA", size=(740, 90), color=(114, 137, 218))
                im.paste(av, (0, 0), av)
                draw = ImageDraw.Draw(im)
                im = add_corners(im, 25)

                if i < 1:
                    r = Image.open(f"./assets/ranking/ribbon_{i + 1}.png").convert("RGBA")
                    r = r.resize((90, 90), Image.BICUBIC)
                    im.paste(r, (515, 0), r)

                data = []
                for r, g, b, c in im.getdata():
                    if (r, g, b, c) == (114, 137, 218, 255):
                        data.append((r, g, b, 150))
                    else:
                        data.append((r, g, b, c))
                im.putdata(data)

                draw.text((110, 22), member.name[:18], (255, 255, 255), font=font(45))

                lvl = str(lvl_dat['level']).rjust(3, " ")
                progress = f"{lvl_dat['progress']}/{lvl_dat['start_to_end']}"

                draw.text((615, 15), f"Lvl {lvl}", (255, 255, 255), font=font(30))
                draw.text((620, 55), progress, (255, 255, 255), font=font(20))

                card.paste(im, (5, 100 * i), im)

            card.save(file, format="png")
            file.seek(0)

        file = BytesIO()
        try:
            await self.bot.loop.run_in_executor(None, create_card)
        except UnidentifiedImageError:
            return await ctx.send("Failed to fetch one of the top users avatars. Rerunning the command might fix")

        await ctx.send(file=discord.File(file, filename="top.png"))

    async def generate_embeds(self, name: str, rankings: list, limit_per_page: int):
        """ Gen a list of embed leaderboards """
        embeds = []

        e = discord.Embed(color=0x4A0E50)
        e.set_author(name=name)
        e.set_thumbnail(url=leaderboard_icon)
        e.description = ""

        rank = 1
        for i, (user_id, xp) in enumerate(rankings):
            await asyncio.sleep(0)
            user = self.bot.get_user(int(user_id))
            if user:
                username = str(user.name)
            else:
                username = "UNKNOWN-USER"

            if i == 0 and user:
                e.set_author(name=name, icon_url=user.display_avatar.url)

            if i and i % limit_per_page == 0:
                embeds.append(e)
                e = discord.Embed(color=0x4A0E50)
                icon_url = user.display_avatar.url if user else None
                e.set_author(name=name, icon_url=icon_url)
                e.set_thumbnail(url=leaderboard_icon)
                e.description = ""

            e.description += f"#{rank}. `{username}` - {xp}\n"
            rank += 1

        embeds.append(e)
        return embeds

    @commands.command(
        name="leaderboard",
        aliases=["lb"],
        description="Ranks everyone in the server"
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.cooldown(6, 60, commands.BucketType.guild)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True, add_reactions=True)
    async def leaderboard(self, ctx):
        """ Refined leaderboard command """

        default = discord.Embed()
        default.description = "Collecting Leaderboard Data.."
        leaderboards = {}

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select user_id, xp from msg where guild_id = {ctx.guild.id} order by xp desc limit 256;"
            )
            results = await cur.fetchall()
            leaderboards["Msg Leaderboard"] = {
                user_id: xp
                for user_id, xp in results
                if ctx.guild.get_member(int(user_id))
            }

            await cur.execute(
                "select user_id, xp from global_msg order by xp desc limit 256;"
            )
            results = await cur.fetchall()
            leaderboards["Global Msg Leaderboard"] = {
                user_id: xp for user_id, xp in results
            }

            lmt = time() - 60 * 60 * 24 * 30
            await cur.execute(
                f"select user_id, sum(xp) as total_xp "
                f"from monthly_msg "
                f"where guild_id = {ctx.guild.id} and msg_time > {lmt} "
                f"group by user_id "
                f"order by total_xp desc limit 256;"
            )
            results = await cur.fetchall()
            leaderboards["Monthly Msg Leaderboard"] = {
                user_id: xp for user_id, xp in results
            }

            await cur.execute(
                f"select user_id, sum(xp) as total_xp "
                f"from global_monthly "
                f"where msg_time > {lmt} "
                f"group by user_id "
                f"order by total_xp desc limit 256;"
            )
            results = await cur.fetchall()
            leaderboards["Globaly Monthly Leaderboard"] = {
                user_id: xp for user_id, xp in results
            }

        mapping = {}
        for name, data in leaderboards.items():
            await asyncio.sleep(0)
            sorted_data = [
                (user_id, xp)
                for user_id, xp in data.items()
                if self.bot.get_user(int(user_id))
            ]
            if not sorted_data or not sorted_data[0]:
                return await ctx.send(
                    "Insufficient leaderboard data. Try again later, or join the support server "
                    f"and ask for help {self.bot.config['support_server']}"
                )
            ems = await self.generate_embeds(
                name=name,
                rankings=sorted_data,
                limit_per_page=15
            )
            for i, embed in enumerate(ems):
                embed.set_footer(text=f"Page {i + 1}/{len(ems)}")
            mapping[name] = ems

        await Menu(ctx, mapping)

    @commands.command(name="clb", description="Shows the command leaderboard")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clb(self, ctx):
        # Remove old uses from the db
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Command Leaderboard", icon_url=self.bot.user.display_avatar.url)
        e.description = ""
        rank = 1
        for cmd, uses in sorted(self.cmds.items(), key=lambda kv: kv[1]["total"], reverse=True)[:10]:
            e.description += f"**#{rank}.** `{cmd}` - {uses['total']}\n"
            rank += 1
        await ctx.send(embed=e)

    @commands.command(name="gen-lb")
    @commands.is_owner()
    async def generate_leaderboard(self, ctx):
        async def update_embed(m, data):
            """ gen and update the leaderboard embed """
            e = discord.Embed(color=0x4A0E50)
            e.title = "Msg Leaderboard"
            e.description = ""
            rank = 1
            for user_id, xp in sorted(data.items(), reverse=True, key=lambda kv: kv[1]):
                user = self.bot.get_user(int(user_id))
                if not isinstance(user, discord.User):
                    continue
                e.description += f"#{rank}. `{user}` - {xp}\n"
                rank += 1
                if rank == 10:
                    break
            e.set_footer(text=footer)
            await m.edit(embed=e)

        e = discord.Embed()
        e.description = "Starting.."
        m = await ctx.send(embed=e)

        xp = {}
        last_update = time() + 5

        for i, channel in enumerate(ctx.guild.text_channels):
            footer = f"Reading #{channel.name} ({i + 1}/{len(ctx.guild.text_channels)})"
            await update_embed(m, xp)
            last_gain = {}
            bot_counter = 0

            async for msg in channel.history(oldest_first=True, limit=None):
                # skip channels where every msg is a bot
                if msg.author.bot:
                    bot_counter += 1
                    if bot_counter == 1024:
                        break
                    continue
                else:
                    bot_counter = 0

                # init
                user_id = str(msg.author.id)
                if user_id not in xp:
                    xp[user_id] = 0
                if user_id not in last_gain:
                    last_gain[user_id] = None
                if last_gain[user_id]:
                    if (msg.created_at - last_gain[user_id]).total_seconds() < 10:
                        continue

                # update stuff
                last_gain[user_id] = msg.created_at
                xp[user_id] += 1
                if last_update < time():
                    await update_embed(m, xp)
                    last_update = time() + 5

        footer = f"Gen Complete ({len(ctx.guild.text_channels)}/{len(ctx.guild.text_channels)})"
        await update_embed(m, xp)


def setup(bot):
    bot.add_cog(Ranking(bot), override=True)
