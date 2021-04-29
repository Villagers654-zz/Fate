# Less api spammy invite manager that relies on high uptime

import asyncio
from datetime import datetime, timedelta
from contextlib import suppress

from discord.ext import commands
from discord.errors import HTTPException, NotFound, Forbidden
import discord


class InviteManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, "invites"):
            bot.invites = self
        self.index = bot.utils.cache("invites")
        self.suppressed = (HTTPException, NotFound, Forbidden)

    def invite_to_dict(self, invite) -> dict:
        return {
            "joins": [],
            "leaves": [],
            "temporary": invite.temporary,
            "user_id": invite.inviter.id,
            "uses": invite.uses
        }

    async def init(self, guild):
        if not isinstance(guild, discord.Guild):
            return
        if guild.id in self.index:
            return
        try:
            invites = await guild.invites()
        except self.suppressed:
            raise self.bot.ignored_exit
        self.index[guild.id] = {
            inv.code: self.invite_to_dict(inv) for inv in invites
        }
        await self.index.flush()

    async def re_sync(self, guild):
        """Update the index with any un-logged changes"""
        try:
            invites = await guild.invites()
        except self.suppressed:
            raise self.bot.ignored_exit
        for invite in invites:
            await asyncio.sleep(0)
            if invite.code in self.index[guild.id]:
                if invite.uses != self.index[guild.id][invite.code]["uses"]:
                    self.index[guild.id][invite.code]["uses"] = invite.uses
            else:
                self.index[guild.id][invite.code] = self.invite_to_dict(invite)
        for code, data in list(self.index[guild.id].items()):
            for user_id in data["joins"]:
                await asyncio.sleep(0)
                if not guild.get_member(user_id):
                    self.index[guild.id][code]["leaves"].append(user_id)
                    self.index[guild.id][code]["joins"].remove(user_id)
        await self.index.flush()

    async def disable(self, guild):
        if isinstance(guild, discord.Guild):
            guild_id = guild.id
        else:
            guild_id = int(guild)
        await self.index.remove(guild_id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild or member.guild.id not in self.index:
            return
        guild = member.guild
        with suppress(*self.suppressed):
            invites = await guild.invites()
            discrepancies = []
            for invite in invites:
                if invite.code not in self.index[guild.id]:
                    self.index[guild.id][invite.code] = self.invite_to_dict(invite)
                    if invite.uses != 0:
                        discrepancies.append(invite)
                elif invite.uses != self.index[guild.id][invite.code]["uses"]:
                    discrepancies.append(invite)
            if len(discrepancies) == 1:
                inv = discrepancies[0]
                self.index[guild.id][inv.code]["joins"].append(member.id)
        await self.index.flush()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id == self.bot.user.id:
            return
        if not member.guild or member.guild.id not in self.index:
            return
        guild = member.guild
        for code, data in list(self.index[guild.id].items()):
            await asyncio.sleep(0)
            if member.id in data["joins"]:
                self.index[guild.id][code]["joins"].remove(member.id)
                self.index[guild.id][code]["leaves"].append(member.id)
        await self.index.flush()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.guild.id in self.index:
            self.index[invite.guild.id][invite.code] = self.invite_to_dict(invite)
        await self.index.flush()


def setup(bot):
    bot.add_cog(InviteManager(bot))
