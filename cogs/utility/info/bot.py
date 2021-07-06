"""
cogs.utility.info.bot
~~~~~~~~~~~~~~~~~~~~~~

A coroutine function for generating the bots information embed

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import platform
import os
from datetime import datetime, timezone

import discord
import psutil

from botutils import colors, bytes2human, get_time


async def fetch_bot_info(ctx):
    guilds = len(list(ctx.bot.guilds))
    users = len(list(ctx.bot.users))
    bot_pid = psutil.Process(os.getpid())
    e = discord.Embed(color=colors.fate)
    e.set_author(
        name="Fate Bot: Core Info",
        icon_url=ctx.bot.get_user(ctx.bot.config["bot_owner_id"]).avatar.url,
    )
    lines = 0
    cog = ctx.bot.cogs["Ranking"]
    commands = sum(cmd[1]["total"] for cmd in list(cog.cmds.items()))
    async with ctx.bot.utils.open("fate.py", "r") as f:
        lines += len(await f.readlines())

    locations = ["botutils", "cogs"]
    for location in locations:
        for root, dirs, files in os.walk(location):
            for file in files:
                if file.endswith(".py"):
                    async with ctx.bot.utils.open(f"{root}/{file}", "r") as f:
                        lines += len(await f.readlines())
    e.description = f"Commands Used This Month: {commands}" \
                    f"\nLines of code: {lines}"
    e.set_thumbnail(url=ctx.bot.user.avatar.url)
    e.add_field(
        name="◈ Summary ◈",
        value="Fate is a ~~multipurpose~~ hybrid bot created for fun",
        inline=False,
    )
    e.add_field(
        name="◈ Statistics ◈",
        value=f"**Commands:** [{len(ctx.bot.commands)}]"
              f"\n**Modules:** [{len(ctx.bot.extensions)}]"
              f"\n**Servers:** [{guilds}]"
              f"\n**Users:** [{users}]",
    )
    e.add_field(
        name="◈ Credits ◈",
        value="\n• **Cortex** ~ `teacher of many things..`"
              "\n• **Luck** ~ `owner & main developer`"
              "\n• **Opal** ~ `artwork / graphic design`"
              "\n• **Legit** ~ `identifying many design flaws`"
    )

    def get_info() -> str:
        disk = psutil.disk_usage('/')
        ram = psutil.virtual_memory()
        freq = psutil.cpu_freq()
        cur = str(round(freq.current))

        if freq.current < 1000:
            cur = f"{cur}GHz"
        else:
            cur = f"{cur[0]}.{cur[1]}GHz"
        max = str(round(freq.max))
        max = f"{max[0]}.{max[1]}GHz"
        c_temp = round(psutil.sensors_temperatures(fahrenheit=False)['coretemp'][0].current)
        f_temp = round(psutil.sensors_temperatures(fahrenheit=True)['coretemp'][0].current)
        value = f"**Storage (NVME)**: {bytes2human(disk.used)}/{bytes2human(disk.total)} - ({round(disk.percent)}%)\n" \
                f"**RAM (DDR4)**: {bytes2human(ram.used)}/{bytes2human(ram.total)} - ({round(ram.percent)}%)\n" \
                f"**CPU i9-10900K:** {round(psutil.cpu_percent())}% @{cur}/{max}\n" \
                f"**CPU Temp:** {c_temp}°C {f_temp}°F\n" \
                f"**Bot Usage:** **RAM:** {bytes2human(bot_pid.memory_full_info().rss)} **CPU:** {round(bot_pid.cpu_percent())}%"

        return value

    e.add_field(
        name="◈ Memory ◈",
        value=await ctx.bot.loop.run_in_executor(None, get_info),
        inline=False,
    )

    online_for = datetime.now(tz=timezone.utc) - ctx.bot.start_time
    e.add_field(
        name="◈ Uptime ◈",
        value=f"Online for {get_time(round(online_for.total_seconds()))}\n",
        inline=False,
    )
    e.set_footer(
        text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}",
        icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png",
    )
    return e
