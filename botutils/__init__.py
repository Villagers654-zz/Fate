"""
Utility Functions Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~

An ease of use wrapper for use with Fate(written in discord.py)

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

__title__ = "BotUtils"
__author__ = "FrequencyX4"
__license__ = "Proprietary and Confidential"
__copyright__ = "Copyright (C) 2021-present Michael Stollings"
__version__ = "1.0.0"

from . import colors, emojis, pillow
from .attributes import Attributes
from .get_user import GetUser
from .listeners import Listener, Conversation
from .menus import *
from .prefixes import *
from .resources import *
from .stack import Stack
from .tools import *
from .views import *
from .regex import *


class Utils(commands.Cog):
    """Represents the bot.utils attribute for utils requiring access to the running instance"""
    def __init__(self, bot):
        self.bot = bot
        self.attrs = Attributes(bot)

        OperationLock.bot = bot
        self.operation_lock = OperationLock

        # Remove the bot arg
        self.get_user = lambda *args, **kwargs: GetUser(bot, *args, **kwargs)
        self.cache = lambda *args, **kwargs: Cache(bot, *args, **kwargs)
        self.cooldown_manager = lambda *args, **kwargs: CooldownManager(bot, *args, **kwargs)
        self.open = lambda *args, **kwargs: AsyncFileManager(bot, *args, **kwargs)
        self.save_json = lambda *args, **kwargs: save_json(bot, *args, **kwargs)

        # Menus
        ui = Menus(bot)
        self.verify_user = ui.verify_user
        self.get_choice = ui.get_choice
        self.configure = ui.configure
        self.get_answers_from = ui.get_answers_from
        self.get_answer = ui.ask

        # Listeners
        listener = Listener(bot)
        self.get_message = listener.get_message
        self.get_reaction = listener.get_reaction
        self.get_role = get_role

        # Formatting
        formatting = Formatting(bot)
        self.format_dict = formatting.format_dict
        self.add_field = formatting.add_field
        self.dump_json = formatting.dump_json

    def cursor(self, *args, **kwargs) -> Cursor:
        return Cursor(self.bot, *args, **kwargs)

    async def is_filtered(self, message, ctx = None) -> bool:
        """|coro|
        Checks if:
        - a message was deleted by chatfilter or antispam,
        - has mentions that it shouldn't
        - contains chat filtered words

        Parameters
        -----------
        message : Message
        ctx : commands.Context
        """
        if isinstance(message, Message):
            if message.guild.id in self.bot.filtered_messages:
                if message.id in self.bot.filtered_messages[message.guild.id]:
                    return True
            message = message.content
        if ctx:
            coro = sanitize(message, ctx)
        else:
            coro = sanitize(message)
        new_content, _flags = await coro
        if new_content:
            return True
        return False
