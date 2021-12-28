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


Key = Union[int, str]


class Cache:
    """ Object for querying and caching data from MongoDB """
    def __init__(self, bot, collection: str):
        self.queries = 0
        self.cache_queries = 0
        self.instances: Dict[Any, "DataContext"] = {}
        self.changes = {}
        self.bot = bot
        self.collection = collection

    @property
    def _db(self) -> AsyncIOMotorCollection:
        """ Shortcut property to get a collection/db instance """
        return self.bot.aio_mongo[self.collection]

    def _has_new(self, key: Key):
        if key in self.instances:
            if time() - 10 > self.instances[key].last_update:
                return False
            return True
        return False

    async def count(self) -> int:
        """ Returns the dbs document count """
        return await self._db.estimated_document_count()

    async def contains(self, key: Key) -> bool:
        """
        Checks if the collection contains a key.
        This should only be used when you don't need the dbs contents returned
        """
        if key in self.instances and len(self.instances[key]):
            return True
        if await self._get(key):
            return True
        return False

    def __getitem__(self, key: Key) -> "Get":
        return Get(self, key)

    def __setitem__(self, key: Key, value):
        if key in self.instances:
            self.instances[key].__init__(self, key, value)
        self.changes[key] = deepcopy(value)
        self.bot.loop.create_task(self.flush())

    def __delitem__(self, key: Key):
        self.bot.loop.create_task(self.remove(key))

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

    async def _get(self, key: Key) -> dict:
        """ Gets the raw results from the db """
        query = await self._db.find({"_id": key}).to_list(length=1)
        for result in query:
            result.pop("_id")
            return result
        return {}

    async def get(self, key: Key, default=None) -> "DataContext":
        """ Gets the results from the db or cache """

        # Remove unused instances
        for _key, instance in list(self.instances.items()):
            await asyncio.sleep(0)
            if time() - 10 > instance.last_update:
                if _key in self.instances:
                    del self.instances[_key]

        # Check if somethings already accessing the document
        if self._has_new(key):
            return self.instances[key]

        result = await self._get(key)

        # Double check after handing off the loop
        # Check if somethings already accessing the document
        if self._has_new(key):
            return self.instances[key]

        if default and not result:
            return default

        self.instances[key] = DataContext(self, key, result)
        return self.instances[key]

    async def fetch(self, key: Key) -> "DataContext":
        """ Skips the cache and queries the DB """
        result = await self._get(key)
        if key in self.instances:
            del self.instances[key]
        self.instances[key] = DataContext(self, key, result)
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
        if key in self.instances:
            self.instances[key].clear()
            del self.instances[key]
        await self._db.delete_many({"_id": key})


class Get:
    context: "DataContext"

    def __init__(self, cache: Cache, key: Key):
        self.cache = cache
        self.key = key

    def __await__(self) -> Generator[None, None, "DataContext"]:
        return self._await().__await__()

    async def _await(self) -> "DataContext":
        return await self.cache.get(self.key)

    async def __aenter__(self) -> "DataContext":
        self.context = await self.cache.get(self.key)
        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.context.save(manual=True)
        if self.key in self.cache.instances:
            del self.cache.instances[self.key]


class DataContext(dict):
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

    async def sync(self):
        """ Merge with changes to the DB variant """
        new_data = await self._state._get(self.key)  # type: ignore
        for key, value in new_data.items():
            await asyncio.sleep(0)
            if key not in self.copy or value != self.copy[key]:
                if value.__class__.__name__ == "dict":
                    value = self.make_subclass(value)
                self[key] = value
        self.copy = new_data
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

    async def delete(self):
        """ Delete the whole config """
        await self._state.remove(self.key)
        self.clear()


class NestedDict(dict):
    """ Updates the parent dictionaries last_update variable """
    def __init__(self, parent: "DataContext", data: dict):
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
