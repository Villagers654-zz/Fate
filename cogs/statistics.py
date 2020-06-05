
from discord.ext import commands
import discord
from utils import colors


class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cogs = {  #  CogName: variable
            "Logger": "config",
            "SelfRoles": "menus",
            "GlobalChat": "config",
            "ChatBot": "toggle",
            "AutoRole": "roles",
            "ChatFilter": "toggle",
            "Giveaways": "data",
            "RestoreRoles": "guilds",
            "Welcome": "toggle",
            "Leave": "toggle"
        }

    @commands.command(name="statistics", aliases=["stats"])
    async def statistics(self, ctx):
        e = discord.Embed(color=colors.fate())
        owner = await self.bot.fetch_user(self.bot.config["bot_owner_id"])
        e.set_author(name="Module Statistics", icon_url=owner.avatar_url)
        e.description = self.bot.utils.format_dict({
            key: f"{len(eval(f'self.bot.get_cog(key).{value}', dict(self=self, key=key)))} active"
            for key, value in self.cogs.items()
        })
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Statistics(bot))