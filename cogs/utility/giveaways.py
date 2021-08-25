# Giveaway cog for random handouts

from os import path
import json
import asyncio
from datetime import datetime, timezone, timedelta
import re
import random
from contextlib import suppress

from discord.ext import commands
import discord
from discord.errors import NotFound, Forbidden

from botutils import colors, extract_time, get_time, Conversation


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/giveaways.json"
        self.data = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.data = json.load(f)  # type: dict

    async def save_data(self):
        async with self.bot.utils.open(self.path, "w+") as f:
            await f.write(json.dumps(self.data))

    async def make_embed(self, dat):
        e = discord.Embed(color=colors.fate)
        user = await self.bot.fetch_user(dat["user"])
        e.set_author(name=f"Giveaway by {user}", icon_url=user.display_avatar.url)
        e.description = dat["giveaway"]
        _end_time = datetime.strptime(dat["end_time"], "%Y-%m-%d %H:%M:%S.%f")
        end_time = get_time((_end_time - datetime.now()).seconds)
        if datetime.now() >= _end_time:
            e.set_footer(text=f"Giveaway Ended")
        else:
            end_time = re.sub("\.[0-9]*", "", end_time)
            e.set_footer(text=f"Winners({dat['winners']}) | Ends in {end_time}")
        return e

    async def run_giveaway(self, guild_id, giveaway_id):
        dat = self.data[guild_id][giveaway_id]
        channel = await self.bot.fetch_channel(dat["channel"])
        try:
            message = await channel.fetch_message(dat["message"])
        except (NotFound, Forbidden):
            del self.data[guild_id][giveaway_id]
            return await self.save_data()
        end_time = datetime.strptime(dat["end_time"], "%Y-%m-%d %H:%M:%S.%f")

        # Wait for the giveaway timer to end
        while datetime.now() < end_time:
            await asyncio.sleep(30)
            try:
                await message.edit(embed=await self.make_embed(dat))
            except (NotFound, Forbidden):
                del self.data[guild_id][giveaway_id]
                return await self.save_data()

        for _ in range(3):
            try:
                await message.edit(content="Giveaway complete")
                message = await channel.fetch_message(dat["message"])
                for reaction in message.reactions:
                    if str(reaction.emoji) == "🎉":
                        reaction = reaction
                        break
                else:
                    break
                users = await reaction.users().flatten()
                users = [user for user in users if not user.bot]
                if not users:
                    await channel.send("There are no winners :[")
                    break
                else:
                    random.shuffle(users)
                    winners = []
                    winner_count = dat["winners"]
                    if dat["winners"] > len(users):
                        winner_count = len(users)
                    for i in range(winner_count):
                        winners.append(users[i])
                    if len(winners) == 1:
                        await channel.send(
                            f"Congratulations {winners[0].mention}, you won the giveaway for {dat['giveaway']}",
                            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                        )
                    else:
                        with suppress(Forbidden):
                            await channel.send(
                                f"Congratulations {', '.join([w.mention for w in winners])}, you won the giveaway for {dat['giveaway']}",
                                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                            )
                    break
            except (NotFound, Forbidden):
                break
            except discord.errors.HTTPException:
                await asyncio.sleep(25)
                continue

        del self.data[guild_id][giveaway_id]
        if not self.data[guild_id]:
            del self.data[guild_id]
        await self.save_data()
        task_id = f"giveaway-{guild_id}-{giveaway_id}"
        if task_id in self.bot.tasks["giveaways"]:
            del self.bot.tasks["giveaways"][task_id]

    @commands.Cog.listener("on_ready")
    async def resume_tasks(self):
        if "giveaways" not in self.bot.tasks:
            self.bot.tasks["giveaways"] = {}
        for guild_id, giveaways in self.data.items():
            for giveaway_id in giveaways.keys():
                task_id = f"giveaway-{guild_id}-{giveaway_id}"
                if (
                    task_id not in self.bot.tasks["giveaways"]
                    or self.bot.tasks["giveaways"][task_id].done()
                ):
                    task = self.bot.loop.create_task(
                        self.run_giveaway(guild_id, giveaway_id)
                    )
                    self.bot.tasks["giveaways"][task_id] = task

    @commands.command(name="giveaway", aliases=["giveaways"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    async def giveaway(self, ctx):
        """ Work with the author in setting up a giveaway """
        guild_id = str(ctx.guild.id)

        # Giveaway timer
        usage = (
            "\nReply in the format of `1d6h9m`"
            "\n`d` represents days, `h` represents hours, `m` represents minutes"
        )
        convo = Conversation(ctx, delete_after=True)

        for i in range(5):
            reply = await convo.ask("How long should the giveaway last" + usage)
            timer = extract_time(reply.content)
            if not timer or not isinstance(timer, int):
                await convo.send("That's not in the proper format, retry or send `cancel`")
                continue
            if timer > 60 * 60 * 24 * 60:
                await convo.send("Hell. Fucking. No.\nI'm not waiting that long. Send a smaller timer")
                continue
            await convo.send(
                f"Alright, set the timer to {get_time(timer)}", delete_after=10
            )
            break
        else:
            return

        # Giveaway information
        reply = await convo.ask("Send a description of what you're giving out")
        giveaway = reply.content

        # Winner count
        for i in range(5):
            reply = await convo.ask("How many winners should there be. Reply in number form")
            if reply.content.isdigit():
                winners = int(reply.content)
                break
            await convo.send("That isn't a number, please retry")
        else:
            return

        # Giveaway channel
        for i in range(5):
            reply = await convo.ask(f"#Mention the channel I should use in {ctx.channel.mention} format")
            if not reply.channel_mentions:
                await convo.send(
                    f"That isn't a channel mention, make sure it's in the {ctx.channel.mention} format"
                )
                continue
            channel = reply.channel_mentions[0]
            break
        else:
            return

        await convo.end()

        # Save giveaway info
        dat = {
            "end_time": str(datetime.now() + timedelta(seconds=timer)),
            "user": ctx.author.id,
            "giveaway": giveaway,
            "winners": winners,
            "channel": channel.id,
        }
        message = await channel.send(embed=await self.make_embed(dat))

        if guild_id not in self.data:
            self.data[guild_id] = {}
        key = random.randint(0, 10000)
        while key in self.data[guild_id]:
            key = random.randint(0, 10000)
        self.data[guild_id][key] = {**dat, "message": message.id}
        await self.save_data()

        task_id = f"giveaway-{guild_id}-{key}"
        task = self.bot.loop.create_task(self.run_giveaway(guild_id, key))
        if "giveaways" not in self.bot.tasks:
            self.bot.tasks["giveaways"] = {}
        self.bot.tasks["giveaways"][task_id] = task

        await ctx.send("Started your giveaway")
        await message.add_reaction("🎉")


def setup(bot):
    bot.add_cog(Giveaways(bot), override=True)
