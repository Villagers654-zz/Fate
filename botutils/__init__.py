"""
Utility Functions Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~

An ease of use wrapper for use with Fate (written in discord.py)

:copyright: (c) Michael Stollings - All Rights Reserved
:license: proprietary and confidential, see LICENSE for details

"""

__title__ = "FateUtils"
__author__ = "FrequencyX4"
__license__ = "proprietary and confidential"
__copyright__ = "Michael Stollings - All Rights Reserved"
__version__ = "1.0.0"

import sys, os
import pkgutil
import importlib

pkgutil.extend_path(os.getcwd(), __name__)

from . import checks, colors, config, custom_logging, get_user, pillow, depricated
from .bytes2human import *
from .prefix import *

from .packages.context_managers import *
from .packages.files import *
from .packages.listeners import *
from .packages.menus import *
from .packages.resources import *
from .packages.tools import *


emotes = Emojis
cache = Cache
operation_lock = OperationLock
format_dict = Formatting.format_dict


def reload():
    """Update the code for all imported modules"""
    for module in sys.modules.values():
        importlib.reload(module)
