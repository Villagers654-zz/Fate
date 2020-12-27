from os.path import isfile
import json
import asyncio
import time
import random

from discord.ext import commands
import discord
from profanity_check import predict_prob

from botutils import checks, colors


class ChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.toggle = {}
        self.cache = {}
        self.prefixes = {}
        self.dir = {}
        self.cd = {}
        self.hell = False
        self.dm_cd = {}
        if isfile("./data/userdata/chatbot.json"):
            with open("./data/userdata/chatbot.json", "r") as infile:
                dat = json.load(infile)
                if (
                    "prefixes" in dat
                    and "cache" in dat
                    and "prefixes" in dat
                    and "dir" in dat
                ):
                    self.toggle = dat["toggle"]
                    self.cache = dat["cache"]
                    self.prefixes = dat["prefixes"]
                    self.dir = dat["dir"]
        self.blocked = []

    async def save_data(self):
        data = {
            "toggle": self.toggle,
            "cache": self.cache,
            "prefixes": self.prefixes,
            "dir": self.dir,
        }
        await self.bot.save_json("./data/userdata/chatbot.json", data)

    @commands.group(name="chatbot")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def _chatbot(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            toggle = "disabled"
            cache = "guilded"
            if guild_id in self.toggle:
                toggle = "enabled"
            if guild_id in self.dir:
                if self.dir[guild_id] == "global":
                    cache = self.dir[guild_id]
            e = discord.Embed(color=colors.fate())
            e.set_author(name="| Chat Bot", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = (
                f"**Current Status:** {toggle}\n" f"**Cache Location:** {cache}\n"
            )
            e.add_field(
                name="◈ Usage ◈",
                value=f".chatbot enable\n"
                f"`enables chatbot`\n"
                f".chatbot disable\n"
                f"`disables chatbot`\n"
                f".chatbot swap_cache\n"
                f"`swaps to global or guilded cache`\n"
                f".chatbot clear_cache\n"
                f"`clears guilded cache`",
                inline=False,
            )
            await ctx.send(embed=e)

    @_chatbot.command(name="enable")
    @commands.has_permissions(manage_messages=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.toggle[guild_id] = ctx.channel.id
            if guild_id not in self.dir:
                self.dir[guild_id] = "guilded"
            await ctx.send("Enabled chatbot")
            return await self.save_data()
        await ctx.send("Chatbot is already enabled")

    @_chatbot.command(name="disable")
    @commands.has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            return await ctx.send("Chatbot is not enabled")
        del self.toggle[guild_id]
        await self.save_data()
        await ctx.send("Disabled chatbot")

    @_chatbot.command(name="swap_cache")
    @commands.has_permissions(manage_messages=True)
    async def _swap_cache(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.dir:
            return await ctx.send(
                "Chatbot needs to be enabled in order for you to use this command"
            )
        if self.dir[guild_id] == "guilded":
            await ctx.send(
                "Are you sure you'd like to switch to global cache? There's a filter to block profanity, "
                "but some things can slip through. If you go through with it, and something does, you can "
                "join the support server and request its removal\nReply with '`yes`' or '`confirm`' to "
                "accept and switch to using global cache, or anything else to deny"
            )
            msg = await self.bot.utils.wait_for_msg(self, ctx)
            if not msg:
                return
            if (
                "yes" in str(msg.content).lower()
                or "confirm" in str(msg.content).lower()
            ):
                self.dir[guild_id] = "global"
            else:
                return await ctx.send(
                    "Alright, maybe some other time in a NSFW channel perhaps?"
                )
        else:
            self.dir[guild_id] = "guilded"
        await ctx.send(f"Swapped cache location to {self.dir[guild_id]}")
        await self.save_data()

    @_chatbot.command(name="clear_cache")
    @commands.has_permissions(manage_messages=True)
    async def _clear_cache(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.cache:
            return await ctx.send("No cached data found")
        del self.cache[guild_id]
        await ctx.send("Cleared cache")
        await self.save_data()

    @_chatbot.command(name="load_preset")
    @commands.has_permissions(manage_messages=True)
    async def _load_preset(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.cache:
            self.cache[guild_id] = []
        presets = []
        for response in open("./data/misc/responses.txt", "r").readlines():
            presets.append(response)
        for response in presets:
            if response not in self.cache[guild_id]:
                self.cache[guild_id].append(response)
        await ctx.send("Loaded preset")
        await self.save_data()

    @commands.command(name="pop")
    @commands.check(checks.luck)
    async def _pop(self, ctx, *, phrase):
        guild_id = str(ctx.guild.id)
        for response in self.cache[guild_id]:
            if phrase in response:
                self.cache[guild_id].pop(self.cache[guild_id].index(response))
        await ctx.message.delete()

    @commands.command(name="globalpop")
    @commands.check(checks.luck)
    async def _globalpop(self, ctx, *, phrase):
        popped = []
        for response in self.cache["global"]:
            if phrase in response:
                self.cache["global"].pop(self.cache["global"].index(response))
                popped.append(response)
        await ctx.send(f"Removed: {popped}")
        await ctx.message.delete()

    @_chatbot.command(name="find")
    async def _find(self, ctx, *, phrase):
        found = []
        for item in self.cache["global"]:
            if phrase.lower() in item.lower():
                found.append(item)
        e = discord.Embed(color=colors.fate())
        results = [str(found)[i : i + 1000] for i in range(0, len(str(found)), 1000)]
        if len(results) > 5:
            results = results[:5]
            e.set_footer(text="Character Limit Reached")
        for i in range(len(results)):
            if i == 0:
                e.description = results[i]
                continue
            e.add_field(name="~", value=results[i])
        await ctx.send(embed=e)

    @commands.command(name="prefixes")
    async def _prefixes(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send(self.prefixes[guild_id])

    @commands.command(name="delprefix")
    @commands.check(checks.luck)
    async def _delprefix(self, ctx, prefix):
        guild_id = str(ctx.guild.id)
        self.prefixes[guild_id].pop(self.prefixes[guild_id].index(prefix))
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """ Tries to respond with related message """

        def get_matches(key) -> list:
            """Returns a list of related messages"""
            cache = self.cache["global"]
            if self.dir[guild_id] == "guilded":
                cache = self.cache[guild_id]
            return [m for m in cache if key in m and m != msg.content and "@" not in m]

        if isinstance(msg.guild, discord.Guild) and not msg.author.bot and msg.content:
            guild_id = str(msg.guild.id)

            if guild_id not in self.toggle:
                return
            if msg.channel.id != self.toggle[guild_id]:
                return
            if msg.raw_mentions:
                return
            if msg.raw_role_mentions:
                return
            if msg.raw_channel_mentions:
                return
            if not msg.channel.permissions_for(msg.guild.me).send_messages:
                return

            content = list(str(msg.content).lower())
            if len(content) >= 4:
                abcs = "abcdefghijklmnopqrstuvwxyz "
                if (
                    not content[0] in abcs
                    or content[0] in abcs
                    and content[1] not in abcs
                    or (len(msg.content.split()) == 2 and content[3] == " ")
                ):
                    return  # probably a bot command

            if guild_id not in self.cd:
                self.cd[guild_id] = 0
            if self.cd[guild_id] > time.time():
                return
            self.cd[guild_id] = time.time() + 2

            msg = await msg.channel.fetch_message(msg.id)  # get the original content
            if guild_id not in self.cache:
                self.cache[guild_id] = []
            self.cache[guild_id].append(msg.content)
            self.cache["global"].append(msg.content)
            await self.save_data()

            choice = None
            index = 0
            while not choice:
                if index == 10:
                    return

                blacklist = ["rape"]
                key = random.choice(msg.content.split())
                matches = get_matches(key)
                if not matches:
                    return

                prob = predict_prob(matches)
                new_prob = []
                for i in prob:
                    if i >= 0.2:
                        new_prob.append(1)
                    elif i < 0.2:
                        new_prob.append(0)

                matches = [
                    match
                    for i, match in enumerate(matches)
                    if new_prob[i] == 0
                    and (not any(phrase in str(match).lower() for phrase in blacklist))
                ]
                if not matches and len(msg.content.split()) == 1:
                    return
                if len(matches) > 0:
                    choice = random.choice(matches)
                index += 1

            name = msg.author.mention
            choice = choice.replace("Fate", name).replace("fate", name)

            async with msg.channel.typing():
                timer = 0
                for char in list(choice):
                    timer += 0.1
                await asyncio.sleep(timer)
                await msg.channel.send(choice)


def setup(bot):
    bot.add_cog(ChatBot(bot))
