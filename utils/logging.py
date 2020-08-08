
import asyncio
from datetime import datetime

from discord.ext import tasks
from termcolor import cprint

from fate import Fate


class Logging:
    def __init__(self, bot: Fate):
        self.bot = bot
        self.queue = []
        self.handle_queue.start()

    @property
    def time(self):
        now = str(datetime.now().strftime("%I:%M%p"))
        if now.startswith('0'):
            now = now.replace('0', '', 1)
        return now

    @tasks.loop(seconds=0.51)
    async def handle_queue(self):
        if not self.queue:
            return
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
            await asyncio.sleep(1)
        channel = self.bot.get_channel(self.bot.config["log_channel"])
        for log in list(self.queue):
            await channel.send(log)
            self.queue.remove(log)

    def debug(self, log, *args, **kwargs):
        if self.bot.config["debug"]:
            log = f"{self.time} | DEBUG | {log}"
            cprint(log, "cyan", *args, **kwargs)
            self.queue.append(f"```{log}```")

    def info(self, log, *args, **kwargs):
        log = f"{self.time} | INFO | {log}"
        cprint(log, "green", *args, **kwargs)
        self.queue.append(f"```{log}```")

    def critical(self, log, *args, **kwargs):
        log = f"{self.time} | CRITICAL | {log}"
        cprint(log, "red", *args, **kwargs)
        owner = self.bot.get_user(self.bot.config["bot_owner_id"])
        self.queue.append(f"{owner.mention} something went wrong```{log}```")
