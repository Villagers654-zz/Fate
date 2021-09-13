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

from pymongo.errors import DuplicateKeyError


class Cache:
    """Object for syncing a dict to MongoDB"""
    def __init__(self, bot, collection, auto_sync=False) -> None:
        self.bot = bot
        self.collection = collection
        self._cache = {}
        self._db_state = {}
        self.auto_sync = auto_sync
        self.task = None

    async def sync_task(self) -> None:
        await asyncio.sleep(10)
        await self.flush()
        self.task = None

    async def flush(self):
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

    def keys(self) -> Iterable:
        return self._cache.keys()

    def items(self) -> Iterable:
        return self._cache.items()

    def values(self) -> Iterable:
        return self._cache.values()

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, item) -> bool:
        if item in self._cache and self._cache[item] is None:
            return False
        return item in self._cache

    def __getitem__(self, item) -> Coroutine:
        return self._cache[item]

    async def cache(self, item) -> None:
        """ Caches a item if not already cached """
        await self.get_or_fetch(item)

    async def get_or_fetch(self, item) -> Any:
        """ Fetches an item from the cache or db """
        if item in self._cache:
            return self._cache[item]
        collection = self.bot.aio_mongo[self.collection]
        value = await collection.find_one({item: 1})
        if not value:
            if value is None:
                print(f"Setting value to None is pointless")
            value = None
        self._cache[item] = value
        self._db_state[item] = value

    def __setitem__(self, key, value):
        self._cache[key] = value
        if self.auto_sync and not self.task:
            self.task = self.bot.loop.create_task(self.sync_task())

    def remove(self, key) -> Awaitable:
        if key in self._db_state:
            return self.bot.loop.create_task(self._remove_from_db(key))
        else:
            del self._cache[key]
            return asyncio.sleep(0)

    def remove_sub(self, key, sub_key) -> Awaitable:
        return self.bot.loop.create_task(self._remove_from_db(key, sub_key))

    async def _remove_from_db(self, key, sub_key=None):
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
