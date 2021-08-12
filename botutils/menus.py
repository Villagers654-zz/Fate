"""
Menus Utils
~~~~~~~~~~~~

Contains classes for emulating menus

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
import random
from time import time
import os
from contextlib import suppress
from typing import *

import discord
from discord import TextChannel, Attachment
from discord.errors import NotFound, Forbidden
from discord import ui
from PIL import Image, ImageFont, ImageDraw

from . import colors
from .tools import get_time


style = discord.ButtonStyle


class ChoiceButtons(ui.View):
    def __init__(self):
        self.choice = None
        self.asyncio_event = asyncio.Event()
        super().__init__()

    @ui.button(label="Yes", style=style.green)
    async def yes(self, _button, interaction):
        self.choice = True
        await interaction.message.edit(view=None)
        self.asyncio_event.set()
        self.stop()

    @ui.button(label="No", style=style.red)
    async def no(self, _button, interaction):
        self.choice = False
        await interaction.message.edit(view=None)
        self.asyncio_event.set()
        self.stop()


class _Select(discord.ui.Select):
    def __init__(self, user_id: int, choices: List[Any], limit: int = 1, placeholder: str = "Select your choice"):
        self.user_id = user_id
        self.limit = limit

        options = []
        for option in choices:
            options.append(discord.SelectOption(label=str(option)[:100]))

        super().__init__(
            custom_id=f"select_choice_{time()}",
            placeholder=placeholder,
            min_values=1,
            max_values=limit,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "Only the user who initiated this command can interact",
                ephemeral=True
            )
        self.view.selected = interaction.data["values"]
        await interaction.response.defer()
        if not self.view.message:
            await interaction.message.delete()
        self.view.stop()


class GetChoice(discord.ui.View):
    selected: List[str] = None
    message: Optional[discord.Message] = None
    def __init__(self, ctx, choices: Union[list, KeysView], limit: int = 1, placeholder: str = "Options", message=None):
        self.ctx = ctx
        self.choices = choices
        self.limit = limit
        if limit > len(choices):
            self.limit = len(choices)
        self.original_choices = choices
        self.message = message
        super().__init__(timeout=45)
        self.add_item(_Select(ctx.author.id, choices, self.limit, placeholder))

    def __await__(self) -> Generator:
        return self._await().__await__()

    async def _await(self) -> Union[str, List[str]]:
        if self.message:
            await self.message.edit(view=self)
            message = self.message
        else:
            message = await self.ctx.send("Select your choice", view=self)
            self.message = message
        await self.wait()
        if not self.selected and not self.message:
            with suppress(Exception):
                await message.delete()
            raise self.ctx.bot.ignored_exit

        if self.limit == 1:
            for choice in self.choices:
                if self.selected[0] in choice:
                    return choice
            return self.selected[0]
        return self.selected

    async def on_error(self, error, _item, _interaction) -> None:
        if not isinstance(error, (NotFound, self.ctx.bot.ignored_exit)):
            raise


class Menus:
    def __init__(self, bot):
        self.bot = bot

    async def verify_user(self, context=None, channel=None, user=None, timeout=45, delete_after=False):
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
            font = ImageFont.truetype("./botutils/fonts/Modern_Sans_Light.otf", 70)
            size = font.getsize(chars)
            card = Image.new("RGBA", size=(size[0] + 20, 80), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(card)
            color = random.choice(colors)
            for i in range(len(chars)):
                draw.text((10 + 35 * i, 10), chars[i], fill=color, font=font)

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
                        5 + (divide * iteration), fix_points[iteration],
                        # End of line
                        max_range - ((divide * redirections) - sum([divide for _i in range(iteration + 1)])),
                        fix_points[iteration + 1],
                    )
                    draw.line(line_positions, fill=color, width=2)

            card.save(fp)

        await self.bot.loop.run_in_executor(None, create_card)

        e = discord.Embed(color=colors.fate)
        e.set_author(name=str(user), icon_url=user.avatar.url)
        e.set_image(url="attachment://" + fp)
        e.set_footer(text=f"You have {get_time(timeout)}")
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
            m = await self.bot.wait_for("message", check=pred, timeout=timeout)
        except asyncio.TimeoutError:
            if delete_after:
                with suppress(NotFound, Forbidden):
                    await message.delete()
            else:
                e.set_footer(text="Captcha Failed")
                with suppress(NotFound, Forbidden):
                    await message.edit(embed=e)
            return False
        else:
            if delete_after:
                with suppress(NotFound, Forbidden):
                    await message.delete()
                    await m.delete()
            else:
                e.set_footer(text="Captcha Passed")
                with suppress(NotFound, Forbidden):
                    await message.edit(content=None, embed=e)
            return True

    async def get_choice(self, ctx, *options, user=None, name="Select which option", timeout=30):
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

        options = options[:8] if not isinstance(options[0], list) else options[0][:8]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"][
            : len(options)
        ]
        if not user:
            user = ctx.author

        e = discord.Embed(color=colors.fate)
        e.set_author(name=name, icon_url=ctx.author.avatar.url)
        e.description = "\n".join(
            f"{emojis[i]} {option}" for i, option in enumerate(options)
        )
        e.set_footer(text=f"You have {get_time(timeout)}")
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
        r_check = lambda r, u: u.id == ctx.author.id and r.message.id == message.id

        async def clear_user_reactions(message) -> None:
            with suppress(NotFound, Forbidden, NameError):
                await message.remove_reaction(reaction.emoji, user)

        async def init_reactions_task() -> None:
            if len(options) > 9:
                other = ["🏡", "◀", "▶"]
                for i, emoji in enumerate(other):
                    if i > 0:
                        await asyncio.sleep(1)
                    await message.add_reaction(emoji)
            for emoji in emojis[:len(options)]:
                await message.add_reaction(emoji)
            await message.add_reaction("✅")

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️"]
        pages = []
        tmp_page = {}
        for i, (key, value) in enumerate(options.items()):
            await asyncio.sleep(0)
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
                e.description += f"\n{emojis[i]} | {key} - {'enabled' if value else 'disabled'}"
            return e

        message = await ctx.send(embed=overview())
        self.bot.loop.create_task(init_reactions_task())
        while True:
            self.bot.loop.create_task(clear_user_reactions(message))
            reaction, user = await self.bot.utils.get_reaction(r_check)
            emoji = str(reaction.emoji)

            # Changing pages
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

            # Altering values
            await clear_user_reactions(message)
            index = emojis.index(str(reaction.emoji))
            value = pages[page][list(pages[page].keys())[index]]

            # Toggling between enabled and disabled
            if isinstance(value, bool):
                pages[page][list(pages[page].keys())[index]] = not value
                await message.edit(embed=overview())
                continue

            # Setting a string
            await ctx.send(
                f"Send the new text for {list(pages[page].keys())[index]}",
                delete_after=30,
            )
            msg = await self.bot.utils.get_message(ctx)
            if not msg.content:
                continue
            pages[page][list(pages[page].keys())[index]] = msg.content

            await message.edit(embed=overview())
            await msg.delete()

    async def ask(self, message, ignore_timeout=True):
        view = ChoiceButtons()
        await message.edit(view=view)
        try:
            await asyncio.wait_for(view.asyncio_event.wait(), timeout=45)
        except asyncio.TimeoutError as error:
            if ignore_timeout:
                raise self.bot.ignored_exit
            raise error
        return view.choice

    async def get_answers_from(self, user, message, questions):
        """|coro|
        Shortcut function to get answers to a series of questions

        Parameters
        ----------
        user: discord.User
            The user to be questioned
        message: discord.Message
            The message to use
        questions: dict
            A dict of questions, and desired return types
        delete_after: bool, optional
            Delete the message used to ask questions when done (default is False)

        Raises
        ------
        exception: discord.errors.NotFound
            the message was deleted
        exception: discord.errors.Forbidden
            lost access to the channel

        Returns
        -------
        dict
            The dict of questions with their answers
        """
        choices = {}
        is_author = lambda m: m.author.id == user.id

        check_presets = {
            str: lambda m: is_author(m) and m.content,
            TextChannel: lambda m: is_author(m) and m.channel_mentions,
            Attachment: lambda m: is_author(m) and m.attachments or "http" in m.content
        }

        for i, (question, ReturnType) in enumerate(questions.items()):
            # Update the message
            q = f"{i + 1}/{len(questions)} {question}"
            view = None

            # Use buttons if wanting a yes/no response
            if ReturnType is bool:
                view = ChoiceButtons()

            # Wait for a button press
            await message.edit(content=q, view=view)
            try:
                if ReturnType is bool:
                    # Use buttons to get the users answer
                    await asyncio.wait_for(view.asyncio_event.wait(), timeout=45)
                    choices[question] = view.choice
                    continue

                if ReturnType is Callable:  # Custom check function
                    check = ReturnType
                else:
                    # Use a preset check function
                    check = check_presets[ReturnType]

                msg = await self.bot.wait_for("message", check=check, timeout=45)

                # Requesting the message content
                if ReturnType is (str, Callable):
                    answer = msg.content

                # Requesting a channel object
                elif ReturnType is TextChannel:
                    answer = msg.channel_mentions[0]

                # Requesting a bytes-like object
                elif ReturnType is Attachment:
                    if msg.attachments:
                        answer = await msg.attachments[0].read()
                    else:
                        urls = [section for section in msg.content.split() if "http" in section]
                        answer = await self.bot.download(urls[0])

                else:
                    raise TypeError("Invalid return-type in 'questions' parameter")

                choices[question] = answer
            except asyncio.TimeoutError:
                return None

        return choices

