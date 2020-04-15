
from os import path
import json
from time import time, monotonic
import asyncio

from discord.ext import commands
import discord

from utils import colors


class AutoModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/auto_mod.json"
        self.config = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)

    def save_data(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, ensure_ascii=False)


def setup(bot):
    bot.add_cog(AutoModeration(bot))
