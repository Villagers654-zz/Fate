from discord.ext import commands
import discord

from fate import Fate
from utils import colors


class Toggles(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot

    @property
    def module_list(self) -> discord.Embed:
        e = discord.Embed(color=colors.fate())
        e.description = "\n".join(self.bot.module_index.keys())
        return e

    async def run_command(self, ctx, module, key) -> None:
        for listed_module in self.bot.module_index.keys():
            if str(module).lower() == str(listed_module).lower():
                module = listed_module  # type: str
                break
        else:
            p = self.bot.utils.get_prefix(ctx)  # type: str
            return await ctx.send(
                f"Module not found. If you're trying to {key} a command, use `{p}{key}-command your_command`"
            )
        command_name = self.bot.module_index[module][key]
        if not command_name:
            await ctx.send(f"There is no {key} command for {module}")
        subcommand = None
        if "." in command_name:
            command_name, subcommand = command_name.split(".")
        command = self.bot.get_command(command_name)
        if not subcommand:
            await command.invoke(ctx)
        else:
            cog = self.bot.get_cog(module)  # type: commands.Cog
            for command in cog.walk_commands():
                if command.name == subcommand:
                    await command.invoke(ctx)
                    break

    @commands.command(name="enable")
    async def enable_module(self, ctx, module):
        await self.run_command(ctx, module=module, key="enable")

    @commands.command(name="disable")
    async def disable_module(self, ctx, module):
        await self.run_command(ctx, module=module, key="disable")


def setup(bot: Fate) -> None:
    bot.add_cog(Toggles(bot))
