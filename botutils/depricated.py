import asyncio
from contextlib import suppress
from time import time
from aiohttp import web

from discord.ext import commands, tasks


cd = {}
cards = {}


def default_cooldown():
    return [2, 5, commands.BucketType.user]


class FakeCtx:
    guild = None


class Result:
    def __init__(self, result, errored=False, traceback=None):
        self.result = result
        self.errored = errored
        self.traceback = traceback


class TempList(list):
    def __init__(self, bot, keep_for: int = 10):
        self.bot = bot
        self.keep_for = keep_for
        super().__init__()

    async def remove_after(self, value):
        await asyncio.sleep(self.keep_for)
        with suppress(IndexError):
            super().remove(value)

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.bot.loop.create_task(
            self.remove_after(args[0])
        )


class CacheWriter:
    def __init__(self, cache, filepath):
        self.cache = cache
        self.filepath = filepath

    async def write(self, *args, **kwargs):
        await self.cache.write(self.filepath, *args, **kwargs)


class Cache:
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
            async with self.bot.open(filepath, "w+") as f:
                await f.write(*args, *kwargs)
            del self.data[filepath]
            self.bot.log.debug(f"Wrote {filepath} from cache")

    async def write(self, filepath, *args, **kwargs):
        self.data[filepath] = {
            "args": args,
            "kwargs": kwargs
        }


class TempConvo:
    def __init__(self, context):
        self.ctx = context
        self.sent = []

    def predicate(self, message):
        return message.author.id in [self.ctx.author.id, self.ctx.bot.user.id]

    async def __aenter__(self):
        return self

    async def __aexit__(self, _type, _tb, _exc):
        before = self.sent[len(self.sent) - 1]
        after = self.sent[0]
        msgs = await self.ctx.channel.history(before=before, after=after).flatten()
        await self.ctx.channel.delete_messages([
            before, after, *[
                msg for msg in msgs if self.predicate(msg)
            ]
        ])

    async def send(self, *args, **kwargs):
        msg = await self.ctx.send(*args, **kwargs)
        self.sent.append(msg)


async def get_top(self, request):
    ip = request.remote
    now = int(time() / 25)
    if ip not in cd:
        cd[ip] = [now, 0]
    if cd[ip][0] == now:
        cd[ip][1] += 1
    else:
        cd[ip] = [now, 0]
    if cd[ip][1] > 3:
        return web.Response(text="You are being rate-limited", status=404)

    guild_id = int(request.path.lstrip("/top/"))
    guild = self.get_guild(guild_id)
    if not guild:
        return web.Response(text="Unknown server", status=404)
    ctx = FakeCtx()
    ctx.guild = guild

    cog = self.cogs["Ranking"]
    if guild_id in cards:
        file = cards[guild_id]
        created = False
    else:
        fp = await cog.top(ctx)
        async with self.open(fp, "rb") as f:
            file = await f.read()
        cards[guild_id] = file
        created = True

    resp = web.StreamResponse()
    resp.headers["Content-Type"] = f"Image/PNG"
    resp.headers["Content-Disposition"] = f"filename='top.png';"
    await resp.prepare(request)
    await resp.write(file)
    await resp.write_eof()

    async def wait():
        await asyncio.sleep(30)
        del cards[guild_id]

    if created:
        self.loop.create_task(wait())
