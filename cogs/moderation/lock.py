import time
from datetime import datetime, timedelta
import asyncio
import re
from contextlib import suppress

from discord.ext import commands
from discord.errors import HTTPException, NotFound, Forbidden
import discord


locks = {
    "kick": "Kicks all new members",
    "ban": "Bans all new members",
    "mute": "Mutes all new members",
    "new": "Bans recently created accounts"
}
unique = ["kick", "ban"]


class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = bot.utils.cache("locks")
        for guild_id, config in self.lock.items():
            self.lock[guild_id][self.lock[guild_id]["type"]] = {}
            del self.lock[guild_id]["type"]
        self.bot.loop.create_task(self.lock.flush())
        self.cd = {}

    def cog_before_invoke(self, ctx):
        if ctx.command.can_run(ctx):
            if ctx.guild.id not in self.lock:
                self.lock[ctx.guild.id] = {}

    def extract_time(self, string):
        replace = {
            'seconds': 's',
            'minutes': 'm',
            'hours': 'h',
            'days': 'd',
            'weeks': 'w',
            'months': 'M',
            'years': 'y'
        }
        for key, value in replace.items():
            string = string.replace(key, value)
            string = string.replace(key.rstrip('s'), value)
        timers = re.findall("[1-9]*[smhdwMy]", string[:8])
        if not timers:
            return None
        timeframe = 0
        for timer in timers:
            num = ''.join(c for c in timer if c.isdigit())
            if 's' in timer:
                pass
            elif 'm' in timer:
                num *= 60
            elif 'h' in timer:
                num *= 60 * 60
            elif 'd' in timer:
                num *= 60 * 60 * 24
            elif 'w' in timer:
                num *= 60 * 60 * 24 * 7
            elif 'H' in timer:
                num *= 60 * 60 * 24 * 30
            elif 'y' in timer:
                num *= 60 * 60 * 24 * 365
            timeframe += num
        return timeframe

    @commands.command(name="lock")
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        choices = [": ".join(item) for item in locks.items()]
        choice = await self.bot.utils.get_choice(ctx, choices, user=ctx.author)
        if not choice:
            return
        lock = locks[list(locks.keys())[choices.index(choice)]]
        guild_id = ctx.guild.id
        if guild_id in self.lock:
            conflict = [ltype for ltype in self.lock[guild_id].keys() if ltype in unique]
            if lock in unique:
                expression = "lock" if len(self.lock[guild_id]) == 1 else "locks"
                conflicts = ', '.join(self.lock[guild_id].keys())
                await self.lock.remove(guild_id)
                await ctx.send(f"Removed conflicting {expression} `{conflicts}`")
            elif conflict:
                await self.lock.remove(guild_id)
                await ctx.send(f"Removed conflicting `{conflict[0]}` lock")
        if guild_id not in self.lock:
            self.lock[guild_id] = {}
        self.lock[guild_id][lock] = {}

        if lock == "new":
            await ctx.send("How long should the minimum account age be")
            reply = await self.bot.utils.get_message(ctx)
            min_age = self.extract_time(reply.content)
            age_lmt = datetime.utcnow() - timedelta(seconds=min_age)
            violations = []
            for member in list(ctx.guild.members):
                await asyncio.sleep(0)
                if member.created_at > age_lmt:
                    violations.append(member)
            if violations:
                await ctx.send(
                    f"Would you like me to kick {len(violations)} members who don't abide by that minimum age? "
                    f"Reply with either `yes` or `no`"
                )
                reply = await self.bot.utils.get_message(ctx)
                if "yes" in reply.content.lower():
                    for member in violations:
                        with suppress(AttributeError, HTTPException, NotFound, Forbidden):
                            await member.kick(reason=f"Didn't pass minimum age requirement set by {ctx.author}")
                    await ctx.send(f"Successfully kicked {len(violations)} accounts")
        await ctx.send(f"Locked the server")

    @commands.command(name="unlock")
    @commands.has_permissions(administrator=True)
    async def _unlock(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.lock:
            return await ctx.send("There currently isn't active lock")
        self.lock.remove(guild_id)
        await ctx.send("Unlocked the server")
        await ctx.message.add_reaction("👍")

    @commands.Cog.listener()
    async def on_member_join(self, m: discord.Member):
        guild_id = m.guild.id
        member_id = str(m.id)
        if guild_id in self.lock:
            if self.lock[guild_id]["type"] == "kick":
                try:
                    await m.guild.kick(m, reason="Server locked")
                except discord.errors.Forbidden:
                    self.lock.remove(guild_id)
                    return
                except discord.errors.NotFound:
                    return
                try:
                    await m.send(
                        f"**{m.guild.name}** is currently locked. Contact an admin or try again later"
                    )
                except:
                    pass
            if self.lock[guild_id]["type"] == "ban":
                try:
                    await m.guild.ban(m, reason="Server locked", delete_message_days=0)
                except discord.errors.Forbidden:
                    self.lock.remove(guild_id)
                    return
                except discord.errors.NotFound:
                    return
                if member_id not in self.cd:
                    self.cd[member_id] = 0
                if self.cd[member_id] < time.time():
                    try:
                        await m.send(
                            f"**{m.guild.name}** is currently locked. Contact an admin or try again later"
                        )
                    except:
                        pass
                    self.cd[member_id] = time.time() + 25

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.lock:
            self.lock.remove(guild.id)


def setup(bot):
    bot.add_cog(Lock(bot))
