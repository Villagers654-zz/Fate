"""
botutils.views
~~~~~~~~~~~~~~~

Quick button menus for ease of use

Classes:
    ChoiceButtons
    CancelButton

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from discord import ui, ButtonStyle, Button, Interaction
from discord.errors import NotFound


class ChoiceButtons(ui.View):
    def __init__(self):
        self.choice = None
        super().__init__(timeout=45)

    @ui.button(label="Yes", style=ButtonStyle.green)
    async def yes(self, _button, interaction):
        self.choice = True
        await interaction.message.edit(view=None)
        self.stop()

    @ui.button(label="No", style=ButtonStyle.red)
    async def no(self, _button, interaction):
        self.choice = False
        await interaction.message.edit(view=None)
        self.stop()


class CancelButton(ui.View):
    is_cancelled: bool = False
    def __init__(self, permission: str):
        self.permission = permission
        super().__init__(timeout=3600)

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel_button(self, _button: Button, interaction: Interaction):
        try:
            member = interaction.guild.get_member(interaction.user.id)
            if not member or not getattr(member.guild_permissions, self.permission):
                return await interaction.response.send_message(
                    "You need manage_message permissions to cancel this", ephemeral=True
                )
            self.is_cancelled = True
            await interaction.response.send_message("Cancelled the operation")
            await interaction.message.edit(view=None)
            self.stop()
        except NotFound:
            pass
