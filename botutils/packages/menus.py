import asyncio
import random
from time import time, monotonic
import os
from contextlib import suppress
from typing import Optional, Union

import discord
from discord.errors import NotFound, Forbidden
from PIL import Image, ImageFont, ImageDraw
from ast import literal_eval


class Menus:
    def __init__(self, bot):
        self.bot = bot

    async def verify_user(
        self, context=None, channel=None, user=None, timeout=45, delete_after=False
    ):
        if not user and not context:
            raise TypeError(
                "verify_user() requires either 'context' or 'user', and neither was given"
            )
        if not channel and not context:
            raise TypeError(
                "verify_user() requires either 'context' or 'channel', and neither was given"
            )
        if not user:
            user = context.author
        if not channel:
            channel = context.channel

        fp = os.path.basename(f"./static/captcha-{time()}.png")
        abcs = "abcdefghijklmnopqrstuvwxyz"
        chars = " ".join([random.choice(list(abcs)).upper() for _i in range(6)])

        def create_card():
            colors = ["orange", "green", "white", "cyan", "red"]
            font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 75)
            size = font.getsize(chars)
            card = Image.new("RGBA", size=(size[0] + 20, 80), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(card)
            draw.text((10, 10), chars, fill=random.choice(colors), font=font)

            redirections = 5
            lowest_range = 5
            max_range = size[0] + 15
            divide = (max_range - lowest_range) / redirections

            for _ in range(2):
                fix_points = [
                    random.choice(range(10, 65)) for _i in range(redirections + 1)
                ]
                color = random.choice(colors)
                for iteration in range(redirections):
                    line_positions = (
                        # Beginning of line
                        5 + (divide * iteration),
                        fix_points[iteration],
                        # End of line
                        max_range
                        - (
                            (divide * redirections)
                            - sum([divide for _i in range(iteration + 1)])
                        ),
                        fix_points[iteration + 1],
                    )
                    draw.line(line_positions, fill=color, width=2)

            card.save(fp)

        await self.bot.loop.run_in_executor(None, create_card)

        e = discord.Embed(color=self.bot.utils.colors.fate())
        e.set_author(name=str(user), icon_url=user.avatar_url)
        e.set_image(url="attachment://" + fp)
        e.set_footer(text=f"You have {self.bot.utils.get_time(timeout)}")
        message = await channel.send(
            f"{user.mention} please verify you're human", embed=e, file=discord.File(fp),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
        )
        os.remove(fp)

        def pred(m):
            return m.author.id == user.id and str(
                m.content
            ).lower() == chars.lower().replace(" ", "")

        try:
            await self.bot.wait_for("message", check=pred, timeout=timeout)
        except asyncio.TimeoutError:
            if delete_after:
                await message.delete()
            else:
                e.set_footer(text="Captcha Failed")
                with suppress(NotFound, Forbidden):
                    await message.edit(embed=e)
            return False
        else:
            if delete_after:
                await message.delete()
            else:
                e.set_footer(text="Captcha Passed")
                with suppress(NotFound, Forbidden):
                    await message.edit(content=None, embed=e)
            return True

    async def get_choice(
        self, ctx, *options, user, name="Select which option", timeout=30
    ) -> Optional[object]:
        """ Reaction based menu for users to choose between things """

        async def add_reactions(message) -> None:
            for emoji in emojis:
                if not message:
                    return
                try:
                    await message.add_reaction(emoji)
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    return
                if len(options) > 5:
                    await asyncio.sleep(1)
                elif len(options) > 2:
                    await asyncio.sleep(0.5)

        def predicate(r, u) -> bool:
            return u.id == user.id and str(r.emoji) in emojis

        options = options if not isinstance(options[0], list) else options[0]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"][
            : len(options)
        ]
        if not user:
            user = ctx.author

        e = discord.Embed(color=self.bot.utils.colors.fate())
        e.set_author(name=name, icon_url=ctx.author.avatar_url)
        e.description = "\n".join(
            f"{emojis[i]} {option}" for i, option in enumerate(options)
        )
        e.set_footer(text=f"You have {self.bot.utils.get_time(timeout)}")
        message = await ctx.send(embed=e)
        self.bot.loop.create_task(add_reactions(message))

        try:
            reaction, _user = await self.bot.wait_for(
                "reaction_add", check=predicate, timeout=timeout
            )
        except asyncio.TimeoutError:
            await message.delete()
            return None
        else:
            await message.delete()
            return options[emojis.index(str(reaction.emoji))]

    async def configure(self, ctx, options: dict) -> Union[dict, None]:
        """ Reaction based configuration """

        async def wait_for_reaction():
            def pred(r, u):
                return u.id == ctx.author.id and r.message.id == message.id

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=pred, timeout=60
                )
            except asyncio.TimeoutError:
                await message.edit(content="Menu Inactive")
                return None
            else:
                return reaction, user

        async def wait_for_msg() -> Optional[discord.Message]:
            def pred(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            now = time()
            try:
                msg = await self.bot.wait_for("message", check=pred, timeout=30)
            except asyncio.TimeoutError:
                await message.edit(content="Menu Inactive")
                return None
            else:

                async def remove_msg(msg):
                    await asyncio.sleep(round(time() - now))
                    await msg.delete()

                self.bot.loop.create_task(remove_msg(msg))
                return msg

        async def clear_user_reactions(message) -> None:
            before = monotonic()
            message = await ctx.channel.fetch_message(message.id)
            for reaction in message.reactions:
                if reaction.count > 1:
                    async for user in reaction.users():
                        if user.id == ctx.author.id:
                            await message.remove_reaction(reaction.emoji, user)
                            break
            after = round((monotonic() - before) * 1000)
            print(f"{after}ms to clear reactions")

        async def init_reactions_task() -> None:
            if len(options) > 9:
                other = ["🏡", "◀", "▶"]
                for i, emoji in enumerate(other):
                    if i > 0:
                        await asyncio.sleep(1)
                    await message.add_reaction(emoji)
            for emoji in emojis[: len(options)]:
                await message.add_reaction(emoji)

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"]
        pages = []
        tmp_page = {}
        for i, (key, value) in enumerate(options.items()):
            value = options[key]
            if i == len(emojis):
                pages.append(tmp_page)
                tmp_page = {}
                continue
            tmp_page[key] = value
        pages.append(tmp_page)
        page = 0

        def overview():
            e = discord.Embed(color=0x992D22)
            e.description = ""
            for i, (key, value) in enumerate(pages[page].items()):
                if isinstance(value, list):
                    value = " ".join([str(v) for v in value])
                e.description += f"\n{emojis[i]} | {key} - {value}"
            return e

        message = await ctx.send(embed=overview())
        self.bot.loop.create_task(init_reactions_task())
        while True:
            await asyncio.sleep(0.5)
            await clear_user_reactions(message)
            payload = await wait_for_reaction()
            if not payload:
                return None
            reaction, user = payload
            emoji = str(reaction.emoji)
            if emoji == "🏡":
                await message.edit(embed=overview())
                continue
            elif emoji == "▶":
                page += 1
                await message.edit(embed=overview())
                continue
            elif emoji == "◀":
                page -= 1
                await message.edit(embed=overview())
                continue
            elif emoji == "✅":
                full = {}
                for page in pages:
                    for key, value in page.items():
                        full[key] = value
                await message.edit(content="Menu Inactive")
                await message.clear_reactions()
                return full
            else:
                while True:
                    await asyncio.sleep(0.5)
                    await clear_user_reactions(message)
                    index = emojis.index(str(reaction.emoji))
                    value = pages[page][list(pages[page].keys())[index]]
                    if isinstance(value, bool):
                        pages[page][list(pages[page].keys())[index]] = (
                            False if value else True
                        )
                        await message.edit(embed=overview())
                        break
                    await ctx.send(
                        f"Send the new value for {list(pages[page].keys())[index]} in the same format as it's listed",
                        delete_after=30,
                    )
                    msg = await wait_for_msg()
                    if not msg:
                        return None
                    msg = await ctx.channel.fetch_message(msg.id)
                    if isinstance(value, list) and "[" not in msg.content:
                        if "," in msg.content:
                            msg.content = msg.content.split(", ")
                        else:
                            msg.content = msg.content.split()
                        new_value = [literal_eval(x) for x in msg.content]
                    else:
                        new_value = literal_eval(msg.content)
                    if type(value) != type(new_value):
                        await ctx.send("Invalid format\nPlease retry", delete_after=5)
                        await msg.delete()
                        continue
                    elif isinstance(value, list):
                        invalid = False
                        for i, v in enumerate(value):
                            if type(v) != type(new_value[i]):
                                await ctx.send(
                                    f"Invalid format at `{discord.utils.escape_markdown(new_value[i])}`\nPlease retry",
                                    delete_after=5,
                                )
                                await msg.delete()
                                invalid = True
                                break
                        if invalid:
                            continue
                    pages[page][list(pages[page].keys())[index]] = new_value
                    await message.edit(embed=overview())
                    await msg.delete()
                    break
                if "✅" not in [str(r.emoji) for r in message.reactions]:
                    await message.add_reaction("✅")


def init(cls):
    menus = Menus(cls.bot)
    cls.verify_user = menus.verify_user
    cls.get_choice = menus.get_choice
    cls.configure = menus.configure
