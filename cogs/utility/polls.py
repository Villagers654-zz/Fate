"""
cogs.utility.polls
~~~~~~~~~~~~~~~~~~~

Create un-mod-abusable polls for users. This cog prevents mods
from deleting reactions to alter the outcome of a poll

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from datetime import datetime, timedelta, timezone
import json
import asyncio
from contextlib import suppress
import re

from discord.ext import commands
import discord
from discord import TextChannel
from discord.errors import NotFound, Forbidden
from base64 import b64encode as encode64, b64decode as decode64

from fate import Fate
from botutils import colors, extract_time, Conversation


def Timer(argument):
    seconds = extract_time(argument)
    if not seconds:
        raise commands.BadArgument
    return seconds


class SafePolls(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.polls = []
        if bot.is_ready():
            bot.loop.create_task(self.cache_msg_ids())
        if "polls" not in self.bot.tasks:
            self.bot.tasks["polls"] = {}
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        self.cache = {}
        self.cd = bot.utils.cooldown_manager(1, 3)

        self.poll_usage = "> Usage: `.poll should we do X or Y?`\n" \
                          "Creates a poll that's safe from reactions being manipulated. " \
                          "Note that when you add a reaction you can only change what you react to, and can't remove it."

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cache_msg_ids()
        async with self.bot.utils.cursor() as cur:
            await cur.execute("select channel_id, msg_id, end_time from polls;")
            results = await cur.fetchall()
        for group in results:
            if group[1] not in self.bot.tasks["polls"]:
                task = self.bot.loop.create_task(self.wait_for_termination(*group))
                self.bot.tasks["polls"][group[1]] = task

    async def cache_msg_ids(self) -> None:
        async with self.bot.utils.cursor() as cur:
            await cur.execute("select msg_id from polls;")
            results = await cur.fetchall()
        self.polls = list(set(self.polls + [r[0] for r in results]))

    async def cache_poll(self, message_id) -> None:
        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select channel_id, user_id, question, votes "
                f"from polls "
                f"where msg_id = {message_id} "
                f"limit 1;"
            )
            results = await cur.fetchone()
        channel_id, user_id, question, votes = results
        self.cache[message_id] = {
            "channel_id": channel_id,
            "user_id": user_id,
            "question": decode64(question.encode()).decode(),
            "votes": json.loads(decode64(votes.encode()).decode()),
        }

    async def update_poll(self, msg_id: int) -> None:
        if msg_id not in self.cache:
            await self.cache_poll(msg_id)
        payload = self.cache[msg_id]

        channel = self.bot.get_channel(payload["channel_id"])
        msg = await channel.fetch_message(msg_id)
        user = await self.bot.fetch_user(payload["user_id"])
        question = payload["question"]
        votes = payload["votes"]
        emojis = votes.keys()

        e = discord.Embed(color=colors.fate)
        e.set_author(name=f"Poll by {user}", icon_url=user.avatar.url if user else None)
        fmt = " | ".join(f"{emoji} {len(votes[emoji])}" for emoji in emojis)
        if any(key not in self.emojis and len(key) > 3 for key in votes.keys()):
            question += f"\n\n{fmt}"
        else:
            e.set_footer(text=fmt)
        e.description = question
        await msg.edit(embed=e)

    async def wait_for_termination(self, channel_id, msg_id, end_time: str) -> None:
        """Sleep until the timer ends and close the poll"""

        async def delete(msg_id) -> None:
            print("Deleting")
            async with self.bot.utils.cursor() as cur:
                await cur.execute(f"delete from polls where msg_id = {msg_id} limit 1;")
            if msg_id in self.polls:
                self.polls.remove(msg_id)
            if msg_id in self.cache:
                del self.cache[msg_id]

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return await delete(msg_id)

        try:
            msg = await channel.fetch_message(msg_id)
        except discord.errors.NotFound:
            return await delete(msg_id)

        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S.%f%z")
        if datetime.now() > end_time:
            with suppress(Forbidden, NotFound):
                await msg.edit(content="Poll Ended")
                await msg.clear_reactions()
            return await delete(msg_id)

        seconds = round((datetime.now() - end_time).seconds)
        await asyncio.sleep(seconds)
        with suppress(Forbidden, NotFound):
            await msg.edit(content="Poll Ended")
            await msg.clear_reactions()
        await delete(msg_id)

    async def ensure_permissions(self, ctx, channel, exit_on_error=True):
        if not channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send("I'm missing perms to send messages in there, you can fix and retry")
        elif not channel.permissions_for(ctx.guild.me).embed_links:
            await ctx.send("I'm missing perms to send embeds there, you can fix and retry")
        elif not channel.permissions_for(ctx.guild.me).add_reactions:
            await ctx.send("I'm missing perms to add reactions there, you can fix and retry")
        elif not channel.permissions_for(ctx.author).send_messages:
            await ctx.send("You can't send in that channel, please select another")
        elif self.bot.attrs.is_restricted(channel, ctx.author):
            await ctx.send("Due to channel restrictions you can't send in that channel")
        else:
            return True
        if exit_on_error:
            raise self.bot.ignored_exit
        return False

    @staticmethod
    def instant_poll_usage() -> str:
        return "Creates a poll in one message. This does require precise formatting.\n"\
               "> Examples:\n"\
               "```.instant-poll #polls 1h\n"\
               "👍 do something\n"\
               "👎 don't do something\n"\
               "✌ do something else```\n"\
               "> An alternative to override the emojis\n"\
               "```.instant-poll #polls 1h\n"\
               "👍 do something\n"\
               "👎 don't do something\n"\
               "✌ do something else|🏆⏳🔨```You can also set the override emojis as a range of numbers like 1-3"

    @commands.command(name="instant-poll")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.cooldown(2, 10, commands.BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    async def instant_poll(self, ctx, channel: TextChannel = None, timer: Timer = None, *, data = None):
        if not channel or not timer or not data:
            return await ctx.send(self.instant_poll_usage())
        await self.ensure_permissions(ctx, channel)

        converter = commands.EmojiConverter()
        sections = data.split("|")
        emojis = []
        if len(sections) > 1:
            args = sections[-1:][0]

            # Set the emojis as numbers
            if args.isdigit():
                emojis = [self.emojis[int(char) - 1] for char in args]

            # Set the emojis as a range of numbers
            elif xrange := re.search("[0-9]-[0-9]", args):
                min, max = xrange.group().split("-")
                if int(min) > int(max):
                    return await ctx.send("Min number for the emojis cannot be greater than the max number")
                if int(min) < 1:
                    return await ctx.send("Min number can't be below 1")
                max = len(self.emojis) - int(max)
                if max > 9:
                    return await ctx.send("Max number can't be greater than 9")
                emojis = self.emojis[int(min) - 1:-max]

            # Set the emojis as custom emojis
            elif " " in args:
                for chars in args.split():
                    if len(chars) < 4:
                        try:
                            await ctx.message.add_reaction(chars)
                        except:
                            return await ctx.send(f"Couldn't convert `{chars}` to an emoji")
                        await ctx.message.remove_reaction(chars, self.bot.user)
                        emojis.append(chars)
                    else:
                        try:
                            emoji = await converter.convert(ctx, chars)
                        except commands.BadArgument:
                            return await ctx.send(f"Couldn't convert `{chars}` to an emoji")
                        emojis.append(str(emoji))
            else:
                return await ctx.send("You need to separate the emojis with spaces")
            data = data.rstrip("|" + args)

        # Automatically detect the emojis
        else:
            for line in data.split("\n"):
                await asyncio.sleep(0)
                if not line:
                    continue
                if line[:0].isdigit():
                    emojis.append(self.emojis[int(line[:0]) - 1])
                elif match := re.search("[1-9]\.? ", line):
                    num = match.group().rstrip().rstrip(".")
                    emojis.append(self.emojis[int(num) - 1])
                elif " " in line:
                    chars = line.split()[0]
                    if len(chars) < 4:
                        try:
                            await ctx.message.add_reaction(chars)
                        except:
                            continue
                        await ctx.message.remove_reaction(chars, self.bot.user)
                        emojis.append(chars)
                    else:
                        try:
                            emoji = await converter.convert(ctx, chars)
                        except commands.BadArgument:
                            continue
                        emojis.append(str(emoji))

        if not emojis:
            return await ctx.send("Invalid format")

        # Format and send the poll
        poll_msg = await channel.send("Creating poll")
        self.polls.append(poll_msg.id)

        async def add_reactions_task(message) -> None:
            """Add the reactions in the background"""
            for emoji in emojis:
                if not message:
                    return
                try:
                    await message.add_reaction(emoji)
                except discord.errors.NotFound:
                    raise self.bot.ignored_exit
                if len(emojis) > 5:
                    await asyncio.sleep(1)
                elif len(emojis) > 2:
                    await asyncio.sleep(0.5)

        self.bot.loop.create_task(add_reactions_task(poll_msg))

        question = encode64(data.encode()).decode()
        vote_index = encode64(json.dumps({e: [] for e in emojis}).encode()).decode()
        end_time = str(datetime.now() + timedelta(seconds=timer))

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"insert into polls "
                f"values ("
                f"{channel.id}, "  # channel_id: int
                f"{ctx.author.id}, "  # user_id: int
                f"'{question}', "  # question: str
                f"{poll_msg.id}, "  # msg_id: int
                f"0, "  # reaction_count: int
                f"'{end_time}', "  # end_time: str
                f"'{vote_index}'"  # votes: str
                f");"
            )

        await self.update_poll(poll_msg.id)
        self.bot.tasks["polls"][poll_msg.id] = self.bot.loop.create_task(
            self.wait_for_termination(channel.id, poll_msg.id, end_time)
        )
        await poll_msg.edit(content=None)
        await ctx.send("Setup your poll", delete_after=3)
        with suppress(Exception):
            await ctx.message.delete()

    @commands.command(
        name="poll", aliases=["safepoll", "safe_poll", "createpoll", "create-poll"]
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def safe_poll(self, ctx, *, question):
        """Start the setup process for creating a poll"""
        convo = Conversation(ctx, delete_after=True)
        # Get the wanted duration of the poll (Max 30 days)

        timer = None
        instructions = "the `m` in `5m` stands for 5 minutes, the `h` stands for hours, and the `d` stands for days"
        while not timer:
            msg = await convo.ask("How long should the poll last? (in the format of 5m, 1h, 7d, etc)")
            result = extract_time(msg.content)
            if not result:
                await convo.send(f"Couldn't find any timers in that, remember {instructions}. Please retry")
                continue
            elif result > 60 * 60 * 24 * 30:  # 30 Days
                await convo.send("You can't pick a time greater than 30 days, please retry")
            else:
                timer = result

        # Get the wanted amount of reactions to add for users to vote with
        reaction_count = None
        while not reaction_count:
            msg = await convo.ask("How many reactions should I add?")
            if not msg.content.isdigit():
                await convo.send("That's not a number, please retry")
            elif int(msg.content) > 9:
                await convo.send("You can't choose a reaction count greater than 9")
            else:
                reaction_count = int(msg.content)

        emojis = self.emojis[:reaction_count]
        if reaction_count == 2:
            reply = await convo.ask("Do you want me to use thumbs up/down reactions instead of numbers?")
            if "yes" in reply.content.lower():
                emojis = ["👍", "👎"]

        # Get the channel to put the poll message in
        channel = None
        while not channel:
            msg = await convo.ask("#mention the channel to send the poll into")
            if not msg.channel_mentions:
                await convo.send(f"Retry, but mention the channel like this: {ctx.channel.mention}")
                continue
            if await self.ensure_permissions(ctx, msg.channel_mentions[0], exit_on_error=False):
                channel = msg.channel_mentions[0]

        # Format and send the poll
        poll_msg = await channel.send("Creating poll")
        self.polls.append(poll_msg.id)

        async def add_reactions_task(message) -> None:
            """Add the reactions in the background"""
            for emoji in emojis:
                if not message:
                    return
                try:
                    await message.add_reaction(emoji)
                except discord.errors.NotFound:
                    return
                if reaction_count > 5:
                    await asyncio.sleep(1)
                elif reaction_count > 2:
                    await asyncio.sleep(0.5)

        self.bot.loop.create_task(add_reactions_task(poll_msg))

        question = encode64(question.encode()).decode()
        vote_index = encode64(json.dumps({e: [] for e in emojis}).encode()).decode()
        end_time = str(datetime.now() + timedelta(seconds=timer))

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"insert into polls "
                f"values ("
                f"{channel.id}, "  # channel_id: int
                f"{ctx.author.id}, "  # user_id: int
                f"'{question}', "  # question: str
                f"{poll_msg.id}, "  # msg_id: int
                f"{reaction_count}, "  # reaction_count: int
                f"'{end_time}', "  # end_time: str
                f"'{vote_index}'"  # votes: str
                f");"
            )

        await self.update_poll(poll_msg.id)
        self.bot.tasks["polls"][poll_msg.id] = self.bot.loop.create_task(
            self.wait_for_termination(channel.id, poll_msg.id, end_time)
        )
        await poll_msg.edit(content=None)
        await convo.end()
        await ctx.send("Successfully setup your poll")

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if msg.id in self.polls:
            self.polls.remove(msg.id)
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"delete from polls where msg_id = {msg.id};")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        msg_id = payload.message_id
        if payload.message_id in self.polls and not self.cd.check(payload.user_id):
            user = self.bot.get_user(payload.user_id)
            if user.bot:
                return
            if msg_id not in self.cache:
                await self.cache_poll(payload.message_id)
            if str(payload.emoji) not in self.cache[msg_id]["votes"]:
                return
            for key, users in self.cache[msg_id]["votes"].items():
                await asyncio.sleep(0)
                if payload.user_id in users:
                    if key == str(payload.emoji):
                        return
                    self.cache[msg_id]["votes"][key].remove(payload.user_id)
            self.cache[msg_id]["votes"][str(payload.emoji)].append(payload.user_id)

            await self.update_poll(payload.message_id)

            # Dump changes to sql
            vote_index = encode64(
                json.dumps(self.cache[msg_id]["votes"]).encode()
            ).decode()
            async with self.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"update polls "
                        f"set votes = '{vote_index}' "
                        f"where msg_id = {payload.message_id};"
                    )


def setup(bot: Fate):
    bot.add_cog(SafePolls(bot), override=True)
