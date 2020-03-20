from discord.ext import commands
from utils import colors
import discord
import json


class Toggles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_toggles(self, toggles):
        with open("./data/userdata/toggles.json", "w") as f:
            json.dump(toggles, f, ensure_ascii=False)

    @commands.group(name="enable")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def enable(self, ctx):
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Toggleable Modules", icon_url=ctx.author.avatar_url)
        e.description = "antispam\nchatbot\nautorole\nchatfilter\nlogger\n"


def setup(bot):
    bot.add_cog(Toggles(bot))
