from discord.ext import commands
import discord
import random
import requests
import json
import os
from botutils import colors
import asyncio


class Custom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    @staticmethod
    def luck(ctx):
        return ctx.message.author.id == 264838866480005122

    @staticmethod
    def tm(ctx):
        return ctx.author.id in [264838866480005122, 355026215137968129]

    @commands.command(name="kio")
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def kio(self, ctx):
        await ctx.send("Kio is a nice boyo 👉👈")

    @commands.command(name="riester")
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def riester(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/788980129031258163/788980519424884786/southparkmexican.png")

    @commands.command(name="kaizen")
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def kaizen(self, ctx):
        await ctx.message.add_reaction(self.bot.get_emoji(764961946491289620))
        await ctx.send("https://cdn.discordapp.com/attachments/681086116195074060/788123405156089916/seal_saturday.mp4")

    @commands.command(name="sploop")
    async def sploop(self, ctx):
        await ctx.send("https://cdn.discordapp.com/avatars/677306009957433404/8a0d8f14aec36096b3de0c9b8be52cd5.png?size=1024")

    @commands.command(name="pog", aliases=["pog.", "poggers"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def pog(self, ctx):
        await ctx.send(file=discord.File("./data/videos/brassmonkey.mp4"))

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

    @commands.command()
    async def eppy(self, ctx: commands.Context):
        """the best command"""
        await ctx.send(
            embed=discord.Embed(
                color=6536612,
                title="Fate > BMO",
                description=f"[Invite]({self.bot.invite_url})",
            )
        )

    @commands.command(name="thot", aliases=["noofy"])
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def thot(self, ctx):
        async with ctx.channel.typing():
            await ctx.message.delete()
            await ctx.send("*inhales*")
            await asyncio.sleep(2)
            await ctx.send("*exhales*")
            await asyncio.sleep(1)
            await ctx.send("THOT")

    @commands.command(name="chaos")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def chaos(self, ctx):
        await ctx.send("*calling the chaotic god*")
        await ctx.send(self.bot.get_user(493082973906927616).mention)

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

    @commands.command(name="hack")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.cooldown(3, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True)
    async def hack(self, ctx):
        await ctx.send("Ender will tamper with your files")

    @commands.command(name="rick")
    @commands.cooldown(1, 500, commands.BucketType.user)
    @commands.bot_has_permissions(attach_files=True)
    async def _rick(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                color=0x64FF00,
                image_url="https://cdn.discordapp.com/attachments/732085276733603974/732156247243227176/image0.jpg",
                description=u"\u200b"
            )
        )


def setup(bot):
    bot.add_cog(Custom(bot))
