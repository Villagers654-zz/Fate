import discord
from discord.ext import commands


class link_len(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name='on_message')
    async def message_link_shitty(self, message: discord.Message):
        if message.content in '.'


def setup(bot):
    bot.add_cog(link_len(bot))
