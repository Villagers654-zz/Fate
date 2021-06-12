import asyncio
from contextlib import suppress
import os

import pymysql
import aiofiles
from discord.ext import commands

from botutils.depricated import CacheWriter


class Cursor:
    def __init__(self, cls, max_retries: int = 10):
        self.cls = cls
        self.conn = None
        self.cursor = None
        self.retries = max_retries

    async def __aenter__(self):
        while not self.cls.pool:
            await asyncio.sleep(10)
        for _ in range(self.retries):
            try:
                self.conn = await self.cls.pool.acquire()
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
            self.cls.pool.release(self.conn)


class AsyncFileManager:
    def __init__(self, cls, file: str, mode: str = "r", lock: bool = True, cache=False):
        self.cls = cls
        self.file = self.temp_file = file
        if "w" in mode:
            self.temp_file += ".tmp"
        self.mode = mode
        self.fp_manager = None
        self.lock = lock if not cache else False
        self.cache = cache
        if lock and file not in cls.locks and not self.cache:
            cls.locks[file] = asyncio.Lock()
        self.writer = None

    async def __aenter__(self):
        if self.cache:
            self.writer = CacheWriter(self.cls.cache, self.file)
            return self.writer
        if self.lock:
            await self.cls.locks[self.file].acquire()
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
            self.cls.locks[self.file].release()
        return None


class WaitForEvent:
    def __init__(self, cls, event, check=None, channel=None, handle_timeout=False, timeout=60):
        self.cls = cls
        self.event = event
        self.channel = channel
        self.check = check
        self.handle_timeout = handle_timeout
        self.timeout = timeout

        ctx = check if isinstance(check, commands.Context) else None
        if ctx and not self.channel:
            self.channel = self.channel
        if ctx and self.event == "message":
            self.check = (
                lambda m: m.author.id == ctx.author.id
                and m.channel.id == ctx.channel.id
            )

    async def __aenter__(self):
        try:
            message = await self.cls.wait_for(
                self.event, check=self.check, timeout=self.timeout
            )
        except asyncio.TimeoutError as error:
            if not self.handle_timeout:
                raise error
            if self.channel:
                await self.channel.send(f"Timed out waiting for {self.event}")
            raise self.cls.ignored_exit()
        else:
            return message

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
