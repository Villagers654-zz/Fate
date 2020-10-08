# Giveaway cog for random handouts

from os import path
import json
import asyncio
from time import time as timestamp
import re
import random

from discord.ext import commands
import discord

from utils import colors


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/giveaways.json"
        self.data = {}
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.data = json.load(f)  # type: dict

    async def save_data(self):
        async with self.bot.open(self.path, "w+") as f:
            await f.write(json.dumps(self.data))

    async def make_embed(self, dat):
        e = discord.Embed(color=colors.fate())
        user = await self.bot.fetch_user(dat['user'])
        e.set_author(name=f"Giveaway by {user}", icon_url=user.avatar_url)
        e.description = dat["giveaway"]
        end_time = self.bot.utils.get_time(dat["end_time"] - timestamp())
        if timestamp() >= dat['end_time']:
            e.set_footer(text=f"Giveaway Ended")
        else:
            end_time = re.sub('\.[0-9]*', '', end_time)
            e.set_footer(text=f"Winners({dat['winners']}) | Ends in {end_time}")
        return e

    async def run_giveaway(self, guild_id, giveaway_id):
        dat = self.data[guild_id][giveaway_id]
        channel = await self.bot.fetch_channel(dat['channel'])
        try:
            message = await channel.fetch_message(dat['message'])
        except discord.errors.NotFound:
            del self.data[guild_id][giveaway_id]
            return await self.save_data()
        while timestamp() < dat['end_time']:
            await asyncio.sleep(30)
            await message.edit(embed=await self.make_embed(dat))
        await message.edit(content="Giveaway complete")
        message = await channel.fetch_message(dat['message'])
        for reaction in message.reactions:
            if str(reaction.emoji) == "🎉":
                users = await reaction.users().flatten()
                users = [user for user in users if not user.bot]
                if not users:
                    await channel.send("There are no winners :[")
                else:
                    random.shuffle(users)
                    winners = []
                    for i in range(dat["winners"]):
                        winners.append(users[i])
                    if len(winners) == 1:
                        await channel.send(f"Congratulations {winners[0].mention}, you won the giveaway for {dat['giveaway']}")
                    else:
                        await channel.send(f"Congratulations {', '.join([w.mention for w in winners])}, you won the giveaway for {dat['giveaway']}")
                break
        del self.data[guild_id][giveaway_id]
        if not self.data[guild_id]:
            del self.data[guild_id]
        await self.save_data()
        task_id = f"giveaway-{guild_id}-{giveaway_id}"
        if task_id in self.bot.tasks["giveaways"]:
            del self.bot.tasks["giveaways"][task_id]

    @commands.Cog.listener('on_ready')
    async def resume_tasks(self):
        if "giveaways" not in self.bot.tasks:
            self.bot.tasks["giveaways"] = {}
        for guild_id, giveaways in self.data.items():
            for giveaway_id in giveaways.keys():
                task_id = f"giveaway-{guild_id}-{giveaway_id}"
                if task_id not in self.bot.tasks["giveaways"] or self.bot.tasks["giveaways"][task_id].done():
                    task = self.bot.loop.create_task(self.run_giveaway(guild_id, giveaway_id))
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
        usage = "\nReply in the format of `1d6h9m`" \
                "\n`d` represents days, `h` represents hours, `m` represents minutes"
        message = await ctx.send("How long should the giveaway last"+usage)
        for i in range(5):
            async with self.bot.require("message", ctx) as msg:
                timers = []
                for timer in [re.findall('[0-9]+[smhd]', arg) for arg in msg.content.split()]:
                    timers = [*timers, *timer]
                if not timers:
                    await ctx.send(usage)
                    continue
                time_to_sleep = [0, []]
                for timer in timers:
                    raw = ''.join(x for x in list(timer) if x.isdigit())
                    if 'd' in timer:
                        time = int(timer.replace('d', '')) * 60 * 60 * 24
                        _repr = 'day'
                    elif 'h' in timer:
                        time = int(timer.replace('h', '')) * 60 * 60
                        _repr = 'hour'
                    elif 'm' in timer:
                        time = int(timer.replace('m', '')) * 60
                        _repr = 'minute'
                    else:  # 's' in timer
                        time = int(timer.replace('s', ''))
                        _repr = 'second'
                    time_to_sleep[0] += time
                    time_to_sleep[1].append(f"{raw} {_repr if raw == '1' else _repr + 's'}")
                timer, expanded_timer = time_to_sleep
                expanded_timer = ', '.join(expanded_timer)
                await ctx.send(f"Alright, set the timer to {expanded_timer}", delete_after=10)
                await message.delete()
                await msg.delete()
                attempts = 0
                break
        else:
            return await ctx.send('oop')

        # Giveaway information
        message = await ctx.send("Send a description of what you're giving out")
        async with self.bot.require("message", ctx) as msg:
            msg = await ctx.channel.fetch_message(msg.id)
            giveaway = msg.content
            await message.delete()
            await msg.delete()

        # Winner count
        message = await ctx.send("How many winners should there be. Reply in number form")
        for i in range(5):
            attempts += 1
            async with self.bot.require("message", ctx) as msg:
                if not msg.content.isdigit():
                    await message.delete()
                    message = await ctx.send("That isn't a number, please retry")
                    await msg.delete()
                    continue
                winners = int(msg.content)
                await message.delete()
                await msg.delete()
                break
        else:
            return

        # Giveaway channel
        message = await ctx.send(f"#Mention the channel I should use in {ctx.channel.mention} format")
        for i in range(5):
            async with self.bot.require("message", ctx) as msg:
                if not msg.channel_mentions:
                    await message.delete()
                    message = await ctx.send(f"That isn't a channel mention, make sure it's in the {ctx.channel.mention} format")
                    await msg.delete()
                    continue
                channel = msg.channel_mentions[0]
                await message.delete()
                await msg.delete()
                break
        else:
            return

        # Save giveaway info
        dat = {
            "end_time": timestamp() + timer,
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
        self.data[guild_id][key] = {
            **dat, "message": message.id
        }
        await self.save_data()
        task_id = f"giveaway-{guild_id}-{key}"
        task = self.bot.loop.create_task(self.run_giveaway(guild_id, key))
        if "giveaways" not in self.bot.tasks:
            self.bot.tasks["giveaways"] = {}
        self.bot.tasks["giveaways"][task_id] = task
        await ctx.send("Started your giveaway")
        await message.add_reaction("🎉")


def setup(bot):
    bot.add_cog(Giveaways(bot))
