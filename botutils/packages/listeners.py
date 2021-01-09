import asyncio

from discord.ext.commands import Context
from discord import User, Member, Message


class CheckError(Exception):
    pass


class CreateListener:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
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

    async def get_reaction(self, check, timeout=60, ignore_timeout=True):
        target_id = self.parse_check(check)  # type: int

        def predicate(r, u):
            return r.message.id == target_id or u.id == target_id

        if hasattr(target_id, "__call__"):
            predicate = target_id

        coro = self.bot.wait_for("reaction_add", check=predicate, timeout=timeout)
        if ignore_timeout:
            try:
                reaction, user = await coro
            except asyncio.TimeoutError:
                raise self.bot.handled_exit
        else:
            reaction, user = await coro

        return reaction, user

    async def get_message(self, check, timeout=60, ignore_timeout=True):
        target = self.parse_check(check)

        def predicate(m):
            return m.author.id == target

        if hasattr(target, "__call__"):
            predicate = target

        coro = self.bot.wait_for("message", check=predicate, timeout=timeout)
        if ignore_timeout:
            try:
                msg = await coro
            except asyncio.TimeoutError:
                raise self.bot.handled_exit
        else:
            msg = await coro

        return msg


def init(cls):
    listener = CreateListener(cls.bot)
    cls.get_message = listener.get_message
    cls.get_reaction = listener.get_reaction
