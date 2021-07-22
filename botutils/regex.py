"""
botutils.regex
~~~~~~~~~~~~~~~

Async friendly regular expression coroutine functions

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""


from typing import *
import re
import asyncio


async def _run_in_executor(func: Callable):
    """ Runs a function in the bots thread pool to avoid blocking the loop """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func)


async def search(pattern: str, string: str) -> Optional[str]:
    """ Returns a single match for a pattern """
    _search = lambda: re.search(pattern, string)
    result = await _run_in_executor(_search)
    return result.group() if result else None


async def findall(pattern: str, string: str) -> List[str]:
    """ Returns a iterable results object """
    _search = lambda: re.finditer(pattern, string, re.S)
    results = await _run_in_executor(_search)
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
