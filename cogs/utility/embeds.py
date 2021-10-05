"""
cogs.utility.embeds
~~~~~~~~~~~~~~~~~~~~

A cog that simply embeds a message

:copyright: (C) 2021-present FrequencyX4
:license: Proprietary and Confidential, see LICENSE for details
"""

from discord.ext import commands
import discord


class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="embed", description="Embeds a message")
    async def embed(self, ctx, *, arg):
        try:
            e = discord.Embed()
            e.description = arg
            await ctx.send(embed=e)
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Embeds(bot), override=True)
