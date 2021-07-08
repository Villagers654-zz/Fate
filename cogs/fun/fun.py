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
from contextlib import suppress
from datetime import datetime, timedelta
from io import BytesIO
from random import random as rd
import json

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from discord.ext import tasks

from botutils import get_prefix, format_date_difference


code = "```py\n{0}\n```"
sexualities = [
    "straight",
    "gay",
    "bi",
    "ace",
    "pan"
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
        with open("./data/moves.json", "r") as f:
            dat = json.load(f)
        self.attacks = dat["attacks"]
        self.dodges = dat["dodges"]

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
            return await ctx.send("Nothing to snipe")

        # Snipe a specific user
        if ctx.message.mentions:
            user_id = ctx.message.mentions[0].id
            if user_id not in self.dat[channel_id]:
                return await ctx.send("Nothing to snipe")
            msg, time = self.dat[channel_id][user_id]
            del self.dat[channel_id][user_id]

        # Snipe the last message in the channel
        else:
            msg, time = self.dat[channel_id]["last"]
            del self.dat[channel_id]

        if msg.embeds:
            return await ctx.send(f"{msg.author} deleted {format_date_difference(time)} ago", embed=msg.embeds[0])
        if len(msg.content) > 256 and not ctx.author.guild_permissions.administrator:
            return await ctx.send("And **wHy** would I snipe a message *that*  big")

        # Prevent sniping messages deleted by the ChatFilter module
        if ctx.guild.id in self.bot.filtered_messages:
            if msg.id in self.bot.filtered_messages[ctx.guild.id]:
                return await ctx.send("You can't snipe messages deleted by chatfilter")

        e = discord.Embed(color=msg.author.color)
        e.set_author(name=msg.author, icon_url=msg.author.avatar.url)
        e.description = msg.content[:4096]
        e.set_footer(text=f"🗑 {format_date_difference(time).replace('.0', '')} ago")
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, m: discord.Message):
        if m.content or m.embeds:
            channel_id = m.channel.id
            user_id = m.author.id
            dat = (m, datetime.now())
            if channel_id not in self.dat:
                self.dat[channel_id] = {}
            self.dat[channel_id]["last"] = dat
            self.dat[channel_id][user_id] = dat

    @tasks.loop(minutes=25)
    async def clear_old_messages_task(self):
        expiration = datetime.now() - timedelta(hours=1)
        for channel_id, data in list(self.dat.items()):
            if data["last"][1] < expiration:
                del self.dat[channel_id]
                continue
            for key, value in list(data.items()):
                if key != "last":
                    if value[1] < expiration:
                        with suppress(KeyError, ValueError):
                            del self.dat[channel_id][key]

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.embeds and not after.embeds:
            channel_id = before.channel.id
            user_id = before.author.id
            dat = (before, datetime.now())
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
        av1 = await self.bot.get_resource(str(user1.avatar.url))
        av2 = await self.bot.get_resource(str(user2.avatar.url))

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
        attacks = dict(self.attacks)
        dodges = list(self.dodges)
        health1 = 200
        health2 = 200
        attacker = 1

        attacks_used = []
        while True:
            if health1 <= 0:
                await msg.edit(content=f"🏆 **{user2.name} won** 🏆")
                return await ctx.send(f"⚔ **{user2.name}** won against **{user1.name}**")
            if health2 <= 0:
                await msg.edit(content=f"🏆 **{user1.name} won** 🏆")
                return await ctx.send(f"⚔ **{user1.name}** won against **{user2.name}**")

            # Ensure we don't get an attack that was already used
            while True:
                await asyncio.sleep(0)
                if len(attacks_used) == len(attacks):
                    attacks_used = []
                attack = random.choice(list(attacks.keys()))
                if attack in attacks_used:
                    continue
                attacks_used.append(attack)
                break

            # Subtract the damage from the targets health and format the attack with their names
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
            if dmg and "∞" not in attack:
                formatted += f" `-{dmg}HP`"

            e.description += f"\n{formatted}"
            e.description = e.description[-4000:]
            e.set_footer(text=f"{user1.name} {health1}HP | {user2.name} {health2}HP")
            attacker = 2 if attacker == 1 else 1
            await msg.edit(embed=e)
            await asyncio.sleep(3)

    @commands.command(name="sex", aliases=["sexdupe"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sex(self, ctx, user: discord.User):
        await ctx.send(f"Sent instructions on the {user.name} sex dupe to dms")
        choices = [
            "There isn't one for *you*",
            "Err.. maybe try being more attractive",
            "Sike! You're nobodys type",
            "I can't dupe your micro penis. zero times 2 is still zero"
        ]
        try:
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
        if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).manage_webhooks:
            webhook = await ctx.channel.create_webhook(name="Fancify")
            await webhook.send(
                output,
                username=ctx.author.display_name,
                avatar_url=ctx.author.avatar.url,
                allowed_mentions=self.bot.allowed_mentions
            )
            await webhook.delete()
            with suppress(Exception):
                await ctx.message.delete()
        else:
            await ctx.send(output)

    @commands.command(pass_context=True)
    async def encode(self, ctx, encoder: int, *, message):
        usage = "`.encode {16, 32, or 64} {message}`"
        if encoder not in [16, 32, 64]:
            return await ctx.send(usage)
        if encoder == 16:
            encode = base64.b16encode(message.encode())
        elif encoder == 32:
            encode = base64.b32encode(message.encode())
        else:
            encode = base64.b64encode(message.encode())
        await ctx.send(encode.decode())

    @commands.command(pass_context=True)
    async def decode(self, ctx, decoder: int, *, message):
        usage = "`.decode {16, 32, or 64} {message}`"
        if decoder not in {16, 32, 64}:
            return await ctx.send(usage)
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
        e = discord.Embed(color=0x0000FF)
        e.set_author(name=f"{member.display_name}'s msg analysis", icon_url=member.avatar.url)
        percentage = random.randint(50, 100)
        choices = ["truth", "the truth", "a lie", "lie"]
        e.description = f"{percentage}% {random.choice(choices)}"
        await ctx.send(embed=e)
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command(name="personality")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def personality(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        colors = [0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082]
        e = discord.Embed(color=random.choice(colors))
        e.set_author(name=f"{member.display_name}'s Personality", icon_url=member.avatar.url)

        # Personality types
        types = [
            "psychopath", "depressed", "cheerful", "bright", "dark", "god", "deceiver", "funny", "fishy", "cool",
            "insecure", "lonely", "optimistic", "brave", "brilliant", "dreamer", "Nurturer", "Peaceful", "Overthinker",
            "Idealist", "Pussy", "Pick-me girl", "Lovable"
        ]
        e.add_field(name="Type", value=f'{random.choice(types)}', inline=False)

        # Social statuses
        statuses = [
            "Ho", "Slut", "Loser", "The nice guy", "The dick", "Dank memer", "Annoying", "Parties hard", "Cool guy",
            "The chad", "Popular", "Unpopular", "Shut-in", "You need to leave the house to have a social status"
        ]
        e.add_field(name="Social Status", value=f'{random.choice(statuses)}', inline=False)

        # Hobbies
        hobbies = [
            "Art", "Drawing", "Painting", "Singing", "Writing", "Anime", "Memes", "Minecraft", "Sucking dick",
            "Gaming", "Programming", "Work", "Swimming"
        ]
        e.add_field(name="Hobby", value=f'{random.choice(hobbies)}', inline=False)

        # Music Genre
        genres = [
            "Nightcore", "Heavy Metal", "Alternative", "Electronic", "Classical", "Dubstep", "Jazz", "Pop", "Rap"
        ]
        e.add_field(name="Music Genre", value=f'{random.choice(genres)}', inline=False)

        await ctx.send(embed=e)
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command(name="notice")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def notice(self, ctx):
        choices = [
            "Depression Strikes Again",
            "Would you like an espresso for your depresso",
            "You're not you when you're hungry",
            "Tfw you realise flies get laid more than you^",
            "*crippling depression*",
            "Really? That's the sperm that won?",
            "Breakdown sponsored by Samsung",
            "pUrE wHiTe pRiVelIdgEd mALe^",
        ]
        await ctx.send(random.choice(choices))
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command(name="pain")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def pain(self, ctx):
        await ctx.send("Spain but the s is silent")

    @commands.command(name="spain")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spain(self, ctx):
        await ctx.send("Pain but with an s")

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
    async def soul(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        r = random.randint(0, 1000)
        e = discord.Embed(color=0xFFFF00)
        e.set_author(name=f"{member.name}'s Soul Analysis", icon_url=member.avatar.url)
        e.description = f"{r} grams of soul"
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(2, 5, commands.BucketType.channel)
    async def roll(self, ctx):
        await ctx.send(random.choice(["1", "2", "3", "4", "5", "6"]))

    @commands.command(name="ask", aliases=["8ball"])
    @commands.cooldown(2, 5, commands.BucketType.channel)
    async def ask(self, ctx):
        choices = [
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
            "silence fatty"
        ]
        await ctx.send(random.choice(choices))

    @commands.command(name="sexuality", aliases=[s.strip(" ") for s in sexualities[::1]])
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.cooldown(3, 6, commands.BucketType.channel)
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
        e.set_author(name=str(user), icon_url=user.avatar.url)
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
            "swag",
            "fat",
            "karen"
        ],
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def cringe(self, ctx):
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        e = discord.Embed(color=user.color)
        e.set_author(name=str(user), icon_url=user.avatar.url)
        percentage = random.randint(0, 100)
        if ctx.invoked_with == "hitler":
            if random.randint(1, 4) == 1:
                ctx.invoked_with = f"worse than {ctx.invoked_with}"
        if ctx.invoked_with in ["fat", "ugly", "dumb", "stupid", "shit", "hitler", "karen"] and user.id == 261451679239634944:
            percentage = 0
        if ctx.invoked_with in ["chad", "epic", "swag"] and user.id == 261451679239634944:
            oop = [69, 99, 420, 999]
            percentage = random.choice(oop)
        if ctx.invoked_with in ["fat", "gay", "stupid", "dumb", "shit", "hitler", "karen"] and user.id in [457210410819649536, 691433369384255518]:
            troll = [69, 99, 100, 1000000]
            percentage = random.choice(troll)
        e.description = f"{percentage}% {ctx.invoked_with}"
        await ctx.send(embed=e)

    @commands.command(name="sue")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def sue(self, ctx, user: discord.Member):
        r = random.randint(1, 1000)
        if user.id in [264838866480005122, 261451679239634944]:
            r = 0
        if ctx.author.id in [264838866480005122, 261451679239634944]:
            r = random.randint(1000000, 1000000000)
        e = discord.Embed(color=0xAAF200)
        e.set_author(
            name=f"{ctx.author.name} has sued {user.name}",
            icon_url=ctx.author.avatar.url,
        )
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/511997534181392424/money-png-12.png"
        )
        e.description = f"Amount: ${r}"
        await ctx.send(embed=e)
        await ctx.message.delete()

    @commands.command(name="roulette", aliases=["rr"])
    @commands.cooldown(2, 5, commands.BucketType.channel)
    async def roulette(self, ctx):
        async with self.bot.utils.open("data/users") as f:
            users = await self.bot.load(await f.read())
        if ctx.author.id in users:
            return await ctx.send("You lived")
        await ctx.send(random.choice([*["You lived"] * 6, "You died"]))


def setup(bot):
    bot.add_cog(Fun(bot), override=True)
