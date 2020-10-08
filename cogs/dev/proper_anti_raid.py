"""
Discord.Py Cog to Prevent Raids:
- Mass kicking and banning
- deletion of roles nearly everyone has
- Mass channel deletion
- Invite spam
"""

from discord.ext import commands


class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(AntiRaid(bot))
