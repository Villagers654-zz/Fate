"""
botutils.interactions
~~~~~~~~~~~~~~~~~~~~~~

A module for template interaction classes

Classes:
    ModView : A View that only moderators can interact with
    AuthorView : A view that only the author of the original message can interact with

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from discord import ui, Interaction
from discord.ext.commands import Context
from . import CooldownManager


class ModView(ui.View):
    ctx: Context
    cd: CooldownManager

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
    cd: CooldownManager

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Only moderators can interact", ephemeral=True
            )
            return False
        if self.cd.check(interaction.user.id):
            return False
        return True
