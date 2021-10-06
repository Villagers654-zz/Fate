"""
cogs.core.messages
~~~~~~~~~~~~~~~~~~~

A module for configuring where message related functions go

:copyright: (C) 2020-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

from typing import *
from copy import copy

from discord.ext import commands
from discord import ui, Interaction, SelectOption

from botutils import AuthorView, GetChoice
import fate


class Messages(commands.Cog):
    """ A cog for configuring where message related functions go """

    # True:  Send to the channel it occured in
    # False: Don't send at all
    # Int:   The channel_id to send to
    default_modules: Dict[str, Union[bool, int]] = {
        "level_up_messages": False,
        "redirect_mod_commands": False
    }

    def __init__(self, bot: fate.Fate) -> None:
        self.bot = bot
        self.config = bot.utils.cache("messages")

    @commands.command(name="messages")
    @commands.has_permissions(administrator=True)
    async def messages(self, ctx):
        await ctx.send("Warning: this command doesn't do anything yet")
        view = ConfigUI(ctx)
        msg = await ctx.send("Choose a module to config", view=view)
        await view.wait()
        view.select.disabled = True
        await msg.edit(view=view)


value_types = {
    "Disable": False,
    "Send in the channel it occured": True,
    "Send to this specific channel": 1
}


class ConfigUI(AuthorView):
    """ The View that contains the select menu """
    class SelectUI(ui.Select):
        """ The dropdown component for the View """
        def __init__(self, ctx: commands.Context, view: "ConfigUI") -> None:
            self.ctx = ctx
            self.bot: fate.Fate = ctx.bot
            self.main_view = view
            self.config: Messages.config = ctx.cog.config  # type: ignore

            config = self.config.get(ctx.guild.id, copy(Messages.default_modules))
            options: List[SelectOption] = [
                SelectOption(
                    label=option.replace("_", " ").title(),
                    description=self.option_description(value),
                    value=option
                )
                for option, value in config.items()
            ]

            super().__init__(
                placeholder="Choose a module",
                options=options,
                min_values=1,
                max_values=1,

            )

        def option_description(self, value: Union[bool, None, int]) -> str:
            """ Gets the description of a setting """
            if value is True:
                return "Send in the channel it occured"
            elif value is False:
                return "Disabled"
            return f"Send to #{self.bot.get_channel(value)}"

        async def callback(self, interaction: Interaction) -> None:
            """ Handle interactions with the select menu """
            await interaction.response.defer()

            choices = list(value_types.keys())
            if "redirect" in interaction.data["values"][0]:
                choices.remove("Send in the channel it occured")
            choice = await GetChoice(
                ctx=self.ctx,
                choices=choices,
                message=interaction.message,
                delete_after=False
            )
            choice = value_types[choice]
            if not isinstance(choice, bool) and isinstance(choice, int):
                choice = self.ctx.channel.id

            guild_id = self.ctx.guild.id
            if guild_id not in self.config:
                self.config[guild_id] = Messages.default_modules
            self.config[guild_id][interaction.data["values"][0]] = choice
            await self.config.flush()

            self.main_view.__init__(self.ctx)
            await interaction.message.edit(
                content="Choose a module to config",
                view=self.view
            )

    def __init__(self, ctx: commands.Context) -> None:
        self.ctx = ctx
        self.cd = ctx.bot.utils.cooldown_manager(2, 5)
        self.select = self.SelectUI(ctx, self)

        super().__init__(timeout=45)
        self.add_item(self.select)


def setup(bot: fate.Fate) -> None:
    """ Add the cog to the bot """
    bot.add_cog(Messages(bot))
