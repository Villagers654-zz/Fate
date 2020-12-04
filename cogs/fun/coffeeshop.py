from discord.ext import commands
import discord
import random


class CoffeeShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="coffee", aliases=["coffeeshop", "cs"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def coffee(self, ctx):
        await ctx.send(
            "**```~~~====🥂🍸🍷Coffee Shop🍷🍸🥂====~~~```**```"
            "• StrawberriesAndCream - 1 kiss\n"
            "• Espresso - 1 hug\n"
            "• IcedCoffee - 1 slap\n"
            "• Mocha -  sum tears```"
        )

    @commands.command(enabled=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def strawberriesandcream(self, ctx):
        e = discord.Embed(color=0xE5CB90)
        e.set_author(
            name=f"{ctx.author.name} kisses {self.bot.user.name}",
            icon_url=ctx.author.avatar_url,
        )
        e.description = "Here's your Strawberries and Cream"
        e.set_image(
            url="https://cdn.discordapp.com/attachments/501871950260469790/511578465800159244/strawberriescreamfrapp.jpg"
        )
        e.set_footer(
            text=random.choice(
                [
                    "Powered by CortexPE",
                    "Powered by Luck",
                    "Powered by Tothy",
                    "Powered by Thready",
                    "Powered by slaves",
                    "Powered by Beddys ego",
                    "Powered by Samsung",
                    "Powered by the supreme",
                    "Powered by doritos",
                    "Cooldown: 5 seconds",
                ]
            )
        )
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def espresso(self, ctx):
        fate = self.bot.get_user(506735111543193601)
        e = discord.Embed(color=0xE5CB90)
        e.set_author(
            name=f"{ctx.author.name} hugs {fate.name}", icon_url=ctx.author.avatar_url
        )
        e.description = "Here's your espresso"
        e.set_footer(
            text=random.choice(
                [
                    "Drinking espresso could be key to cutting your risk of prostate cancer",
                    "Powered by CortexPE",
                    "Powered by Luck",
                    "Powered by Tothy",
                    "Powered by Thready",
                    "Powered by slaves",
                    "Powered by Beddys ego",
                    "Powered by Samsung",
                    "Powered by the supreme",
                    "Powered by doritos",
                    "Cooldown: 5 seconds",
                ]
            )
        )
        e.set_image(
            url=random.choice(
                [
                    "https://cdn.discordapp.com/attachments/501871950260469790/511747452257173545/IKAWA-espresso-roast-espresso-cappuccino-1024x576.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511747462227165214/85153452-56a176765f9b58b7d0bf84dd.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511750545938055168/espresso-cafeniro-com.jpg",
                ]
            )
        )
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def expresso(self, ctx):
        await ctx.send(
            "https://cdn.discordapp.com/attachments/501871950260469790/511572631384752129/espresso-not-expresso-2.png"
        )

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def icedcoffee(self, ctx):
        fate = self.bot.get_user(506735111543193601)
        e = discord.Embed(color=0xE5CB90)
        e.set_author(
            name=f"{fate.name} slaps {ctx.author.name}", icon_url=ctx.author.avatar_url
        )
        e.description = "Here's your Iced Coffee"
        e.set_footer(
            text=random.choice(
                [
                    "Powered by CortexPE",
                    "Powered by Luck",
                    "Powered by Tothy",
                    "Powered by Thready",
                    "Powered by slaves",
                    "Powered by Beddys ego",
                    "Powered by Samsung",
                    "Powered by the supreme",
                    "Powered by doritos",
                    "Cooldown: 5 seconds",
                ]
            )
        )
        e.set_image(
            url=random.choice(
                [
                    "https://cdn.discordapp.com/attachments/501871950260469790/511757901195509770/img48l.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511757901556351016/Vegan-Iced-Coffee-13.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511757908829143041/BBYePZZ4TAisolysQWvR_1coffee.jpg",
                ]
            )
        )
        await ctx.send(embed=e)

    @commands.command(enabled=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mocha(self, ctx):
        cry = discord.Embed(color=0x80B0FF)
        cry.set_author(
            name=f"◈ {ctx.author.name} starts crying ◈", icon_url=ctx.author.avatar_url
        )
        cry.set_image(url="null")
        e = discord.Embed(color=0xE5CB90)
        e.description = "Here's your Mocha"
        e.set_footer(
            text=random.choice(
                [
                    "Powered by CortexPE",
                    "Powered by Luck",
                    "Powered by Tothy",
                    "Powered by Thready",
                    "Powered by slaves",
                    "Powered by Beddys ego",
                    "Powered by Samsung",
                    "Powered by the supreme",
                    "Powered by doritos",
                    "Cooldown: 10 seconds",
                ]
            )
        )
        e.set_image(
            url=random.choice(
                [
                    "https://cdn.discordapp.com/attachments/501871950260469790/511752344229380126/homemade-mocha-e1452548176858.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511752349828513799/white-russian-mocha-cocktail-11.jpg",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511752359156776960/20181112_225859.jpg",
                ]
            )
        )
        await ctx.send(embed=cry)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(CoffeeShop(bot))