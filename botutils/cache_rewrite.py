"""
botutils.cache_rewrite
~~~~~~~~~~~~~~~~~~~~~~~

A module for querying and caching data from MongoDB in a simple to use dictionary-like object

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import asyncio
from copy import deepcopy
from typing import *
from time import time

from motor.motor_asyncio import AsyncIOMotorCollection


class Cache:
    """ Object for querying and caching data from MongoDB """
    queries = 0
    cache_queries = 0
    instances: Dict[Any, "Data"] = {}
    changes = {}

    def __init__(self, bot, collection: str) -> None:
        self.bot = bot
        self.collection = collection

    @property
    def _db(self) -> AsyncIOMotorCollection:
        return self.bot.aio_mongo[self.collection]

    async def count(self):
        return await self._db.estimated_document_count()

    def __getitem__(self, key) -> "Cache.get":
        return self.get(key)

    def __setitem__(self, key, value):
        self.changes[key] = deepcopy(value)

    async def keys(self) -> AsyncGenerator:
        async for document in self._db.find({}):
            yield document["_id"]

    async def values(self) -> AsyncGenerator:
        async for document in self._db.find({}):
            document.pop("_id")
            return document

    async def items(self) -> AsyncGenerator:
        async for document in self._db.find({}):
            _id = document.pop("_id")
            yield _id, document

    async def _get(self, key) -> Optional[dict]:
        query = await self._db.find({"_id": key}).to_list(length=1)
        for result in query:
            result.pop("_id")
            return result
        return None

    async def get(self, key) -> Optional["Data"]:
        # Remove unused instances
        for key, instance in list(self.instances.items()):
            await asyncio.sleep(0)
            if time() - 300 > instance.last_sync:
                if key in self.instances:
                    del self.instances[key]

        # Check if somethings already accessing the document
        if key in self.instances:
            return await self.instances[key].reinstate()

        result = await self._get(key)
        if not result:
            return None

        # Double check after handing off the loop
        if key in self.instances:
            return await self.instances[key].reinstate()

        self.instances[key] = Data(self, key, result)
        return self.instances[key]

    async def flush(self) -> None:
        """ Pushes changes from cache into the actual database """
        collection = self.bot.aio_mongo[self.collection]
        for key, value in list(self.changes.items()):
            await asyncio.sleep(0)
            value["_id"] = key
            await collection.replace_one(
                filter={"_id": key},
                replacement=value,
                upsert=True
            )
            del self.changes[key]

    async def remove(self, key):
        """ An awaitable to remove an item from the cache, and database """
        await self._db.delete_one({key: 1})


class Data(dict):
    def __init__(self, state: Cache, key, data):
        self.state = state
        self.key = key

        for _key, value in data.items():
            self[_key] = value
        self.copy = deepcopy(data)

        self.last_sync = time()
        super().__init__()

    async def reinstate(self) -> "Data":
        """ Ran when another process starts using the same object """
        if time() - 300 > self.last_sync:
            await self.sync()
        return self

    async def sync(self):
        """ Merge with changes to the DB variant """
        new_data = await self.state._get(self.key)
        for key, value in new_data.items():
            await asyncio.sleep(0)
            if key not in self.copy or value != self.copy[key]:
                self[key] = value
        self.last_sync = time()

    async def flush(self, manual: bool = True):
        if manual or dict(self) != self.copy:
            self.state.changes[self.key] = dict(self)
        else:
            for key, value in self.items():
                await asyncio.sleep(0)
                if value != self.copy[key]:
                    self.state.changes[self.key] = dict(self)
                    break
        await self.state.flush()
