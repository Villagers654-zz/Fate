from discord.ext import commands
import discord
from discord.errors import NotFound, Forbidden, HTTPException
import asyncio
from time import monotonic



class get_user:
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        self.multi = False

        # Configurable arguments
        self.ctx = None
        self.channel = None
        self.guild = None
        self.user_ids = []
        self.names = []

        self.__parse(*args, **kwargs)

    def __parse(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, commands.Context):
                self.ctx = arg
                if arg.guild:
                    self.guild = arg.guild
                self.channel = arg.channel
            elif isinstance(arg, discord.Message):
                self.channel = arg.channel
                self.guild = arg.guild
                self.user_ids.extend(arg.raw_mentions)
            elif isinstance(arg, int) or (isinstance(arg, str) and arg.isdigit()):
                self.user_ids.append(int(arg))
            elif isinstance(arg, str):
                for word in arg.split():
                    if "@" in word and any(c.isdigit() for c in word):
                        self.user_ids.append(int("".join([c for c in word if c.isdigit()])))
                    elif "@" in word:
                        self.names.append(word.lstrip("@"))
                    else:
                        self.names.append(word)
        if "ctx" in kwargs:
            self.ctx = kwargs["context"]
            self.channel = self.ctx.channel
            if self.ctx.guild:
                self.guild = self.ctx.guild
        elif "context" in kwargs:
            self.ctx = kwargs["context"]
            self.channel = self.ctx.channel
            if self.ctx.guild:
                self.guild = self.ctx.guild
        if "channel" in kwargs:
            self.channel = kwargs["channel"]
            self.guild = self.channel.guild
        if "name" in kwargs:
            self.names.append(kwargs["name"])
        if "names" in kwargs:
            self.names.extend(kwargs["names"])
        if "guild" in kwargs:
            self.guild = kwargs["guild"]
        if "user_id" in kwargs:
            self.user_ids.append(kwargs["user_id"])
        if "user_ids" in kwargs:
            self.user_ids.extend(kwargs["user_ids"])

    def all(self):
        self.multi = True
        return self

    def __await__(self):
        return self.get_user().__await__()

    async def get_user(self):
        users = []
        if self.guild:
            for user_id in self.user_ids:
                member = self.guild.get_member(user_id)
                if member:
                    users.append(member)
            options = []
            for name in self.names:
                for member in self.guild.members:
                    await asyncio.sleep(0)
                    if name.lower() in str(member).lower():
                        options.append(member)
            if len(options) == 1:
                users.append(options[0])
            elif not self.channel:
                users.append(options[0])
            else:
                choices = [m.mention for m in options]
                choice = await self.bot.utils.get_choice(self.ctx, choices, name="Which user")
                if not choice:
                    raise self.bot.ignored_exit
                users.append(options[choices.index(choice)])
        else:
            for user_id in self.user_ids:
                user = self.bot.get_user(user_id)
                if not user:
                    try:
                        user = await self.bot.fetch_user(user_id)
                    except (NotFound, Forbidden, HTTPException):
                        continue
                users.append(user)
            for name in self.names:
                for user in self.bot.users:
                    await asyncio.sleep(0)
                    if name == str(user):
                        users.append(user)

        if not users:
            if self.ctx:
                await self.ctx.send("Couldn't find any users going by that")
                raise self.bot.ignored_exit
            return None

        if len(users) > 1:
            if self.multi:
                return users
            choices = [u.mention for u in users]
            choice = await self.bot.utils.get_choice(self.ctx, choices, name="Which user")
            if not choice:
                if self.channel:
                    await self.channel.send("Timed out waiting for response")
                    raise self.bot.ignored_exit
                return None
            return users[choices.index(choice)]

        return users


async def main():
    await get_user(None, 123, "@no", user_ids=[123, 456, 789, 111])
    await get_user(None, "yes", "<@456>").multiple()


asyncio.run(main())
