from discord.ext import commands
from os.path import isfile
import discord
import random
import json
import os


class Farewell:
    def __init__(self, bot):
        self.bot = bot
        self.identifier = {}
        self.channel = {}
        self.useimages = {}
        self.toxicity = {}
        if isfile("./data/userdata/config/farewell.json"):
            with open("./data/userdata/config/farewell.json", "r") as infile:
                dat = json.load(infile)
                if (
                    "identifier" in dat
                    and "channel" in dat
                    and "useimages" in dat
                    and "toxicity" in dat
                ):
                    self.identifier = dat["identifier"]
                    self.channel = dat["channel"]
                    self.useimages = dat["useimages"]
                    self.toxicity = dat["toxicity"]

    def save(self):
        with open("./data/userdata/config/farewell.json", "w") as outfile:
            json.dump(
                {
                    "identifier": self.identifier,
                    "channel": self.channel,
                    "useimages": self.useimages,
                    "toxicity": self.toxicity,
                },
                outfile,
                ensure_ascii=False,
            )

    @commands.group(name="farewell")
    @commands.has_permissions(manage_guild=True)
    async def _farewell(self, ctx):
        async with ctx.typing():
            if ctx.invoked_subcommand is None:
                await ctx.send(
                    "**Farewell Message Instructions:**\n"
                    ".farewell enable ~ `enables welcome messages`\n"
                    ".farewell disable ~ `disables welcome messages`\n"
                    ".farewell setchannel ~ `sets the channel`\n"
                    ".farewell useimages ~ `true or false`\n"
                    ".farewell toxicity ~ `true or false`"
                )

    @_farewell.command(name="toggle")
    async def _toggle(self, ctx):
        """Not in use, but still works"""
        report = ""
        if str(ctx.guild.id) not in self.identifier:
            self.identifier[str(ctx.guild.id)] = "True"
            report += "Enabled farewell messages"
        else:
            if self.identifier[str(ctx.guild.id)] == "True":
                self.identifier[str(ctx.guild.id)] = "False"
                report += "Disabled farewell messages"
            else:
                if self.identifier[str(ctx.guild.id)] == "False":
                    self.identifier[str(ctx.guild.id)] = "True"
                    report += "Enabled farewell messages"
        if str(ctx.guild.id) not in self.channel:
            self.channel[str(ctx.guild.id)] = ctx.channel.id
            report += f"\nFarewell channel not set, therefore it has been automatically set to `{ctx.channel.name}`"
        if str(ctx.guild.id) not in self.useimages:
            self.useimages[str(ctx.guild.id)] = "False"
            report += "\nUseimages not set, therefore it has been automatically set to `false`"
        if str(ctx.guild.id) not in self.toxicity:
            self.toxicity[str(ctx.guild.id)] = "False"
            report += (
                "\nToxicity not set, therefore it has been automatically set to `false`"
            )
        self.save()
        await ctx.send(report)

    @_farewell.command(name="enable")
    async def _enable(self, ctx):
        report = ""
        if str(ctx.guild.id) not in self.identifier:
            self.identifier[str(ctx.guild.id)] = "True"
            report += "Enabled farewell messages"
        else:
            self.identifier[str(ctx.guild.id)] = "True"
            report += "Enabled farewell messages"
        if str(ctx.guild.id) not in self.channel:
            self.channel[str(ctx.guild.id)] = ctx.channel.id
            report += f"\nFarewell channel not set, therefore it has been automatically set to `{ctx.channel.name}`"
        if str(ctx.guild.id) not in self.useimages:
            self.useimages[str(ctx.guild.id)] = "False"
            report += "\nUseimages not set, therefore it has been automatically set to `false`"
        if str(ctx.guild.id) not in self.toxicity:
            self.toxicity[str(ctx.guild.id)] = "False"
            report += (
                "\nToxicity not set, therefore it has been automatically set to `false`"
            )
        self.save()
        await ctx.send(report)

    @_farewell.command(name="disable")
    async def _disable(self, ctx):
        report = ""
        if str(ctx.guild.id) not in self.identifier:
            self.identifier[str(ctx.guild.id)] = "False"
            report += "Disabled farewell messages"
        else:
            self.identifier[str(ctx.guild.id)] = "False"
            report += "Disabled farewell messages"
        self.save()
        await ctx.send(report)

    @_farewell.command(name="setchannel")
    async def _setchannel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        self.channel[str(ctx.guild.id)] = channel.id
        self.save()
        await ctx.send(f"Set the farewell channel to `{channel.name}`")

    @_farewell.command(name="useimages")
    async def _useimages(self, ctx, toggle=None):
        if toggle is None:
            if str(ctx.guild.id) not in self.useimages:
                self.useimages[str(ctx.guild.id)] = "True"
                await ctx.send("Enabled `useimages`")
            else:
                if self.useimages[str(ctx.guild.id)] == "False":
                    self.useimages[str(ctx.guild.id)] = "True"
                    await ctx.send("Enabled `useimages`")
                else:
                    self.useimages[str(ctx.guild.id)] = "False"
                    await ctx.send("Disabled `useimages`")
        else:
            toggle = toggle.lower()
            if toggle == "true":
                self.useimages[str(ctx.guild.id)] = "True"
                await ctx.send("Enabled `useimages`")
            else:
                if toggle == "false":
                    self.useimages[str(ctx.guild.id)] = "False"
                    await ctx.send("Disabled `useimages`")
        self.save()

    @_farewell.command(name="toxicity")
    async def _toxicity(self, ctx, toggle=None):
        if toggle is None:
            if str(ctx.guild.id) not in self.useimages:
                self.useimages[str(ctx.guild.id)] = "True"
                await ctx.send("Enabled `toxicity`")
            else:
                if self.useimages[str(ctx.guild.id)] == "False":
                    self.useimages[str(ctx.guild.id)] = "True"
                    await ctx.send("Enabled `toxicity`")
                else:
                    self.useimages[str(ctx.guild.id)] = "False"
                    await ctx.send("Disabled `toxicity`")
        else:
            toggle = toggle.lower()
            if toggle == "true":
                self.useimages[str(ctx.guild.id)] = "True"
                await ctx.send("Enabled `toxicity`")
            else:
                if toggle == "false":
                    self.useimages[str(ctx.guild.id)] = "False"
                    await ctx.send("Disabled `toxicity`")
        self.save()

    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.identifier:
            if self.identifier[str(member.guild.id)] == "True":
                message = None
                channel = self.bot.get_channel(self.channel[guild_id])
                path = (
                    os.getcwd()
                    + "/data/images/reactions/farewell/"
                    + random.choice(
                        os.listdir(os.getcwd() + "/data/images/reactions/farewell/")
                    )
                )
                e = discord.Embed(color=0x80B0FF)
                if self.toxicity[str(member.guild.id)] == "True":
                    toxicity = random.choice(
                        [
                            "and good riddance",
                            "and please never come back",
                            "I've always gagged every time I read one of your messages",
                            "never come back",
                        ]
                    )
                    message = f"Cya {member.name}, {toxicity}"
                else:
                    e.set_author(name=f"Cya {member.name}")
                if self.useimages[str(member.guild.id)] == "True":
                    e.set_image(url="attachment://" + os.path.basename(path))
                    if message == None:
                        await channel.send(
                            file=discord.File(path, filename=os.path.basename(path)),
                            embed=e,
                        )
                    else:
                        await channel.send(
                            message,
                            file=discord.File(path, filename=os.path.basename(path)),
                            embed=e,
                        )
                else:
                    if message == None:
                        await channel.send(embed=e)
                    else:
                        await channel.send(message)


def setup(bot):
    bot.add_cog(Farewell(bot))
