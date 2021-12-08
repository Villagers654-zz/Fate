"""
botutils.interactions
~~~~~~~~~~~~~~~~~~~~~~

A module for template interaction classes

Classes:
    GetConfirmation : An object for confirming a question with a user
    ModView : A View that only moderators can interact with
    AuthorView : A view that only the author of the original message can interact with
    Menu : A ease of use embed paginator
    Configure : A menu for having a user modify a config

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
from contextlib import suppress

from discord import ui, Interaction, SelectOption, Embed, ButtonStyle
from discord.ext.commands import Context
import discord

from . import Cooldown, emojis, colors
from .cache_rewrite import DataContext


class GetConfirmation(ui.View):
    value: bool = False

    def __init__(self, ctx: Context, question: str):
        self.ctx = ctx
        self.question = question
        super().__init__(timeout=30)

    def __await__(self) -> Generator[None, None, bool]:
        return self._await().__await__()

    async def _await(self) -> bool:
        msg = await self.ctx.send(self.question, view=self)
        await self.wait()
        await msg.delete()
        if not self.value:
            await self.ctx.message.delete()
        return self.value

    @ui.button(label="Confirm", style=ButtonStyle.green)
    async def confirm(self, _button, interaction):
        self.value = True
        await interaction.response.send_message(
            f"Alright, confirmed", ephemeral=True
        )
        self.stop()

    @ui.button(label="Deny", style=ButtonStyle.red)
    async def deny(self, _button, interaction):
        await interaction.response.send_message(
            f"Alright, operation cancelled", ephemeral=True
        )
        self.stop()


class ModView(ui.View):
    ctx: Context
    cd: Cooldown

    async def interaction_check(self, interaction: Interaction):
        """ Ensure the interaction is from the user who initiated the view """
        member = interaction.guild.get_member(interaction.user.id)
        if not self.ctx.bot.attrs.is_moderator(member):
            await interaction.response.send_message(
                "Only moderators can interact", ephemeral=True
            )
            return False
        if self.cd.check(member.id):
            await interaction.response.send_message("You're on cooldown. Try again in a few seconds")
            return False
        return True


class AuthorView(ui.View):
    ctx: Context
    cd: Cooldown = None
    def __init__(self, *args, **kwargs) -> None:
        if not self.cd:
            self.cd = Cooldown(2, 5)
        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Only the user who initiated this menu can interact", ephemeral=True
            )
            return False
        if self.cd.check(interaction.user.id):
            await interaction.response.send_message(
                "You're on cooldown; try again in a few seconds", ephemeral=True
            )
            return False
        return True


class Menu(AuthorView):
    items: Dict[str, Union[Embed, List[Embed]]] = {}
    message: discord.Message = None  # Filled when the class is awaited

    def __init__(self, ctx: Context, pages: Union[dict, list]):
        self.cd = Cooldown(3, 5)
        self.ctx = ctx
        self.page = 0
        super().__init__(timeout=120)

        if isinstance(pages, dict):
            self.items = pages
            self.pages = pages[list(pages.keys())[0]]
            if isinstance(self.pages, Embed):
                self.pages = [self.pages]
            self.add_item(_Dropdown(self))
        else:
            self.pages = pages

        if len(self.pages) != 1:
            self.buttons = {
                "seek_left": ui.Button(emoji="◀", custom_id="seek_left"),
                "seek_right": ui.Button(emoji="▶", custom_id="seek_right")
            }
            for button in self.buttons.values():
                button.callback = self.seek
                self.add_item(button)
            self.buttons["seek_left"].disabled = True

    def __await__(self) -> Generator[None, None, None]:
        """ Fill in the message object """
        return self._init_message().__await__()

    async def _init_message(self) -> discord.Message:
        """ Send the View and fill in the message var """
        self.message = await self.ctx.send(
            embed=self.pages[self.page],
            view=self
        )
        return self.message

    async def on_timeout(self):
        await self.message.edit(view=None)

    async def update_message(self, interaction: Interaction):
        await interaction.message.edit(
            embed=self.pages[self.page],
            view=self
        )

    async def seek(self, interaction: Interaction):
        """ Seek to the previous page """
        value: str = interaction.data["custom_id"]
        if value == "seek_left":
            self.page -= 1
            if self.page == 0:
                self.buttons[value].disabled = True
            self.buttons["seek_right"].disabled = False
        elif value == "seek_right":
            self.page += 1
            if self.page == len(self.pages) - 1:
                self.buttons[value].disabled = True
            self.buttons["seek_left"].disabled = False
        await self.update_message(interaction)


class _Dropdown(ui.Select):
    """ The Dropdown button for the Menus class """
    def __init__(self, cls: Menu):
        self.cls = cls

        options = []
        for label, items in cls.items.items():
            options.append(SelectOption(label=label))

        super().__init__(
            placeholder="Change Category",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        label: str = interaction.data["values"][0]
        if isinstance(embed := self.cls.items[label], Embed):
            return await interaction.response.edit_message(
                embed=embed,
                view=self.cls
            )
        self.cls.pages = self.cls.items[label]
        self.cls.page = 0
        self.cls.buttons["seek_left"].disabled = True
        self.cls.buttons["seek_right"].disabled = False
        await self.cls.update_message(interaction)


class Configure(ui.View):
    message: discord.Message = None
    deleted: bool = False

    def __init__(self, ctx, options: dict) -> None:
        self.ctx = ctx
        self.options = options
        super().__init__(timeout=45)
        self.add_item(_ConfigureDropdown(self))

    def __await__(self) -> Generator[Any, Any, Union[dict, DataContext]]:
        return self._await().__await__()

    async def _await(self) -> Union[dict, DataContext]:
        self.message = await self.ctx.send(embed=self.embed, view=self)
        await self.wait()
        if not self.deleted:
            with suppress(Exception):
                await self.message.delete()
        return self.options

    @property
    def embed(self) -> discord.Embed:
        e = discord.Embed(color=colors.fate)
        e.set_author(name="Configure Options", icon_url=self.ctx.author.display_avatar.url)
        e.description = ""
        for option, toggle in self.options.items():
            emote = emojis.online if toggle else emojis.dnd
            e.description += f"\n{emote} **{option.title()}**"
        return e

    @ui.button(emoji=emojis.yes, row=2)
    async def done(self, _button, interaction: Interaction):
        self.deleted = True
        with suppress(Exception):
            await interaction.message.delete()
        self.stop()


class _ConfigureDropdown(ui.Select):
    def __init__(self, menu: Configure):
        self.menu = menu
        super().__init__(
            placeholder="Toggle an Option",
            min_values=1,
            max_values=len(menu.options),
            options=[
                SelectOption(
                    emoji=emojis.online if toggle else emojis.dnd,
                    label=option.title().replace("_", " "),
                    value=option,
                    description=f"click to {'disable' if toggle else 'enable'}"
                )
                for option, toggle in menu.options.items()
            ]
        )

    async def callback(self, interaction: Interaction):
        for option in interaction.data["values"]:
            self.menu.options[option] = not self.menu.options[option]
        self.__init__(self.menu)
        await interaction.response.edit_message(
            embed=self.menu.embed,
            view=self.menu
        )
