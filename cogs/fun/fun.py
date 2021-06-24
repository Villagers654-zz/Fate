"""
cogs.fun.fun
~~~~~~~~~~~~~

A cog containing generally fun commands

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
import base64
import random
from random import random as rd
from datetime import datetime, timedelta
from contextlib import suppress
from io import BytesIO

import aiohttp
import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from discord.ext import tasks
from PIL import Image, ImageDraw, ImageFont

from botutils import get_prefix


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
        self.gay = bot.utils.cache("sexuality")
        for sexuality in sexualities:
            if sexuality not in self.gay:
                self.gay[sexuality] = {}

        self.clear_old_messages_task.start()

    def cog_unload(self):
        self.clear_old_messages_task.stop()

    @commands.command(name="snipe")
    @commands.cooldown(1, 10, commands.BucketType.channel)
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
            del self.dat[channel_id][user_id]
        else:
            msg, time = self.dat[channel_id]["last"]
            del self.dat[channel_id]
        if msg.embeds:
            await ctx.send(f"{msg.author} at {time}", embed=msg.embeds[0])
        else:
            if ctx.guild.id in self.bot.filtered_messages:
                if msg.id in self.bot.filtered_messages[ctx.guild.id]:
                    return await ctx.send("I think not m8")
            if len(msg.content) > 1000 and not ctx.author.guild_permissions.administrator:
                return await ctx.send("wHy would I snipe that?")
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

    @commands.command(name="battle", aliases=["fight"])
    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.cooldown(2, 45, commands.BucketType.channel)
    @commands.cooldown(2, 30, commands.BucketType.guild)
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def battle(self, ctx, user1: discord.User, user2: discord.User = None):
        if not user2:
            user2 = user1
            user1 = ctx.author
        large_font = ImageFont.truetype("./botutils/fonts/pdark.ttf", 70)
        W, H = 350, 125
        border_color = "black"
        background_url = "https://cdn.discordapp.com/attachments/632084935506788385/834605220302553108/battle.jpg"
        frame_url = "https://cdn.discordapp.com/attachments/632084935506788385/834609401855213598/1619056781596.png"

        background = await self.bot.get_resource(background_url)
        frame = await self.bot.get_resource(frame_url)
        av1 = await self.bot.get_resource(str(user1.avatar_url))
        av2 = await self.bot.get_resource(str(user2.avatar_url))

        def generate_card(frame, av1, av2):
            card = Image.new("RGBA", (W, H), (0, 0, 0, 100))
            im = Image.open(BytesIO(background)).convert("RGBA").resize((W, H))
            card.paste(im, (0, 0), im)

            draw = ImageDraw.Draw(card)
            w, h = draw.textsize("VS", font=large_font)
            draw.text(((W - w) / 2, (H - h) / 2), text="VS", fill="white", font=large_font)

            frame = Image.open(BytesIO(frame)).convert("RGBA").resize((70, 70), Image.BICUBIC)
            av1 = Image.open(BytesIO(av1)).convert("RGBA").resize((70, 70), Image.BICUBIC)
            av2 = Image.open(BytesIO(av2)).convert("RGBA").resize((70, 70), Image.BICUBIC)
            av1.paste(frame, (0, 0), frame)
            av2.paste(frame, (0, 0), frame)
            card.paste(av1, (25, 30), av1)
            card.paste(av2, (255, 30), av1)

            draw.line((0, 0, W, 0), border_color, 5)
            draw.line((W, 0, W, H), border_color, 5)
            draw.line((0, 0, 0, H), border_color, 5)
            draw.line((0, H, W, H), border_color, 5)

            mem_file = BytesIO()
            card.save(mem_file, format="PNG")
            mem_file.seek(0)
            return mem_file

        e = discord.Embed(color=discord.Color.red())
        e.title = f"{user1.name} Vs. {user2.name}"
        create_card = lambda: generate_card(frame, av1, av2)

        mem_file = await self.bot.loop.run_in_executor(None, create_card)
        msg = await ctx.send(
            embed=e,
            file=discord.File(mem_file, filename="card.png")
        )
        e.description = ""
        health1 = 150
        health2 = 150
        attacker = 1

        attacks = {
            "🔪 | !user shanked !target `-15HP`": 15,
            "⚔ | !user ran a sword right through !target's stomach `-20HP`": 20,
            "⚔ | !user ran a sword right through !target's chest `-35HP`": 30,
            "🏹 | !user shot !target in the arm with an arrow `-10HP`": 10,
            "🏹 | !user shot !target in the leg with an arrow `-10HP`": 10,
            "🏹 | !user shot !target in the chest with an arrow `-30HP`": 30,
            "🔫 | Pew pew! !target got shot by !user `-50HP`": 50,
            "💣 | YEET!.. 💥 !target got blown up `-50HP`": 50,
            "⚡ | !user struck !target with lightning `-50HP`": 50,
            "🔥 | !user set !target on fire `-10HP`": 10,
            "🌠 | !user used astral power to strike !target `-50HP`": 50,
            "🚗 | !user ran into !target `-25HP`": 25,
            "🛴 | !user hit !target's ankles with a scooter `-10HP`": 10,
            "👻 | !user scared !target shitless `-2HP`": 2,
            "👊 | !user punched !target `-10HP`": 10,
            "💅 | !user ignored !target `-1HP`": 1,
            "🖐 | !user slapped !target `-5HP`": 5,
            "😈 | !user triggered !target's vietnam war flashbacks `-10HP`": 10,
            "🦝 | !user threw !target like a raccoon": 15,
            "🦶 | !user tripped !target": 10,
            "🦵 | !user hit the back of !target's knee and made them fold like origami": 10,
            "📱 | !user got cancelled by !target on twitter": 25
            # "🏓 | !user played ping-pong with !targets nuts `-5HP`": 5
        }

        dodges = [
            "🔮 | !target foretold !users attack and dodged",
            "🥋 | !target used expert martial arts to dodge",
            "💁‍♀️ | !target dodged because they're not like other girls"
        ]

        last = None
        while True:
            if health1 <= 0:
                await msg.edit(content=f"🏆 **{user2.name} won** 🏆")
                return await ctx.send(f"⚔ **{user2.name}** won against **{user1.name}**")
            if health2 <= 0:
                await msg.edit(content=f"🏆 **{user1.name} won** 🏆")
                return await ctx.send(f"⚔ **{user1.name}** won against **{user2.name}**")
            attack = random.choice(list(attacks.keys()))
            if attack == last:
                attack = random.choice(list(attacks.keys()))
            last = attack
            dmg = attacks[attack]
            if random.randint(1, 10) == 1:
                attack = random.choice(dodges)
                dmg = 0
            if attacker == 1:
                formatted = attack.replace('!user', user1.name).replace('!target', user2.name)
                health2 -= dmg
            else:
                formatted = attack.replace('!user', user2.name).replace('!target', user1.name)
                health1 -= dmg
            e.description += f"\n{formatted}"
            e.description = e.description[-2000:]
            e.set_footer(text=f"{user1.name} {health1}HP | {user2.name} {health2}HP")
            attacker = 2 if attacker == 1 else 1
            await msg.edit(embed=e)
            await asyncio.sleep(3)

    @commands.command(name="sex", aliases=["sexdupe"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sex(self, ctx, user: discord.User):
        await ctx.send(f"Sent instructions on the {user.name} sex dupe to dms")
        try:
            choices = [
                "There isn't one for *you*",
                "Err.. maybe try being more attractive",
                "Sike! You're nobodys type",
                "I can't dupe your micro penis. zero times 2 is still zero"
            ]
            await ctx.author.send(random.choice(choices))
        except:
            pass

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
            f"Usage: `{get_prefix(ctx)}{ctx.invoked_with} percentage/reset/help`"
            f"\nExample Usage: `{get_prefix(ctx)}{ctx.invoked_with} 75%`"
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
                self.gay.remove_sub(invoked_with, user_id)
                await ctx.send(f"Removed your custom {invoked_with} percentage")
            elif percentage.lower() == "help":
                return await ctx.send(usage)
            else:
                stripped = percentage.strip("%")
                try:
                    if int(stripped) > 100:
                        return await ctx.send("That's too high of a percentage")
                    if int(stripped) < 0:
                        return await ctx.send("Yikes, must suck")
                except ValueError:
                    return await ctx.send("The percentage needs to be an integer")
                self.gay[invoked_with][user_id] = int(stripped)
                await ctx.send(
                    f"Use `{get_prefix(ctx)}{invoked_with} reset` to go back to random results"
                )
            await self.gay.flush()
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
            "swag"
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
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rr(self, ctx):
        async with self.bot.utils.open("data/users") as f:
            users = await self.bot.load(await f.read())
        if ctx.author.id in users:
            return await ctx.send("You lived")
        await ctx.send(random.choice([*["You lived"] * 6, "You died"]))


def setup(bot):
    bot.add_cog(Fun(bot))
