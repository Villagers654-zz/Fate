"""
botutils.cache_rewrite
~~~~~~~~~~~~~~~~~~~~~~~

The completed version of botutils.resources.Cache that doesn't
fetch from the db until needed, rather than fetching everything on startup

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from contextlib import suppress
from copy import deepcopy
from typing import *
from time import time

from pymongo.errors import DuplicateKeyError
from discord.ext import tasks


class Cache:
    """Object for syncing a dict to MongoDB"""
    _cache: Dict[str, Any] = {}
    _db_state: Dict[str, Any] = {}
    last_used: Dict[str, float] = {}
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
        if key in self._cache:
            self.last_used[key] = time()
            if self._cache[key] == {}:
                return False
            return True
        return key in self._cache

    def __getitem__(self, key):
        return self._cache[key]

    def __setitem__(self, key, value):
        self._cache[key] = deepcopy(value)

    def keys(self) -> Iterable:
        return self._cache.keys()

    def items(self) -> Iterable:
        return self._cache.items()

    def values(self) -> Iterable:
        return self._cache.values()

    @tasks.loop(minutes=5)
    async def remove_unused_keys(self):
        """ Remove keys that haven't been accessed in over an hour """
        for key, time_used in list(self.last_used.items()):
            await asyncio.sleep(0)
            if key not in self._cache and key not in self._db_state:
                continue
            if time() - (60 * 10) > time_used:
                if key in self._cache:
                    del self._cache[key]
                if key in self._db_state:
                    del self._db_state[key]
                del self.last_used[key]

    async def flush(self) -> None:
        """ Pushes changes from cache into the actual database """
        collection = self.bot.aio_mongo[self.collection]
        for key, value in list(self._cache.items()):
            if value == {} and key not in self._db_state:
                continue
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
            self.cache_queries += 1
            return self._cache[key]
        collection = self.bot.aio_mongo[self.collection]
        value = await collection.find_one({"_id": key})
        if not value:
            value = {}
        else:
            del value["_id"]
        self._cache[key] = deepcopy(value)
        self._db_state[key] = deepcopy(value)
        self.last_used[key] = time()
        if remove_after:
            asyncio.create_task(self._remove_after(key, remove_after))
        self.queries += 1

    def remove(self, key) -> Union[asyncio.Future, asyncio.Task]:
        """ Removes an item from the cache, and database """
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
