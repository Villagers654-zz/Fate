"""
classes.logging
~~~~~~~~~~~~~~~~

A cog for reporting statistics to influxdb

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from contextlib import suppress
import asyncio
import os

from discord.ext import commands, tasks
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import psutil


class Influx(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        auth = self.bot.auth["InfluxDB"]
        self.client = InfluxDBClient(
            url=auth["url"],
            token=auth["token"],
            org=auth["org"]
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.last = {
            "users": len(bot.users),
            "guilds": len(bot.guilds)
        }
        self.process = psutil.Process(os.getpid())
        self.messages = 0
        self.update_user_count.start()
        self.update_stats.start()

    def cog_unload(self):
        self.update_user_count.cancel()
        self.update_stats.cancel()

    def start_thread(self, pointer):
        with suppress(Exception):
            layer = lambda: self.write_api.write("542f070eec1976be", record=pointer)
            return self.bot.loop.run_in_executor(None, layer)

    @tasks.loop(seconds=60)
    async def update_user_count(self):
        with suppress(Exception):
            async def user_count():
                count = 0
                for guild in list(self.bot.guilds):
                    await asyncio.sleep(0)
                    count += guild.member_count
                return count

            if not self.bot.is_ready():
                await self.bot.wait_until_ready()
                self.last = {
                    "users": await user_count(),
                    "guilds": len(self.bot.guilds)
                }

            # Update user count
            new_count = await user_count()
            if new_count != self.last["users"]:
                pointer = Point("activity").field("users", new_count)
                await self.start_thread(pointer)
                self.last["users"] = new_count

    @tasks.loop(seconds=10)
    async def update_stats(self):
        """ Updates the cpu usage and bot ping """
        def get_cpu_percentage():
            """ Returns the bots cpu usage over the span of 3s """
            return self.process.cpu_percent(interval=5)

        with suppress(Exception):
            result = await self.bot.loop.run_in_executor(
                None, get_cpu_percentage
            )
            cpu = round(result)
            ping = round(self.bot.latency * 1000)
            pointer = Point("stats").field("cpu", cpu).field("ping", ping).field("messages", self.messages)
            self.messages = 0
            await self.start_thread(pointer)

    @commands.Cog.listener("on_guild_join")
    @commands.Cog.listener("on_guild_remove")
    async def on_guild_count_change(self, _guild):
        if self.bot.is_ready():
            pointer = Point("activity").field("guilds", len(self.bot.guilds))
            await self.start_thread(pointer)
            self.last["guilds"] = len(self.bot.guilds)

    @commands.Cog.listener()
    async def on_message(self, _message):
        self.messages += 1

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await asyncio.sleep(1)  # Let the command process first
        pointer = Point("commands").field(ctx.command.name, 1)
        await self.start_thread(pointer)


def setup(bot):
    bot.add_cog(Influx(bot))
