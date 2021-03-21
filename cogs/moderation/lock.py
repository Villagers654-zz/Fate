from typing import Optional

from discord.ext import commands
from os.path import isfile
import discord
import json
import time


class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = bot.utils.cache("locks")
        self.cd = {}

    @commands.command(name="lock")
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.lock:
            self.lock[guild_id] = {"type": "kick"}
            await self.lock.flush()
            await ctx.send("Locked the server")
            return await ctx.message.add_reaction("👍")
        if self.lock[guild_id]["type"] != "kick":
            self.lock[guild_id]["type"] = "kick"
            await self.lock.flush()
            await ctx.send("Changed the server lock type to kick")
            return await ctx.message.add_reaction("👍")
        self.lock.remove(guild_id)
        await ctx.send("Unlocked the server")
        await ctx.message.add_reaction("👍")

    @commands.command(name="lockb")
    @commands.has_permissions(administrator=True)
    async def lockb(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.lock:
            self.lock[guild_id] = {"type": "ban"}
            await self.lock.flush()
            await ctx.send("Locked the server")
            return await ctx.message.add_reaction("👍")
        if self.lock[guild_id]["type"] != "ban":
            self.lock[guild_id]["type"] = "ban"
            await self.lock.flush()
            await ctx.send("Changed the server lock type to ban")
            return await ctx.message.add_reaction("👍")
        self.lock.remove(guild_id)
        await ctx.send("Unlocked the server")
        await ctx.message.add_reaction("👍")

    @commands.command(name="unlock")
    @commands.has_permissions(administrator=True)
    async def _unlock(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.lock:
            await ctx.send("There currently isn't active lock")
            return await ctx.message.add_reaction("⚠")
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
