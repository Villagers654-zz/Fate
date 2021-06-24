"""
cogs.fun.actions
~~~~~~~~~~~~~~~~~

A cog for rp actions

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from discord.ext import commands
import discord
import random


class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.protected = [
            264838866480005122,  # luck
            355026215137968129,  # tother
            243233669148442624,  # opal
            506735111543193601,  # Fate
            644579811607707659   # Cabaretta
        ]
        self.mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

    @commands.command(description="Shoots a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shoot(self, ctx, user: discord.Member):
        if user.id in self.protected:
            if ctx.author.id in self.protected:
                return await ctx.send("nO")
            return await ctx.send("*shoots you instead*")
        results = [
            "$user got shot in the head and died instantly",
            "$user got shot in the heart and died quickly and painfully",
            "$user got shot in the arm and is rolling around in agonizing pain",
            "$user got shot in the leg and is now hopping around on one leg",
            "$user got shot in the dick",
            "$user pulled his own gun out and shot you first, seems my stage 4 brain cancer is faster than you",
            "$author shot $user skillfully; piercing $user's heart",
        ]
        result = (
            random.choice(results)
            .replace("$user", user.mention)
            .replace("$author", ctx.author.mention)
        )
        await ctx.send(f"🔫 | pew pew, {result}", allowed_mentions=self.mentions)

    def shoot_usage(self):
        return discord.Embed(description="yeet yoot shoot help")

    @commands.command(description="Injects a user with something random")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def inject(self, ctx, user: discord.Member):
        if user.id in self.protected:
            if ctx.author.id in self.protected:
                return await ctx.send("nO")
            return await ctx.send("*injects you instead*")
        injections = [
            "AIDS",
            "HIV positive blood",
            "an STD",
            "the cure",
            "FLex Seal",
            "Kool-Aid powder",
            "soda",
            "the flu",
            "Coronavirus",
            "Covid-19",
        ]
        choices = [
            "$user has been injected with $injection",
            "$user was injected with $injection and died",
            "injected $injection into $user's dick",
            "$user was injected with $injection and got autism",
            "$author tripped and injected themself with $injection",
        ]
        choice = (
            random.choice(choices)
            .replace("$user", user.mention)
            .replace("$author", ctx.author.mention)
        )
        await ctx.send(
            f"💉 | {choice.replace('$injection', random.choice(injections))}",
            allowed_mentions=self.mentions
        )

    @commands.command(description="Slices anything into bits")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slice(self, ctx, user: discord.Member):
        if user.id in self.protected:
            if ctx.author.id in self.protected:
                return await ctx.send("nO")
            return await ctx.send("*slices you instead*")
        await ctx.send(
            "⚔ | {} {}".format(user.mention, random.choice([
                "just got sliced up into sushi",
                "just got sliced up into string cheese",
                "just got their paycheck sliced in half",
                "got sliced and diced just like the carrots in my salad",
            ])),
            allowed_mentions=self.mentions
        )

    @commands.command(description="Boops a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def boop(self, ctx, user: discord.Member):
        await ctx.send(
            "<@{}> {} boops {}".format(
                ctx.author.id,
                random.choice(
                    ["sneakily", "sexually", "forcefully", "gently", "softly"]
                ),
                user.name,
            ), allowed_mentions=self.mentions
        )
        await ctx.message.delete()

    @commands.command(description="Stabs a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def stab(self, ctx, user: discord.Member):
        if user.id in self.protected:
            if ctx.author.id in self.protected:
                return await ctx.send("nO")
            return await ctx.send("*stabs you instead*")
        await ctx.send(
            "⚔ | {} {}, {}".format(
                user.mention,
                random.choice([
                    "has been stabbed in the head",
                    "has been stabbed in the shoulder",
                    "has been stabbed in the chest",
                    "has been stabbed in the arm",
                    "has been stabbed in the gut",
                    "has been stabbed in the dick",
                    "has been stabbed in the leg",
                    "has been stabbed in the foot",
                ]),
                random.choice([
                    "you really shouldn't let a bot carry a blade :p",
                    "you should let me stab people more often",
                    "you should let me stab **it** more often",
                    "this is fun",
                    "poor thing didn't stand a chance",
                    "whatever that **thing** is, it definitely deserved it",
                    "poor thing dropped like a fly",
                ]),
            ), allowed_mentions=self.mentions
        )


def setup(bot):
    bot.add_cog(Actions(bot))
