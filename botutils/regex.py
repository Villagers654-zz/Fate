"""
botutils.regex
~~~~~~~~~~~~~~~

Async friendly regular expression functions

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""


from typing import *
import re
import asyncio


def _loop() -> asyncio.AbstractEventLoop:
    return asyncio.get_running_loop()


async def findall(regex: str, string: str) -> List[str]:
    """ Returns a iterable results object """
    search = lambda: re.finditer(regex, string, re.S)
    results = await _loop().run_in_executor(None, search)
    return [r.group() for r in results]


async def sanitize(string: str) -> str:
    """ Sanitizes a string of pings, and urls """
    regexes = [
        "(https?://)?(www\.)?[^. ]+\.[a-zA-Z]{2,3}[^ ]*",
        "\@((everyone)|(here))",
        "\<\@!?&?[0-9]+\>"
    ]
    fs = map(findall, regexes, [string] * len(regexes))
    for future in asyncio.as_completed(fs):
        results = await future
        for result in results:
            string = string.replace(result, "🚫")
    return string
