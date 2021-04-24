"""
Core bot functions like:
Prefix, Invite, and Ping
"""

from bs4 import BeautifulSoup as bs
import json
from io import BytesIO
import requests
import aiohttp
from time import time, monotonic
from typing import Union
import asyncio
from datetime import datetime

from discord.ext import commands
import discord
from discord import Webhook, AsyncWebhookAdapter
import dbl

from botutils import config, colors, auth
from cogs.core.utils import Utils as utils


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last = {}
        self.spam_cd = {}
        creds = bot.auth["TopGG"]  # type: dict
        self.dblpy = dbl.DBLClient(
            bot=self.bot,
            token=creds["token"],
            autopost=True,
            webhook_path=creds["path"],
            webhook_auth=creds["auth"],
            webhook_port=creds["port"]
        )
        self.path = "./data/userdata/disabled_commands.json"
        self.config = bot.utils.cache("disabled")

    async def on_guild_post(self):
        self.bot.log.debug("Server count posted successfully")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        self.bot.log.info(f"Received a test upvote from {self.bot.get_user(int(data['user']))}")
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into votes values ({int(data['user'])}, {time()});"
            )

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        self.bot.log.info(f"Received an upvote from {self.bot.get_user(int(data['user']))}")
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into votes values ({int(data['user'])}, {time()});"
            )

    @commands.command(name='dbl')
    @commands.is_owner()
    async def dbl(self, ctx):
        await ctx.send()

    @commands.command(name="votes")
    @commands.is_owner()
    async def votes(self, ctx):
        votes = await self.dblpy.get_bot_upvotes()
        await ctx.send(", ".join(dat["username"] for dat in votes))

    @commands.command(name="topguilds")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def topguilds(self, ctx):
        e = discord.Embed(color=0x80B0FF)
        e.title = "Top Guilds"
        e.description = ""
        rank = 1
        for guild in sorted(
            [[g.name, g.member_count] for g in self.bot.guilds],
            key=lambda k: k[1],
            reverse=True,
        )[:8]:
            e.description += "**{}.** {}: `{}`\n".format(rank, guild[0], guild[1])
            rank += 1
        await ctx.send(embed=e)

    @staticmethod
    def topguilds_usage():
        return "Displays the top 8 servers based on highest member count"

    @commands.command(name="invite", aliases=["links", "support"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def invite(self, ctx):
        await ctx.send(embed=config.links())

    @staticmethod
    def invite_usage():
        return "Gives the link to invite the bot to another server. " \
               "Alongside the invite to the support server. Just click the blue hyperlink text"

    @commands.command(name="vote")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def vote(self, ctx):
        await ctx.send("https://top.gg/bot/506735111543193601")

    @commands.command(name="say")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    async def say(self, ctx, *, content: commands.clean_content = None):
        has_perms = ctx.channel.permissions_for(ctx.guild.me).manage_messages
        if len(str(content).split("\n")) > 4:
            await ctx.send(f"{ctx.author.mention} too many lines")
            if has_perms and ctx.message:
                await ctx.message.delete()
            return
        if content:
            content = self.bot.utils.cleanup_msg(ctx.message, content)
            content = content[:2000]
        if ctx.message.attachments and ctx.channel.is_nsfw():
            file_data = [
                (f.filename, BytesIO(requests.get(f.url).content))
                for f in ctx.message.attachments
            ]
            files = [
                discord.File(file, filename=filename) for filename, file in file_data
            ]
            await ctx.send(content, files=files)
            if has_perms:
                await ctx.message.delete()
        elif content and not ctx.message.attachments:
            await ctx.send(content)
            if has_perms and ctx.message:
                await ctx.message.delete()
        elif ctx.message.attachments:
            await ctx.send("You can only attach files if the channel's nsfw")
        else:
            await ctx.send("Content is a required argument that is missing")

    @commands.command(name="prefix")
    @commands.cooldown(*utils.default_cooldown())
    @commands.guild_only()
    async def prefix(self, ctx, *, prefix = None):
        if not prefix:
            prefixes = await self.bot.utils.get_prefixes_async(self.bot, ctx.message)
            formatted = "\n".join(prefixes[1::])
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Prefixes", icon_url=ctx.author.avatar_url)
            e.description = formatted
            return await ctx.send(embed=e)
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send(f"You need manage_server permission(s) to use this")
        if not isinstance(ctx.guild, discord.Guild):
            return await ctx.send("This command can't be used in dm")
        if len(prefix) > 5:
            return await ctx.send("That prefix is too long")
        opts = ["yes", "no"]
        choice = await self.bot.utils.get_choice(ctx, opts, name="Allow personal prefixes?")
        override = True if choice == "no" else False
        if ctx.guild.id in self.bot.guild_prefixes:
            if not override and prefix == ".":
                await self.bot.aio_mongo["GuildPrefixes"].delete_one({
                    "_id": ctx.guild.id
                })
                del self.bot.guild_prefixes[ctx.guild.id]
                return await ctx.send("Reset the prefix to default")
            else:
                await self.bot.aio_mongo["GuildPrefixes"].update_one(
                    filter={"_id": ctx.guild.id},
                    update={"$set": {"prefix": prefix, "override": override}}
                )
        else:
            if not override and prefix == ".":
                return await ctx.send("tHaT's tHe sAmE aS thE cuRreNt cOnfiG")
            await self.bot.aio_mongo["GuildPrefixes"].insert_one({
                "_id": ctx.guild.id,
                "prefix": prefix,
                "override": override
            })
        self.bot.guild_prefixes[ctx.guild.id] = {
            "prefix": prefix,
            "override": override
        }
        await ctx.send(f"Changed the servers prefix to `{prefix}`")

    @commands.command(name="personal-prefix", aliases=["pp"])
    @commands.cooldown(*utils.default_cooldown())
    async def personal_prefix(self, ctx, *, prefix=""):
        if prefix.startswith('"') and prefix.endswith('"') and len(prefix) > 2:
            prefix = prefix.strip('"')
        prefix = prefix.strip("'\"")
        if len(prefix) > 5:
            return await ctx.send("Your prefix can't be more than 8 chars long")
        if ctx.author.id in self.bot.user_prefixes:
            await self.bot.aio_mongo["UserPrefixes"].update_one(
                filter={"_id": ctx.author.id},
                update={"$set": {"prefix": prefix}}
            )
        else:
            await self.bot.aio_mongo["UserPrefixes"].insert_one({
                "_id": ctx.author.id,
                "prefix": prefix
            })
        self.bot.user_prefixes[ctx.author.id] = {"prefix": prefix}
        nothing = "something that doesn't exist"
        await ctx.send(
            f"Set your personal prefix as `{prefix if prefix else nothing}`\n"
            f"Note you can still use my mention as a sub-prefix"
        )

    @commands.command(name="enable-command", aliases=["enablecommand"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    async def enable_command(self, ctx, *, command):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("This server has no disabled commands")
        if not self.bot.get_command(command):
            return await ctx.send("That's not a command")
        command = self.bot.get_command(command).name
        for key, value in list(self.config[guild_id].items()):
            await asyncio.sleep(0)
            if command in value:
                break
        else:
            return await ctx.send(f"`{command}` isn't disabled anywhere")
        locations = [
            "enable globally", "enable in category", "enable in this channel"
        ]
        choice = await self.bot.utils.get_choice(ctx, locations, user=ctx.author)
        if not choice:
            return
        if choice == "enable globally":
            for key, value in list(self.config[guild_id].items()):
                await asyncio.sleep(0)
                if command in value:
                    self.config[guild_id][key].remove(command)
                    if not self.config[guild_id][key]:
                        await self.config.remove_sub(guild_id, key)
            await ctx.send(f"Enabled `{command}` in all channels")
        elif choice == "enable in category":
            if not ctx.channel.category:
                return await ctx.send("This channel has no category")
            for channel in ctx.channel.category.text_channels:
                await asyncio.sleep(0)
                channel_id = str(channel.id)
                if channel_id in self.config[guild_id]:
                    if command in self.config[guild_id][channel_id]:
                        self.config[guild_id][channel_id].remove(command)
                        if not self.config[guild_id][channel_id]:
                            await self.config.remove_sub(guild_id, channel_id)
            await ctx.send(f"Enabled `{command}` in all of {ctx.channel.category}'s channels")
        elif choice == "enable in this channel":
            channel_id = str(ctx.channel.id)
            if channel_id not in self.config[guild_id]:
                return await ctx.send("This channel has no disabled commands")
            if command not in self.config[guild_id][channel_id]:
                return await ctx.send(f"`{command}` isn't disabled in this channel")
            self.config[guild_id][channel_id].remove(command)
            if not self.config[guild_id][channel_id]:
                await self.config.remove_sub(guild_id, key)
            await ctx.send(f"Enabled `{command}` in this channel")
        if not self.config[guild_id]:
            await self.config.remove(guild_id)
        else:
            await self.config.flush()

    @commands.command(name="disable-command", aliases=["disablecommand"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    async def disable_command(self, ctx, *, command):
        guild_id = ctx.guild.id
        if not self.bot.get_command(command):
            return await ctx.send("That's not a command")
        command = self.bot.get_command(command).name
        if guild_id in self.config and "global" in self.config[guild_id]:
            if command in self.config[guild_id]["global"]:
                return await ctx.send(f"`{command}` is already disabled everywhere")
        locations = [
            "disable globally", "disable in category", "disable in this channel"
        ]
        choice = await self.bot.utils.get_choice(ctx, locations, user=ctx.author)
        if not choice:
            return
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if choice == "disable globally":
            for channel in ctx.guild.text_channels:
                await asyncio.sleep(0)
                channel_id = str(channel.id)
                if channel_id not in self.config[guild_id]:
                    self.config[guild_id][channel_id] = []
                if command not in self.config[guild_id][channel_id]:
                    self.config[guild_id][channel_id].append(command)
            await ctx.send(f"Disabled `{command}` in all existing channels")
        elif choice == "disable in category":
            if not ctx.channel.category:
                return await ctx.send("This channel has no category")
            for channel in ctx.channel.category.text_channels:
                await asyncio.sleep(0)
                channel_id = str(channel.id)
                if channel_id not in self.config[guild_id]:
                    self.config[guild_id][channel_id] = []
                if command not in self.config[guild_id][channel_id]:
                    self.config[guild_id][channel_id].append(command)
            await ctx.send(f"Disabled `{command}` in all of {ctx.channel.category}'s channels")
        elif choice == "disable in this channel":
            channel_id = str(ctx.channel.id)
            if command not in self.config[guild_id][channel_id]:
                self.config[guild_id][channel_id].append(command)
            self.config[guild_id][channel_id]["commands"].remove(command)
            await ctx.send(f"Disabled `{command}` in this channel")
        await self.config.flush()

    @commands.command(name="disabled")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.has_permissions(administrator=True)
    async def disabled(self, ctx):
        """ Lists the guilds disabled commands """
        async with self.bot.open(self.path, "r") as f:
            config = json.loads(await f.read())  # type: dict
        guild_id = str(ctx.guild.id)
        if guild_id not in config:
            return await ctx.send("This server has no disabled commands")
        conf = config[guild_id]
        if guild_id not in config or not any(
            conf[key]
            if isinstance(conf[key], list)
            else any(v[1] for v in conf[key].items())
            for key in conf.keys()
        ):
            return await ctx.send("There are no disabled commands")
        e = discord.Embed(color=colors.fate())
        if config[guild_id]["global"]:
            e.add_field(name="Global", value=", ".join(conf["global"]), inline=False)
        channels = {}
        dat = [*conf["channels"].items(), *conf["categories"].items()]
        for channel_id, commands in dat:
            await asyncio.sleep(0)
            if commands:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    channels[channel] = []
                    for cmd in commands:
                        await asyncio.sleep(0)
                        channels[channel].append(cmd)
        for channel, commands in channels.items():
            await asyncio.sleep(0)
            e.add_field(name=channel.name, value=", ".join(commands), inline=False)
        await ctx.send(embed=e)

    @commands.command(name="ping")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def ping(self, ctx):
        emojis = self.bot.utils.emotes
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Measuring ping:")
        before = monotonic()
        msg = await ctx.send(embed=e)
        api_ping = f"{emojis.discord} **Discord API:** `{round((monotonic() - before) * 1000)}ms`"
        response_time = (datetime.utcnow() - ctx.message.created_at).total_seconds() * 1000
        response_ping = f"\n{emojis.verified} **Message Trip:** `{round(response_time)}ms`"
        imgs = [
            "https://cdn.discordapp.com/emojis/562592256939393035.png?v=1",
            "https://cdn.discordapp.com/emojis/562592178204049408.png?v=1",
            "https://cdn.discordapp.com/emojis/562592177692213248.png?v=1",
            "https://cdn.discordapp.com/emojis/562592176463151105.png?v=1",
            "https://cdn.discordapp.com/emojis/562592175880405003.png?v=1",
            "https://cdn.discordapp.com/emojis/562592175192539146.png?v=1"
        ]
        for i, limit in enumerate(range(175, 175 * 6, 175)):
            if response_time < limit:
                img = imgs[i]
                break
        else:
            img = imgs[5]
        shard_ping = ""
        for shard, latency in self.bot.latencies:
            shard_ping += f"\n{emojis.boost} **Shard {shard}:** `{round(latency * 1000)}ms`"
        e.set_author(name=f"Bots Latency", icon_url=self.bot.user.avatar_url)
        e.set_thumbnail(url=img)
        e.description = api_ping + response_ping + shard_ping
        await msg.edit(embed=e)

    @commands.command(name="devping")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def devping(self, ctx):
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Measuring ping:")
        before = monotonic()
        message = await ctx.send(embed=e)
        ping = (monotonic() - before) * 1000

        if ping < 175:
            img = "https://cdn.discordapp.com/emojis/562592256939393035.png?v=1"
        elif ping < 250:
            img = "https://cdn.discordapp.com/emojis/562592178204049408.png?v=1"
        elif ping < 400:
            img = "https://cdn.discordapp.com/emojis/562592177692213248.png?v=1"
        elif ping < 550:
            img = "https://cdn.discordapp.com/emojis/562592176463151105.png?v=1"
        elif ping < 700:
            img = "https://cdn.discordapp.com/emojis/562592175880405003.png?v=1"
        else:
            img = "https://cdn.discordapp.com/emojis/562592175192539146.png?v=1"

        api = str(self.bot.latency * 1000)
        api = api[: api.find(".")]
        e.set_author(name=f"Bots Latency", icon_url=self.bot.user.avatar_url)
        e.set_thumbnail(url=img)
        e.description = (
            f"**Message Trip 1:** `{int(ping)}ms`\n**Websocket Heartbeat:** `{api}ms`"
        )

        before = monotonic()
        await message.edit(embed=e)
        edit_ping = (monotonic() - before) * 1000
        e.description = f"**Message Trip 1:** `{int(ping)}ms`\n**Msg Edit Trip:** `{int(edit_ping)}ms`\n**Websocket Heartbeat:** `{api}ms`"

        before = monotonic()
        await message.edit(embed=e)
        second_edit_ping = (monotonic() - before) * 1000

        before = monotonic()
        await ctx.send("Measuring Ping", delete_after=0.5)
        second_ping = (monotonic() - before) * 1000
        e.description = f"**Message Trip 1:** `{int(ping)}ms`\n**Message Trip 2:** `{int(second_ping)}ms`\n**Msg Edit Trip 1:** `{int(edit_ping)}ms`\n**Msg Edit Trip 2:** `{int(second_edit_ping)}ms`\n**Websocket Heartbeat:** `{api}ms`"
        await message.edit(embed=e)

    @commands.is_nsfw()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def ud(self, ctx, *, query: str):
        channel_id = str(ctx.channel.id)
        if channel_id not in self.last:
            self.last[channel_id] = (None, None)
        if query == self.last[channel_id][0]:
            if self.last[channel_id][1] > time() - 60:
                return await ctx.message.add_reaction("❌")
        self.last[channel_id] = (query, time())
        url = "http://www.urbandictionary.com/define.php?term={}".format(
            query.replace(" ", "%20")
        )
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                r = await resp.read()
        resp = bs(r, "html.parser")
        try:
            if (
                len(
                    resp.find("div", {"class": "meaning"})
                    .text.strip("\n")
                    .replace("\u0027", "'")
                )
                >= 1000
            ):
                meaning = (
                    resp.find("div", {"class": "meaning"})
                    .text.strip("\n")
                    .replace("\u0027", "'")[:1000]
                    + "..."
                )
            else:
                meaning = (
                    resp.find("div", {"class": "meaning"})
                    .text.strip("\n")
                    .replace("\u0027", "'")
                )
            e = discord.Embed(color=0x80B0FF)
            e.set_author(name=f"{query} 🔍", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/450528552199258123/524139193723781120/urban-dictionary-logo.png"
            )
            e.description = "**Meaning:**\n{}\n\n**Example:**\n{}\n".format(
                meaning, resp.find("div", {"class": "example"}).text.strip("\n")
            )

            e.set_footer(
                text="~{}".format(
                    resp.find("div", {"class": "contributor"}).text.strip("\n")
                )
            )
            await ctx.send(embed=e)
        except AttributeError:
            await ctx.send(
                "Either the page doesn't exist, or you typed it in wrong. Either way, please try again."
            )
        except Exception as e:
            await ctx.send(f"**```ERROR: {type(e).__name__} - {e}```**")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if isinstance(msg.channel, discord.DMChannel):
            user_id = msg.author.id
            now = int(time() / 5)
            if user_id not in self.spam_cd:
                self.spam_cd[user_id] = [now, 0]
            if self.spam_cd[user_id][0] == now:
                self.spam_cd[user_id][1] += 1
            else:
                self.spam_cd[user_id] = [now, 0]
            if self.spam_cd[user_id][1] < 2 or msg.author.bot:
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(
                        "https://discordapp.com/api/webhooks/673290242819883060/GDXiMBwbzw7dbom57ZupHsiEQ76w8TfV_mEwi7_pGw8CvVFL0LNgwRwk55yRPxNdPA4b",
                        adapter=AsyncWebhookAdapter(session),
                    )
                    msg.content = discord.utils.escape_mentions(msg.content)
                    if msg.attachments:
                        for attachment in msg.attachments:
                            return await webhook.send(
                                username=msg.author.name,
                                avatar_url=msg.author.avatar_url,
                                content=msg.content,
                                file=discord.File(
                                    BytesIO(requests.get(attachment.url).content),
                                    filename=attachment.filename,
                                ),
                            )
                    if msg.embeds:
                        if msg.author.id == self.bot.user.id:
                            return await webhook.send(
                                username=f"{msg.author.name} --> {msg.channel.recipient.name}",
                                avatar_url=msg.author.avatar_url,
                                embed=msg.embeds[0],
                            )
                        return await webhook.send(
                            username=msg.author.name,
                            avatar_url=msg.author.avatar_url,
                            embed=msg.embeds[0],
                        )
                    if msg.author.id == self.bot.user.id:
                        e = discord.Embed(color=colors.fate())
                        e.set_author(
                            name=msg.channel.recipient,
                            icon_url=msg.channel.recipient.avatar_url,
                        )
                        return await webhook.send(
                            username=msg.author.name,
                            avatar_url=msg.author.avatar_url,
                            content=msg.content,
                            embed=e,
                        )
                    await webhook.send(
                        username=msg.author.name,
                        avatar_url=msg.author.avatar_url,
                        content=msg.content,
                    )


def setup(bot):
    bot.add_cog(Core(bot))
