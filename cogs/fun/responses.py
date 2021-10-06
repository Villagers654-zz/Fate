"""
cogs.fun.responses
~~~~~~~~~~~~~~~~~~~

A cog for adding random bot responses to messages in a server

:copyright: (C) 2019-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

import random
import asyncio
from time import time

import discord
from discord.ext import commands


class Responses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = bot.utils.cache("responses")
        self.cooldown = bot.utils.cooldown_manager(1, 10, raise_error=True)
        self.cd = {}
        self.spam_cd = {}
        self.last = {}

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def disableresponses(self, ctx):
        self.responses[ctx.guild.id] = {}
        await ctx.send("Disabled responses")
        await self.responses.flush()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def enableresponses(self, ctx):
        self.responses[ctx.guild.id] = {}
        await ctx.send("Enabled responses")
        await self.responses.flush()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if isinstance(m.guild, discord.Guild) and self.bot.is_ready():
            if not m.guild or not m.guild.me:
                return
            if not m.channel or not m.channel.permissions_for(m.guild.me):
                return
            if not m.channel.permissions_for(m.guild.me).send_messages:
                return
            await asyncio.sleep(0.21)
            if self.bot.user.mentioned_in(m):
                content = str(m.content).replace("@!", "@")
                mention = f"<@{self.bot.user.id}> "
                if content.startswith(f"<@{self.bot.user.id}> "):
                    content = content.replace(mention, "")

                    # Make sure the author isn't invoking a command
                    for command in self.bot.commands:
                        await asyncio.sleep(0)
                        if content.lower().startswith((command.name, *command.aliases)):
                            return

                    # Cooldowns to prevent spam
                    user_id = m.author.id
                    if user_id not in self.cd:
                        self.cd[user_id] = time() + 3
                    else:
                        if self.cd[user_id] > time():
                            self.cd[user_id] += 3
                            return
                        self.cd[user_id] = time() + 3

                    guild_id = m.guild.id
                    if guild_id not in self.cd:
                        self.cd[guild_id] = time() + 3
                    else:
                        if self.cd[guild_id] > time():
                            return
                        self.cd[guild_id] = time() + 3

                    now = int(time() / 3600)
                    if user_id not in self.spam_cd:
                        self.spam_cd[user_id] = [now, 0]
                    if self.spam_cd[user_id][0] == now:
                        self.spam_cd[user_id][1] += 1
                    else:
                        self.spam_cd[user_id] = [now, 0]
                    if self.spam_cd[user_id][1] >= 120:
                        return await m.channel.send("You're on cooldown")

                    if guild_id not in self.spam_cd:
                        self.spam_cd[guild_id] = [now, 0]
                    if self.spam_cd[guild_id][0] == now:
                        self.spam_cd[guild_id][1] += 1
                    else:
                        self.spam_cd[guild_id] = [now, 0]
                    if self.spam_cd[guild_id][1] >= 240:
                        return await m.channel.send("This server's on cooldown")

                    # Clean up old conversations
                    for guild_id, last_used in list(self.last.items()):
                        await asyncio.sleep(0)
                        if time() - 240 > last_used:
                            if guild_id in self.bot.chats:
                                self.bot.chats[guild_id].reset()
                    self.last[guild_id] = time()
                    for _id, cooldown_end in list(self.cd.items()):
                        await asyncio.sleep(0)
                        if time() - 120 > cooldown_end:
                            del self.cd[_id]

                    # Interact with CleverBot
                    if guild_id not in self.bot.chats:
                        self.bot.chats[guild_id] = self.bot.cb.conversation(guild_id)
                    try:
                        reply = await self.bot.chats[guild_id].say(content)
                    except:
                        self.bot.chats[guild_id].reset()
                        reply = await self.bot.chats[guild_id].say(content)
                    return await m.channel.send(reply)

            if m.guild.id in self.responses:
                if not m.author.bot and m.channel and m.guild and m.guild.owner and m.guild.me:
                    if not m.channel.permissions_for(m.guild.me).send_messages:
                        return
                    if random.randint(1, 4) == 4:
                        self.cooldown.check(m.channel.id)
                        if m.content.startswith("hello"):
                            await m.channel.send(
                                random.choice(
                                    ["Hello", "Hello :3", "Suh", "Suh :3", "Wazzuh"]
                                )
                            )
                        elif m.content.startswith("gm"):
                            await m.channel.send(
                                random.choice(
                                    [
                                        "Gm",
                                        "Gm :3",
                                        "Morning",
                                        "Morning :3",
                                        "Welcome to heaven",
                                    ]
                                )
                            )
                        elif m.content.startswith("gn"):
                            await m.channel.send(
                                random.choice(["Gn", "Gn :3", "Night", "Nighty"])
                            )
                        elif m.content.startswith("ree"):
                            await m.channel.send(
                                random.choice(
                                    [
                                        "*depression strikes again*",
                                        "*pole-man strikes again*",
                                        "Would you like an espresso for your depresso",
                                        "You're not you when you're hungry",
                                        "*crippling depression*",
                                        "Breakdown sponsored by Samsung",
                                        "No espresso for you",
                                        "Sucks to be you m8",
                                        "Ripperoni",
                                        "Sucks to suck",
                                    ]
                                )
                            )
                        elif m.content.startswith("kys"):
                            await m.channel.send(
                                random.choice(
                                    [
                                        "NoT iN mY cHriSTiAn sErVeR..\nDo it in threadys",
                                        "Shut your skin tone chicken bone google chrome no home flip phone disowned ice cream cone garden gnome extra chromosome metronome dimmadome genome full blown monochrome student loan indiana jones overgrown flintstone x and y hormone friend zoned sylvester stallone sierra leone autozone professionally seen silver patrone head ass tf up.",
                                        "Well aren't you just a fun filled little lollipop tripple dipped in psycho",
                                        "Woah, calm down satan",
                                    ]
                                )
                            )


def setup(bot):
    bot.add_cog(Responses(bot), override=True)
