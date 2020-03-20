from discord.ext import commands
import discord
import random
import requests
import json
import os
from utils import colors


class Custom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def luck(ctx):
        return ctx.message.author.id == 264838866480005122

    def tm(ctx):
        return ctx.author.id in [264838866480005122, 355026215137968129]

    @commands.command(name="hernie")
    async def hernie(self, ctx):
        choices = [
            "I knew i smelled cookies wafting from the ovens of the little elves who live between your dickless legs",
            "micro-dick hernie",
            'Hernie has a "not enough storage" dick',
            "Hernie has a fatal error in the cock department",
            "FitMC made me a personal picture, u mad?",
            "BarrenDome made me a personal picture, u mad?",
            "Salc1 made me a personal picture, u mad?",
            "Heart and Soul is the best song ever made, don't @ Hernie",
            "PayPal me 5 and I'll give you a kiss",
            "Family guy is a masterpiece and no one can change my mind",
            "Heart and Soul is the best song ever made, don't @ Hernie",
            "Step one, step two, do my dance in this bitch, "
            "Got a hunnid some' drums like a band in this bitch. Mane she keep on bitchin', all that naggin' and shit, "
            "Hoe shut the fuck up and jus' gag on this dick",
            "Hernie's address is [redacted]",
        ]
        await ctx.send(random.choice(choices))

    @commands.command()
    async def nigward(self, ctx):
        e = discord.Embed(color=0xFF0000)
        e.set_image(
            url="https://cdn.discordapp.com/attachments/501492059765735426/505687664805281802/Nigward.jpg"
        )
        await ctx.send(embed=e)

    @commands.command()
    async def agent(self, ctx):
        await ctx.send(
            random.choice(
                ["big gay", "kys", "get off me property", "now that's alotta damage"]
            )
        )
        await ctx.message.delete()

    @commands.command()
    async def yarnamite(self, ctx):
        await ctx.send("go back to your ghetto!!!!")

    @commands.command(name="villicool112")
    async def villicool(self, ctx):
        await ctx.send("villicool112 is indeed cool")

    # @commands.command(name='elon', aliases=['elongated', 'elongatedmuskrat'])
    # @commands.cooldown(1, 3, commands.BucketType.user)
    # async def elon(self, ctx):
    # 	with open('./data/images/urls/nekos.txt', 'r') as f:
    # 		image_urls = f.readlines()
    # 	e = discord.Embed(color=colors.cyan())
    # 	e.set_image(url=random.choice(image_urls))
    # 	await ctx.send(embed=e)

    @commands.command(name="opal")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def opal(self, ctx):
        with open("./data/images/urls/opal.txt", "r") as f:
            image_urls = f.readlines()
        e = discord.Embed(color=colors.cyan())
        e.set_image(url=random.choice(image_urls))
        await ctx.send(embed=e)

    @commands.command(name="cactus")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(
        embed_links=True, attach_files=True, manage_messages=True
    )
    async def _cactus(self, ctx):
        apikey = "LIWIXISVM3A7"
        lmt = 50
        r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
        if r.status_code == 200:
            anon_id = json.loads(r.content)["anon_id"]
        else:
            anon_id = ""
        r = requests.get(
            "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s"
            % ("cactus", apikey, lmt, anon_id)
        )
        if r.status_code == 200:
            try:
                dat = json.loads(r.content)
                e = discord.Embed(color=colors.random())
                e.set_image(
                    url=dat["results"][random.randint(0, len(dat["results"]) - 1)][
                        "media"
                    ][0]["gif"]["url"]
                )
                await ctx.send(embed=e)
            except Exception as e:
                await ctx.send(e)
        else:
            await ctx.send("error")

    @commands.command(name="lion")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(
        embed_links=True, attach_files=True, manage_messages=True
    )
    async def _lion(self, ctx):
        apikey = "LIWIXISVM3A7"
        lmt = 50
        r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
        if r.status_code == 200:
            anon_id = json.loads(r.content)["anon_id"]
        else:
            anon_id = ""
        r = requests.get(
            "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s"
            % ("baby lion", apikey, lmt, anon_id)
        )
        if r.status_code == 200:
            try:
                dat = json.loads(r.content)
                e = discord.Embed(color=colors.random())
                e.set_image(
                    url=dat["results"][random.randint(0, len(dat["results"]) - 1)][
                        "media"
                    ][0]["gif"]["url"]
                )
                await ctx.send(embed=e)
            except Exception as e:
                await ctx.send(e)
        else:
            await ctx.send("error")

    @commands.command(name="tother")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def tother(self, ctx):
        choices = [
            "Fagitos",
            "https://discord.gg/BQ23Z2E",
            "Reeeeeeeeeeeeeeeeeeeeeee",
            "pUrE wHiTe pRiVelIdgEd mALe",
            "there's a wasp sucking out all my stick juices",
            "Really? That's the sperm that won?",
            "May the fly be with you",
            "You're not you when you're hungry",
            "I recognize that flower, see you soon :)",
            "FBI OPEN UP",
            "Sponsored by Samsung",
            "iLiKe NuT",
            "Florin joins, Yall dislocate yo joints...",
            "old school tricks rise again",
            "i can't see, my thumbs are in the way",
            "All Heil nut",
            "SARGON NEED MORE DOPAMINE",
            ".prune 1000",
            "Nani",
            "I’m more blind then Hitler when he had that chlorine gas up in his eye",
            "real art^",
            "2b2t.org is a copy of the middle east",
            "warned for advertising",
            "jOiN sR",
            "6 million juice",
            "The 7th SR Fag",
            "7th team lgbt",
            "DAiLy reMinDer sEx RoboTs coSt lesS thAn ReAl gRilLs",
            "elon's musk",
            "Fuck the battle cat",
            "9/11",
            "is it bad language or bad code",
            "clonk gay",
            "i have social diabetes",
            "https://cdn.discordapp.com/attachments/457322344818409482/531321000361721856/image0-1.jpg",
            "Tother: Sharon",
            "we're giving them what they want, if they wanna identify as a peice of coal we can burn them freely",
            f"You've been muted for spam in {ctx.guild.name} for 2 minutes and 30 seconds",
        ]
        await ctx.send(random.choice(choices))

    @commands.command(name="trash")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def trash(self, ctx):
        choices = ["the best piece of garbage faggot"]
        await ctx.send(random.choice(choices))

    @commands.command(name="orange")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.cooldown(3, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True)
    async def orange(self, ctx):
        files = os.listdir("./data/images/custom/orange_emotes")
        await ctx.send(
            file=discord.File(
                f"./data/images/custom/orange_emotes/{random.choice(files)}"
            )
        )


def setup(bot):
    bot.add_cog(Custom(bot))
