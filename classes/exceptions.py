"""
Exceptions
~~~~~~~~~~~

Classes of custom exceptions

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from aiohttp import web


class EmptyException(Exception):
    pass


class aiohttp:
    rate_limit = web.Response(text="You are being rate-limited", status=404)
    invalid_data = web.Response(text="Invalid data", status=404)
    invalid_login = web.Response(text="Invalid Login Credentials", status=404)
