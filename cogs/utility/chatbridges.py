import asyncio
from time import time
from contextlib import suppress
import aiohttp
from datetime import datetime, timezone, timedelta

from discord.ext import commands
from discord import Guild, Webhook, AllowedMentions, Message
from discord.errors import NotFound, Forbidden, HTTPException
import discord


mentions = AllowedMentions(everyone=False, roles=False, users=True)


class ChatBridges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if "bridges" not in self.bot.tasks:
            self.bot.tasks["bridges"] = {}
        self.queue = {}
        self.config = self.bot.utils.cache("chatbridges")
        self.waiters = {}
        self.ignored = {}
        self.spam_cd = {}
        self.msgs = {}

        self.link_usage = "> Links two or more channels together so that you can chat with people from other servers. " \
                          "With a limit of 3 channels. Usage is just running `.link` in both channels"

        # Start each bridges task
        for channel_id, config in self.config.items():
            self.bot.tasks["bridges"][channel_id] = self.bot.loop.create_task(
                self.queue_task(channel_id)
            )

    def cog_unload(self):
        """Stop all running tasks"""
        for guild_id, task in list(self.bot.tasks["bridges"].items()):
            if not task.done():
                task.cancel()
            del self.bot.tasks["bridges"][guild_id]

    def get_webhook_urls(self, guild_id):
        return [
            self.config[guild_id]["webhook_url"],
            *list(self.config[guild_id]["channels"].values())
        ]

    async def destroy(self, bridge_id, reason):
        with suppress(HTTPException, NotFound, Forbidden, KeyError):
            webhooks = self.get_webhook_urls(bridge_id)
            async with aiohttp.ClientSession() as session:
                for webhook_url in webhooks:
                    webhook = Webhook.from_url(webhook_url, session=session)
                    with suppress(NotFound, Forbidden, HTTPException):
                        await webhook.send(reason)
                        await webhook.delete()
            if bridge_id in self.config:
                self.config.remove(bridge_id)
            if bridge_id in self.bot.tasks["bridges"]:
                del self.bot.tasks["bridges"][bridge_id]

    async def queue_task(self, bridge_id):
        await self.bot.wait_until_ready()
        self.queue[bridge_id] = asyncio.Queue(maxsize=3)
        webhook_cache = {}
        bans = {}
        last = {}
        async with aiohttp.ClientSession() as session:
            while True:
                msg, webhooks = await self.queue[bridge_id].get()
                file = None

                if isinstance(msg, Message) and msg.attachments:
                    if msg.attachments[0].size > 4000000:
                        if not msg.embeds:
                            msg.embeds = [discord.Embed(
                                description=f"[file too large to send]({msg.attachments[0].url})"
                            )]
                    else:
                        with suppress(NotFound, Forbidden, HTTPException):
                            _file = await msg.attachments[0].to_file()
                            file = _file

                for channel_id, webhook_url in webhooks:
                    channel = self.bot.get_channel(int(channel_id))
                    ref = alternate_content = None

                    # Check if they're banned in the sister server
                    if channel and channel.guild:
                        guild = channel.guild
                        if guild.id not in last:
                            last[guild.id] = 0
                            bans[guild.id] = []
                        member = guild.get_member(msg.author.id)
                        if member:
                            mute_role = await self.bot.attrs.get_mute_role(guild, upsert=False)
                            if mute_role in member.roles:
                                continue
                        if channel.guild.me and  channel.guild.me.guild_permissions.ban_members:
                            if time() - 30 > last[guild.id]:
                                with suppress(Exception):
                                    _bans = await guild.bans()
                                    bans[guild.id] = [entry.user.id for entry in _bans]
                                    last[guild.id] = time()
                            if msg.author.id in bans[guild.id]:
                                continue

                    # Reformat message replies into quoted messages
                    if msg.reference and msg.reference.cached_message:
                        ref = msg.reference.cached_message
                    if ref and ref.content:
                        formatted = "\n".join(f"> {line}" for line in ref.content.split("\n"))
                        target = r"\@" + ref.author.display_name
                        if channel and channel.guild and channel.guild.get_member(ref.author.id):
                            target = ref.author.mention
                        alternate_content = f"{formatted}\n{target} {msg.content}"

                    # Link any attachments inside of message replies
                    if ref and ref.attachments:
                        if not channel or not channel.permissions_for(channel.guild.me).read_message_history:
                            continue
                        async for m in channel.history(limit=75):
                            if ref.content == m.content and len(m.attachments) == len(ref.attachments):
                                if ref.attachments[0].filename == m.attachments[0].filename:
                                    if ref.attachments[0].size == m.attachments[0].size:
                                        msg.embeds = [discord.Embed(description=f"[attachment]({m.jump_url})")]
                                        break

                    try:
                        if webhook_url not in webhook_cache:
                            webhook = Webhook.from_url(webhook_url, session=session)
                            webhook_cache[webhook_url] = webhook
                        if isinstance(msg, str):
                            await webhook_cache[webhook_url].send(msg)
                        else:
                            await webhook_cache[webhook_url].send(
                                content=alternate_content if alternate_content else msg.content,
                                embeds=msg.embeds if msg.embeds else None,
                                file=file,
                                username=msg.author.display_name,
                                avatar_url=msg.author.display_avatar.url,
                                allowed_mentions=mentions
                            )
                    except (NotFound, Forbidden):
                        if bridge_id not in self.config:
                            return
                        if webhook_url == self.config[bridge_id]["webhook_url"]:
                            return await self.destroy(bridge_id, "Host webhook deleted. Disabling the chatbridge")

                        # Iterate through and remove the unavailable webhook
                        for channel_id, _webhook_url in list(self.config[bridge_id]["channels"].items()):
                            if webhook_url == _webhook_url:
                                self.config[bridge_id]["channels"] = {
                                    c: w for c, w in self.config[bridge_id]["channels"].items()
                                    if c != channel_id
                                }
                                await self.config.flush()

                                # Notify the other webhooks that another was deleted
                                channel = self.bot.get_channel(int(channel_id))
                                if channel:
                                    warning = f"The webhook for {channel.mention} in {channel.guild} was deleted"
                                else:
                                    warning = f"The webhook for {channel_id} was deleted"

                                await self.queue[bridge_id].put([warning, self.get_webhook_urls(bridge_id)])

                        # Disable the bridge if there's only the host channel
                        if not self.config[bridge_id]["channels"]:
                            await self.destroy(bridge_id, "Disabled the chatbridge due to the only other channel removing their webhook")

                    except aiohttp.ClientOSError:
                        with suppress(Exception):
                            await msg.channel.send("Couldn't send your message due to a connection reset")
                    except Exception as error:
                        with suppress(Exception):
                            await msg.channel.send(f"Error: couldn't send your message to the other channels. {error}")

                await asyncio.sleep(0.5)

    async def get_bridge_id(self, channel):
        bridge_id = channel.id
        if channel.id not in self.config:
            for channel_id, config in list(self.config.items()):
                await asyncio.sleep(0)
                if str(channel.id) in config["channels"]:
                    return channel_id
        return bridge_id

    async def block(self, channel, user):
        self.config[await self.get_bridge_id(channel)]["blocked"].append(user.id)

    async def is_blocked(self, channel, user) -> bool:
        return user.id in self.config[await self.get_bridge_id(channel)]["blocked"]

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Run anti spam checks and send the message to the queue"""
        if not isinstance(msg.guild, Guild):
            return
        bridge_id = await self.get_bridge_id(msg.channel)
        if bridge_id not in self.config:
            return
        if msg.author.discriminator == "0000" or (not msg.content and not msg.embeds and not msg.attachments):
            return
        if not msg.channel.permissions_for(msg.guild.me).send_messages:
            return
        blacklist = (
            "Error:",
            "That's too many pings",
            "Woah, slow down"
        )
        if msg.author.bot and any(msg.content.startswith(content) for content in blacklist):
            return
        user_id = msg.author.id
        if msg.channel.id not in self.config:
            if str(msg.channel.id) not in self.config[bridge_id]["channels"]:
                return
        if await self.is_blocked(msg.channel, msg.author):
            return
        if msg.author.id in self.ignored:
            if time() - 60 > self.ignored[msg.author.id]:
                del self.ignored[msg.author.id]
            else:
                return

        async def warn():
            if "warnings" not in self.config[bridge_id]:
                with suppress(NotFound, Forbidden):
                    await msg.add_reaction("❌")
            return None

        # Prevent all caps messages
        abcs = "abcdefghijklmnopqrstuvwxyz"
        if len([c for c in msg.content if c.lower() in abcs]) > 10:
            total_uppercase = len([c for c in msg.content if c == c.upper()])
            div = 100 * total_uppercase / len(msg.content)
            if div >= 75:
                return await warn()

        # Prevent long messages:
        if len(msg.content) > 1000 or "\n\n\n" in msg.content:
            return await warn()
        if len(msg.content) > 50 and msg.content.count(" ") == 0:
            if "http" not in msg.content or len(msg.content) > 750:
                return await warn()
        if len(msg.content) > 5 and all(c == msg.content[0] for c in msg.content):
            return await warn()

        # Prevent repeating lines
        if msg.content.count("\n") > 3 and all(line == line for line in msg.content.split("\n")):
            return await warn()

        # Prevent repeating sentences
        if any(msg.content.count(sentence) > 1 for sentence in msg.content.split(".") if sentence):
            return await warn()
        if len(msg.content) <= 50 and any(msg.content.count(word) > 3 for word in msg.content.split(" ") if len(word) > 3):
            return await warn()
        if len(msg.content) > 50 and any(msg.content.count(word) > 10 for word in msg.content.split(" ") if len(word) > 3):
            return await warn()

        # Prevent custom emoji spam
        if msg.content.count(":") > 10:
            return await warn()

        # Prevent random char spam alongside unicode emoji spam
        if len(msg.content) > 50 and not any(c in abcs for c in msg.content):
            return await warn()

        # Prevent sending messages too quickly
        thresholds = [(5, 4), (10, 7)]
        for timeframe, threshold in thresholds:
            await asyncio.sleep(0)
            _id = str([timeframe, threshold])
            if _id not in self.spam_cd:
                self.spam_cd[_id] = {}
            now = int(time() / int(timeframe))
            if user_id not in self.spam_cd[_id]:
                self.spam_cd[_id][user_id] = [now, 0]
            if self.spam_cd[_id][user_id][0] == now:
                self.spam_cd[_id][user_id][1] += 1
            else:
                self.spam_cd[_id][user_id] = [now, 0]
            if self.spam_cd[_id][user_id][1] >= int(threshold):
                await msg.channel.send("Woah slow down, you've been muted from the bridge for 1 minute")
                self.ignored[msg.author.id] = time()
                return

        # Prevent mass pinging
        pings = [msg.raw_mentions, msg.raw_role_mentions]
        total_pings = sum(len(group) for group in pings)
        if total_pings > 3:
            await msg.channel.send("That's too many pings, you've been muted from the bridge for 1 minute")
            self.ignored[msg.author.id] = time()
            return

        if user_id not in self.msgs:
            self.msgs[user_id] = []
        self.msgs[user_id].append(msg)
        self.msgs[user_id] = self.msgs[user_id][:15]

        pongs = lambda s: [
            m for m in self.msgs[user_id]
            if m and m.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=s)
               and sum(len(group) for group in [
                m.mentions, m.raw_mentions, m.role_mentions, m.raw_role_mentions
            ])
        ]
        if len(pongs(10)) > 3:
            await msg.channel.send("That's too many pings, you've been muted from the bridge for 1 minute")
            self.ignored[msg.author.id] = time()
            return

        # Parse what channels to forward to
        webhooks = []
        for channel_id, webhook_url in list(self.config[bridge_id]["channels"].items()):
            await asyncio.sleep(0)
            channel = self.bot.get_channel(int(channel_id))
            if channel and channel.id != msg.channel.id:
                member = channel.guild.get_member(msg.author.id)
                mute_role = await self.bot.attrs.get_mute_role(channel.guild, upsert=False)
                if member and mute_role and mute_role in member.roles:
                    continue
                webhooks.append([channel_id, webhook_url])
        if msg.channel.id not in self.config:
            webhooks.append([bridge_id, self.config[bridge_id]["webhook_url"]])

        try:
            self.queue[bridge_id].put_nowait([msg, webhooks])
        except asyncio.QueueFull:
            with suppress(Forbidden, NotFound):
                if self.bot.tasks["bridges"][bridge_id].done():
                    await msg.add_reaction("⚠")
                else:
                    await msg.add_reaction("⏳")
        except KeyError:
            pass

    @commands.group(name="link", aliases=["chatbridge", "bridge"], description="Starts the channel linking process")
    @commands.cooldown(4, 10, commands.BucketType.user)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def link(self, ctx):
        """Start the process to link two channels"""
        def check(m):
            if m.channel.id != ctx.channel.id:
                return False
            if ".confirm link" not in m.content:
                return False
            member = ctx.guild.get_member(m.author.id)
            if not member:
                return False
            return member.guild_permissions.administrator

        if not ctx.invoked_subcommand:
            linked_channels = len([
                c for c in ctx.guild.text_channels if await self.get_bridge_id(c) in self.config
            ])
            if linked_channels == 3:
                return await ctx.send("You can't create more than 3 bridges in a single server")

            for channel, (_user_id, start_time) in list(self.waiters.items()):
                await asyncio.sleep(0)
                if start_time < time() - 120:
                    del self.waiters[channel]
            if ctx.channel in self.waiters:
                return await ctx.send("I'm already waiting on you to link a channel")
            for channel, (user_id, start_time) in list(self.waiters.items()):
                await asyncio.sleep(0)
                if user_id == ctx.author.id:
                    channel = channel
                    break
            else:
                if not ctx.author.guild_permissions.administrator:
                    await ctx.send("Someone with administrator send `.confirm link`")
                    await self.bot.utils.get_message(check=check)
                self.waiters[ctx.channel] = [ctx.author.id, time()]
                return await ctx.send(f"Run `.link` in the other channel you wanna link")

            if not ctx.author.guild_permissions.administrator:
                await ctx.send("Someone with administrator send `.confirm link`")
                await self.bot.utils.get_message(check=check)
            bridge_id = await self.get_bridge_id(channel)
            linked_channels = len([
                c for c in ctx.guild.text_channels if await self.get_bridge_id(c) in self.config
            ])
            if linked_channels == 3:
                return await ctx.send("You can't create more than 3 bridges in a single server")
            for config in list(self.config.values()):
                await asyncio.sleep(0)
                if str(channel.id) in config["channels"]:
                    return await ctx.send("That channel's already linked")
            if bridge_id in self.config and len(self.config[bridge_id]["channels"]) >= 2:
                if "additional_channels" in self.config[bridge_id]:
                    lmt = 2 + self.config[bridge_id]["additional_channels"]
                    if len(self.config[bridge_id]["channels"]) >= lmt:
                        return await ctx.send(f"You can only link a max of {lmt + 1} channels together")
                else:
                    return await ctx.send(
                        "You can only link a max of 3 channels together. "
                        "You can request more in the support server"
                    )
            webhook = None
            if bridge_id not in self.config:
                webhook = await channel.create_webhook(name="F8 ChatBridge")
            sub_webhook = await ctx.channel.create_webhook(name="F8 ChatBridge")
            if webhook:
                await webhook.send(f"Successfully linked with {ctx.channel.mention}")
            await sub_webhook.send(
                f"Successfully linked with {channel.mention} in {channel.guild}",
                allowed_mentions=AllowedMentions.all()
            )

            if bridge_id in self.config:
                self.config[bridge_id]["channels"][str(ctx.channel.id)] = sub_webhook.url
            else:
                self.config[bridge_id] = {
                    "guild_id": self.bot.get_channel(bridge_id).guild.id,
                    "webhook_url": webhook.url,
                    "channels": {
                        str(ctx.channel.id): sub_webhook.url
                    },
                    "blocked": []
                }
            await self.config.flush()
            self.bot.tasks["bridges"][bridge_id] = self.bot.loop.create_task(
                self.queue_task(bridge_id)
            )
            if channel in self.waiters:
                del self.waiters[channel]

    @commands.command(name="unlink", description="Unlinks a channel from the bridge")
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def unlink(self, ctx):
        """Unlink a channel from a bridge"""
        bridge_id = await self.get_bridge_id(ctx.channel)
        if bridge_id not in self.config:
            return await ctx.send("This channel isn't linked")
        guild = self.bot.get_guild(self.config[bridge_id]["guild_id"])
        if ctx.channel.id == bridge_id:
            await ctx.send(f"Unlinked from {guild}")
            return await self.destroy(bridge_id, "Host disabled the chatbridge")

        # Remove the webhook if we can
        for channel in ctx.guild.text_channels:
            if str(channel.id) in self.config[bridge_id]["channels"]:
                channel = channel
                break
        else:
            return await ctx.send("This channel isn't linked")
        with suppress(NotFound, Forbidden, HTTPException):
            webhooks = await ctx.channel.webhooks()
            for webhook in webhooks:
                if webhook.url == self.config[bridge_id]["channels"][str(channel.id)]:
                    await webhook.delete()
                    break

        # Remove the channel_id from the hosts linked channels
        self.config[bridge_id]["channels"] = {
            c: w for c, w in self.config[bridge_id]["channels"].items()
            if c != str(ctx.channel.id)
        }
        await self.config.flush()

        # If the host has no linked channels disable the whole thing
        if not self.config[bridge_id]["channels"]:
            await ctx.send(f"Unlinked from {guild}")
            return await self.destroy(
                bridge_id,
                "Disabled the chatbridge due to the only other channel removing their webhook"
            )

        await ctx.send(f"Unlinked from {guild}")

    @link.command(name="toggle-warnings", description="Toggles whether or not to send warning msgs")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def toggle_warnings(self, ctx):
        guild_id = await self.get_bridge_id(ctx.channel)
        if guild_id not in self.config:
            return await ctx.send("This channel isn't linked")
        if "warnings" in self.config[guild_id]:
            await self.config.remove_sub(guild_id, "warnings")
            return await ctx.send("Enabled warnings")
        self.config[guild_id]["warnings"] = False
        await self.config.flush()
        await ctx.send("Disabled warnings")

    @link.command(name="grant")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def grant_slots(self, ctx, channel_id: int, amount: int):
        channel_id = await self.get_bridge_id(self.bot.get_channel(channel_id))
        if channel_id not in self.config:
            return await ctx.send("That's not a bridge id")
        if "additional_channels" not in self.config[channel_id]:
            self.config[channel_id]["additional_channels"] = 0
        self.config[channel_id]["additional_channels"] += amount
        count = self.config[channel_id]["additional_channels"]
        await ctx.send(f"{self.bot.get_channel(channel_id).guild} now has {count} additional channels")
        await self.config.flush()

    @link.command(name="remove-grant")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def remove_granted_slots(self, ctx, channel_id: int):
        channel_id = await self.get_bridge_id(self.bot.get_channel(channel_id))
        channel = self.bot.get_channel(channel_id)
        if "additional_channels" not in self.config[channel_id]:
            return await ctx.send(f"{channel.guild} has no extra channel slots")
        del self.config[channel_id]["additional_channels"]
        await ctx.send(f"Removed {channel.guild}'s extra channel slots")
        await self.config.flush()

    @link.command(name="block", description="Blocks a user from using the bridge")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _block(self, ctx, *users):
        guild_id = await self.get_bridge_id(ctx.channel)
        if guild_id not in self.config:
            return await ctx.send("This channel isn't linked")
        blocked = ""
        for user in users:
            await asyncio.sleep(0)
            try:
                user = await self.bot.utils.get_user(ctx, user)
                if user.id in self.config[guild_id]["blocked"]:
                    blocked += f"\n{user} was already blocked"
                else:
                    self.config[guild_id]["blocked"].append(user.id)
                    blocked += f"\nBlocked {user} from using the chatbridge"
            except:
                blocked += f"\nCouldn't get {user}"
        await self.config.flush()
        await ctx.send(blocked)

    @link.command(name="unblock", description="Unblocks a user from using the bridge")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _unblock(self, ctx, *, user):
        guild_id = await self.get_bridge_id(ctx.channel)
        if guild_id not in self.config:
            return await ctx.send("This channel isn't linked")
        user = await self.bot.utils.get_user(ctx, user)
        if user.id not in self.config[guild_id]["blocked"]:
            return await ctx.send(f"{user} isn't blocked")
        self.config[guild_id]["blocked"].remove(user.id)
        await self.config.flush()
        await ctx.send(f"Unblocked {user}")

    @commands.command(name="bridges", aliases=["chatbridges"], description="Lists all the bridges the server uses")
    async def chatbridges(self, ctx):
        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name="ChatBridges", icon_url=self.bot.user.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)

        bridges = ""
        for channel in ctx.guild.text_channels:
            await asyncio.sleep(0)
            if channel.id in self.config:
                bridges += f"◈ {channel.guild.name}\n"
                for channel_id in self.config[channel.id]["channels"]:
                    _channel = self.bot.get_channel(int(channel_id))
                    if _channel:
                        bridges += f"﹂{_channel.guild.name}\n"
                bridges += "\n"

        for channel in ctx.guild.text_channels:
            await asyncio.sleep(0)
            bridge_id = await self.get_bridge_id(channel)
            if channel.id not in self.config and bridge_id in self.config:
                main = self.bot.get_channel(bridge_id)
                if not main:
                    continue
                bridges += f"◈ {main.guild.name}\n"
                for channel_id in self.config[bridge_id]["channels"]:
                    _channel = self.bot.get_channel(int(channel_id))
                    if _channel:
                        bridges += f"﹂{_channel.guild.name}\n"

        e.description = bridges
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(ChatBridges(bot), override=True)
