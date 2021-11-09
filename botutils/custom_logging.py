"""
Custom Logging
~~~~~~~~~~~~~~

A helper class intended for formatting logs and printing to console

:copyright: (C) 2020-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import asyncio
import traceback
from datetime import datetime

from discord import AllowedMentions
from discord.ext import tasks
from termcolor import cprint


class Logging:
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.handle_queue.start()

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            raise ValueError("No arguments were provided")
        levels = ["DEBUG", "INFO", "CRITICAL"]

        if any(level in args for level in levels):
            args = [arg for arg in args if arg not in levels]
            args[0] += f"\n~The method of logging on this one needs updated"

        self.info(*args, **kwargs)

    @property
    def time(self):
        now = str(datetime.now().strftime("%I:%M%p"))
        if now.startswith("0"):
            now = now.replace("0", "", 1)
        return now

    @tasks.loop(seconds=0.51)
    async def handle_queue(self):
        if not self.queue:
            return
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
            await asyncio.sleep(1)
        msg = ""
        try:
            channel = self.bot.get_channel(self.bot.config["log_channel"])
            for log in list(self.queue):
                old = log
                log = log[:1000]
                if len(msg) + len(log) > 1900:
                    if channel:
                        await channel.send(msg)
                    msg = ""
                msg += f"{log}"
                msg = msg.replace("``````", "\n")
                self.queue.remove(old)
            if channel:
                await channel.send(msg, allowed_mentions=AllowedMentions.all())
        except:
            self.info(
                f"There was an error in the log queue\n{traceback.format_exc()}\n{msg}"
            )
            await asyncio.sleep(5)

    def debug(self, log, *args, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = "cyan"
        if self.bot.config["debug_mode"]:
            log = "\n".join(f"{self.time} | DEBUG | {line}" for line in log.split("\n"))
            cprint(log, *args, **kwargs)
            self.queue.append(f"```{log}```")

    def info(self, log, *args, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = "green"
        log = "\n".join(f"{self.time} | INFO | {line}" for line in log.split("\n"))
        cprint(log, *args, **kwargs)
        self.queue.append(f"```{log}```")

    def critical(self, log, *args, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = "red"
        log = "\n".join(f"{self.time} | CRITICAL | {line}" for line in log.split("\n"))
        cprint(log, *args, **kwargs)
        owner = self.bot.get_user(self.bot.config["bot_owner_id"])
        self.queue.append(
            f"{owner.mention if owner else 'Frick,'} something went wrong\n```{log}```"
        )
