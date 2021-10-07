"""
Exceptions
~~~~~~~~~~~

Classes of custom exceptions

:copyright: (C) 2019-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

from aiohttp import web


class IgnoredExit(Exception):
    """
    An exception ignored by the bots error handler.
    This is used to easily stop operation inside something nested
    """
    pass


class aiohttp:
    """ Web response shortcuts """
    rate_limit = web.Response(text="You are being rate-limited", status=404)
    invalid_data = web.Response(text="Invalid data", status=404)
    invalid_login = web.Response(text="Invalid Login Credentials", status=404)
