"""
botutils.cache_rewrite
~~~~~~~~~~~~~~~~~~~~~~~

A module for querying and caching data from MongoDB in a simple to use dictionary-like object

:copyright: (C) 2021-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

import asyncio
from contextlib import suppress
from copy import deepcopy
from typing import *
from time import time

from pymongo.errors import DuplicateKeyError
from discord.ext import tasks


class Cache:
    """ Object for querying and caching data from MongoDB """
    _cache: Dict[str, Any] = {}
    _db_state: Dict[str, Any] = {}
    not_enabled: Dict[str, float] = {}
    queries = 0
    cache_queries = 0

    def __init__(self, bot, collection: str, auto_sync=False) -> None:
        self.bot = bot
        self.collection = collection
        self.auto_sync = auto_sync
        self.task = self.remove_unused_keys
        self.task.start()

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key) -> bool:
        return key in self._cache

    def __getitem__(self, key):
        return self._cache[key]

    def __setitem__(self, key, value):
        if key in self.not_enabled:
            del self.not_enabled[key]
        self._cache[key] = deepcopy(value)

    def keys(self) -> Iterable:
        return self._cache.keys()

    def items(self) -> Iterable:
        return self._cache.items()

    def values(self) -> Iterable:
        return self._cache.values()

    def get(self, *args, **kwargs) -> Optional[Any]:
        return self._cache.get(*args, **kwargs)

    @tasks.loop(minutes=5)
    async def remove_unused_keys(self):
        """ Remove keys that haven't been accessed in the last 5 minutes """
        for key, last_accessed in list(self.not_enabled.items()):
            await asyncio.sleep(0)
            if key not in self._cache and key not in self._db_state:
                continue
            if time() - (60 * 5) > last_accessed:
                del self.not_enabled[key]

    async def flush(self) -> None:
        """ Pushes changes from cache into the actual database """
        collection = self.bot.aio_mongo[self.collection]
        for key, value in list(self._cache.items()):
            await asyncio.sleep(0)
            if key not in self._cache:
                continue
            if key not in self._db_state:
                await asyncio.sleep(0.21)
                with suppress(DuplicateKeyError):
                    await collection.insert_one({
                        "_id": key, **self._cache[key]
                    })
                self._db_state[key] = deepcopy(value)
            elif value != self._db_state[key]:
                await asyncio.sleep(0.21)
                await collection.replace_one(
                    filter={"_id": key},
                    replacement=self._cache[key],
                    upsert=True
                )
                self._db_state[key] = deepcopy(value)

    async def cache(self, key) -> None:
        """ Caches a key if not already cached """
        await self.get_or_fetch(key)

    async def _remove_after(self, key, duration: int):
        """ Removes an key from cache after a certain duration """
        await asyncio.sleep(duration)
        if key in self._cache:
            del self._cache[key]
        if key in self._db_state:
            del self._db_state[key]

    async def get_or_fetch(self, key, remove_after: Optional[int] = None) -> Any:
        """ Fetches an key from the cache or db """
        if key in self._cache:
            return self._cache[key]
        if key in self.not_enabled:
            self.not_enabled[key] = time()
            return
        collection = self.bot.aio_mongo[self.collection]
        value = await collection.find_one({"_id": key})
        if not value:
            self.not_enabled[key] = time()
            return
        del value["_id"]
        self._cache[key] = deepcopy(value)
        self._db_state[key] = deepcopy(value)
        if remove_after:
            asyncio.create_task(self._remove_after(key, remove_after))

    def remove(self, key):
        """ An awaitable to remove an item from the cache, and database """
        if key in self._db_state:
            return asyncio.create_task(self._remove_from_db(key))
        else:
            del self._cache[key]
            return asyncio.sleep(0)

    def remove_sub(self, key, sub_key) -> asyncio.Task:
        """ Removes a key from inside the keys dict """
        return asyncio.create_task(self._remove_from_db(key, sub_key))

    async def _remove_from_db(self, key, sub_key=None) -> None:
        """ The coro to remove an item from the cache, and database """
        collection = self.bot.aio_mongo[self.collection]
        if sub_key:
            await collection.update_one(
                filter={"_id": key},
                update={"$unset": {sub_key: 1}}
            )
            with suppress(KeyError):
                del self._cache[key][sub_key]
            with suppress(KeyError):
                if sub_key in self._db_state[key]:
                    del self._db_state[key][sub_key]
        else:
            await collection.delete_one({"_id": key})
            del self._cache[key]
            if key in self._db_state:
                del self._db_state[key]
