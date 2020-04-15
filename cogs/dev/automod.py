
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
        self.example_config = {
            "toggle": bool,
            "spam": bool,
            "raids": bool
        }

    def save_data(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, ensure_ascii=False)

    # @commands.Cog.listener()
    async def on_message(self, msg):
        cog = self.bot.get_cog("Moderation")
        if cog and isinstance(msg.guild, discord.Guild):
            await cog.warn_user(msg.channel, msg.author, "reason")

def setup(bot):
    bot.add_cog(AutoModeration(bot))
