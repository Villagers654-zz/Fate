# Create un-abusable polls for users to react to
# - works by keeping the tally saved, and once reacted you can only change
#   your reaction, and not remove it in order to prevent mods removing reactions

from os import path
import json
import asyncio

from discord.ext import commands

from fate import Fate


class SafePolls(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.path = "./data/userdata/safe_polls.json"
        self.lock = asyncio.Lock()
        self.polls = {}
        if path.isfile(self.path):
            with open(self.path, mode="r") as f:
                self.polls = json.load(f)

    async def save_data(self) -> None:
        async with self.bot.open(self.path, "w", lock=self.lock) as f:
            await f.write(json.dumps(self.polls))

    @commands.command(name="safe-poll", aliases=["safepoll", "safe_poll"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def safe_poll(self, ctx, *, question):
        pass


def setup(bot: Fate):
    bot.add_cog(SafePolls(bot))
