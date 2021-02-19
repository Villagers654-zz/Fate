import random

import discord
from discord.ext import commands


class Responses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = bot.utils.cache(bot, "responses")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def disableresponses(self, ctx):
        self.responses[ctx.guild.id] = {}
        await ctx.send("Disabled responses")
        await self.responses.flush()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def enableresponses(self, ctx):
        self.responses[ctx.guild.id] = {}
        await ctx.send("Enabled responses")
        await self.responses.flush()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if isinstance(m.guild, discord.Guild) and m.guild.id in self.responses:
            if not m.author.bot and m.channel.permissions_for(m.guild.me).send_messages:
                if random.randint(1, 4) == 4:
                    if m.content.startswith("hello"):
                        await m.channel.send(
                            random.choice(
                                ["Hello", "Hello :3", "Suh", "Suh :3", "Wazzuh"]
                            )
                        )
                    elif m.content.startswith("gm"):
                        await m.channel.send(
                            random.choice(
                                [
                                    "Gm",
                                    "Gm :3",
                                    "Morning",
                                    "Morning :3",
                                    "Welcome to heaven",
                                ]
                            )
                        )
                    elif m.content.startswith("gn"):
                        await m.channel.send(
                            random.choice(["Gn", "Gn :3", "Night", "Nighty"])
                        )
                    elif m.content.startswith("ree"):
                        await m.channel.send(
                            random.choice(
                                [
                                    "*depression strikes again*",
                                    "*pole-man strikes again*",
                                    "Would you like an espresso for your depresso",
                                    "You're not you when you're hungry",
                                    "*crippling depression*",
                                    "Breakdown sponsored by Samsung",
                                    "No espresso for you",
                                    "Sucks to be you m8",
                                    "Ripperoni",
                                    "Sucks to suck",
                                ]
                            )
                        )
                    elif m.content.startswith("kys"):
                        await m.channel.send(
                            random.choice(
                                [
                                    "NoT iN mY cHriSTiAn sErVeR..\nDo it in threadys",
                                    "Shut your skin tone chicken bone google chrome no home flip phone disowned ice cream cone garden gnome extra chromosome metronome dimmadome genome full blown monochrome student loan indiana jones overgrown flintstone x and y hormone friend zoned sylvester stallone sierra leone autozone professionally seen silver patrone head ass tf up.",
                                    "Well aren't you just a fun filled little lollipop tripple dipped in psycho",
                                    "Woah, calm down satan",
                                ]
                            )
                        )


def setup(bot):
    bot.add_cog(Responses(bot))
