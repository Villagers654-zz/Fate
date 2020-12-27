import json
import os
import aiohttp
import asyncio

import aiofiles


class TempDownload:
    def __init__(self, filename: str, url: str):
        self.filename = filename
        self.url = url
        files = os.listdir("./.local")
        if filename in files:
            self.filename += str(len([f for f in files if filename in f]))
        self.fp = os.path.join(os.getcwd(), ".local", self.filename)

    async def __aenter__(self):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self.url) as resp:
                raw_dat = await resp.read()
        async with aiofiles.open(self.fp, "wb") as f:
            await f.write(raw_dat)
        return self.fp

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        if os.path.isfile(self.fp):
            os.remove(self.fp)


async def save_json(fp, data, mode="w+", **json_kwargs) -> None:
    # self.log(f"Saving {fp}", "DEBUG")
    # before = monotonic()
    async with aiofiles.open(fp + ".tmp", mode) as f:
        await f.write(json.dumps(data, **json_kwargs))
    # ping = str(round((monotonic() - before) * 1000))
    # self.log(f"Wrote to tmp file in {ping}ms", "DEBUG")
    # before = monotonic()
    try:
        os.rename(fp + ".tmp", fp)
    except FileNotFoundError:
        pass
        # self.log("Tmp file didn't exist, not renaming", "DEBUG")
    # ping = str(round((monotonic() - before) * 1000))
    # self.log(f"Replaced old file in {ping}ms", "DEBUG")


async def download(url: str, timeout: int = 10):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(str(url), timeout=timeout) as resp:
                if resp.status != 200:
                    return None
                return await resp.read()
        except (asyncio.TimeoutError, aiohttp.ClientPayloadError):
            return None


def init(cls):
    cls.tempdl = TempDownload
    cls.save_json = save_json
    cls.download = download
