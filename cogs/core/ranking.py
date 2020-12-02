# Customizable xp ranking system

from os import path
import json
from time import time
from random import *
import asyncio
import requests
from io import BytesIO
from datetime import datetime
import aiohttp
from pymysql.err import DataError, InternalError
from contextlib import suppress

from discord.ext import commands, tasks
import discord
from discord.errors import NotFound, Forbidden
from PIL import Image, ImageFont, ImageDraw, ImageSequence, UnidentifiedImageError

from utils import colors
from cogs.core.utils import Utils as utils


def profile_help():
    e = discord.Embed(color=colors.purple())
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

        # xp config
        self.config = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)

        # save storage
        for guild_id, config in list(self.config.items()):
            if config == self.static_config():
                del self.config[guild_id]

        # profile config
        self.profile = {}
        if path.isfile(self.profile_path):
            with open(self.profile_path, "r") as f:
                self.profile = json.load(f)

        # top command lb
        self.cmds = {}
        if path.isfile(self.clb_path):
            with open(self.clb_path, "r") as f:
                self.cmds = json.load(f)

        # vc caching
        self.vclb = {}
        self.vc_counter = 0

        self.xp_cleanup_task.start()

    def cog_unload(self):
        self.xp_cleanup_task.cancel()

    async def save_config(self):
        """ Saves per-server configuration """
        async with self.bot.open(self.path, "w+") as f:
            await f.write(json.dumps(self.config))

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
    async def xp_cleanup_task(self):
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

            # anti macro
            if user_id not in self.macro_cd:
                self.macro_cd[user_id] = {}
                self.macro_cd[user_id]["intervals"] = []
            if "last" not in self.macro_cd[user_id]:
                self.macro_cd[user_id]["last"] = datetime.now()
            else:
                last = self.macro_cd[user_id]["last"]
                self.macro_cd[user_id]["intervals"].append(
                    (datetime.now() - last).seconds
                )
                intervals = self.macro_cd[user_id]["intervals"]
                self.macro_cd[user_id]["intervals"] = intervals[-3:]
                if len(intervals) > 2:
                    if all(interval == intervals[0] for interval in intervals):
                        return await punish()

            set_time = datetime.timestamp(
                datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)
            )
            if user_id not in self.global_cd:
                self.global_cd[user_id] = 0
            if self.global_cd[user_id] < time():
                self.global_cd[user_id] = time() + 10
                try:
                    async with self.bot.cursor() as cur:
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
                    async with self.bot.cursor() as cur:

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

                        await cur.execute(
                            f"select xp from msg "
                            f"where guild_id = {guild_id} "
                            f"and user_id = {user_id} "
                            f"limit 1;"
                        )
                        result = await cur.fetchone()
                    dat = await self.calc_lvl_info(result[0], conf)
                    async with self.bot.cursor() as cur:
                        await cur.execute(
                            f"select role_id from role_rewards "
                            f"where guild_id = {guild_id} "
                            f"and lvl <= {dat['level']};"
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
                            except (NotFound, Forbidden):
                                await self.bot.execute(
                                    f"delete from role_rewards "
                                    f"where role_id = {result[0]} limit 1;"
                                )

                except DataError as error:
                    self.bot.log(f"Error updating guild xp\n{error}")
                except InternalError:
                    pass

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        user_id = ctx.author.id
        cmd = ctx.command.name
        if user_id not in self.cmd_cd:
            self.cmd_cd[user_id] = []
        if cmd not in self.cmd_cd[user_id]:
            self.cmd_cd[user_id].append(cmd)
            if cmd not in self.cmds:
                self.cmds[cmd] = []
            self.cmds[cmd].append(time())
            await self.bot.save_json(self.clb_path, self.cmds)
            await asyncio.sleep(5)
            self.cmd_cd[user_id].remove(cmd)

    @commands.command(name="level-roles", aliases=["level-rewards", "role-rewards", "lr"])
    @commands.cooldown(*utils.default_cooldown())
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def level_roles(self, ctx, *args):
        if not args or len(args) == 1:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Level Roles", icon_url=self.bot.user.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = "Grant roles as a reward to users whence they reach a specified level"
            p = utils.get_prefix(ctx)  # type: str
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
            async with self.bot.cursor() as cur:
                await cur.execute(f"select role_id, lvl from role_rewards where guild_id = {ctx.guild.id};")
                results = await cur.fetchall()
            if results:
                value = ""
                for role_id, level in sorted(list(results), key=lambda kv: kv[1], reverse=True):
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
        level = int(args[1])
        stack = False
        await ctx.send(
            "Should I remove this role when the user gets a higher role reward? "
            "Reply with `yes` or `no`"
        )
        async with self.bot.require("message", ctx) as msg:
            if "yes" in msg.content.lower():
                stack = True

        await self.bot.execute(
            f"insert into level_roles "
            f"values ({ctx.guild.id}, {role.id}, {level}, {stack}) "
            f"on duplicate key update lvl = {level} and stack = {stack};"
        )
        await ctx.send(f"Setup complete")


    @commands.command(name="xp-config")
    @commands.cooldown(*utils.default_cooldown())
    @commands.bot_has_permissions(embed_links=True)
    async def xp_config(self, ctx):
        """ Sends an overview for the current config """
        e = discord.Embed(color=0x4A0E50)
        e.set_author(name="XP Configuration", icon_url=ctx.guild.owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        conf = self.config[str(ctx.guild.id)]
        e.description = (
            f"• Min XP Per Msg: {conf['min_xp_per_msg']}"
            f"\n• Max XP Per Msg: {conf['max_xp_per_msg']}"
            f"\n• Timeframe: {conf['timeframe']}"
            f"\n• Msgs Within Timeframe: {conf['msgs_within_timeframe']}"
            f"\n• First Lvl XP Req: {conf['first_lvl_xp_req']}"
        )
        p = utils.get_prefix(ctx)
        e.set_footer(text=f"Use {p}set to adjust these settings")
        await ctx.send(embed=e)

    @commands.group(name="set")
    @commands.cooldown(*utils.default_cooldown())
    @commands.guild_only()
    async def set(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Set Usage", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=self.bot.user.avatar_url)
            p = utils.get_prefix(ctx)  # type: str
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
            return await ctx.send("There's a character limit is 22!")
        user_id = str(ctx.author.id)
        if user_id not in self.profile:
            self.profile[user_id] = {}
        self.profile[user_id]["title"] = title
        await ctx.send("Set your title")
        await self.bot.save_json(self.profile_path, self.profile)

    @set.command(name="background")
    async def _set_background(self, ctx, url=None):
        user_id = str(ctx.author.id)
        if user_id not in self.profile:
            self.profile[user_id] = {}
        if not url and not ctx.message.attachments:
            if "background" not in self.profile[user_id]:
                return await ctx.send("You don't have a custom background")
            del self.profile[user_id]["background"]
            with open(self.profile_path, "w+") as f:
                json.dump(self.profile, f)
            return await ctx.send("Reset your background")
        if not url:
            url = ctx.message.attachments[0].url
        self.profile[user_id]["background"] = url
        await ctx.send("Set your background image")
        await self.bot.save_json(self.profile_path, self.profile)

    @set.command(name="min-xp-per-msg")
    @commands.has_permissions(administrator=True)
    async def _min_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        guild_id = str(ctx.guild.id)
        self.config[guild_id]["min_xp_per_msg"] = amount
        await ctx.send(f"Set the minimum xp gained per msg to {amount}")
        if amount > self.config[guild_id]["max_xp_per_msg"]:
            self.config[guild_id]["max_xp_per_msg"] = amount
            await ctx.send(f"I also upped the maximum xp per msg to {amount}")
        await self.save_config()

    @set.command(name="max-xp-per-msg")
    @commands.has_permissions(administrator=True)
    async def _max_xp_per_msg(self, ctx, amount: int):
        """ sets the minimum gained xp per msg """
        if amount > 100:
            return await ctx.send("biTcH nO, those heels are too high")
        guild_id = str(ctx.guild.id)
        self.config[guild_id]["max_xp_per_msg"] = amount
        await ctx.send(f"Set the maximum xp gained per msg to {amount}")
        if amount < self.config[guild_id]["max_xp_per_msg"]:
            self.config[guild_id]["max_xp_per_msg"] = amount
            await ctx.send(f"I also lowered the minimum xp per msg to {amount}")
        await self.save_config()

    @set.command(name="timeframe")
    @commands.has_permissions(administrator=True)
    async def _timeframe(self, ctx, amount: int):
        """ sets the timeframe to allow x messages """
        guild_id = str(ctx.guild.id)
        self.config[guild_id]["timeframe"] = amount
        await ctx.send(f"Set the timeframe that allows x messages to {amount}")
        await self.save_config()

    @set.command(name="msgs-within-timeframe")
    @commands.has_permissions(administrator=True)
    async def _msgs_within_timeframe(self, ctx, amount: int):
        """ sets the limit of msgs within the timeframe """
        guild_id = str(ctx.guild.id)
        self.config[guild_id]["msgs_within_timeframe"] = amount
        await ctx.send(f"Set msgs within timeframe limit to {amount}")
        await self.save_config()

    @set.command(name="first-lvl-xp-req")
    @commands.has_permissions(administrator=True)
    async def _first_level_xp_req(self, ctx, amount: int):
        """ sets the required xp to level up your first time """
        guild_id = str(ctx.guild.id)
        self.config[guild_id]["first_lvl_xp_req"] = amount
        await ctx.send(f"Set the required xp to level up your first time to {amount}")
        await self.save_config()

    @commands.command(name="profile", aliases=["rank"], usage=profile_help())
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    async def profile(self, ctx):
        """ Profile / Rank Image Card """

        def add_corners(im, rad):
            """ Adds transparent corners to an img """
            circle = Image.new("L", (rad * 2, rad * 2), 0)
            d = ImageDraw.Draw(circle)
            d.ellipse((0, 0, rad * 2, rad * 2), fill=255)
            alpha = Image.new("L", im.size, 255)
            w, h = im.size
            alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
            alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
            alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
            alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
            im.putalpha(alpha)
            return im

        def font(size):
            return ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", size)

        # core
        _path = "./static/card.png"
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        user_id = str(user.id)
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
            background_url = ctx.guild.splash_url
        if ctx.guild.banner:
            background_url = ctx.guild.banner_url
        if user_id in self.profile:
            if "title" in self.profile[user_id]:
                title = self.profile[user_id]["title"]
            if "background" in self.profile[user_id]:
                background_url = self.profile[user_id]["background"]

        # xp variables
        guild_rank = "unranked"  # this is required, remember to get this here
        async with self.bot.cursor() as cur:
            if (
                "global" in ctx.message.content
                or "profile" in ctx.message.content.lower()
            ):
                await cur.execute(
                    f"select xp from global_msg where user_id = {user_id} limit 1;"
                )
                results = await cur.fetchone()  # type: tuple
                if not results:
                    return await ctx.send(
                        "You currently have no global xp, try rerunning this command now"
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
                        "You currently have no xp in this server, try rerunning this command now"
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
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.avatar_url)) as resp:
                    avatar = Image.open(BytesIO(await resp.read())).convert("RGBA")
        except UnidentifiedImageError:
            return await ctx.send(
                "Sorry, but I seem to be having issues using your avatar"
            )
        if background_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(background_url)) as resp:
                        background = Image.open(BytesIO(await resp.read()))
            except (aiohttp.InvalidURL, UnidentifiedImageError):
                return await ctx.send(
                    "Sorry, but I seem to be having issues using your current background"
                    "\nYou can use `.set background` to reset it, or attach a file while "
                    "using that command to change it"
                )

        def create_card(avatar, status, path, background):
            card = Image.open(BytesIO(requests.get(url).content))
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
            avatar = add_corners(avatar.resize((175, 175), Image.BICUBIC), 87)
            card.paste(avatar, (75, 85), avatar)
            draw.ellipse((75, 85, 251, 261), outline="black", width=6)
            status = Image.open(BytesIO(requests.get(status).content)).convert("RGBA")
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
            if background_url:
                if "gif" in str(background_url):
                    dur = background.info["duration"]
                    count = len(list(ImageSequence.Iterator(background)))
                    skip = False
                    skip_two = False
                    skipped = 0
                    frames = []
                    index = 0
                    for frame in ImageSequence.Iterator(background):
                        if 40 < count < 100:
                            if skip:
                                skip = False
                                continue
                            elif skip_two:
                                skip_two = False
                                continue
                            else:
                                skip = True
                                skip_two = True
                        elif count > 100:
                            skip = int(str(count)[:1]) + 2
                            if skipped <= skip:
                                skipped += 1
                                continue
                            else:
                                skipped = 0

                        frame = frame.convert("RGBA")
                        frame = frame.resize((1000, 500), Image.BICUBIC)
                        frame.paste(card, (0, 0), card)
                        b = BytesIO()
                        frame.save(b, format="GIF")
                        frame = Image.open(b)
                        frames.append(frame)
                        index += 1
                        if index == 50:
                            break
                    path = path.replace("png", "gif")
                    frames[0].save(
                        path,
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                        duration=dur*2,
                        optimize=False,
                    )
                else:
                    background = background.convert("RGBA")
                    background = background.resize((1000, 500), Image.BICUBIC)
                    background.paste(card, (0, 0), card)
                    background.save(path, format="PNG")
            else:
                card.save(path, format="PNG")
            return path

        _path = await self.bot.loop.run_in_executor(
            None, create_card, avatar, status, _path, background
        )
        ty = "Profile" if "profile" in ctx.message.content.lower() else "Rank"
        await ctx.send(f"> **{ty} card for {user}**", file=discord.File(_path))

    @commands.command(name="sub-from-lb")
    @commands.is_owner()
    async def sub_from_lb(self, ctx, user_id: int, new_xp: int):
        await ctx.send(f"user_id {user_id}")
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"select xp from global_msg where user_id = {user_id};"
                )
                xp = await cur.fetchone()
                await ctx.send(xp)
                await cur.execute(
                    f"update global_msg set xp = {xp[0] - new_xp} where user_id = {user_id};"
                )
                await conn.commit()
                await ctx.send("Done")
                # await cur.execute(f"select * from global_monthly where msg_time > {time() - 60 * 60 * 24 * 30} order by xp desc;")
                # results = await cur.fetchall()
                # Dict = {}
                # for user_id, msg_time, xp in results:
                # 	if user_id not in Dict:
                # 		Dict[user_id] = []
                # 	Dict[user_id].append(msg_time)
                # for user_id, msg_times in Dict.items():
                # 	for msg_time in sorted(msg_times):

    @commands.command(name="reset-monthly")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def reset_monthly_xp(self, ctx):
        await ctx.send("Removing xp")
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                lmt = time()
                await cur.execute(f"delete from monthly_msg where msg_time < {lmt};")
                await ctx.send("Removed monthly guilded xp")
                await cur.execute(f"delete from global_monthly where msg_time < {lmt};")
                await ctx.send("Removed monthly global xp")
                await conn.commit()
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"select * from monthly_msg;")
                results = await cur.fetchall()
                await ctx.send(f"{len(results)} still exist")

    @commands.command(name="yeet-pls")
    @commands.is_owner()
    async def yeet_pls(self, ctx):
        await ctx.send("beginning the yeeting")
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"delete from global_msg where xp > 175000")
                await conn.commit()
        await ctx.send("Done")

    @commands.command(name="yeet-duplicates")
    @commands.is_owner()
    async def yeet_exploiters(self, ctx):
        total = 0
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"select guild_id, user_id, xp from msg;")
                results = await cur.fetchall()
                index = {}
                for guild_id, user_id, xp in results:
                    if guild_id not in index:
                        index[guild_id] = {}
                    if user_id in index[guild_id]:
                        if xp < index[guild_id][user_id]:
                            await cur.execute(
                                f"delete from msg "
                                f"where guild_id = {guild_id} "
                                f"and user_id = {user_id} "
                                f"and xp = {xp};"
                            )
                            total += 1
                        else:
                            index[guild_id][user_id] = xp
                    else:
                        index[guild_id][user_id] = xp
                await conn.commit()
        await ctx.send(f"Removed {total} duplicates")

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
    @commands.cooldown(*utils.default_cooldown())
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.cooldown(6, 60, commands.BucketType.guild)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
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
            # 		icon_url = user.avatar_url
            # 	else:
            # 		guild = self.bot.get_guild(int(top_user))
            # 		if isinstance(guild, discord.Guild):
            # 			icon_url = guild.icon_url
            embeds = []
            e = discord.Embed(color=0x4A0E50)
            # if icon_url:
            # 	e.set_author(name=name, icon_url=icon_url)
            # else:
            # 	e.set_author(name=name, icon_url=self.bot.user.avatar_url)
            e.set_author(name=name, icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=thumbnail_url)
            e.description = ""
            rank = 1
            index = 0
            for user_id, xp in rankings:
                await asyncio.sleep(0)
                if index == lmt:
                    embeds.append(e)
                    e = discord.Embed(color=0x4A0E50)
                    e.set_author(name=name, icon_url=ctx.author.avatar_url)
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

        async with self.bot.open("./data/userdata/config.json", "r") as f:
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

        async with self.bot.cursor() as cur:
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
        for cmd, uses in list(self.cmds.items()):
            for use in uses:
                if use < time() - 60 * 60 * 24 * 30:
                    self.cmds[cmd].remove(use)
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Command Leaderboard", icon_url=self.bot.user.avatar_url)
        e.description = ""
        rank = 1
        for cmd, uses in sorted(
            self.cmds.items(), key=lambda kv: len(kv[1]), reverse=True
        )[:10]:
            e.description += f"**#{rank}.** `{cmd}` - {len(uses)}\n"
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
    bot.add_cog(Ranking(bot))
