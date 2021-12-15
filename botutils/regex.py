"""
botutils.regex
~~~~~~~~~~~~~~~

Async friendly regular expression coroutine functions

Functions:
    search : Returns a single match for a pattern
    findall : Returns a iterable results object
    sanitize : Sanitizes a string of pings, and urls
    find_links : Finds all the urls in a string
    find_link : Finds the first url in a string

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
import re
import asyncio

from discord.ext.commands import Context


url_expression = "[a-zA-Z0-9]+\.[a-zA-Z]{2,16}[a-zA-Z0-9./\-_?]*"
ping_expression = "(\@((everyone)|(here)))|(\<\@!?&?[0-9]+\>)"


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


async def sanitize(string: str, ctx: Context = None) -> str:
    """ Sanitizes a string of pings, and urls """
    fs = map(findall, [url_expression, ping_expression], [string] * 2)
    for future in asyncio.as_completed(fs):
        results = await future
        for result in results:
            string = string.replace(result, "🚫")
    if cog := ctx.bot.get_cog("ChatFilter") if ctx else None:
        clean_content, _flags = await cog.run_default_filter(ctx.guild.id, string)
        if clean_content:
            string = clean_content
    return string


async def find_links(string: str) -> List[str]:
    """ Finds all the urls in a string """
    return await findall(url_expression, string)


async def find_link(string: str) -> Optional[str]:
    """ Finds the first url in a string """
    for url in await find_links(string):
        return url
