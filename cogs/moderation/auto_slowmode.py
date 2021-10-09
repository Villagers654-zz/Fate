"""
cogs.moderation.auto_slowmode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A module for automatically adjusting slowmode based on the chats activity

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
from time import time
import asyncio
from contextlib import suppress

from discord.ext import commands
import discord


# The threshold, and the slowmode delay
rates: List[Tuple[int, int]] = [
    (5, 10),
    (7, 30),
    (11, 60),
    (14, 120),
    (19, 300),
    (24, 600)
]


class AutomaticSlowmode(commands.Cog):
    """ A cog for automatically adjusting slowmode based on the chats activity """
    guilds: List[int] = []
    index: Dict[int, List[Union[float, int]]] = {}
    active: List[int] = []

    @commands.command(name="auto-slowmode", description="Automatically adjusts slowmode")
    @commands.is_owner()
    async def auto_slowmode(self, ctx: commands.Context, toggle: str = None) -> None:
        if toggle == "enable":
            self.guilds.append(ctx.guild.id)
            await ctx.send("Enabled auto slowmode")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        """ Check if slowmode needs enabled """
        if msg.guild and msg.guild.id in self.guilds:

            # Get the current rate of messages
            _id = msg.channel.id
            now = int(time() / 15)
            if _id not in self.index:
                self.index[_id] = [now, 0]
            if self.index[_id][0] == now:
                self.index[_id][1] += 1
            else:
                self.index[_id] = [now, 1]
            current_rate: int = self.index[_id][1]

            # Check if the rate of messages surpasses any thresholds
            for threshold, slowmode_delay in reversed(rates):
                if current_rate >= threshold * 3:
                    # Skip if the new slowmode is smaller than the active slowmode delay
                    if msg.guild.id in self.active and threshold < slowmode_delay:
                        return

                    # Keep the slowmode locked to the new setting unless the new recommended rate is bigger
                    if msg.channel.slowmode_delay != slowmode_delay:
                        self.active.append(msg.guild.id)
                        with suppress(Exception):
                            await msg.channel.edit(slowmode_delay=slowmode_delay)

                        # Mark as no longer active after 60 seconds. This lets
                        # slowmode either disable, or switch to a lower delay
                        # based on the new rate of messages
                        await asyncio.sleep(120)
                        self.active.remove(msg.guild.id)

                        break
            else:
                # Disable slowmode if there isn't enough activity to maintain it
                if msg.channel.slowmode_delay != 0 and msg.guild.id not in self.active:
                    await msg.channel.edit(slowmode_delay=0)


def setup(bot):
    bot.add_cog(AutomaticSlowmode())
