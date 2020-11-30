import asyncio
import base64
import json
import random
from os import path
from random import random as rd
from datetime import datetime, timedelta
from contextlib import suppress

import aiohttp
import discord
import praw
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from discord.ext import tasks

from utils import colors, auth

code = "```py\n{0}\n```"
sexualities = [
    "allosexual",
    "allosexism",
    "androsexual",
    "asexual",
    "aromantic",
    "autosexual",
    "autoromantic",
    "bicurious",
    "bisexual",
    "biromantic",
    "closeted",
    "coming out",
    "cupiosexual",
    "demisexual",
    "demiromantic",
    "fluid",
    "gay",
    "graysexual",
    "grayromantic",
    "gynesexual",
    "heterosexual",
    "homosexual",
    "lesbian",
    "lgbtqia+",
    "libidoist asexual",
    "Monosexual",
    "non-libidoist asexual",
    "omnisexual",
    "pansexual",
    "panromantic",
    "polysexual",
    "pomosexual",
    "passing",
    "queer",
    "questioning",
    "romantic attraction",
    "sapiosexual",
    "sexual attraction",
    "sex-averse",
    "sex-favorable",
    "sex-indifferent",
    "sex-repulsed",
    "skoliosexual",
    "spectrasexual",
    "straight",
    "bi",
    "ace",
]


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dat = {}
        self.bullying = []
        self.gay = {sexuality: {} for sexuality in sexualities}
        self.gp = "./data/userdata/gay.json"
        if path.isfile(self.gp):
            with open(self.gp, "r") as f:
                self.gay = json.load(f)
        for sexuality in sexualities:
            if sexuality not in self.gay:
                self.gay[sexuality] = {}
        self.clear_old_messages_task.start()

    def cog_unload(self):
        self.clear_old_messages_task.stop()

    def save_gay(self):
        with open(self.gp, "w") as f:
            json.dump(self.gay, f, ensure_ascii=False)

    @commands.command(name="bully")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(send_messages=True)
    async def bully(self, ctx, user: discord.Member):
        """ Bullies a target user :] """

        def cleanup():
            """ remove channel from list of active bullying channels """
            self.bullying.remove(ctx.channel.id)

        if ctx.channel.id in self.bullying:
            return await ctx.send("I'm already bullying someone :[")
        self.bullying.append(ctx.channel.id)
        await ctx.send("I might as well..")

        try:
            creds = auth.Reddit()
            reddit = praw.Reddit(
                client_id=creds.client_id,
                client_secret=creds.client_secret,
                user_agent=creds.user_agent,
            )
        except Exception as e:
            await ctx.send(f"Error With Reddit Credentials\n{e}")
            return cleanup()

        reddits = ["insults", "rareinsults"]
        reddit_posts = []  # type: praw.Reddit.submission

        for reddit_page in reddits:
            for submission in reddit.subreddit(reddit_page).hot(limit=250):
                exts = [".png", ".jpg", ".jpeg", ".gif"]
                if submission.title and all(ext not in submission.url for ext in exts):
                    if (
                        "insult" not in submission.title
                        and "roast" not in submission.title
                    ):
                        reddit_posts.append(submission)

        for i in range(5):
            random.shuffle(reddit_posts)
        for iteration, submission in enumerate(reddit_posts[:3]):

            def pred(m):
                return m.channel.id == ctx.channel.id and m.author.id == user.id

            try:
                msg = await self.bot.wait_for("message", check=pred, timeout=60)
            except asyncio.TimeoutError:
                continue
            if "stop" in msg.content or "cancel" in msg.content:
                await ctx.send("*yeets out the door*")
                break
            try:
                await asyncio.sleep(random.randint(1, 3))
                async with ctx.channel.typing():
                    await asyncio.sleep(len(submission.title) * 0.1)
                    await ctx.send(submission.title)
            except discord.errors.Forbidden:
                break

        cleanup()

    @commands.command(name="meme")
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def meme(self, ctx):
        """ fetches a random meme from a random meme subreddit """
        creds = auth.Reddit()
        reddit = praw.Reddit(
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            user_agent=creds.user_agent,
        )

        reddits = ["memes", "dankmemes", "MemeEconomy", "ComedyCemetery"]
        reddit_posts = []  # type: praw.Reddit.submission

        for submission in reddit.subreddit(random.choice(reddits)).hot(limit=100):
            extensions = [".png", ".jpg", ".jpeg", ".webp", "gif"]
            if any(ext in submission.url for ext in extensions):
                reddit_posts.append(submission)

        post = random.choice(reddit_posts)
        e = discord.Embed(color=colors.red())
        e.set_author(
            name=post.title, icon_url=post.author.icon_img if post.author else None
        )
        e.set_image(url=post.url)
        e.set_footer(
            text=f"{post.author.name} | 👍 {post.score} | 💬 {post.num_comments}"
        )
        await ctx.send(embed=e)

    @commands.command(name="snipe")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def snipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id not in self.dat:
            await ctx.send("Nothing to snipe", delete_after=1)
            return await ctx.message.delete()
        if ctx.message.mentions:
            user_id = ctx.message.mentions[0].id
            if user_id not in self.dat[channel_id]:
                await ctx.send("Nothing to snipe", delete_after=1)
                return await ctx.message.delete()
            msg, time = self.dat[channel_id][user_id]
        else:
            msg, time = self.dat[channel_id]["last"]
        if msg.embeds:
            await ctx.send(f"{msg.author} at {time}", embed=msg.embeds[0])
        else:
            e = discord.Embed(color=msg.author.color)
            e.set_author(name=msg.author, icon_url=msg.author.avatar_url)
            e.description = msg.content[:2048]
            e.set_footer(text=time)
            await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, m: discord.Message):
        if m.content or m.embeds:
            channel_id = m.channel.id
            user_id = m.author.id
            dat = (m, m.created_at.strftime("%I:%M%p UTC on %b %d, %Y"))
            if channel_id not in self.dat:
                self.dat[channel_id] = {}
            self.dat[channel_id]["last"] = dat
            self.dat[channel_id][user_id] = dat

    @tasks.loop(minutes=25)
    async def clear_old_messages_task(self):
        expiration = datetime.utcnow() - timedelta(hours=1)
        for channel_id, data in list(self.dat.items()):
            if data["last"][0].created_at < expiration:
                del self.dat[channel_id]
                continue
            for key, value in list(data.items()):
                if key != "last":
                    if value[0].created_at < expiration:
                        with suppress(KeyError, ValueError):
                            del self.dat[channel_id][key]

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.embeds and not after.embeds:
            channel_id = before.channel.id
            user_id = before.author.id
            dat = (before, before.created_at.strftime("%I:%M%p UTC on %b %d, %Y"))
            if channel_id not in self.dat:
                self.dat[channel_id] = {}
            self.dat[channel_id]["last"] = dat
            self.dat[channel_id][user_id] = dat

    @commands.command(name="sex", aliases=["sexdupe"], enabled=False)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sex(self, ctx, user: discord.User):
        await ctx.send(f"Sent instructions on the {user.name} sex dupe to dms")

    @commands.command(name="fancify", aliases=["cursive"])
    @commands.cooldown(2, 3, commands.BucketType.channel)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def fancify(self, ctx, *, text: str):
        output = ""
        for letter in text:
            if 65 <= ord(letter) <= 90:
                output += chr(ord(letter) + 119951)
            elif 97 <= ord(letter) <= 122:
                output += chr(ord(letter) + 119919)
            elif letter == " ":
                output += " "
            else:
                output += letter
        if (
            isinstance(ctx.guild, discord.Guild)
            and ctx.channel.permissions_for(ctx.guild.me).manage_webhooks
        ):
            webhook = await ctx.channel.create_webhook(name="Fancify")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(
                    webhook.url, adapter=AsyncWebhookAdapter(session)
                )
                await webhook.send(
                    output,
                    username=ctx.author.display_name,
                    avatar_url=ctx.author.avatar_url,
                    allowed_mentions=self.bot.allowed_mentions
                )
                await webhook.delete()
            await ctx.message.delete()
        else:
            await ctx.send(output)

    @commands.command(pass_context=True)
    async def encode(self, ctx, encoder: int, *, message):
        usage = "`.encode {16, 32, or 64} {message}`"
        if encoder not in [16, 32, 64]:
            await ctx.send(usage)
        else:
            if encoder == 16:
                encode = base64.b16encode(message.encode())
            elif encoder == 32:
                encode = base64.b32encode(message.encode())
            elif encoder == 64:
                encode = base64.b64encode(message.encode())
            else:
                return await ctx.send(f"Invalid Encoder:\n{usage}")
            await ctx.send(encode.decode())

    @commands.command(pass_context=True)
    async def decode(self, ctx, decoder: int, *, message):
        usage = "`.decode {16, 32, or 64} {message}`"
        if decoder not in {16, 32, 64}:
            await ctx.send(usage)
        else:
            try:
                if decoder == 16:
                    decode = base64.b16decode(message.encode())
                elif decoder == 32:
                    decode = base64.b32decode(message.encode())
                elif decoder == 64:
                    decode = base64.b64decode(message.encode())
                else:
                    return await ctx.send(f"Invalid decoder:\n{usage}")
                await ctx.send(self.bot.utils.cleanup_msg(str(decode.decode())))
            except:
                await ctx.send(f"That's not properly encoded in {decoder}")

    @commands.command(name="liedetector", aliases=["ld"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def liedetector(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        r = random.randint(50, 100)
        e = discord.Embed(color=0x0000FF)
        e.set_author(
            name="{}'s msg analysis".format(member.name), icon_url=member.avatar_url
        )
        e.description = "{}% {}".format(
            r, random.choice(["truth", "the truth", "a lie", "lie"])
        )
        await ctx.send(embed=e)
        await ctx.message.delete()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def personality(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        e = discord.Embed(
            color=random.choice(
                [0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082]
            )
        )
        e.set_author(
            name="{}'s Personality".format(member.name), icon_url=member.avatar_url
        )
        e.set_thumbnail(url=member.avatar_url)
        e.add_field(
            name="Type",
            value=f'{random.choice(["psychopath", "depressed", "cheerful", "bright", "dark", "god", "deceiver", "funny", "fishy", "cool", "insecure", "lonely", "optimistic", "brave", "brilliant", "dreamer", "Nurturer", "Peaceful", "Overthinker", "Idealist", "Pussy"])}',
            inline=False,
        )
        e.add_field(
            name="Social Status",
            value=f'{random.choice(["Ho", "Slut", "Loser", "The nice guy", "The dick", "Dank memer"])}',
            inline=False,
        )
        e.add_field(
            name="Hobby",
            value=f'{random.choice(["Art", "Drawing", "Painting", "Singing", "Writing", "Anime", "Memes", "Minecraft", "Sucking dick"])}',
            inline=False,
        )
        e.add_field(
            name="Music Genre",
            value=f'{random.choice(["Nightcore", "Heavy Metal", "Alternative", "Electronic", "Classical", "Dubstep", "Jazz", "Pop", "Rap"])}',
            inline=False,
        )
        await ctx.send(embed=e)
        await ctx.message.delete()

    @commands.command()
    async def notice(self, ctx):
        await ctx.send(
            random.choice(
                [
                    "Depression Strikes Again",
                    "Would you like an espresso for your depresso",
                    "You're not you when you're hungry",
                    "Tfw you realise flies get laid more than you^",
                    "*crippling depression*",
                    "Really? That's the sperm that won?",
                    "Breakdown sponsored by Samsung",
                    "pUrE wHiTe pRiVelIdgEd mALe^",
                ]
            )
        )
        await ctx.message.delete()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pain(self, ctx):
        await ctx.send("Spain but the s is silent")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def spain(self, ctx):
        await ctx.send("Pain but with an s")

    @commands.command()
    async def choose(self, ctx, *choices: str):
        if len(choices) < 2:
            return await ctx.send("You need to provide at least 2 choices when running this command")
        await ctx.send(random.choice(choices))

    @commands.command(pass_context=True)
    async def mock(self, ctx, *, message):
        msgbuf = ""
        uppercount = 0
        lowercount = 0
        for c in message:
            if c.isalpha():
                if uppercount == 2:
                    uppercount = 0
                    upper = False
                    lowercount += 1
                elif lowercount == 2:
                    lowercount = 0
                    upper = True
                    uppercount += 1
                else:
                    upper = rd() > 0.5
                    uppercount = uppercount + 1 if upper else 0
                    lowercount = lowercount + 1 if not upper else 0
                msgbuf += c.upper() if upper else c.lower()
            else:
                msgbuf += c
        await ctx.send(msgbuf)
        await asyncio.sleep(0.5)
        await ctx.message.delete()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rate(self, ctx):
        async for msg in ctx.channel.history(limit=3):
            if msg.id != ctx.message.id:
                await msg.add_reaction(
                    random.choice(
                        ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
                    )
                )
                return await ctx.message.delete()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def soul(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        r = random.randint(0, 1000)
        e = discord.Embed(color=0xFFFF00)
        e.set_author(name=f"{member.name}'s Soul Analysis", icon_url=member.avatar_url)
        e.description = f"{r} grams of soul"
        await ctx.send(embed=e)

    @commands.command()
    async def roll(self, ctx):
        await ctx.send(random.choice(["1", "2", "3", "4", "5", "6"]))

    @commands.command(name="ask", aliases=["8ball"])
    async def ask(self, ctx):
        await ctx.send(
            random.choice(
                [
                    "Yes",
                    "No",
                    "It's certain",
                    "110% no",
                    "It's uncertain",
                    "Ofc",
                    "I think not m8",
                    "Ig",
                    "Why not ¯\_(ツ)_/¯",
                    "Ye",
                    "Yep",
                    "Yup",
                    "tHe AnSwEr LiEs WiThIn",
                    "Basically yes^",
                    "Not really",
                    "Well duh",
                    "hell yeah",
                    "hell no",
                ]
            )
        )

    @commands.command(
        name="sexuality", aliases=[s.strip(" ") for s in sexualities[::1]]
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def sexuality(self, ctx, percentage=None):
        usage = (
            f"Usage: `{self.bot.utils.get_prefix(ctx)}{ctx.invoked_with} percentage/reset/help`"
            f"\nExample Usage: `{self.bot.utils.get_prefix(ctx)}{ctx.invoked_with} 75%`"
            f"\n\nThe available sexualities are {', '.join(sexualities)}."
        )
        invoked_with = str(ctx.invoked_with).lower()
        if invoked_with == "sexuality":
            return await ctx.send(usage)
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        user_id = str(user.id)
        if percentage and not ctx.message.mentions:
            if percentage.lower() == "reset":
                if user_id not in self.gay[invoked_with]:
                    return await ctx.send("You don't have a custom percentage set")
                del self.gay[invoked_with][user_id]
                await ctx.send(f"Removed your custom {invoked_with} percentage")
            elif percentage.lower() == "help":
                return await ctx.send(usage)
            else:
                stripped = percentage.strip("%")
                if not stripped.isdigit():
                    return await ctx.send("The percentage needs to be an integer")
                if int(stripped) > 100:
                    return await ctx.send("That's too high of a percentage")
                self.gay[invoked_with][user_id] = int(stripped)
                self.save_gay()
                await ctx.send(
                    f"Use `{self.bot.utils.get_prefix(ctx)}{invoked_with} reset` to go back to random results"
                )
        e = discord.Embed(color=user.color)
        e.set_author(name=str(user), icon_url=user.avatar_url)
        percentage = random.randint(0, 100)
        if user_id in self.gay[invoked_with]:
            percentage = self.gay[invoked_with][user_id]
        e.description = f"{percentage}% {invoked_with}"
        await ctx.send(embed=e)

    @commands.command(
        name="cringe",
        aliases=[
            "based",
            "penis",
            "shit",
            "bruh",
            "high",
            "smart",
            "stupid",
            "dumb",
            "chad",
            "epic",
            "lucky",
            "unlucky",
            "hot",
            "sexy",
            "ugly",
            "hitler",
        ],
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def cringe(self, ctx):
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        e = discord.Embed(color=user.color)
        e.set_author(name=str(user), icon_url=user.avatar_url)
        percentage = random.randint(0, 100)
        if ctx.invoked_with == "hitler":
            if random.randint(1, 4) == 1:
                ctx.invoked_with = f"worse than {ctx.invoked_with}"
        e.description = f"{percentage}% {ctx.invoked_with}"
        await ctx.send(embed=e)

    @commands.command()
    async def rps(self, ctx):
        try:

            def pred(m):
                return m.author == ctx.author and m.channel == ctx.channel

            choose = await ctx.send("Choose: rock, paper, or scissors")
            await asyncio.sleep(0.5)
            msg = await self.bot.wait_for("message", check=pred, timeout=10.0)
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long!", delete_after=5)
        else:
            result = discord.Embed(color=0x80B0FF)
            result.set_author(
                name="Rock, Paper, Scissors", icon_url=ctx.author.avatar_url
            )
            r = random.randint(0, 2)
            result.set_thumbnail(
                url=(
                    "https://cdn.discordapp.com/attachments/501871950260469790/511284253728702465/5a0ac29f5a997e1c2cea10a1.png",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511284234275782656/1541969980955.png",
                    "https://cdn.discordapp.com/attachments/501871950260469790/511284246506110997/Scissor-PNG.png",
                )[r]
            )
            result.description = f'**Fate [Zero] chose: **{("rock", "paper", "scissors")[r]}\n**{ctx.author.name} chose:** {msg.content} '
            await choose.delete()
            await ctx.message.delete()
            await msg.delete()

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def sue(self, ctx, user: discord.Member):
        r = random.randint(1, 1000)
        if user.id == 264838866480005122:
            r = 0
        if ctx.author.id == 264838866480005122:
            r = random.randint(1000000, 1000000000)
        e = discord.Embed(color=0xAAF200)
        e.set_author(
            name=f"{ctx.author.name} has sued {user.name}",
            icon_url=ctx.author.avatar_url,
        )
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/511997534181392424/money-png-12.png"
        )
        e.description = f"Amount: ${r}"
        await ctx.send(embed=e)
        await ctx.message.delete()

    @commands.command()
    async def rr(self, ctx):
        if ctx.author.id in [281576231902773248, 401230282272800768]:
            return await ctx.send("You lived")
        await ctx.send(random.choice(["You lived", "You died"]))


def setup(bot):
    bot.add_cog(Fun(bot))
