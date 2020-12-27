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

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", check=predicate, timeout=timeout
            )
        except asyncio.TimeoutError:
            if ignore_timeout:
                raise self.bot.handled_exit
            return None
        return reaction, user


def init(cls):
    cls.listener = CreateListener(cls.bot)
