from time import time
import json
import asyncio
from contextlib import suppress

from discord.ext import commands
import discord
from discord.errors import NotFound, Forbidden
from base64 import b64encode as encode64, b64decode as decode64

from fate import Fate
from utils import colors


class SafeSuggestion(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.Suggestion = []
        if bot.is_ready():
            bot.loop.create_task(self.cache_msg_ids())
        if "Suggestion" not in self.bot.tasks:
            self.bot.tasks["Suggestion"] = {}
        self.emojis = ["🔼", "🔽"]
        self.cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cache_msg_ids()
        async with self.bot.cursor() as cur:
            await cur.execute("select channel_id, msg_id, end_time from Suggestion;")
            results = await cur.fetchall()
        for group in results:
            if group[1] not in self.bot.tasks["Suggestion"]:
                task = self.bot.loop.create_task(self.wait_for_termination(*group))
                self.bot.tasks["Suggestion"][group[1]] = task

    async def cache_msg_ids(self) -> None:
        async with self.bot.cursor() as cur:
            await cur.execute("select msg_id from Suggestion;")
            results = await cur.fetchall()
        self.Suggestion = list(set(self.Suggestion + [r[0] for r in results]))

    async def cache_Suggestion(self, message_id) -> None:
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select channel_id, user_id, Suggestion, votes "
                f"from Suggestion "
                f"where msg_id = {message_id} "
                f"limit 1;"
            )
            results = await cur.fetchone()
        channel_id, user_id, Suggestion, votes = results
        self.cache[message_id] = {
            "channel_id": channel_id,
            "user_id": user_id,
            "Suggestion": decode64(Suggestion.encode()).decode(),
            "votes": json.loads(decode64(votes.encode()).decode()),
        }

    async def update_Suggestion(self, msg_id: int) -> None:
        if msg_id not in self.cache:
            await self.cache_Suggestion(msg_id)
        payload = self.cache[msg_id]

        channel = self.bot.get_channel(payload["channel_id"])
        msg = await channel.fetch_message(msg_id)
        user = await self.bot.fetch_user(payload["user_id"])
        Suggestion = payload["Suggestion"]
        votes = payload["votes"]
        emojis = votes.keys()

        e = discord.Embed(color=colors.fate())
        e.set_author(name=f"Suggestion by {user}", icon_url=user.avatar_url if user else None)
        e.description = Suggestion
        e.set_footer(
            text=" | ".join(f"{emoji} {len(votes[emoji])}" for emoji in emojis)
        )
        await msg.edit(embed=e)

    async def wait_for_termination(self, channel_id, msg_id, end_time: float) -> None:
        """Sleep until the timer ends and close the Suggestion"""

        async def delete(msg_id) -> None:
            async with self.bot.cursor() as cur:
                await cur.execute(f"delete from Suggestion where msg_id = {msg_id} limit 1;")
            if msg_id in self.Suggestion:
                self.Suggestion.remove(msg_id)
            if msg_id in self.cache:
                del self.cache[msg_id]

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return await delete(msg_id)

        try:
            msg = await channel.fetch_message(msg_id)
        except discord.errors.NotFound:
            return await delete(msg_id)

        if time() > end_time:
            with suppress(Forbidden, NotFound):
                await msg.edit(content="Suggestion Ended")
                await msg.clear_reactions()
            return await delete(msg_id)

        await asyncio.sleep(end_time - time())
        with suppress(Forbidden, NotFound):
            await msg.edit(content="Suggestion Ended")
            await msg.clear_reactions()
        await delete(msg_id)

    @commands.command(
        name="Suggestion", aliases=["safeSuggestion", "safe_Suggestion", "createSuggestion", "create-Suggestion"]
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def safe_Suggestion(self, ctx, *, Suggestion):
        """Start the setup process for creating a Suggestion"""

        # Get the wanted duration of the Suggestion (Max 30 days)
        message = await ctx.send(
            "How long should the Suggestion last? (in the format of 5m, 1h, 7d, etc)"
        )
        timer = None
        instructions = "the `m` in `5m` stands for 5 minutes, the `h` stands for hours, and the `d` stands for days"
        while not timer:
            async with self.bot.require("message", ctx, handle_timeout=True) as msg:
                result = self.bot.utils.extract_timer(msg.content)
                if not result:
                    await ctx.send(
                        f"Couldn't find any timers in that, remember {instructions}. Please retry",
                        delete_after=30,
                    )
                elif result[0] > 60 * 60 * 24 * 30:  # 30 Days
                    await ctx.send(
                        "You can't pick a time greater than 30 days, please retry",
                        delete_after=16,
                    )
                else:
                    timer = result[0]
                await msg.delete()

        await message.delete()

        # Get the wanted amount of reactions to add for users to vote with
        message = await ctx.send(
            "How many reactions should I add?"
        )
        reaction_count = None
        while not reaction_count:
            async with self.bot.require("message", ctx, handle_timeout=True) as msg:
                if not msg.content.isdigit():
                    await ctx.send("That's not a number, please retry", delete_after=30)
                elif int(msg.content) > 9:
                    await ctx.send(
                        "You can't choose a reaction count greater than 9",
                        delete_after=16,
                    )
                else:
                    reaction_count = int(msg.content)
                await msg.delete()
        await message.delete()

        # Get the channel to put the Suggestion message in
        message = await ctx.send("#mention the channel to send the Suggestion into")
        channel = None
        while not channel:
            async with self.bot.require("message", ctx, handle_timeout=True) as msg:
                if not msg.channel_mentions:
                    await ctx.send(
                        f"Retry, but mention the channel like this: {ctx.channel.mention}",
                        delete_after=16,
                    )
                elif (
                    not msg.channel_mentions[0]
                    .permissions_for(ctx.guild.me)
                    .send_messages
                ):
                    await ctx.send(
                        "I'm missing perms to send messages in there, you can fix and retry",
                        delete_after=16,
                    )
                elif (
                    not msg.channel_mentions[0]
                    .permissions_for(ctx.guild.me)
                    .embed_links
                ):
                    await ctx.send(
                        "I'm missing perms to send embeds there, you can fix and retry",
                        delete_after=16,
                    )
                elif (
                    not msg.channel_mentions[0]
                    .permissions_for(ctx.guild.me)
                    .add_reactions
                ):
                    await ctx.send(
                        "I'm missing perms to add reactions there, you can fix and retry",
                        delete_after=16,
                    )
                else:
                    if (
                        msg.channel_mentions[0]
                        .permissions_for(ctx.author)
                        .send_messages
                    ):
                        channel = msg.channel_mentions[0]
                    else:
                        await ctx.send(
                            "You can't send in that channel, please select another",
                            delete_after=16,
                        )
                await msg.delete()
        await message.delete()

        # Format and send the Suggestion
        Suggestion_msg = await channel.send("Creating Suggestion")
        self.Suggestion.append(Suggestion_msg.id)

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

        emojis = self.emojis[:reaction_count]
        self.bot.loop.create_task(add_reactions_task(Suggestion_msg))

        Suggestion = encode64(Suggestion.encode()).decode()
        vote_index = encode64(json.dumps({e: [] for e in emojis}).encode()).decode()
        end_time = time() + timer

        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into Suggestion "
                f"values ("
                f"{channel.id}, "  # channel_id: int
                f"{ctx.author.id}, "  # user_id: int
                f"'{Suggestion}', "  # Suggestion: str
                f"{Suggestion_msg.id}, "  # msg_id: int
                f"{reaction_count}, "  # reaction_count: int
                f"{end_time}, "  # end_time: bool
                f"'{vote_index}'"  # votes: str
                f");"
            )

        await self.update_Suggestion(Suggestion_msg.id)
        self.bot.tasks["Suggestion"][Suggestion_msg.id] = self.bot.loop.create_task(
            self.wait_for_termination(channel.id, Suggestion_msg.id, end_time)
        )
        await Suggestion_msg.edit(content=None)
        await ctx.send("Successfully setup your Suggestion")

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if msg.id in self.Suggestion:
            self.Suggestion.remove(msg.id)
        async with self.bot.cursor() as cur:
            await cur.execute(f"delete from Suggestion where msg_id = {msg.id};")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.Suggestion:
            user = self.bot.get_user(payload.user_id)
            if user.bot:
                return
            msg_id = payload.message_id
            if msg_id not in self.cache:
                await self.cache_Suggestion(payload.message_id)
            for key, users in self.cache[msg_id]["votes"].items():
                if payload.user_id in users:
                    if key == str(payload.emoji):
                        return
                    self.cache[msg_id]["votes"][key].remove(payload.user_id)
            self.cache[msg_id]["votes"][str(payload.emoji)].append(payload.user_id)

            await self.update_Suggestion(payload.message_id)
            channel = self.bot.get_channel(payload.channel_id)
            try:
                msg = await channel.fetch_message(payload.message_id)
            except NotFound:
                return
            await msg.remove_reaction(payload.emoji, user)

            # Dump changes to sql
            vote_index = encode64(
                json.dumps(self.cache[msg_id]["votes"]).encode()
            ).decode()
            async with self.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"update Suggestion "
                        f"set votes = '{vote_index}' "
                        f"where msg_id = {payload.message_id};"
                    )


def setup(bot: Fate):
    bot.add_cog(SafeSuggestion(bot))
