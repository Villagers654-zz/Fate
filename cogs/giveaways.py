# Giveaway cog for random handouts

from os import path
import json
import asyncio
from time import time as timestamp
import re
import random

from discord.ext import commands
import discord
import aiofiles

from utils import colors, utils


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/giveaways.json"
        self.data = {}
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.data = json.load(f)  # type: dict

    async def save_data(self):
        async with aiofiles.open(self.path, 'w') as f:
            await f.write(json.dumps(self.data))

    async def make_embed(self, dat):
        e = discord.Embed(color=colors.fate())
        user = await self.bot.fetch_user(dat['user'])
        e.set_author(name=f"Giveaway by {user}", icon_url=user.avatar_url)
        e.description = dat["giveaway"]
        end_time = utils.get_time(dat["end_time"] - timestamp())
        if timestamp() >= dat['end_time']:
            e.set_footer(text=f"Giveaway Ended")
        else:
            end_time = re.sub('\.[0-9]*', '', end_time)
            e.set_footer(text=f"Ends in {end_time}")
        return e

    async def run_giveaway(self, guild_id, giveaway_id):
        dat = self.data[guild_id][giveaway_id]
        channel = await self.bot.fetch_channel(dat['channel'])
        message = await channel.fetch_message(dat['message'])
        while timestamp() < dat['end_time']:
            await asyncio.sleep(30)
            await message.edit(embed=await self.make_embed(dat))
        await message.edit(content="Giveaway complete")
        message = await channel.fetch_message(dat['message'])
        for reaction in message.reactions:
            if str(reaction.emoji) == "🎉":
                users = await reaction.users().flatten()
                users = [user for user in users if not user.bot]
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

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id, giveaways in self.data.items():
            for giveaway_id in giveaways.keys():
                self.bot.tasks.start(self.run_giveaway, guild_id, giveaway_id, task_id=f"giveaway-{guild_id}-{giveaway_id}")

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
            msg = await self.bot.wait_for_msg(ctx, action="giveaway setup")
            if not msg:
                return
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
                    repr = 'day'
                elif 'h' in timer:
                    time = int(timer.replace('h', '')) * 60 * 60
                    repr = 'hour'
                elif 'm' in timer:
                    time = int(timer.replace('m', '')) * 60
                    repr = 'minute'
                else:  # 's' in timer
                    time = int(timer.replace('s', ''))
                    repr = 'second'
                time_to_sleep[0] += time
                time_to_sleep[1].append(f"{raw} {repr if raw == '1' else repr + 's'}")
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
        message = await ctx.send("Send a description of the giveaway. Be sure to include what you're giving out")
        msg = await self.bot.wait_for_msg(ctx, timeout=60*3, action="giveaway setup")
        if not msg:
            return
        msg = await ctx.channel.fetch_message(msg.id)
        giveaway = msg.content
        await message.delete()
        await msg.delete()

        # Winner count
        message = await ctx.send("How many winners should there be. Reply in number form")
        for i in range(5):
            attempts += 1
            msg = await self.bot.wait_for_msg(ctx, action="giveaway setup")
            if not msg:
                return
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
            msg = await self.bot.wait_for_msg(ctx, action="giveaway setup")
            if not msg:
                return
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
        if key in self.data[guild_id]:
            key = random.randint(0, 10000)
        self.data[guild_id][key] = {
            **dat, "message": message.id
        }
        await self.save_data()
        self.bot.tasks.start(self.run_giveaway, guild_id, key, task_id=f"giveaway-{guild_id}-{key}")
        await ctx.send("Started your giveaway")
        await message.add_reaction("🎉")


def setup(bot):
    bot.add_cog(Giveaways(bot))
