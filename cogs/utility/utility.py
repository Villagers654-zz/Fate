"""
cogs.utility.utility
~~~~~~~~~~~~~~~~~~~~~

A cog for general utility commands

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from datetime import datetime, timezone, timedelta
import asyncio
import random
from io import BytesIO
import json
import os
import requests
import re
from typing import *
from time import time
import platform
from contextlib import suppress

import discord
from discord import User, Role, TextChannel, Member, ui, ButtonStyle, SelectOption, Message, Embed, Interaction, Guild
from discord.ext.commands import Context
from discord import NotFound, HTTPException
from PIL import Image
from colormap import rgb2hex
import psutil
from discord.ext import commands, tasks

from botutils import colors, bytes2human, get_time, emojis, extract_time, \
get_prefixes_async, format_date, sanitize, GetChoice, AuthorView, Cooldown


default = {
    "public": False,
    "xp": True
}


class ProfileType(ui.View):
    def __init__(self, cls, ctx, msg, **kwargs):
        self.cls = cls
        self.ctx = ctx
        self.user = ctx.author
        self.msg = msg
        super().__init__(**kwargs)

        label, style = self.get_style()
        self.button = discord.ui.Button(label=label, style=style)
        self.button.callback = self.process
        self.add_item(self.button)

    def get_style(self):
        label = "Make Profile Public"
        style = ButtonStyle.green
        if self.user.id in self.cls.settings:
            if self.cls.settings[self.user.id]["public"]:
                label = "Make Profile Private"
                style = ButtonStyle.red
        return label, style

    async def process(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "Only the user who initiated this command can use it", ephemeral=True
            )

        # Update the settings in the DB
        label, style = self.get_style()
        new = label.split()[2].lower()
        if new == "private":
            self.cls.settings[self.user.id]["public"] = False
            if self.cls.settings[self.user.id] == default:
                await self.cls.settings.remove(self.user.id)
        else:
            if self.user.id not in self.cls.settings:
                self.cls.settings[self.user.id] = default
            self.cls.settings[self.user.id]["public"] = True

        # Switch to the new style
        label, style = self.get_style()
        self.button.label = label
        self.button.style = style
        new_embed = await self.cls.fetch_user_info(self.ctx, self.user)
        await interaction.message.edit(embed=new_embed, view=self)


class SatisfiableChannel(commands.Converter):
    async def convert(self, ctx, argument):
        converter = commands.TextChannelConverter()
        channel = await converter.convert(ctx, argument)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send(f'"{argument}" is not a valid channel')
            return False
        perms = [
            "read_messages",
            "read_message_history",
            "send_messages",
            "manage_webhooks",
        ]
        for perm in perms:
            if not eval(f"channel.permissions_for(ctx.guild.me).{perm}"):
                await ctx.send(f"I'm missing {perm} permissions in that channel")
                return False
        return channel


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.utils.cache("settings", auto_sync=True)
        self.find = {}
        self.afk = {}
        self.timer_path = "./data/userdata/timers.json"
        self.timers = {}
        if os.path.isfile(self.timer_path):
            with open(self.timer_path, "r") as f:
                self.timers = json.load(f)
        if "timers" not in bot.tasks:
            bot.tasks["timers"] = {}
        self.database_cleanup_task.start()

    def cog_unload(self):
        self.database_cleanup_task.cancel()

    @tasks.loop(hours=6)
    async def database_cleanup_task(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        for _iteration in range(6):
            if self.bot.pool:
                break
            await asyncio.sleep(10)
        else:
            self.bot.log.critical("Can't connect to the DB to cleanup invites")
            return
        lmt = time() + 60 * 60 * 24 * 30
        set_to_remove = 0
        async with self.bot.utils.cursor() as cur:
            # Invites
            await cur.execute(f"select * from invites where created_at > {lmt};")
            set_to_remove += cur.rowcount
            await cur.execute(f"select * from invites where deleted_at > {lmt};")
            set_to_remove += cur.rowcount
            if set_to_remove:
                self.bot.log.info(f"Removing {set_to_remove} old invites")
            await cur.execute(f"delete from invites where created_at > {lmt};")
            await cur.execute(f"delete from invites where deleted_at > {lmt};")

            # Usernames
            lmt = 60 * 60 * 24 * 30
            await cur.execute(
                f"delete from usernames where changed_at > {lmt};"
            )

            # Activity
            lmt = 60 * 60 * 24 * 365
            await cur.execute(
                f"delete from activity "
                f"where last_online > {lmt} "
                f"and last_message > {lmt};"
            )

    async def save_timers(self):
        await self.bot.utils.save_json(self.timer_path, self.timers)

    @staticmethod
    def avg_color(url):
        """Gets an image and returns the average color"""
        if not url:
            return colors.fate
        im = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
        pixels = list(im.getdata())
        r = g = b = c = 0
        for pixel in pixels:
            brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
            if pixel[3] > 64 and brightness > 80:
                r += pixel[0]
                g += pixel[1]
                b += pixel[2]
                c += 1
        r = r / c
        g = g / c
        b = b / c
        return eval("0x" + rgb2hex(round(r), round(g), round(b)).replace("#", ""))

    @staticmethod
    async def wait_for_dismissal(ctx, msg):
        def pred(m):
            return m.channel.id == ctx.channel.id and m.content.lower().startswith("k")

        try:
            reply = await ctx.bot.wait_for("message", check=pred, timeout=25)
        except asyncio.TimeoutError:
            pass
        else:
            await asyncio.sleep(0.21)
            await ctx.message.delete()
            await asyncio.sleep(0.21)
            await msg.delete()
            await asyncio.sleep(0.21)
            await reply.delete()

    @commands.command(name="delete-data", enabled=False)
    async def delete_data(self, ctx):
        # user_id = str(ctx.author.id)
        # if user_id not in self.user_logs:
        #     return await ctx.send("You have no user data saved")
        # del self.user_logs[user_id]
        await ctx.send("Removed your data from .info")

    @commands.command(name="info", description="Shows info on users, roles, channels, etc")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def info(self, ctx, *, target: Union[Member, User, Role, TextChannel, str] = None):
        view = await InfoView(ctx, target)
        await view.wait()
        await view.message.edit(view=None)

    def to_num(self, string):
        return int.from_bytes(string.encode('utf-8'), "little")

    def from_num(self, number):
        recovered = int(number).to_bytes((int(number).bit_length() + 7) // 8, 'little')
        return recovered.decode("utf-8")

    def collect_invite_info(self, inv):
        info = {
            "code": self.bot.encode(inv.id),
            "guild_id": None,
            "guild_name": None,
            "channel_id": None,
            "channel_name": None,
            "inviter": None,
            "uses": "0"
        }
        guild_types = (discord.Guild, discord.PartialInviteGuild)
        guild = inv.guild
        if not isinstance(inv.guild, guild_types) and hasattr(inv.guild, "id"):
            tmp = self.bot.get_guild(inv.guild.id)
            if isinstance(tmp, discord.Guild):
                guild = tmp

        if guild.id and guild.name:
            info["guild_id"] = guild.id
            info["guild_name"] = self.bot.encode(guild.name)

        if inv.inviter:
            info["inviter"] = inv.inviter.id

        if inv.channel:
            info["channel_id"] = inv.channel.id
            if hasattr(inv.channel, "name"):
                info["channel_name"] = self.bot.encode(inv.channel.name)

        if inv.uses:
            info["uses"] = inv.uses

        return info

    async def invite_to_sql(self, invite):
        info = self.collect_invite_info(invite)
        iv = {}
        for key, value in info.items():
            if value is None:
                iv[key] = "null"
            else:
                iv[key] = repr(value)

        insert_values = [
            iv["code"], iv["guild_id"], iv["guild_name"], iv["channel_id"], iv["channel_name"],
            iv["inviter"], iv["uses"], time(), "null"
        ]

        update_values = {
            "guild_id": info["guild_id"] if info["guild_id"] else "null",
            "guild_name": repr(info["guild_name"]) if info["guild_name"] else "guild_name",
            "channel_id": info["channel_id"] if info["channel_id"] else "channel_id",
            "channel_name": repr(info["channel_name"]) if info["channel_name"] else "channel_name",
            "inviter": info["inviter"] if info["inviter"] else "inviter",
            "uses": f"case when uses is null then 0 when {info['uses']} is not null and {info['uses']} > uses then {info['uses']} else uses end",
            "created_at": f"case when created_at is null then {time()} else created_at end"
        }

        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from invites where code = {iv['code']} limit 1;")
            if cur.rowcount:
                await cur.execute(
                    f"update invites "
                    f"set {', '.join(f'{k} = {v}' for k, v in update_values.items())} "
                    f"where code = {iv['code']} limit 1;"
                )
            else:
                await cur.execute(f"insert into invites values ({', '.join(str(v) for v in insert_values)})")

    @commands.Cog.listener()
    async def on_message(self, msg):
        # AFK Command
        if msg.author.bot:
            return
        for user_id in list(set(msg.raw_mentions)):
            if user_id in self.afk and msg.author.id != user_id:
                replies = ["shh", "shush", "shush child", "nO"]
                choice = random.choice(replies)
                await msg.channel.send(f"{choice} they're {self.afk[user_id]}")
                return

        # Keep track of their last message time
        if msg.author.id not in self.settings:
            return
        if not self.settings[msg.author.id]["public"]:
            return
        await asyncio.sleep(1)
        await self.bot.execute(
            f"insert into activity values ({msg.author.id}, null, '{datetime.now(tz=timezone.utc)}') "
            f"on duplicate key update "
            f"last_message = '{time()}';"
        )

        # Check for invites and log their current state
        if "discord.gg" in msg.content:
            invites = re.findall("discord.gg/.{4,8}", msg.content)
            invites = invites if invites else []
            for invite in invites:
                code = discord.utils.resolve_invite(invite)
                if any(c.lower() not in "abcdefghijklmnopqrstuvwxyz0123456789" for c in code):
                    return  # Not a real invite

                try:
                    invite = await self.bot.fetch_invite(code, with_counts=True)
                except NotFound:
                    return await self.bot.execute(
                        f"update invites "
                        f"set deleted_at = {time()} "
                        f"where code = '{self.to_num(code)}' "
                        f"and deleted_at = null;"
                    )
                except HTTPException:
                    return

                guild = self.bot.get_guild(invite.guild.id)
                if guild and guild.me.guild_permissions.administrator:
                    invites = await guild.invites()
                    for _invite in invites:
                        await asyncio.sleep(0)
                        if invite.id == _invite.id:
                            invite = _invite
                            break
                await self.invite_to_sql(invite)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before and after and str(before) != str(after):
            async with self.bot.utils.cursor() as cur:
                await cur.execute(
                    f"select * from usernames "
                    f"where user_id = {after.id} "
                    f"and username = {repr(self.bot.encode(str(before)))};"
                )
                if not cur.rowcount:
                    await cur.execute(
                        f"insert into usernames values ({after.id}, {repr(self.bot.encode(str(before)))}, '{time()}');"
                    )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status != after.status:
            status = discord.Status
            if before.status != status.offline and after.status == status.offline:
                await self.bot.execute(
                    f"insert into activity values ({before.id}, '{datetime.now(tz=timezone.utc)}', null) "
                    f"on duplicate key update "
                    f"last_online = '{time()}';"
                )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.invite_to_sql(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.bot.execute(
            f"update invites "
            f"set deleted_at = {time()} "
            f"where code = {self.to_num(invite.code)};"
        )

    @commands.command(name="userinfo", aliases=["uinfo"], description="Shows extra info on a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def user_info(self, ctx, *, user: Union[Member, User] = None):
        if not user:
            user = ctx.author
        view = await InfoView(ctx, user)
        await view.wait()
        await view.message.edit(view=None)

    @commands.command(name="serverinfo", aliases=["sinfo"], description="Shows extra info on the server")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def server_info(self, ctx):
        view = await InfoView(ctx, ctx.guild)
        await view.wait()
        await view.message.edit(view=None)

    @commands.command(name="servericon", aliases=["icon"], description="Shows the server icon")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def servericon(self, ctx):
        if not ctx.guild.icon or not str(ctx.guild.icon.url):
            return await ctx.send("This server has no icon")
        e = discord.Embed(color=0x80B0FF)
        e.set_image(url=ctx.guild.icon.url)
        e.description = "Server Icon"
        await ctx.send(embed=e)

    @commands.command(name="create-template", aliases=["backup"], description="Creates a server template")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.cooldown(1, 25, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_guild=True)
    async def create_template(self, ctx, *, name):
        description = f"Created by {ctx.author} : {ctx.author.id}"
        if templates := await ctx.guild.templates():
            await templates[0].edit(name=name, description=description)
            template = await templates[0].sync()
        else:
            template = await ctx.guild.create_template(name=name[:28], description=description)
        await ctx.send(template.url)

    @commands.command(name="members", aliases=["membercount"], description="Shows the member counts")
    @commands.cooldown(1, 15, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def members(self, ctx, *, role = None):
        if role:  # returns a list of members that have the role
            if ctx.message.role_mentions:
                role = ctx.message.role_mentions[0]
            else:
                role = await self.bot.utils.get_role(ctx, role)
                if not isinstance(role, discord.Role):
                    return
            if len(role.members) > 50:
                members = "\n".join([
                    f"{m.id}, {m}, {m.display_name}"
                    for m in role.members
                ])
                buffer = BytesIO()
                buffer.write(members.encode())
                buffer.seek(0)
                return await ctx.send(file=discord.File(buffer, filename="members.txt"))
            e = discord.Embed(color=role.color)
            e.set_author(name=role.name, icon_url=ctx.author.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = ""
            dat = [(m, m.top_role.position) for m in role.members]
            for member, position in sorted(dat, key=lambda kv: kv[1], reverse=True):
                new_line = f"• {member}\n"
                if len(e.description) + len(new_line) > 2000:
                    await ctx.send(embed=e)
                    e.description = ""
                e.description += new_line
            if not e.description:
                e.description = "This role has no members"
            e.set_footer(text=f"{len(role.members)} member(s)")
            return await ctx.send(embed=e)
        else:  # return the servers member count
            status_list = [
                discord.Status.online,
                discord.Status.idle,
                discord.Status.dnd,
            ]
            humans = len([m for m in ctx.guild.members if not m.bot])
            bots = len([m for m in ctx.guild.members if m.bot])
            online = len([m for m in ctx.guild.members if m.status in status_list])
            e = discord.Embed(color=colors.fate)
            e.set_author(name=f"Member Count", icon_url=ctx.guild.owner.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = (
                f"**Total:** [`{ctx.guild.member_count}`]\n"
                f"**Online:** [`{online}`]\n"
                f"**Humans:** [`{humans}`]\n"
                f"**Bots:** [`{bots}`]"
            )
            await ctx.send(embed=e)

    @commands.command(name="permissions", aliases=["perms", "perm"], description="Checks what has a specific permission")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def permissions(self, ctx, permission=None):
        perms = [perm[0] for perm in [perm for perm in discord.Permissions()]]
        if not permission:
            return await ctx.send(f'Perms: {", ".join(perms)}')
        permission = permission.lower()
        if permission not in perms:
            return await ctx.send("Unknown perm")
        e = discord.Embed(color=colors.fate)
        e.set_author(name=f"Things with {permission}", icon_url=ctx.author.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        members = ""
        for member in ctx.guild.members:
            if getattr(member.guild_permissions, permission):
                members += f"{member.mention}\n"
        if members:
            e.add_field(name="Members", value=members[:1000])
        roles = ""
        for role in ctx.guild.roles:
            if eval(f"role.permissions.{permission}"):
                roles += f"{role.mention}\n"
        if roles:
            e.add_field(name="Roles", value=roles[:1000])
        await ctx.send(embed=e)

    @commands.command(name="avatar", aliases=["av", "pfp"], description="Shows a users avatar")
    @commands.cooldown(2, 45, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def avatar(self, ctx, *, user: discord.User = None):
        if not user:
            user = ctx.author
        e = discord.Embed(color=0x80B0FF)
        e.set_image(url=str(user.display_avatar.url))
        await ctx.send(
            f"◈ {await sanitize(user.display_name)}'s avatar ◈", embed=e
        )

    @commands.command(name="banner", description="Shows a users profile banner")
    @commands.cooldown(2, 45, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def banner(self, ctx, *, user: discord.User = None):
        if not user:
            user = ctx.author
        user = await self.bot.fetch_user(user.id)
        if not user.banner:
            return await ctx.send("That user doesn't have a banner")
        e = discord.Embed(color=0x80B0FF)
        e.set_image(url=str(user.banner.url))
        await ctx.send(
            f"◈ {await sanitize(user.display_name)}'s banner ◈", embed=e
        )

    @commands.command(name="owner", description="Shows who owns the server")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def owner(self, ctx):
        e = discord.Embed(color=colors.fate)
        e.description = f"**Server Owner:** {ctx.guild.owner.mention}"
        await ctx.send(embed=e)

    @commands.command(name="topic", description="Sends the channel topic")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.guild_only()
    async def topic(self, ctx):
        if not ctx.channel.topic:
            return await ctx.send("This channel has no topic")
        await ctx.send(ctx.channel.topic)

    @commands.command(name="color", aliases=["setcolor", "changecolor"], description="Shows or generates a random color")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def color(self, ctx, *args):
        if len(args) == 0:
            color = colors.random()
            e = discord.Embed(color=color)
            e.set_author(name=f"#{color}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=e)
        if len(args) == 1:
            _hex = args[0].strip("#")
            try:
                color = int("0x" + _hex, 0)
            except ValueError:
                return await ctx.send("That's not a real hex")
            if color > 16777215:
                return await ctx.send("That hex value is too large")
            e = discord.Embed(color=color)
            e.description = f"#{_hex}"
            return await ctx.send(embed=e)
        if not ctx.author.guild_permissions.manage_roles:
            return await ctx.send("You need manage roles permissions to use this")
        if "<@" in args[0]:
            target = "".join(x for x in args[0] if x.isdigit())
            if not target:
                return await ctx.send("Wtf man.. wHo")
            role = ctx.guild.get_role(int(target))
        else:
            role = await self.bot.utils.get_role(ctx, args[0])
        if not role:
            return await ctx.send("Unknown role")
        try:
            color = int("0x" + args[1].strip("#").strip("0x"), 0)
            if color > 16777215:
                return await ctx.send("That hex value is too large")
            _hex = discord.Color(color)
        except:
            return await ctx.send("Invalid Hex")
        if role.position >= ctx.author.top_role.position:
            return await ctx.send("That roles above your paygrade, take a seat")
        previous_color = role.color
        await role.edit(color=_hex)
        await ctx.send(f"Changed {role.name}'s color from {previous_color} to {_hex}")

    async def remind(self, user_id, msg, dat):
        end_time = datetime.strptime(dat["timer"], "%Y-%m-%d %H:%M:%S.%f")
        await discord.utils.sleep_until(end_time)
        channel = self.bot.get_channel(dat["channel"])
        with suppress(Exception):
            await channel.send(
                f"{dat['mention']} remember dat thing: {discord.utils.escape_mentions(msg)}",
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
            )
        del self.timers[user_id][msg]
        with suppress(KeyError):
            if not self.timers[user_id]:
                del self.timers[user_id]
        await self.save_timers()
        with suppress(KeyError):
            del self.bot.tasks["timers"][f"timer-{dat['timer']}"]

    @commands.command(name="reminder", aliases=["timer", "remindme", "remind"], description="Creates a timer")
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def timer(self, ctx, timer, *, reminder):
        p = await get_prefixes_async(self.bot, ctx.message)
        p = p[2]
        usage = (
            f">>> Usage: `{p}reminder [30s|5m|1h|2d]`"
            f"Example: `{p}reminder 1h take out da trash`"
        )
        timer = extract_time(timer)
        if not timer:
            return await ctx.send(usage)
        if timer < 25:
            return await ctx.send("That timer's too smol")
        if timer > 60 * 60 * 24 * 365:
            return await ctx.send("You can't set a timer that long")
        user_id = str(ctx.author.id)
        if user_id not in self.timers:
            self.timers[user_id] = {}
        if "http" in reminder:
            return await ctx.send("You can't include links in timers")
        if ctx.message.raw_mentions:
            return await ctx.send("You can't include additional pings in timers")
        if len(reminder) <= 1:
            return await ctx.send("Too smol")
        reminder = reminder[:200]
        if reminder in self.timers[user_id]:
            return await ctx.send("You already have a timer for that")
        expanded = format_date(seconds=timer)
        try:
            self.timers[user_id][reminder] = {
                "timer": str(datetime.now() + timedelta(seconds=timer)),
                "channel": ctx.channel.id,
                "mention": ctx.author.mention,
                "expanded_timer": expanded,
            }
        except OverflowError:
            return await ctx.send("That's a bit.. *too far*  into the future")
        await ctx.send(
            f"I'll remind you about {reminder} in {expanded}"
        )
        with suppress(KeyError):
            task = self.bot.loop.create_task(
                self.remind(user_id, reminder, self.timers[user_id][reminder])
            )
            self.bot.tasks["timers"][f"timer-{self.timers[user_id][reminder]['timer']}"] = task
        await self.save_timers()

    @commands.command(name="timers", aliases=["reminders"], description="Shows your timers")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def timers(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.timers:
            return await ctx.send("You currently have no timers")
        if not self.timers[user_id]:
            return await ctx.send("You currently have no timers")
        e = discord.Embed(color=colors.fate)
        for msg, dat in list(self.timers[user_id].items()):
            fmt = "%Y-%m-%d %H:%M:%S.%f"
            end_time = datetime.strptime(dat["timer"], fmt)
            if datetime.now() > end_time:
                del self.timers[user_id][msg]
                await self.save_timers()
                continue
            expanded_time = format_date(end_time)
            channel = self.bot.get_channel(dat["channel"])
            if not channel:
                del self.timers[user_id][msg]
                await self.save_timers()
                continue
            e.add_field(
                name=f"Ending in {expanded_time}",
                value=f"{channel.mention} - `{msg}`",
                inline=False,
            )
        if not e.fields:
            return await ctx.send("You currently have no timers")
        await ctx.send(embed=e)

    @commands.command(name="delete-timer", aliases=["remove-timer", "clear-timers"], description="Removes a timer")
    async def delete_timers(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.timers or not self.timers[user_id]:
            return await ctx.send("You have no timers")
        if len(self.timers[user_id]) == 1:
            for key, dat in list(self.timers[user_id].items()):
                with suppress(KeyError):
                    self.bot.tasks["timers"][f"timer-{dat['timer']}"].cancel()
                    del self.bot.tasks["timers"][f"timer-{dat['timer']}"]
                del self.timers[user_id]
            return await ctx.send("Removed your only timer")
        choice = await GetChoice(ctx, self.timers[user_id].keys())
        dat = self.timers[user_id][choice]
        with suppress(KeyError):
            self.bot.tasks["timers"][f"timer-{dat['timer']}"].cancel()
            del self.bot.tasks["timers"][f"timer-{dat['timer']}"]
        del self.timers[user_id][choice]
        await ctx.send(f"Deleted 👍")

    @commands.Cog.listener("on_ready")
    async def resume_timers(self):
        if "timers" not in self.bot.tasks:
            self.bot.tasks["timers"] = {}
        for user_id, timers in self.timers.items():
            for timer, dat in timers.items():
                if f"timer-{dat['timer']}" in self.bot.tasks["timers"]:
                    continue
                task = self.bot.loop.create_task(self.remind(user_id, timer, dat))
                self.bot.tasks["timers"][f"timer-{dat['timer']}"] = task

    @commands.command(name="findmsg", description="Finds a message in the channel history")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def _findmsg(self, ctx, *, content=None):
        if content is None:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Error ⚠", icon_url=ctx.author.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = (
                "Content is a required argument\n"
                "Usage: `.find {content}`\n"
                "Limit: 16,000"
            )
            e.set_footer(text="Searches for a message")
            return await ctx.send(embed=e)
        async with ctx.typing():
            channel_id = str(ctx.channel.id)
            if channel_id in self.find:
                return await ctx.send("I'm already searching")
            self.find[channel_id] = True
            async for msg in ctx.channel.history(limit=1000):
                if ctx.message.id != msg.id:
                    if content.lower() in msg.content.lower():
                        e = discord.Embed(color=colors.fate)
                        e.set_author(
                            name="Message Found 🔍", icon_url=ctx.author.display_avatar.url
                        )
                        if ctx.guild.icon:
                            e.set_thumbnail(url=ctx.guild.icon.url)
                        e.description = (
                            f"**Author:** `{msg.author}`\n"
                            f"[Jump to MSG]({msg.jump_url})"
                        )
                        if msg.content != "":
                            e.add_field(name="Full Content:", value=msg.content)
                        if len(msg.attachments) > 0:
                            for attachment in msg.attachments:
                                e.set_image(url=attachment.url)
                        await ctx.send(embed=e)
                        del self.find[channel_id]
                        return await ctx.message.delete()
        await ctx.send("Nothing found")
        del self.find[channel_id]

    @commands.command(name="last-entry", description="Shows the last audit log entry")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(view_audit_log=True)
    @commands.bot_has_permissions(view_audit_log=True)
    async def last_entry(self, ctx, user: Optional[discord.User], action=None):
        """ Gets the last entry for a specific action """
        last_entry = None
        if not user and not action:
            return await ctx.send("You need to specify a user, or an audit log action")
        elif user:
            async for entry in ctx.guild.audit_logs(limit=250):
                if (
                    entry.target and entry.target.id == user.id
                ) or entry.user.id == user.id:
                    last_entry = entry
                    break
        else:
            try:
                action = eval("discord.AuditLogAction." + action)
            except SyntaxError:
                return await ctx.send(f"`{action}` isn't an audit log action")
            async for entry in ctx.guild.audit_logs(limit=1, action=action):
                last_entry = entry
        if not last_entry:
            return await ctx.send(f"I couldn't find anything")
        e = discord.Embed(color=colors.fate)
        e.description = self.bot.utils.format_dict(
            {
                "Action": last_entry.action.name,
                "User": last_entry.user,
                "Target": last_entry.target,
                "Reason": last_entry.reason if last_entry.reason else "None Specified",
                "When": last_entry.created_at,
            }
        )
        await ctx.send(embed=e)

    @commands.command(name="id", description="Shows a users ID")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def id(self, ctx, *, user=None):
        if user:
            user = await self.bot.utils.get_user(ctx, user)
            if not user:
                return await ctx.send("User not found")
            return await ctx.send(user.id)
        for user in ctx.message.mentions:
            return await ctx.send(user.id)
        for channel in ctx.message.channel_mentions:
            return await ctx.send(channel.id)
        e = discord.Embed(color=colors.fate)
        e.description = (
            f"{ctx.author.mention}: {ctx.author.id}\n"
            f"{ctx.channel.mention}: {ctx.channel.id}"
        )
        await ctx.send(embed=e)

    @commands.command(name="estimate-inactives", description="Estimates how many would get kicked from pruning")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    async def estimate_inactives(self, ctx, days: int):
        if days > 30:
            return await ctx.send("That's too big of a number to check with")
        elif days < 1:
            return await ctx.send("The number of days must at least be 1")
        inactive_count = await ctx.guild.estimate_pruned_members(days=days)
        e = discord.Embed(color=colors.fate)
        e.description = f"Inactive Users: {inactive_count}"
        await ctx.send(embed=e)

    @commands.command(name="create-webhook", aliases=["createwebhook"], description="Creates and sends a webhook url")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_webhooks=True)
    @commands.bot_has_permissions(
        manage_webhooks=True, embed_links=True, manage_messages=True
    )
    async def create_webhook(self, ctx, *, name=None):
        if not name:
            return await ctx.send(
                'Usage: "`.create-webhook name`"\nYou can attach a file for its avatar'
            )
        avatar = None
        if ctx.message.attachments:
            avatar = await ctx.message.attachments[0].read()
        webhook = await ctx.channel.create_webhook(name=name, avatar=avatar)
        e = discord.Embed(color=colors.fate)
        e.set_author(name=f"Webhook: {webhook.name}", icon_url=webhook.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.description = webhook.url
        try:
            await ctx.author.send(embed=e)
            await ctx.send("Sent the webhook url to dm 👍")
        except:
            await ctx.send("Failed to dm you the webhook url", embed=e)

    @commands.command(name="webhooks", description="Lists the servers webhooks")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def webhooks(self, ctx, channel: discord.TextChannel = None):
        """ Return all the servers webhooks """
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Webhooks", icon_url=ctx.author.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        if channel:
            if not channel.permissions_for(ctx.guild.me).manage_webhooks:
                return await ctx.send(
                    "I need manage webhook(s) permissions in that channel"
                )
            webhooks = await channel.webhooks()
            e.description = "\n".join([f"• {webhook.name}" for webhook in webhooks])
            await ctx.send(embed=e)
        else:
            for channel in ctx.guild.text_channels:
                if channel.permissions_for(ctx.guild.me).manage_webhooks:
                    webhooks = await channel.webhooks()
                    if webhooks:
                        e.add_field(
                            name=f"◈ {channel}",
                            value="\n".join(
                                [f"• {webhook.name}" for webhook in webhooks]
                            ),
                            inline=False,
                        )
            await ctx.send(embed=e)

    @commands.command(name="move", aliases=["mv"], description="Moves messages to a different channel")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def move(self, ctx, amount: int, channel: discord.TextChannel):
        """ Moves a conversation to another channel """

        if ctx.channel.id == channel.id:
            return await ctx.send("Hey! that's illegal >:(")
        if amount > 250:
            return await ctx.send("That's too many :[")
        cooldown = 1
        if amount > 50:
            await ctx.send("That's a lot.. ima do this a lil slow then")
            cooldown *= cooldown

        webhook = await channel.create_webhook(name="Chat Transfer")
        msgs = await ctx.channel.history(limit=amount + 1).flatten()

        e = discord.Embed()
        e.set_author(name=f"Progress: 0/{amount}", icon_url=ctx.author.display_avatar.url)
        e.set_footer(text=f"Moving to #{channel.name}")
        transfer_msg = await ctx.send(embed=e)

        em = discord.Embed()
        em.set_author(name=f"Progress: 0/{amount}", icon_url=ctx.author.display_avatar.url)
        em.set_footer(text=f"Moving from #{channel.name}")
        channel_msg = await channel.send(embed=em)

        await ctx.message.delete()

        index = 1
        for iteration, msg in enumerate(msgs[::-1]):
            if ctx.message.id == msg.id:
                continue
            avatar = msg.author.display_avatar.url
            embed = None
            if msg.embeds:
                embed = msg.embeds[0]

            files = []
            file_paths = []
            for attachment in msg.attachments:
                fp = os.path.join("static", attachment.filename)
                await attachment.save(fp)
                files.append(discord.File(fp))
                file_paths.append(fp)

            if not msg.content and not files and not embed:
                continue
            await webhook.send(
                msg.content,
                username=msg.author.display_name,
                avatar_url=avatar,
                files=files,
                embed=embed,
            )
            for fp in file_paths:
                os.remove(fp)
            if index == 5:
                e.set_author(
                    name=f"Progress: {iteration+1}/{amount}",
                    icon_url=ctx.author.display_avatar.url,
                )
                em.set_author(
                    name=f"Progress: {iteration+1}/{amount}",
                    icon_url=ctx.author.display_avatar.url,
                )
                await transfer_msg.edit(embed=e)
                await channel_msg.edit(embed=em)
                index = 1
            else:
                index += 1
            await msg.delete()
            await asyncio.sleep(cooldown)

        await webhook.delete()
        result = f"Progress: {amount}/{amount}"
        e.set_author(name=result, icon_url=ctx.author.display_avatar.url)
        em.set_author(name=result, icon_url=ctx.author.display_avatar.url)
        await transfer_msg.edit(embed=e)
        await channel_msg.edit(embed=em)

    @commands.command(name="afk", description="Tells users you're afk when they ping you")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def afk(self, ctx, *, reason="afk"):
        if ctx.message.mentions or ctx.message.role_mentions:
            return await ctx.send("nO -_-\nMentions are forbidden in afk messages")
        if ctx.author.id in self.afk:
            return
        e = discord.Embed(color=colors.fate)
        if len(reason) > 64:
            return await ctx.send("Your afk message can't be greater than 64 characters")
        e.set_author(name="You are now afk", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=e, delete_after=5)
        reason = await sanitize(reason)
        self.afk[ctx.author.id] = reason
        await asyncio.sleep(5)
        await ctx.message.delete()

    @commands.Cog.listener("on_message")
    async def remove_afk(self, msg):
        if msg.author.id in self.afk:
            del self.afk[msg.author.id]
            if msg.channel.permissions_for(msg.guild.me).send_messages:
                await msg.channel.send("Removed your afk")

    @commands.command(name="embed", description="Embeds a message and/or image")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.has_permissions(embed_links=True, manage_messages=True)
    async def embed(self, ctx, *, embed_content = ""):
        if not embed_content and not ctx.message.attachments:
            return await ctx.send(
                "You have to include content to embed, or attach a file when running the command. "
                f"**Usage:** `{ctx.prefix}embed #ffffff your message`. Note the #hex is optional"
            )
        color = discord.Embed.Empty
        if embed_content.startswith("#"):
            color, *embed_content = embed_content.split()
            try:
                color = int(color.replace("#", "0x"), 0)
            except ValueError:
                return await ctx.send(f"{color} isn't a valid color/hex")
            if color > 16777215:
                return await ctx.send(f"{color} isn't a valid color/hex")
            embed_content = " ".join(embed_content)
        e = discord.Embed(color=color)
        if embed_content:
            e.description = embed_content
        if ctx.message.attachments:
            e.set_image(url=ctx.message.attachments[0].url)
        await ctx.send(embed=e)

    @commands.command(name="export-bans", description="Sends a txt of the ban list")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True, attach_files=True)
    async def export_bans(self, ctx):
        bans = await ctx.guild.bans()
        members = "\n".join([
            f"{u.id}, {u}, {ban.reason}"
            for ban in bans if (u := ban.user)
        ])
        buffer = BytesIO()
        buffer.write(members.encode())
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, filename="bans.txt"))


# Method index
pages: Dict[Type, str] = {
    None: "bot_info",
    str: "invite_info",
    User: "user_info",
    Member: "user_info",
    TextChannel: "channel_info",
    Role: "role_info",
    Guild: "server_info"
}


class InfoView(AuthorView):
    """ An awaitable for an interactive info menu """
    message: Message = None

    def __init__(self, ctx: Context, target: Union[None, str, User, Member, TextChannel, Role]) -> None:
        self.cd = Cooldown(1, 3)

        self.ctx = ctx
        self.bot = ctx.bot
        self.target = target
        if isinstance(target, str) and "discord.gg" not in target:
            self.target = target = None

        self.current_page = pages[type(target) if target else target]

        super().__init__(timeout=45)
        self.add_item(SelectMenu(parent=self))

    def __await__(self) -> Generator[None, None, "InfoView"]:
        """ Return the coro function for initializing the message """
        return self._await().__await__()

    async def _await(self) -> "InfoView":
        """ Initialize the info message """
        async for embed in getattr(self, self.current_page)():
            if self.message:
                await self.message.edit(embed=embed)
            else:
                self.message = await self.ctx.send(embed=embed, view=self)
        return self

    async def on_error(self, error: Exception, item: ui.Item, interaction: Interaction) -> None:
        """ Ignore errors related to altered permissions or deletions mid-process """
        if not isinstance(error, NotFound):
            raise

    async def bot_info(self) -> Generator[Embed, None, Embed]:
        e = Embed()
        e.set_author(
            name="Collecting Information..",
            icon_url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif",
        )
        yield e
        bot_pid = psutil.Process(os.getpid())
        e = Embed(color=colors.fate)
        e.set_author(
            name="Fate Bot: Core Info",
            icon_url= self.bot.get_user( self.bot.config["bot_owner_id"]).display_avatar.url,
        )

        async with  self.bot.utils.cursor() as cur:
            await cur.execute("select sum(total) from commands;")
            commands = await cur.fetchone()

        lines = 0
        async with  self.bot.utils.open("fate.py", "r") as f:
            lines += len(await f.readlines())
        locations = ["botutils", "cogs"]
        for location in locations:
            for root, dirs, files in os.walk(location):
                for file in files:
                    await asyncio.sleep(0)
                    if file.endswith(".py"):
                        async with  self.bot.utils.open(f"{root}/{file}", "r") as f:
                            lines += len(await f.readlines())

        e.description = f"Commands Used This Month: {commands[0]}" \
                        f"\nLines of Code: {lines}"
        if core :=  self.bot.get_cog("Core"):
            e.description += f"\nVotes This Month: {len(await core.dblpy.get_bot_upvotes())}"

        guilds = len(list( self.bot.guilds))
        users = 0
        for guild in list( self.bot.guilds):
            await asyncio.sleep(0)
            users += guild.member_count

        e.set_thumbnail(url= self.bot.user.display_avatar.url)
        e.add_field(
            name="◈ Summary ◈",
            value="Fate is a ~~multipurpose~~ hybrid bot created for fun",
            inline=False,
        )
        e.add_field(
            name="◈ Statistics ◈",
            value=f"**Commands:** [{len( self.bot.commands)}]"
                  f"\n**Modules:** [{len( self.bot.extensions)}]"
                  f"\n**Servers:** [{guilds}]"
                  f"\n**Users:** [{users}]",
        )
        e.add_field(
            name="◈ Credits ◈",
            value="\n• **Cortex** ~ `teacher of many things..`"
                  "\n• **Luck** ~ `owner & main developer`"
                  "\n• **Opal** ~ `artwork / graphic design`"
                  "\n• **Legit** ~ `identifying many design flaws`"
        )

        def get_info() -> str:
            disk = psutil.disk_usage('/')
            ram = psutil.virtual_memory()
            freq = psutil.cpu_freq()
            cur = str(round(freq.current))

            if freq.current < 1000:
                cur = f"{cur}GHz"
            else:
                cur = f"{cur[0]}.{cur[1]}GHz"
            max = str(round(freq.max))
            max = f"{max[0]}.{max[1]}GHz"
            c_temp = round(psutil.sensors_temperatures(fahrenheit=False)['coretemp'][0].current)
            f_temp = round(psutil.sensors_temperatures(fahrenheit=True)['coretemp'][0].current)
            value = f"**Storage (NVME)**: {bytes2human(disk.used)}/{bytes2human(disk.total)} - ({round(disk.percent)}%)\n" \
                    f"**RAM (DDR4)**: {bytes2human(ram.used)}/{bytes2human(ram.total)} - ({round(ram.percent)}%)\n" \
                    f"**CPU i9-10900K:** {round(psutil.cpu_percent())}% @{cur}/{max}\n" \
                    f"**CPU Temp:** {c_temp}°C {f_temp}°F\n" \
                    f"**Bot Usage:** **RAM:** {bytes2human(bot_pid.memory_full_info().rss)} **CPU:** {round(bot_pid.cpu_percent())}%"

            return value

        e.add_field(
            name="◈ Memory ◈",
            value=await  self.bot.loop.run_in_executor(None, get_info),
            inline=False,
        )

        online_for = datetime.now(tz=timezone.utc) -  self.bot.start_time
        e.add_field(
            name="◈ Uptime ◈",
            value=f"Online for {get_time(round(online_for.total_seconds()))}\n",
            inline=False,
        )
        e.set_footer(
            text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}",
            icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png",
        )
        yield e

    async def user_info(self) -> Generator[None, None, Embed]:
        if isinstance(self.target, (Member, User)):
            user = self.target
        else:
            user = self.ctx.author

        e = discord.Embed(color=colors.fate)
        e.set_author(
            name="Here's what I got on them..", icon_url=self.bot.user.display_avatar.url
        )
        e.set_thumbnail(url=str(user.display_avatar))
        e.description = ""
        has_public_profile = False

        cog: Utility
        if cog := self.bot.get_cog("Utility"):  # type: ignore
            if user.id in cog.settings:
                if cog.settings[user.id]["public"]:
                    has_public_profile = True

        # User Information
        guilds = []
        nicks = []
        if has_public_profile and user.id !=  self.bot.user.id:
            guilds = user.mutual_guilds
            for guild in guilds:
                await asyncio.sleep(0)
                if guild and user in guild.members:
                    member = guild.get_member(user.id)
                    if member.display_name != user.display_name:
                        nicks = list(set(list([member.display_name, *nicks])))
        user_info = {
            "Profile": f"{user.mention}",
            "ID": user.id,
            "Created at": user.created_at.strftime("%m/%d/%Y %I%p"),
            "Shared Servers": str(len(guilds))
        }
        if nicks:
            user_info["Nicks"] = ", ".join(nicks[:5])

        # Member Information
        member_info = {}
        if isinstance(user, discord.Member):
            user_info["Profile"] = f"{user.mention}"

            if user.name != user.display_name:
                member_info["Display Name"] = user.display_name
            if user.activity:
                member_info["Activity"] = user.activity.name
            member_info["Top Role"] = user.top_role.mention

            text = len([
                c for c in self.ctx.guild.text_channels
                if c.permissions_for(user).read_messages
            ])
            voice = len([
                c for c in self.ctx.guild.voice_channels
                if c.permissions_for(user).read_messages
            ])

            notable = [
                "view_audit_log",
                "manage_roles",
                "manage_channels",
                "manage_emojis",
                "kick_members",
                "ban_members",
                "manage_messages",
                "mention_everyone",
            ]
            member_info["Access"] = f"{emojis.text_channel} {text} {emojis.voice_channel} {voice}"
            if any(k in notable and v for k, v in list(user.guild_permissions)):
                perms = [k for k, v in user.guild_permissions if k in notable and v]
                perms = (
                    ["administrator"]
                    if user.guild_permissions.administrator
                    else perms
                )
                member_info["Notable Perms"] = f"`{', '.join(perms)}`"

            # Bot Information
            if user.bot:  # search the audit log to see who invited the bot
                inviter = "Unknown"
                if self.ctx.guild.me.guild_permissions.view_audit_log:
                    async for entry in self.ctx.guild.audit_logs(limit=250, action=discord.AuditLogAction.bot_add):
                        if entry.target and entry.target.id == user.id:
                            inviter = entry.user
                            break
                user_info["Inviter"] = inviter

        # Activity Information
        activity_info = {}
        if guilds:
            user = guilds[0].get_member(user.id)  # type: discord.Member
            async with  self.bot.utils.cursor() as cur:
                if user.status is discord.Status.offline:
                    await cur.execute(
                        f"select format(last_online, 3) from activity "
                        f"where user_id = {user.id} "
                        f"and last_online is not null "
                        f"limit 1;"
                    )
                    if cur.rowcount:
                        r = await cur.fetchone()
                        if r and hasattr(r[0], "replace"):
                            seconds = round(time() - float(r[0].replace(',', '')))
                            activity_info["Last Online"] = f"{get_time(seconds)} ago"
                        else:
                            activity_info["Last Online"] = "Unknown"
                    else:
                        activity_info["Last Online"] = "Unknown"
                await cur.execute(
                    f"select format(last_message, 3) from activity "
                    f"where user_id = {user.id} "
                    f"and last_message is not null "
                    f"limit 1;"
                )
                if cur.rowcount:
                    r = await cur.fetchone()
                    if r and hasattr(r[0], "replace"):
                        seconds = round(time() - float(r[0].replace(',', '')))
                        activity_info["Last Msg"] = f"{get_time(seconds)} ago"
                    else:
                        activity_info["Last Msg"] = "Unknown"
                else:
                    activity_info["Last Msg"] = "Unknown"

        if isinstance(user, discord.Member):
            if user.status is discord.Status.online:
                if user.is_on_mobile():
                    activity_info["Active on Mobile 📱"] = None
                else:
                    activity_info["Active on PC 🖥"] = None

        # Username history
        if has_public_profile:
            async with  self.bot.utils.cursor() as cur:
                await cur.execute(f"select username from usernames where user_id = {user.id};")
                if cur.rowcount:
                    results = await cur.fetchall()
                    decoded_results = [self.bot.decode(r[0]) for r in results]
                    names = [name for name in decoded_results if name != str(user)]
                    if names:
                        user_info["Usernames"] = ",".join(names)

        e.description += (
            f"◈ User Information{ self.bot.utils.format_dict(user_info)}\n\n"
        )
        if member_info:
            e.description += (
                f"◈ Member Information{ self.bot.utils.format_dict(member_info)}\n\n"
            )
        if activity_info:
            e.description += f"◈ Activity Information{ self.bot.utils.format_dict(activity_info)}\n\n"
        yield e

    async def channel_info(self) -> Generator[None, None, Embed]:
        e = discord.Embed(color=colors.fate)
        e.set_author(
            name="Alright, here's what I got..", icon_url=self.bot.user.display_avatar.url
        )

        channel: discord.TextChannel = self.ctx.channel
        if isinstance(self.target, discord.TextChannel):
            channel = self.target

        channel_info = {
            "Name": channel.name,
            "ID": channel.id,
            "Members": str(len(channel.members)),
        }

        if channel.category:
            channel_info["Category"] = f"`{channel.category}`"
        if channel.is_nsfw():
            channel_info["Marked as NSFW"] = None
        if channel.is_news():
            channel_info["Is the servers news channel"] = None
        channel_info["Created at"] = channel.created_at.strftime("%m/%d/%Y %I%p")

        e.add_field(
            name="◈ Channel Information",
            value= self.bot.utils.format_dict(channel_info),
            inline=False,
        )
        yield e

    async def role_info(self) -> Generator[None, None, Embed]:
        e = discord.Embed(color=colors.fate)
        e.set_author(
            name="Alright, here's what I got..", icon_url= self.bot.user.display_avatar.url
        )
        role = self.target  # type: discord.Role

        core = {
            "Name": role.name,
            "Mention": role.mention,
            "ID": role.id,
            "Members": len(role.members) if role.members else "None",
            "Created at": role.created_at.strftime("%m/%d/%Y %I%p"),
        }

        extra = {
            "Mentionable": str(role.mentionable),
            "HEX Color": role.color,
            "RGB Color": role.colour.to_rgb(),
        }
        if role.hoist:
            extra["**Shows Above Other Roles**"] = None
        if role.managed:
            extra["**And Is An Integrated Role**"] = None

        e.add_field(
            name="◈ Role Information",
            value= self.bot.utils.format_dict(core),
            inline=False,
        )
        e.add_field(
            name="◈ Extra", value= self.bot.utils.format_dict(extra), inline=False
        )
        e.set_footer(text="React With ♻ For History")
        yield e

    async def invite_info(self) -> Generator[None, None, Embed]:
        e = discord.Embed(color=colors.fate)
        e.set_author(
            name="Alright, here's what I got..", icon_url=self.bot.user.display_avatar.url
        )
        data = {}
        inv = [arg for arg in self.ctx.message.content.split() if "discord.gg" in arg][0]
        code = discord.utils.resolve_invite(inv)
        try:
            invite = await self.bot.fetch_invite(code)
            e.set_author(
                name="Alright, here's what I got..", icon_url=invite.guild.icon.url
            )
            if invite.guild.splash:
                e.set_thumbnail(url=invite.guild.splash.url)
            if invite.guild.banner:
                e.set_image(url=invite.guild.banner.url)
            data = {
                "Guild": invite.guild.name,
                "GuildID": invite.guild.id,
                "channel_name": invite.channel.name,
                "channel_id": invite.channel.id
            }
        except (discord.NotFound, discord.Forbidden):
            async with self.bot.utils.cursor() as cur:
                await cur.execute(
                    f"select guild_id, guild_name, channel_id, channel_name "
                    f"from invites "
                    f"where code = {self.bot.encode(code)};"
                )
                if not cur.rowcount:
                    await self.ctx.send("Failed to query that invite")
                    raise StopIteration()
                results = await cur.fetchone()
                data = {
                    "guild_name": self.bot.decode(results[1]),
                    "guild_id": results[0],
                    "channel_name": self.bot.decode(results[3]),
                    "channel_id": results[2],
                }
                e.set_footer(text="⚠ From Cache ⚠")

        inviters = []

        e.add_field(
            name="◈ Invite Information",
            value=self.bot.utils.format_dict(data),
            inline=False,
        )
        if inviters:
            e.add_field(
                name="◈ Inviters", value=", ".join(inviters[:16]), inline=False
            )
        yield e

    async def server_info(self):
        ctx = self.ctx
        e = discord.Embed(color=colors.fate)
        e.set_author(name=f"{ctx.guild.name}:", icon_url=ctx.guild.owner.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        main = {
            "ID": ctx.guild.id,
            "Owner": ctx.guild.owner,
            "AFK Timeout": format_date(seconds=ctx.guild.afk_timeout),
            "Region": ctx.guild.region,
            "Members": ctx.guild.member_count
        }
        e.description = self.bot.utils.format_dict(main)
        security = {
            "Content Filter": ctx.guild.explicit_content_filter,
            "Verification Level": ctx.guild.verification_level,
            "2FA to Moderate": "enabled" if ctx.guild.mfa_level else "disabled"
        }
        e.add_field(name="◈ Security", value=self.bot.utils.format_dict(security), inline=False)
        if ctx.guild.premium_tier:
            perks = {
                "Boost Level": ctx.guild.premium_tier,
                "Boosts": ctx.guild.premium_subscription_count,
                "Max Emojis": ctx.guild.emoji_limit,
                "Max Bitrate": bytes2human(ctx.guild.bitrate_limit).replace(".0", ""),
                "Max Filesize": bytes2human(ctx.guild.filesize_limit).replace(".0", "")
            }
            e.add_field(name="◈ Perks ◈", value=self.bot.utils.format_dict(perks), inline=False)
        created = datetime.date(ctx.guild.created_at)
        e.add_field(
            name="◈ Created", value=created.strftime("%m/%d/%Y"), inline=False
        )
        yield e


class SelectMenu(ui.Select):
    """ Select options for the parent view """
    def __init__(self, parent: InfoView) -> None:
        self.parent = parent  # The View class this is being added to
        options = [
            SelectOption(label="User Info"),
            SelectOption(label="Bot Info"),
            SelectOption(label="Server Info"),
            SelectOption(label="Channel Info")
        ]
        if isinstance(self.parent.target, str):
            options.append(SelectOption(label="Invite Info"))
        if isinstance(self.parent.target, Role):
            options.append(SelectOption(label="Role Info"))
        super().__init__(
            min_values=1,
            max_values=1,
            placeholder="Change Target",
            options=options
        )

    async def callback(self, interaction: Interaction) -> None:
        """ Call the parent classes info function """
        await interaction.response.defer()  # We're not sending anything, only editing
        choice: str = interaction.data["values"][0].lower().replace(" ", "_")
        async for embed in getattr(self.parent, choice)():
            await interaction.message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot), override=True)

