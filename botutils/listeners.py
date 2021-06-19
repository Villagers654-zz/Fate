import asyncio

from discord.ext.commands import Context
from discord import User, Member, Message
from discord.ext import commands


class CheckError(Exception):
    pass


class WaitForEvent:
    def __init__(self, bot, event, check=None, channel=None, handle_timeout=False, timeout=60):
        self.bot = bot
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
            message = await self.bot.wait_for(
                self.event, check=self.check, timeout=self.timeout
            )
        except asyncio.TimeoutError as error:
            if not self.handle_timeout:
                raise error
            if self.channel:
                await self.channel.send(f"Timed out waiting for {self.event}")
            raise self.bot.ignored_exit()
        else:
            return message

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def parse_check(check) -> int:
    if hasattr(check, "__call__"):
        return check
    ids = []
    if isinstance(check, Context):
        ids.append(check.author.id)
    elif isinstance(check, (User, Member, Message)):
        ids.append(check.id)
    elif isinstance(check, int):
        ids.append(check)
    else:
        raise CheckError(f"Check of type '{type(check)}' isn't implemented")
    return ids[0]


class Listener:
    def __init__(self, bot):
        self.bot = bot

    async def get_reaction(self, check, timeout=60, ignore_timeout=True, duel=False):
        target_id = parse_check(check)  # type: int

        def predicate(r, u):
            return r.message.id == target_id or u.id == target_id

        if hasattr(target_id, "__call__"):
            predicate = target_id

        coro = self.bot.wait_for("reaction_add", check=predicate, timeout=timeout)

        if duel:
            async def wait_for(event):
                coro = self.bot.wait_for(event, check=predicate, timeout=timeout)
                try:
                    return await coro
                except:
                    return None

            tasks = [
                self.bot.loop.create_task(wait_for("reaction_add")),
                self.bot.loop.create_task(wait_for("reaction_remove"))
            ]
            while True:
                for i, task in enumerate(tasks):
                    await asyncio.sleep(0)
                    if task.done() and task.exception():
                        raise self.bot.ignored_exit
                    if task.done():
                        tasks[0 if i == 1 else 1].cancel()
                        result = task.result()
                        if result is None:
                            raise self.bot.ignored_exit
                        return result
                await asyncio.sleep(0.01)

        if ignore_timeout:
            try:
                reaction, user = await coro
            except asyncio.TimeoutError:
                raise self.bot.ignored_exit
        else:
            reaction, user = await coro

        return reaction, user

    async def get_message(self, check, timeout=60, ignore_timeout=True):
        target = parse_check(check)

        def predicate(m):
            return m.author.id == target

        if hasattr(target, "__call__"):
            predicate = target

        coro = self.bot.wait_for("message", check=predicate, timeout=timeout)
        if ignore_timeout:
            try:
                msg = await coro
            except asyncio.TimeoutError:
                raise self.bot.ignored_exit
        else:
            msg = await coro

        return msg
