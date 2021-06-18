"""
Utility module to make managing files & dbs easier

Classes:
    Cache
    TempDownload

Methods:
    save_json
    download

Copyright (C) 2020-present Michael Stollings
Unauthorized copying, or reuse of anything in this module written by its owner, via any medium is strictly prohibited.
This copyright notice, and this permission notice must be included in all copies, or substantial portions of the Software
Proprietary and confidential
Written by Michael Stollings <mrmichaelstollings@gmail.com>
"""

import asyncio
from copy import deepcopy
from contextlib import suppress
import json
import os
import aiohttp
import aiofiles


class Cache:
    """Object for syncing a dict to MongoDB"""
    def __init__(self, bot, collection, auto_sync=False):
        self.bot = bot
        self.collection = collection
        self._cache = {}
        self._db_state = {}
        for config in bot.mongo[collection].find({}):
            self._cache[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }
        self._db_state = deepcopy(self._cache)
        self.auto_sync = auto_sync
        self.task = None

    async def sync_task(self):
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
                await collection.insert_one({
                    "_id": key, **self._cache[key]
                })
                self._db_state[key] = deepcopy(value)
            elif value != self._db_state[key]:
                await collection.replace_one(
                    filter={"_id": key},
                    replacement=self._cache[key],
                    upsert=True
                )
                self._db_state[key] = deepcopy(value)

    def keys(self):
        return self._cache.keys()

    def items(self):
        return self._cache.items()

    def values(self):
        return self._cache.values()

    def __len__(self):
        return len(self._cache)

    def __contains__(self, item):
        return item in self._cache

    def __getitem__(self, item):
        return self._cache[item]

    def __setitem__(self, key, value):
        self._cache[key] = value
        if self.auto_sync and not self.task:
            self.task = self.bot.loop.create_task(self.sync_task())

    def remove(self, key):
        if key in self._db_state:
            return self.bot.loop.create_task(self._remove_from_db(key))
        else:
            del self._cache[key]
            return asyncio.sleep(0)

    def remove_sub(self, key, sub_key):
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


class TempDownload:
    """ContextManager for saving a file and removing it after use"""
    def __init__(self, filename: str, url: str):
        self.filename = filename
        self.url = url
        files = os.listdir("./.temp")
        if filename:
            if filename in files:
                self.filename += str(len([f for f in files if filename in f]))
            self.fp = os.path.join(os.getcwd(), ".temp", self.filename)

    async def __aenter__(self):
        if not self.filename:
            return None
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self.url) as resp:
                raw_dat = await resp.read()
        async with aiofiles.open(self.fp, "wb") as f:
            await f.write(raw_dat)
        return self.fp

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        if not self.filename:
            return None
        if os.path.isfile(self.fp):
            os.remove(self.fp)


async def save_json(bot, fp, data, mode="w+", **json_kwargs) -> None:
    dump = lambda: json.dumps(data, **json_kwargs)
    async with aiofiles.open(fp + ".tmp", mode) as f:
        await f.write(await bot.loop.run_in_executor(None, dump))
    try:
        os.rename(fp + ".tmp", fp)
    except FileNotFoundError:
        pass


async def download(url: str, timeout: int = 10):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(str(url), timeout=timeout) as resp:
                if resp.status != 200:
                    return None
                return await resp.read()
        except (asyncio.TimeoutError, aiohttp.ClientPayloadError):
            return None
