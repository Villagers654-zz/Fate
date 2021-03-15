import asyncio
from time import time
from contextlib import suppress
import aiohttp
from datetime import datetime, timedelta

from discord.ext import commands
from discord import Guild, Webhook, AsyncWebhookAdapter, AllowedMentions
from discord.errors import NotFound, Forbidden, HTTPException


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
        for guild_id, config in self.config.items():
            self.bot.tasks["bridges"][guild_id] = self.bot.loop.create_task(
                self.queue_task(guild_id)
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

    async def destroy(self, guild_id, reason):
        webhooks = self.get_webhook_urls(guild_id)
        async with aiohttp.ClientSession() as session:
            for webhook_url in webhooks:
                webhook = Webhook.from_url(webhook_url, adapter=AsyncWebhookAdapter(session))
                with suppress(NotFound, Forbidden, HTTPException):
                    await webhook.send(reason)
                    await webhook.delete()
        await self.config.remove(guild_id)
        del self.bot.tasks["bridges"][guild_id]

    async def queue_task(self, guild_id):
        await self.bot.wait_until_ready()
        self.queue[guild_id] = asyncio.Queue(maxsize=2)
        webhook_cache = {}
        async with aiohttp.ClientSession() as session:
            while True:
                msg, webhooks = await self.queue[guild_id].get()
                for webhook_url in webhooks:
                    try:
                        if webhook_url not in webhook_cache:
                            webhook = Webhook.from_url(webhook_url, adapter=AsyncWebhookAdapter(session))
                            webhook_cache[webhook_url] = webhook
                        if isinstance(msg, str):
                            await webhook_cache[webhook_url].send(msg)
                        else:
                            await webhook_cache[webhook_url].send(
                                content=msg.content,
                                embeds=msg.embeds if msg.embeds else None,
                                username=msg.author.display_name,
                                avatar_url=msg.author.avatar_url,
                                allowed_mentions=mentions
                            )
                    except (NotFound, Forbidden):
                        if guild_id not in self.config:
                            return
                        if webhook_url == self.config[guild_id]["webhook_url"]:
                            return await self.destroy(guild_id, "Host webhook deleted. Disabling the chatbridge")

                        # Iterate through and remove the unavailable webhook
                        for channel_id, _webhook_url in list(self.config[guild_id]["channels"].items()):
                            if webhook_url == _webhook_url:
                                self.config[guild_id]["channels"] = {
                                    c: w for c, w in self.config[guild_id]["channels"].items()
                                    if c != channel_id
                                }
                                await self.config.flush()

                                # Notify the other webhooks that another was deleted
                                channel = self.bot.get_channel(int(channel_id))
                                if channel:
                                    warning = f"The webhook for {channel.mention} in {channel.guild} was deleted"
                                else:
                                    warning = f"The webhook for {channel_id} was deleted"

                                await self.queue[guild_id].put([warning, self.get_webhook_urls(guild_id)])

                        # Disable the bridge if there's only the host channel
                        if not self.config[guild_id]["channels"]:
                            await self.destroy(guild_id, "Disabled the chatbridge due to the only other channel removing their webhook")

                    except HTTPException as error:
                        await msg.channel.send(f"Error: couldn't send your message to the other channels. {error}")

                await asyncio.sleep(1)

    def get_guild_id(self, channel):
        guild_id = channel.guild.id
        if guild_id not in self.config:
            guild_ids = [
                guild_id for guild_id, config in self.config.items()
                if str(channel.id) in config["channels"]
            ]
            if guild_ids:
                guild_id = guild_ids[0]
        return guild_id

    async def block(self, channel, user):
        self.config[self.get_guild_id(channel)]["blocked"].append(user.id)

    def is_blocked(self, channel, user) -> bool:
        return user.id in self.config[self.get_guild_id(channel)]["blocked"]

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Run anti spam checks and send the message to the queue"""
        if not isinstance(msg.guild, Guild) or msg.guild.id not in self.config:
            return
        if msg.author.discriminator == "0000" or (not msg.content and not msg.embeds):
            return
        blacklist = (
            "Error:",
            "I'm not forwarding that",
            "That's too long for me to forward",
            "That's too many pings"
        )
        if msg.author.bot and any(msg.content.startswith(content) for content in blacklist):
            return
        guild_id = msg.guild.id
        user_id = msg.author.id
        if msg.channel.id != self.config[guild_id]["channel_id"]:
            if str(msg.channel.id) not in self.config[guild_id]["channels"]:
                return
        if self.is_blocked(msg.channel, msg.author):
            return
        if msg.author.id in self.ignored:
            if time() - 60 > self.ignored[msg.author.id]:
                del self.ignored[msg.author.id]
            else:
                return

        # Prevent all caps messages
        abcs = "abcdefghijklmnopqrstuvwxyz"
        if len([c for c in msg.content if c.lower() in abcs]) > 10:
            total_uppercase = len([c for c in msg.content if c == c.upper()])
            div = 100 * total_uppercase / len(msg.content)
            if div >= 75:
                return await msg.channel.send("I'm not forwarding that")

        # Prevent long messages:
        if len(msg.content) > 1000 or "\n\n\n" in msg.content:
            return await msg.channel.send("That's too long for me to forward")
        if len(msg.content) > 50 and msg.content.count(" ") == 0:
            return await msg.channel.send("I'm not forwarding that")

        # Prevent repeating lines
        if msg.content.count("\n") > 3 and all(line == line for line in msg.content.split("\n")):
            return await msg.channel.send("I'm not forwarding that")

        # Prevent repeating sentences
        if any(msg.content.count(sentence) > 1 for sentence in msg.content.split(".") if sentence):
            return await msg.channel.send("I'm not forwarding that")
        if any(msg.content.count(word) > 10 for word in msg.content.split(" ")):
            return await msg.channel.send("I'm not forwarding that")

        # Prevent custom emoji spam
        if msg.content.count(":") > 10:
            return await msg.channel.send("I'm not forwarding that")

        # Prevent random char spam alongside unicode emoji spam
        if len(msg.content) > 5 and not any(c in abcs for c in msg.content):
            return await msg.channel.send("I'm not forwarding that")

        # Prevent sending messages too quickly
        thresholds = [(5, 3), (10, 6)]
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
            if m and m.created_at > datetime.utcnow() - timedelta(seconds=s)
               and sum(len(group) for group in [
                m.mentions, m.raw_mentions, m.role_mentions, m.raw_role_mentions
            ])
        ]
        if len(pongs(10)) > 3:
            await msg.channel.send("That's too many pings, you've been muted from the bridge for 1 minute")
            self.ignored[msg.author.id] = time()
            return

        # Parse what channels to forward to
        webhooks = [
            webhook_url for channel_id, webhook_url in self.config[guild_id]["channels"].items()
            if int(channel_id) != msg.channel.id
        ]
        if msg.channel.id != self.config[guild_id]["channel_id"]:
            webhooks.append(self.config[guild_id]["webhook_url"])

        with suppress(asyncio.QueueFull, KeyError):
            self.queue[guild_id].put_nowait([msg, webhooks])

    @commands.group(name="link", aliases=["chatbridge", "bridge"])
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def link(self, ctx):
        """Start the process to link two channels"""
        if not ctx.invoked_subcommand:
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
                self.waiters[ctx.channel] = [ctx.author.id, time()]
                return await ctx.send(f"Run `.link` in the other channel you wanna link")

            guild_id = channel.guild.id
            if guild_id in self.config and channel.id in self.config[guild_id]["channels"]:
                return await ctx.send("That channel's already linked")
            if guild_id in self.config and len(self.config[guild_id]["channels"]) == 2:
                return await ctx.send("You can only link a max of 3 channels together")
            webhook = None
            if guild_id not in self.config:
                webhook = await channel.create_webhook(name="F8 ChatBridge")
            sub_webhook = await ctx.channel.create_webhook(name="F8 ChatBridge")
            if webhook:
                await webhook.send(f"Successfully linked with {ctx.channel.mention}")
            await sub_webhook.send(
                f"Successfully linked with {channel.mention} in {channel.guild}",
                allowed_mentions=AllowedMentions.all()
            )

            if guild_id in self.config:
                self.config[guild_id]["channels"][str(ctx.channel.id)] = sub_webhook.url
            else:
                self.config[guild_id] = {
                    "channel_id": channel.id,
                    "webhook_url": webhook.url,
                    "channels": {
                        str(ctx.channel.id): sub_webhook.url
                    },
                    "blocked": []
                }
            await self.config.flush()
            self.bot.tasks["bridges"][guild_id] = self.bot.loop.create_task(
                self.queue_task(guild_id)
            )
            if channel in self.waiters:
                del self.waiters[channel]

    @commands.command(name="unlink")
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def unlink(self, ctx):
        """Unlink a channel from a bridge"""
        guild_id = self.get_guild_id(ctx.channel)
        if guild_id not in self.config:
            return await ctx.send("This channel isn't linked")
        if ctx.channel.id == self.config[guild_id]["channel_id"]:
            await ctx.send(f"Unlinked from {self.bot.get_guild(int(guild_id))}")
            return await self.destroy(guild_id, "Host disabled the chatbridge")

        # Remove the webhook if we can
        with suppress(NotFound, Forbidden, HTTPException):
            webhooks = await ctx.channel.webhooks()
            for webhook in webhooks:
                if webhook.url == self.config[guild_id]["channels"][str(ctx.channel.id)]:
                    await webhook.delete()
                    break

        # Remove the channel_id from the hosts linked channels
        self.config[guild_id]["channels"] = {
            c: w for c, w in self.config[guild_id]["channels"].items()
            if c != str(ctx.channel.id)
        }
        await self.config.flush()

        # If the host has no linked channels disable the whole thing
        if not self.config[guild_id]["channels"]:
            await ctx.send(f"Unlinked from {self.bot.get_guild(guild_id)}")
            return await self.destroy(
                guild_id,
                "Disabled the chatbridge due to the only other channel removing their webhook"
            )

        await ctx.send(f"Unlinked from {self.bot.get_guild(guild_id)}")

    @link.command(name="block")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _block(self, ctx, *users):
        guild_id = self.get_guild_id(ctx.channel)
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

    @link.command(name="unblock")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _unblock(self, ctx, *, user):
        guild_id = self.get_guild_id(ctx.channel)
        if guild_id not in self.config:
            return await ctx.send("This channel isn't linked")
        user = await self.bot.utils.get_user(ctx, user)
        if user.id not in self.config[guild_id]["blocked"]:
            return await ctx.send(f"{user} isn't blocked")
        self.config[guild_id]["blocked"].remove(user.id)
        await self.config.flush()
        await ctx.send(f"Unblocked {user}")


def setup(bot):
    bot.add_cog(ChatBridges(bot))
