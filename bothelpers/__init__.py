"""
Utility Functions Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~

An ease of use wrapper for use with Fate(written in discord.py)

Copyright (C) 2020-present Michael Stollings
Unauthorized copying, or reuse of anything in this module written by its owner, via any medium is strictly prohibited.
This copyright notice, and this permission notice must be included in all copies, or substantial portions of the Software
Proprietary and confidential
Written by Michael Stollings <mrmichaelstollings@gmail.com>
"""

__title__ = "BotUtils"
__author__ = "FrequencyX4"
__license__ = "proprietary and confidential"
__copyright__ = "Copyright (C) 2020-present Michael Stollings"
__version__ = "2.0.0"

from discord.ext import commands

from . import colors, emojis
from .get_user import GetUser
from .listeners import Listener
from .menus import Menus
from .resources import *
from .stack import Stack
from .tools import *


class Utils(commands.Cog):
    """Represents the bot.utils attribute for utils requiring access to the running instance"""
    def __init__(self, bot):
        self.bot = bot

        OperationLock.bot = bot
        self.operation_lock = OperationLock

        # Remove the bot arg
        self.get_user = lambda *args, **kwargs: GetUser(bot, *args, **kwargs)
        self.cache = lambda *args, **kwargs: Cache(bot, *args, **kwargs)
        self.cooldown_manager = lambda *args, **kwargs: CooldownManager(bot, *args, **kwargs)

        # Menus
        ui = Menus(bot)
        self.verify_user = ui.verify_user
        self.get_choice = ui.get_choice
        self.configure = ui.configure

        # Listeners
        listener = Listener(bot)
        self.get_message = listener.get_message
        self.get_reaction = listener.get_reaction

        # Formatting
        formatting = Formatting(bot)
        self.format_dict = formatting.format_dict
        self.add_field = formatting.add_field
        self.dump_json = formatting.dump_json
