import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import os

import discord
from discord.ext import commands, tasks


async def ainput(prompt: str = ""):
    """Credit to https://gist.github.com/delivrance/"""
    with ThreadPoolExecutor(1, "AsyncInput", lambda x: print(x, end="", flush=True), (prompt,)) as executor:
        return (await asyncio.get_event_loop().run_in_executor(
            executor, sys.stdin.readline
        )).rstrip()


class Console(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def stats(self):
        return {
            "users": len(self.bot.users),
            "guilds": len(self.bot.guilds)
        }

    @tasks.loop(seconds=3)
    async def update_console(self):
        print(chr(27) + "[2J")  # Clear the terminal
        columns, lines = os.get_terminal_size()
        lines = ["" for _ in range(lines)]
        lines[0] = f"◈ {self.bot.user}"
        lines[1] = f"• {self.bot.user.id}"
        lines[2] = f"• "


def setup(bot):
    bot.add_cog(Console(bot))
