"""
cogs.core.menus
~~~~~~~~~~~~~~~~

A beta help menu that uses views instead of reactions

Classes:
    Menus
    HelpView
    HelpSelect

Functions:
    setup

Vars:
    structure

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
import asyncio
import inspect
from discord.ext import commands
from discord.ext.commands import Command, Context
from discord import ui, Interaction, Embed, Message, SelectOption
from fate import Fate
from botutils import AuthorView, colors, Cooldown


command_attrs = (commands.core.Command, commands.core.Group)


# Use strings or lists to denote what module goes on what page
structure = {
    "Core": [
        "Core", "Statistics", "CustomCommands"
    ],
    "Moderation": {
        "Mod Cmds": [
            "Moderation", "Lock"
        ],
        "Modmail": [
            "ModMail", "CaseManager"
        ],
        "Logger": "Logger",
        "AntiSpam": "AntiSpam",
        "AntiRaid": "AntiRaid",
        "Chatfilter": "ChatFilter",
        "Verification": "Verification"
    },
    "Utility": {
        "Welcome Messages": "Welcome",
        "Leave Messages": "Leave",
        "AutoRole": "AutoRole",
        "Self-Roles": "SelfRoles",
        "Restore-Roles": "RestoreRoles",
        "Emojis": "Emojis",
        "Vc-Log": "VcLog",
        "Chat Bridges": "ChatBridges",
        "Suggestions": "Suggestions",
        "ServerStatistics": "ServerStatistics",
        "Misc": [
            "Polls",
            "Audit",
            "Notepad",
            "Utility"
        ]
    },
    "Ranking": "Ranking",
    "Fun": {
        "Factions": "Factions",
        "Actions": "Actions",
        "Reactions": "Reactions",
        "Misc": "Fun"
    }
}


class Menus(commands.Cog):
    """ A Cog for handling the help menu, and its command """
    structure: Dict[str, Union[List[Command], Dict[str, List[Command]]]] = {}

    def __init__(self, bot: Fate) -> None:
        self.bot = bot
        if bot.is_ready():  # Cog was reloaded, update the index
            bot.loop.create_task(self.restructure())

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Build Menus.structure when the bots cache is initialized """
        await self.restructure()

    async def construct(self, item: Union[str, List[str]]) -> List[Command]:
        """ Convert a string or list of strings into a list of commands """
        if isinstance(item, str):
            return list(c for c in self.bot.get_cog(item).walk_commands())
        items = []
        for sub_item in item:
            await asyncio.sleep(0)
            items.extend(list(c for c in self.bot.get_cog(sub_item).walk_commands()))

        # Update each commands usage
        for command in items:
            await asyncio.sleep(0)
            usage_attr = command.name + "_usage"
            if hasattr(command.cog, usage_attr):
                usage = getattr(command.cog, usage_attr)

                # Do conversion from function to value/awaitable
                if hasattr(usage, "__call__"):
                    usage = usage()

                # Convert from awaitable if usage is a coroutine
                if inspect.iscoroutine(usage):
                    usage = await usage

                command.usage = usage

        return items

    async def restructure(self) -> None:
        """ Rebuilds Menus.structure with the updated list of commands """
        rebuilt = {}
        for category, value in structure.items():
            await asyncio.sleep(0)  # Hand off the loop incase anything needs it
            rebuilt[category] = {}
            if isinstance(value, dict):
                for sub_category, sub_value in value.items():
                    rebuilt[category][sub_category] = await self.construct(sub_value)
            else:
                rebuilt[category] = await self.construct(value)
        self.structure = rebuilt

    @commands.command(name="help")
    @commands.cooldown(1, 25, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def help(self, ctx):
        await HelpMenu(self.structure, ctx)


def setup(bot: Fate):
    bot.add_cog(Menus(bot))


class HelpMenu(AuthorView):
    """ The View for interacting with the help menu. Needs to be awaited """
    structure: Dict[str, Union[List[Command], Dict[str, List[Command]]]]
    state: Dict[str, Union[List[Command], Dict[str, List[Command]]]]
    message: Optional[Message]

    def __init__(self, structure, ctx: Context) -> None:
        self.structure = structure
        self.ctx = ctx
        self.bot: Fate = ctx.bot
        self.cd = Cooldown(3, 5)

        # Set up the embed to use
        self.embed = Embed(color=colors.fate)
        self.embed.set_author(name="~==🥂🍸🍷Help🍷🍸🥂==~")
        self.embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
        self.embed.description = (
            f"[Support]({self.bot.config['support_server']}) | "
            f"[Bot Invite]({self.bot.invite_url}) | [Privacy Policy](https://github.com/FrequencyX4/Fate/blob/master/PRIVACY.md)\n"
            f"• using a cmd with no args will usually send its help menu\n"
            f"• try using `.module enable` instead of `.enable module`"
        )

        self.state = dict(structure)
        super().__init__(timeout=45)
        self.add_item(HelpSelect(main=self))

    def __await__(self) -> Generator[None, None, "HelpMenu"]:
        return self._await().__await__()

    async def _await(self) -> "HelpMenu":
        """ Send the help menus message """
        self.message = await self.ctx.send(embed=self.embed, view=self)
        await self.wait()
        await self.message.edit(view=None)
        return self


class HelpSelect(ui.Select):
    """ The Select class for handling interactions """
    cancel_option = SelectOption(
        emoji="🚫",
        label="Return to Categories",
        description="Shows the module categories"
    )

    def __init__(self, main: HelpMenu):
        self.main = main
        self.pre_init_options = None
        self._options = [self.cancel_option]

        # Shows the module list
        if isinstance(main.state, dict):
            emoji = "📖"
            if main.state == main.structure:
                emoji = "📚"
            self._options = [SelectOption(emoji=emoji, label=key) for key in main.state.keys()]

        # Shows a list of commands
        elif isinstance(main.state, list):
            p: str = main.ctx.prefix
            for command in main.state:
                if not command:
                    continue
                checks = str(command.checks)
                if "luck" in checks or "is_owner" in checks:
                    continue
                description = None
                if isinstance(command.usage, str):
                    description = command.usage[:100]
                if command.description:
                    description = command.description

                label = f"{p}{command}"
                if len(command.params) > 2:
                    for param, ptype in list(command.params.items())[2:]:
                        names = ["User", "Member", "Role"]
                        if param == "user" or any(name in str(ptype) for name in names):
                            label += f" @{param}"
                        elif "TextChannel" in str(ptype) or param == "channel":
                            label += f" #{param}"
                        else:
                            label += f" [{param}]"

                self._options.append(SelectOption(emoji="🌐", label=label, description=description))

        # Copy the _options var
        options = list(self._options)

        # Split the options up into two pages
        if len(options) > 25:
            remainder = len(options) - 24
            options = options[:24]
            self.view_rest_button = SelectOption(
                emoji="🔍", label=f"Show Remaining {remainder} Commands"
            )
            self._options.append(self.view_rest_button)
            options.append(self.view_rest_button)

        super().__init__(
            placeholder="Select an option",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction) -> None:
        """ The function that receives and processes interactions """
        key, = interaction.data["values"]  # type: str

        # Reset the menu
        if key == "Return to Categories":
            self.main.state = dict(self.main.structure)
            self.__init__(self.main)

        # Show first page of options
        elif "First" in key:
            self.options = self._options[:24]
            self.options.append(self.view_rest_button)

        # Show second page of options
        elif "Remaining" in key:
            cut = int("".join(c for c in key if c.isdigit())) + 1
            self.options = [self.cancel_option] + self._options[-cut:]  # type: ignore
            self.options = self.options[:len(self.options) - 1]
            self.options.append(SelectOption(emoji="🔍", label="Show First Section of Commands"))

        # Send a commands help
        else:
            if isinstance(self.main.state, list):
                command = self.main.bot.get_command(key.lstrip(".").split()[0])
                if not command or not command.usage:
                    return await interaction.response.send_message(
                        "No help information is currently available for that command", ephemeral=True
                    )

                if isinstance(command.usage, Embed):
                    return await interaction.response.send_message(embed=command.usage, ephemeral=True)
                return await interaction.response.send_message(command.usage, ephemeral=True)

            # Show the options for the selected key
            self.main.state = self.main.state[key]
            self.__init__(self.main)

        # Update the view on the users end
        await interaction.response.edit_message(view=self.main)
