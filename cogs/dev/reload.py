import asyncio
import random
import traceback

import discord
from discord.ext import commands

from botutils import colors


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload", description="reloads a cog", hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *modules: lambda x: x.lower()):
        if not modules:
            modules = [*self.bot.initial_extensions, *self.bot.awaited_extensions]
        successful = []
        unsuccessful = []
        for module in modules:
            try:
                try:
                    self.bot.unload_extension(f"cogs.{module}")
                except:
                    pass
                self.bot.load_extension(f"cogs.{module}")
                successful.append(module)
            except:
                unsuccessful.append([module, traceback.format_exc()])
        e = discord.Embed(color=colors.fate())
        e.set_author(name=f"| {ctx.author.name} | 🍪", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png"
        )
        e.description = ""
        if successful:
            e.description += (
                f"Reloaded {len(successful)} cogs"
                if len(successful) > 1
                else f"Reloaded {successful[0]}"
            )
        if unsuccessful:
            e.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/501871950260469790/513637807680389121/lzbecdmvffggwmxconlk.png"
            )
            e.set_footer(
                text=f'{random.choice(["So sorry", "Apologies", "Sucks to be you", "Sorry"])} {random.choice(["dad", "master", "mike", "luck"])}'
            )
            for cog, error in unsuccessful:
                for text_group in [
                    str(error)[i : i + 900] for i in range(0, len(str(error)), 990)
                ]:
                    if len(e) >= 5000:
                        break
                    e.add_field(
                        name=f"Error - {cog}",
                        value=f"```{discord.utils.escape_markdown(text_group)}```",
                        inline=False,
                    )
        await ctx.send(embed=e)

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload(self, ctx, *, module: str):
        try:
            self.bot.unload_extension("cogs." + module)
        except:
            return await ctx.send("That module isn't loaded")
        e = discord.Embed(color=colors.fate())
        e.set_author(name=f"| {ctx.author.name} | 🍪", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/513637799530856469/fzilwhwdxgubnoohgsas.png"
        )
        e.description = f"Disabled {module}"
        await ctx.send(embed=e, delete_after=5)
        await asyncio.sleep(0.5)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Reload(bot))
