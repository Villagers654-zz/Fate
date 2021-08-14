from datetime import datetime, timezone, timedelta
import asyncio
from contextlib import suppress

from discord.ext import commands
from discord.errors import HTTPException, NotFound, Forbidden
import discord

from botutils import extract_time, GetChoice
from fate import Fate


locks = {
    "kick": "Kicks all new members",
    "ban": "Bans all new members",
    "mute": "Mutes all new members",
    "new": "Bans recently created accounts"
}

unique = ["kick", "ban"]


class Lock(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.lock = bot.utils.cache("locks")
        self.cd = {}

    def is_enabled(self, guild_id):
        return guild_id in self.lock

    async def cog_before_invoke(self, ctx):
        if await ctx.command.can_run(ctx):
            if ctx.guild.id not in self.lock:
                self.lock[ctx.guild.id] = {}

    @commands.command(name="lock")
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        choices = [": ".join(item) for item in locks.items()]
        choice = await GetChoice(ctx, choices)
        lock = list(locks.keys())[choices.index(choice)]
        guild_id = ctx.guild.id
        if guild_id in self.lock:
            conflict = [ltype for ltype in self.lock[guild_id].keys() if ltype in unique]
            if lock in unique and self.lock[guild_id]:
                expression = "lock" if len(self.lock[guild_id]) == 1 else "locks"
                conflicts = ', '.join(self.lock[guild_id].keys())
                await self.lock.remove(guild_id)
                await ctx.send(f"Removed conflicting {expression} `{conflicts}`")
            elif conflict:
                await self.lock.remove(guild_id)
                await ctx.send(f"Removed conflicting `{conflict[0]}` lock")
        if guild_id not in self.lock:
            self.lock[guild_id] = {}

        # Kick and ban lock
        if lock in unique:
            self.lock[guild_id][lock] = {}

        # Mute on_join lock
        if lock == "mute":
            await ctx.send("How long should I mute new users? Reply with `0` to permanently mute")
            reply = await self.bot.utils.get_message(ctx)
            if reply.content == "0":
                duration = None
            else:
                duration = extract_time(reply.content)
            self.lock[guild_id]["mute"] = {
                "duration": duration
            }

        # Kick new accounts lock
        if lock == "new":
            await ctx.send("How long should the minimum account age be?")
            reply = await self.bot.utils.get_message(ctx)
            min_age = extract_time(reply.content)
            if not min_age:
                return await ctx.send("Invalid format")
            self.lock[guild_id][lock] = {"age_lmt": min_age}

        await ctx.send(f"Locked the server")
        await self.lock.flush()

        # Check members that have already joined
        if lock == "new":
            age_lmt = datetime.now(tz=timezone.utc) - timedelta(seconds=self.lock[guild_id][lock]["age_lmt"])
            violations = []
            for member in list(ctx.guild.members):
                await asyncio.sleep(0)
                if member.created_at > age_lmt:
                    if ctx.author.top_role.position > member.top_role.position:
                        violations.append(member)
            if violations:
                await ctx.send(
                    f"Would you like me to kick {len(violations)} members who don't abide by that minimum age? "
                    f"Reply with either `yes` or `no`"
                )
                reply = await self.bot.utils.get_message(ctx)
                if "yes" in reply.content.lower():
                    await ctx.send(f"Beginning to kick {len(violations)} members. Reply with `cancel` to stop")
                    for member in violations:
                        await asyncio.sleep(1.21)
                        last = ctx.channel.last_message
                        if last and not last.author.bot and "cancel" in last.content:
                            await ctx.send("Alright, kick operation cancelled")
                            break
                        with suppress(AttributeError, HTTPException, NotFound, Forbidden):
                            await member.kick(reason=f"Didn't pass minimum age requirement set by {ctx.author}")
                    await ctx.send(f"Successfully kicked {len(violations)} accounts")

    @commands.command(name="unlock")
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.lock:
            return await ctx.send("There currently isn't active lock")
        has_bans = False
        if "ban" in self.lock[guild_id] or "new" in self.lock[guild_id]:
            has_bans = True
        await self.lock.remove(guild_id)
        await self.lock.flush()
        await ctx.send("Unlocked the server")
        if has_bans:
            await ctx.send("Do you want me to unban anyone that was banned by the lock?")
            reply = await self.bot.utils.get_message(ctx)
            if "yes" not in reply.content.lower():
                return
            await ctx.send("Okay, unbanning now")
            bans = await ctx.guild.bans()
            counter = 0
            for ban_entry in bans:
                if ban_entry.reason and "Server locked" in ban_entry.reason:
                    await ctx.guild.unban(ban_entry.user)
                    counter += 1
            await ctx.send(f"Unbanned {counter} users")

    @commands.Cog.listener()
    async def on_member_join(self, m: discord.Member):
        guild_id = m.guild.id
        if not m.bot and guild_id in self.lock:
            if "kick" in self.lock[guild_id]:
                with suppress(HTTPException, Forbidden):
                    await m.send(f"**{m.guild.name}** is currently locked. Contact an admin or try again later")
                try:
                    await m.guild.kick(m, reason="Server locked")
                except Forbidden:
                    self.lock.remove(guild_id)
                except NotFound:
                    return
            elif "ban" in self.lock[guild_id]:
                with suppress(HTTPException, Forbidden):
                    await m.send(f"**{m.guild.name}** is currently locked. Contact an admin or try again later")
                try:
                    await m.guild.ban(m, reason="Server locked", delete_message_days=0)
                except Forbidden:
                    self.lock.remove(guild_id)
                except NotFound:
                    pass
            elif "new" in self.lock[guild_id]:
                age_lmt = datetime.now(tz=timezone.utc) - timedelta(seconds=self.lock[guild_id]["new"]["age_lmt"])
                if m.created_at > age_lmt:
                    with suppress(HTTPException, Forbidden):
                        await m.send(f"Your account's too new to join **{m.guild}**. Try again in the future")
                    try:
                        await m.guild.ban(m, reason="Server locked")
                    except Forbidden:
                        self.lock.remove(guild_id)
                    except NotFound:
                        return
            elif "mute" in self.lock[guild_id]:
                mute_role = await self.bot.attrs.get_mute_role(m.guild)
                if not mute_role:
                    self.lock.remove(guild_id)
                with suppress(Forbidden, HTTPException):
                    await m.add_roles(mute_role)
                if duration := self.lock[guild_id]["mute"]["duration"]:
                    await asyncio.sleep(duration)
                    await m.remove_roles(mute_role)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.lock:
            self.lock.remove(guild.id)


def setup(bot):
    bot.add_cog(Lock(bot), override=True)
