"""
cogs.core.ranking
~~~~~~~~~~~~~~~~~~

A customizable xp ranking cog

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import json
from time import time, monotonic
from random import *
import asyncio
from io import BytesIO
from datetime import datetime, timezone
import aiohttp
from pymysql.err import DataError, InternalError
from contextlib import suppress
import os

from discord.ext import commands, tasks
import discord
from discord.errors import NotFound, Forbidden
from PIL import Image, ImageFont, ImageDraw, ImageSequence, UnidentifiedImageError

from botutils import colors, get_prefix
from botutils.pillow import add_corners


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


class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/xp.json"  # filepath: Per-guild xp configs
        self.profile_path = "./data/userdata/profiles.json"  # filepath: Profile data
        self.clb_path = "./data/userdata/cmd-lb.json"  # filepath: Commands used
        self.msg_cooldown = 3600
        self.cd = {}
        self.global_cd = {}
        self.spam_cd = {}
        self.macro_cd = {}
        self.cmd_cd = {}
        self.counter = 0
        self.vc_counter = 0
        self.backup_counter = 0
        self.cache = {}
        self.leaderboards = {}
        self.guild_xp = {}
        self.global_xp = {}
        self.monthly_guild_xp = {}
        self.global_monthly_xp = {}

        # Configs
        self.config = bot.utils.cache("ranking")
        self.profile = bot.utils.cache("profiles")
        self.cmds = bot.utils.cache("commands", auto_sync=True)
        self.bot.loop.create_task(self.cmds.flush())

        # Save storage
        for guild_id, config in list(self.config.items()):
            if config == self.static_config():
                self.config.remove(guild_id)

        # Vc caching
        self.vclb = {}
        self.vc_counter = 0

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

    async def cog_before_invoke(self, ctx):
        if ctx.guild.id not in self.config:
            self.config[ctx.guild.id] = self.static_config()

    async def save_config(self):
        """ Saves per-server configuration """
        pass
        # async with self.bot.utils.open(self.path, "w+") as f:
        #     raw = json.dumps(self.config)
        #     await f.write(raw)

    def static_config(self):
        """ Default config """
        return {
            "min_xp_per_msg": 1,
            "max_xp_per_msg": 1,
            "first_lvl_xp_req": 250,
            "timeframe": 10,
            "msgs_within_timeframe": 1,
        }

    async def init(self, guild_id: str):
        """ Saves static config as the guilds initial config """
        self.config[guild_id] = self.static_config()
        await self.save_config()

    @tasks.loop(hours=1)
    async def cmd_cleanup_task(self):
        for cmd, dat in list(self.cmds.items()):
            for date in dat["uses"]:
                await asyncio.sleep(0)
                if (datetime.now() - date).days > 30:
                    self.cmds[cmd]["uses"].remove(date)
                    self.cmds[cmd]["total"] -= 1
        await self.cmds.flush()

    @tasks.loop(minutes=1)
    async def cooldown_cleanup_task(self):
        before = monotonic()
        total = 0
        for user_id, timestamp in list(self.global_cd.items()):
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
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                limit = time() - 60 * 60 * 24 * 30  # One month
                await cur.execute(f"delete from monthly_msg where msg_time < {limit};")
                await cur.execute(
                    f"delete from global_monthly where msg_time < {limit};"
                )
                await conn.commit()
                self.bot.log.debug("Removed expired messages from monthly leaderboards")

    async def calc_lvl_info(self, xp, config):
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

        level = 0
        remaining_xp = xp
        base_requirement = config["first_lvl_xp_req"]

        while True:
            await asyncio.sleep(0)
            multiplier = await get_multiplier_for(level)
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
            guild_id = str(msg.guild.id)
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
            conf = self.static_config()  # type: dict
            if guild_id in self.config:
                conf = self.config[guild_id]
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

                        # Fetch current xp for xp based roles
                        await cur.execute(
                            f"select xp from msg "
                            f"where guild_id = {guild_id} "
                            f"and user_id = {user_id} "
                            f"limit 1;"
                        )
                        result = await cur.fetchone()
                        if not result:
                            return
                    dat = await self.calc_lvl_info(result[0], conf)
                    async with self.bot.utils.cursor() as cur:
                        await cur.execute(
                            f"select role_id from role_rewards "
                            f"where guild_id = {guild_id} "
                            f"and lvl <= {dat['level']} "
                            f"order by lvl asc;"
                        )
                        results = await cur.fetchall()
                    for result in results:
                        role = msg.guild.get_role(result[0])
                        if role not in msg.author.roles:
                            try:
                                await msg.author.add_roles(role)
                                e = discord.Embed(color=role.color)
                                e.description = f"You leveled up and earned {role.mention}"
                                with suppress(Forbidden):
                                    await msg.channel.send(embed=e)
                            except (NotFound, Forbidden, AttributeError):
                                await self.bot.execute(
                                    f"delete from role_rewards "
                                    f"where role_id = {result[0]} limit 1;"
                                )
#
                except DataError as error:
                    self.bot.log(f"Error updating guild xp\n{error}")
                except InternalError:
                    pass

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.command.name == "sexuality":
            ctx.command.name = "gay"
        if ctx.command.name not in self.cmds:
            self.cmds[ctx.command.name] = {"uses": [], "total": 0}
        self.cmds[ctx.command.name]["uses"].append(datetime.now())
        self.cmds[ctx.command.name]["total"] += 1

    @commands.command(name="role-rewards", aliases=["level-rewards", "level-roles", "lr"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def role_rewards(self, ctx, *args):
        if not args or len(args) == 1:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Level Roles", icon_url=self.bot.user.avatar.url)
            e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Grant roles as a reward to users whence they reach a specified level"
            p = get_prefix(ctx)  # type: str
            e.add_field(
                name="◈ Usage",
                value=f"{p}level-rewards @role [level]\n"
                      f"`adds a level reward`\n"
                      f"{p}level-rewards remove @role\n"
                      f"`removes a level reward`",
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
            return await ctx.send(embed=e)

        if ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
        else:
            role = await self.bot.utils.get_role(ctx, args[1])
            if not role:
                return await ctx.send("Role not found")

        if "remove" in args[0].lower():
            await self.bot.execute(f"delete from role_rewards where role_id = {role.id};")
            return await ctx.send(f"Removed the level-role for {role.mention} if it existed")
        if not args[1].isdigit():
            return await ctx.send(
                "Your command isn't formatted properly. "
                "The level argument you put wasn't a number"
            )

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select * from role_rewards "
                f"where guild_id = {ctx.guild.id};"
            )
            entries = cur.rowcount
        if entries >= 10:
            return await ctx.send("You can't have more than 10 level rewards")

        level = int(args[1])
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
        await ctx.send(f"Setup complete")

    @commands.command(name="xp-config")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def xp_config(self, ctx):
        """ Sends an overview for the current config """
        e = discord.Embed(color=0x4A0E50)
        e.set_author(name="XP Configuration", icon_url=ctx.guild.owner.avatar.url)
        e.set_thumbnail(url=self.bot.user.avatar.url)
        conf = self.config[ctx.guild.id]
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

    @commands.group(name="set")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    async def set(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Set Usage", icon_url=ctx.author.avatar.url)
            e.set_thumbnail(url=self.bot.user.avatar.url)
            p = get_prefix(ctx)  # type: str
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

    @set.command(name="title")
    async def _set_title(self, ctx, *, title):
        if len(title) > 32:
            return await ctx.send("Titles can't be greater than 22 characters")
        user_id = ctx.author.id
        if user_id not in self.profile:
            self.profile[user_id] = {}
        self.profile[user_id]["title"] = title
        await ctx.send("Set your title")
        await self.profile.flush()

    @set.command(name="background")
    async def _set_background(self, ctx, url=None):
        user_id = ctx.author.id  # type: dict
        if user_id not in self.profile:
            self.profile[user_id] = {}
        if not url and not ctx.message.attachments:
            if "background" not in self.profile[user_id]:
                return await ctx.send("You don't have a custom background")
            self.profile.remove_sub(user_id, "background")
            await ctx.send("Reset your background")
            return await self.profile.flush()
        if not url:
            url = ctx.message.attachments[0].url
        self.profile[user_id]["background"] = url
        await ctx.send("Set your background image")
        await self.profile.flush()

    @set.command(name="min-xp-per-msg")
    @commands.has_permissions(administrator=True)
    async def _min_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        guild_id = ctx.guild.id
        self.config[guild_id]["min_xp_per_msg"] = amount
        msg = f"Set the minimum xp gained per msg to {amount}"
        if amount > self.config[guild_id]["max_xp_per_msg"]:
            self.config[guild_id]["max_xp_per_msg"] = amount
            msg += f". I also upped the maximum xp per msg to {amount}"
        await ctx.send(msg)
        await self.config.flush()

    @set.command(name="max-xp-per-msg")
    @commands.has_permissions(administrator=True)
    async def _max_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        guild_id = ctx.guild.id
        self.config[guild_id]["max_xp_per_msg"] = amount
        msg = f"Set the maximum xp gained per msg to {amount}"
        if amount < self.config[guild_id]["min_xp_per_msg"]:
            self.config[guild_id]["min_xp_per_msg"] = amount
            msg += f". I also lowered the minimum xp per msg to {amount}"
        await ctx.send(msg)
        await self.config.flush()

    @set.command(name="timeframe")
    @commands.has_permissions(administrator=True)
    async def _timeframe(self, ctx, amount: int):
        """ sets the timeframe to allow x messages """
        guild_id = ctx.guild.id
        self.config[guild_id]["timeframe"] = amount
        await ctx.send(f"Set the timeframe that allows x messages to {amount}")
        await self.config.flush()

    @set.command(name="msgs-within-timeframe")
    @commands.has_permissions(administrator=True)
    async def _msgs_within_timeframe(self, ctx, amount: int):
        """ sets the limit of msgs within the timeframe """
        guild_id = ctx.guild.id
        self.config[guild_id]["msgs_within_timeframe"] = amount
        await ctx.send(f"Set msgs within timeframe limit to {amount}")
        await self.config.flush()

    @set.command(name="first-lvl-xp-req")
    @commands.has_permissions(administrator=True)
    async def _first_level_xp_req(self, ctx, amount: int):
        """ sets the required xp to level up your first time """
        if amount > 2500:
            return await ctx.send("You can't set an amount greater than 2,500")
        elif amount < 100:
            return await ctx.send("You can't set an amount smaller than 100")
        guild_id = ctx.guild.id
        self.config[guild_id]["first_lvl_xp_req"] = amount
        await ctx.send(f"Set the required xp to level up your first time to {amount}")
        await self.config.flush()

    @commands.command(name="profile", aliases=["rank"], usage=profile_help())
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    async def profile(self, ctx):
        """ Profile / Rank Image Card """
        path = "./static/card.png"
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        user_id = user.id
        guild_id = str(ctx.guild.id)
        conf = self.config[guild_id]

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
        if user_id in self.profile:
            if "title" in self.profile[user_id]:
                title = self.profile[user_id]["title"]
            if "background" in self.profile[user_id]:
                background_url = self.profile[user_id]["background"]
        if "gif" in background_url:
            path = path.replace("png", "gif")

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
                dat = await self.calc_lvl_info(results[0], self.static_config())
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

        base_req = self.config[guild_id]["first_lvl_xp_req"]
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
        raw_avatar = await self.bot.get_resource(str(user.avatar.url))
        raw_status = await self.bot.get_resource(status)
        try:
            raw_background = await self.bot.get_resource(background_url)
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
                raise self.bot.ignored_exit

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

    @commands.command(name="top")
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

        fp = os.path.basename(f"static/card-{time()}.png")
        r = await self.bot.fetch(
            f"select user_id, xp from msg where guild_id = {ctx.guild.id} order by xp desc limit 20;"
        )
        members = []
        for user_id, xp in r:
            await asyncio.sleep(0)
            member = ctx.guild.get_member(user_id)
            if member:
                members.append([member, xp])

        conf = self.static_config()
        if str(ctx.guild.id) in self.config:
            conf = self.config[str(ctx.guild.id)]

        tasks = [
            [
                m, xp,
                await self.calc_lvl_info(xp, conf),
                self.bot.loop.create_task(get_av_task(m.avatar.url))
            ] for m, xp in members[:9]
        ]
        for i in range(50):
            await asyncio.sleep(0.21)
            if all(task.done() for _m, _xp, _lvl_dat, task in tasks):
                break
        else:
            return await ctx.send("Couldn't get all of the avatars for the top 9 users")

        def create_card():
            card = Image.new("RGBA", (750, 900), color=(0, 0, 0, 0))
            for i, (member, xp, lvl_dat, task) in enumerate(tasks):
                av = Image.open(task.result()).convert("RGBA")
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

            card.save(fp)

        await self.bot.loop.run_in_executor(None, create_card)
        if not hasattr(ctx, "channel"):
            return fp

        e = discord.Embed(color=colors.fate)
        icon_url = self.bot.user.avatar.url
        if ctx.guild.icon:
            icon_url = ctx.guild.icon.url
        e.set_author(name=ctx.guild.name, icon_url=icon_url)
        e.set_image(url=f"attachment://{fp}")
        await ctx.send(embed=e, file=discord.File(fp, filename=fp))
        os.remove(fp)

    @commands.command(
        name="leaderboard",
        aliases=[
            "lb",
            "mlb",
            "vclb",
            "glb",
            "gmlb",
            "gvclb",
            "gglb",
            "ggvclb",
            "mleaderboard",
            "vcleaderboard",
            "gleaderboard",
            "gvcleaderboard",
            "ggleaderboard",
            "ggvcleaderboard",
        ],
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.cooldown(6, 60, commands.BucketType.guild)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True, add_reactions=True)
    async def leaderboard(self, ctx):
        """ Refined leaderboard command """

        async def wait_for_reaction():
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=lambda r, u: u == ctx.author
                )
            except asyncio.TimeoutError:
                return [None, None]
            else:
                return [reaction, str(reaction.emoji)]

        def index_check(index):
            """ Ensures the index isn't too high or too low """
            if index > len(embeds) - 1:
                index = len(embeds) - 1
            if index < 0:
                index = 0
            return index

        async def add_emojis_task():
            """ So the bot can read reactions before all are added """
            with suppress(Forbidden, NotFound):
                for emoji in emojis:
                    await msg.add_reaction(emoji)
                    await asyncio.sleep(0.5)
            return

        async def create_embed(name: str, rankings: list, lmt, top_user=None):
            """ Gen a list of embed leaderboards """
            # icon_url = None
            thumbnail_url = "https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png"
            # if top_user:
            # 	user = self.bot.get_user(int(top_user))
            # 	if isinstance(user, discord.User):
            # 		icon_url = user.avatar.url
            # 	else:
            # 		guild = self.bot.get_guild(int(top_user))
            # 		if isinstance(guild, discord.Guild):
            # 			icon_url = guild.icon.url
            embeds = []
            e = discord.Embed(color=0x4A0E50)
            # if icon_url:
            # 	e.set_author(name=name, icon_url=icon_url)
            # else:
            # 	e.set_author(name=name, icon_url=self.bot.user.avatar.url)
            e.set_author(name=name, icon_url=ctx.author.avatar.url)
            e.set_thumbnail(url=thumbnail_url)
            e.description = ""
            rank = 1
            index = 0
            for user_id, xp in rankings:
                await asyncio.sleep(0)
                if index == lmt:
                    embeds.append(e)
                    e = discord.Embed(color=0x4A0E50)
                    e.set_author(name=name, icon_url=ctx.author.avatar.url)
                    e.set_thumbnail(url=thumbnail_url)
                    e.description = ""
                    index = 0
                user = self.bot.get_user(int(user_id))
                if isinstance(user, discord.User):
                    username = str(user.name)
                else:
                    guild = self.bot.get_guild(int(user_id))
                    if isinstance(guild, discord.Guild):
                        username = guild.name
                    else:
                        username = "INVALID-USER"
                e.description += f"#{rank}. `{username}` - {xp}\n"
                rank += 1
                index += 1
            embeds.append(e)

            return embeds

        async with self.bot.utils.open("./data/userdata/config.json", "r") as f:
            config = json.loads(await f.read())  # type: dict
        prefix = "."  # default prefix
        guild_id = str(ctx.guild.id)
        if guild_id in config["prefix"]:
            prefix = config["prefix"][guild_id]
        target = ctx.message.content.split()[0]
        cut_length = len(target) - len(prefix)
        aliases = [
            ("lb", "leaderboard"),
            # ('vclb', 'vcleaderboard'),
            ("glb", "gleaderboard"),
            # ('gvclb', 'gvcleaderboard'),
            ("mlb", "mleaderboard"),
            ("gmlb", "gmleaderboard"),
            # ('gglb', 'ggleaderboard'),
            # ('ggvclb', 'ggvcleaderboard')
        ]
        index = 0  # default
        for i, (cmd, alias) in enumerate(aliases):
            if target[-cut_length:] in [cmd, alias]:
                index = i
                break

        default = discord.Embed()
        default.description = "Collecting Leaderboard Data.."
        msg = await ctx.send(embed=default)
        emojis = ["🏡", "⏮", "⏪", "⏩", "⏭"]
        self.bot.loop.create_task(add_emojis_task())

        embeds = []
        leaderboards = {}

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select user_id, xp from msg where guild_id = {guild_id} order by xp desc limit 256;"
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
                f"where guild_id = {guild_id} and msg_time > {lmt} "
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
            ems = await create_embed(
                name=name,
                rankings=sorted_data,
                lmt=15,
                top_user=sorted_data[0][0],  # user_id
            )
            embeds.append(ems)

        sub_index = 0
        embeds[index][0].set_footer(
            text=f"Leaderboard {index + 1}/{len(embeds)} Page {sub_index + 1}/{len(embeds[index])}"
        )
        await msg.edit(embed=embeds[index][0])

        while True:
            await asyncio.sleep(0.5)
            reaction, emoji = await wait_for_reaction()
            if not reaction:
                return await msg.clear_reactions()

            if emoji == emojis[0]:  # home
                index = 0
                sub_index = 0

            if emoji == emojis[1]:
                index -= 1
                sub_index = 0

            if emoji == emojis[2]:
                if isinstance(embeds[index], list):
                    if not isinstance(sub_index, int):
                        sub_index = len(embeds[index]) - 1
                    else:
                        if sub_index == 0:
                            index -= 1
                            sub_index = 0
                            index = index_check(index)
                            if isinstance(embeds[index], list):
                                sub_index = len(embeds[index]) - 1
                        else:
                            sub_index -= 1
                else:
                    index -= 1
                    if isinstance(embeds[index], list):
                        sub_index = len(embeds[index]) - 1

            if emoji == emojis[3]:
                if isinstance(embeds[index], list):
                    if not isinstance(sub_index, int):
                        sub_index = 0
                    else:
                        if sub_index == len(embeds[index]) - 1:
                            index += 1
                            sub_index = 0
                            index = index_check(index)
                            if isinstance(embeds[index], list):
                                sub_index = 0
                        else:
                            sub_index += 1
                else:
                    index += 1
                    index = index_check(index)
                    if isinstance(embeds[index], list):
                        sub_index = 0

            if emoji == emojis[4]:
                index += 1
                sub_index = 0
                index = index_check(index)

            if index > len(embeds) - 1:
                index = len(embeds) - 1
            if index < 0:
                index = 0

            embeds[index][sub_index].set_footer(
                text=f"Leaderboard {index + 1}/{len(embeds)} Page {sub_index+1}/{len(embeds[index])}"
            )
            await msg.edit(embed=embeds[index][sub_index])
            self.bot.loop.create_task(msg.remove_reaction(reaction, ctx.author))

    @commands.command(name="clb")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clb(self, ctx):
        # Remove old uses from the db
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Command Leaderboard", icon_url=self.bot.user.avatar.url)
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

    @_min_xp_per_msg.before_invoke
    @_max_xp_per_msg.before_invoke
    @_first_level_xp_req.before_invoke
    @_timeframe.before_invoke
    @_msgs_within_timeframe.before_invoke
    @xp_config.before_invoke
    @profile.before_invoke
    async def initiate_config(self, ctx):
        """ Make sure the guild has a config """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            await self.init(guild_id)


def setup(bot):
    bot.add_cog(Ranking(bot), override=True)
