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

    def __init__(self, bot, collection: str):
        self.bot = bot
        self.collection = collection

    @property
    def _db(self) -> AsyncIOMotorCollection:
        return self.bot.aio_mongo[self.collection]

    async def count(self) -> int:
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

    async def _get(self, key) -> dict:
        query = await self._db.find({"_id": key}).to_list(length=1)
        for result in query:
            result.pop("_id")
            return result
        return {}

    async def get(self, key) -> "Data":
        # Remove unused instances
        for key, instance in list(self.instances.items()):
            await asyncio.sleep(0)
            if time() - 300 > instance.last_update:
                if key in self.instances:
                    del self.instances[key]

        # Check if somethings already accessing the document
        if key in self.instances:
            return await self.instances[key].reinstate()

        result = await self._get(key)

        # Double check after handing off the loop
        if key in self.instances:
            return await self.instances[key].reinstate()

        self.instances[key] = Data(self, key, result)
        return self.instances[key]

    async def flush(self):
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
        await self._db.delete_one({"_id": key})


class Data(dict):
    """ Represents a temporary dataclass-like object """
    def __init__(self, state: Cache, key, data):
        self._state = state
        self.key = key

        for _key, value in data.items():
            if value.__class__.__name__ == "dict":
                value = self.make_subclass(deepcopy(value))
            self[_key] = value
        self.copy = deepcopy(data)

        self.last_update = time()
        super().__init__()

    def __setitem__(self, key, value):
        """ Make sure nested dictionaries inherit from NestedData """
        if value.__class__.__name__ == "dict":
            value = self.make_subclass(deepcopy(value))
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.last_update = time()
        super().__delitem__(key)

    def make_subclass(self, dictionary: dict) -> "NestedDict":
        """ Make sure nested dictionaries inherit from NestedData """
        for key, value in list(dictionary.items()):
            if value.__class__.__name__ == "dict":
                dictionary[key] = self.make_subclass(value)
        return NestedDict(self, dictionary)

    async def reinstate(self) -> "Data":
        """ Ran when another process starts using the same object """
        if time() - 300 > self.last_update:
            await self.sync()
        return self

    async def sync(self):
        """ Merge with changes to the DB variant """
        new_data = await self._state._get(self.key)  # type: ignore
        for key, value in new_data.items():
            await asyncio.sleep(0)
            if key not in self.copy or value != self.copy[key]:
                self[key] = value
        self.last_update = time()

    async def save(self, manual: bool = True):
        if self.copy and not self.keys():
            self.copy = {}
            return await self._state.remove(self.key)
        if manual or dict(self) != self.copy:
            self._state.changes[self.key] = dict(self)
        else:
            # Check nested values
            for key, value in self.items():
                await asyncio.sleep(0)
                if value != self.copy[key]:
                    self._state.changes[self.key] = dict(self)
                    break
            else:
                return

        await self._state.flush()
        self.copy = await self._state._get(self.key)


class NestedDict(dict):
    """ Updates the parent dictionaries last_update variable """
    def __init__(self, parent: "Data", data: dict):
        self._parent = parent
        super().__init__(**data)

    def __setitem__(self, key, value):
        # Subclass any new dictionaries
        if value.__class__.__name__ == "dict":
            value = self._parent.make_subclass(value)

        self._parent.last_update = time()

        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._parent.last_update = time()
        super().__delitem__(key)
