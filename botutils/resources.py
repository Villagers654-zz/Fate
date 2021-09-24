"""
External Resources
~~~~~~~~~~~~~~~~~~~

Utility module to make managing files & dbs easier

Classes:
    Cache
    TempDownload

Functions:
    save_json
    download

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from copy import deepcopy
from contextlib import suppress
import json
import os
import aiohttp
import aiofiles
import pymongo.errors
import pymysql
from discord.ext import tasks


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
                await asyncio.sleep(0.21)
                with suppress(pymongo.errors.DuplicateKeyError):
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

    def keys(self):
        return self._cache.keys()

    def items(self):
        return self._cache.items()

    def values(self):
        return self._cache.values()

    def get(self, *args, **kwargs):
        return self._cache.get(*args, **kwargs)

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


class _CacheWriter:
    def __init__(self, cache, filepath):
        self.cache = cache
        self.filepath = filepath

    async def write(self, *args, **kwargs):
        await self.cache.write(self.filepath, *args, **kwargs)


class FileCache:
    def __init__(self, bot):
        self.bot = bot
        self.data = {}  # Filepath: {"args": list, "kwargs": dict}
        self.dump_task.start()

    def __del__(self):
        self.dump_task.stop()

    @tasks.loop(minutes=15)
    async def dump_task(self):
        for filepath, data in list(self.data.items()):
            args = data["args"]
            kwargs = data["kwargs"]
            async with self.bot.utils.open(filepath, "w+") as f:
                await f.write(*args, *kwargs)
            del self.data[filepath]
            self.bot.log.debug(f"Wrote {filepath} from cache")

    async def write(self, filepath, *args, **kwargs):
        self.data[filepath] = {
            "args": args,
            "kwargs": kwargs
        }


class AsyncFileManager:
    def __init__(self, bot, file: str, mode: str = "r", lock: bool = True, cache=False):
        self.bot = bot
        self.file = self.temp_file = file
        if "w" in mode:
            self.temp_file += ".tmp"
        self.mode = mode
        self.fp_manager = None
        self.lock = lock if not cache else False
        self.cache = cache
        if lock and file not in self.bot.locks and not self.cache:
            self.bot.locks[file] = asyncio.Lock()
        self.writer = None

    async def __aenter__(self):
        if self.cache:
            self.writer = _CacheWriter(self.bot.cache, self.file)
            return self.writer
        if self.lock:
            await self.bot.locks[self.file].acquire()
        self.fp_manager = await aiofiles.open(
            file=self.temp_file, mode=self.mode
        )
        return self.fp_manager

    async def __aexit__(self, _exc_type, _exc_value, _exc_traceback):
        if self.cache:
            del self.writer
            return None
        await self.fp_manager.close()
        if self.file != self.temp_file:
            os.rename(self.temp_file, self.file)
        if self.lock:
            self.bot.locks[self.file].release()
        return None


class Cursor:
    def __init__(self, bot, max_retries: int = 10):
        self.bot = bot
        self.conn = None
        self.cursor = None
        self.retries = max_retries

    async def __aenter__(self):
        while not self.bot.pool:
            await asyncio.sleep(10)
        for _ in range(self.retries):
            try:
                self.conn = await self.bot.pool.acquire()
            except (pymysql.OperationalError, RuntimeError):
                await asyncio.sleep(1.21)
                continue
            self.cursor = await self.conn.cursor()
            break
        else:
            raise pymysql.OperationalError("Can't connect to db")
        return self.cursor

    async def __aexit__(self, _type, _value, _tb):
        with suppress(RuntimeError):
            self.bot.pool.release(self.conn)


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
