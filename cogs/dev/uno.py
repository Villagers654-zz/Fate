from discord.ext import commands


class Uno(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.solo = {}
        self.multi = {}


def setup(bot):
    bot.add_cog(Uno(bot))
