# keeps track of invites

from os import path
import json

from discord.ext import commands
import discord


class InviteManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/invites.json"
        self.index = {}
        self.invites = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.invites = json.load(f)
        if bot.is_ready():
            bot.loop.create_task(self.index_invites())

    def save_data(self):
        with open(self.path, "w+") as f:
            json.dump(self.invites, f)

    async def index_invites(self):
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                guild_id = str(guild.id)
                if guild_id not in self.index:
                    self.index[guild_id] = {}
                for invite in invites:
                    self.index[guild_id][invite.code] = invite.uses
                print(f"Indexed {guild.name}")
            except discord.errors.Forbidden:
                pass
        print("Finished indexing")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.index_invites()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        guild_id = str(invite.guild.id)
        if guild_id not in self.invites:
            self.index[guild_id] = {}
        self.index[guild_id][invite.code] = 0

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        guild_id = str(invite.guild.id)
        if guild_id in self.invites:
            del self.index[guild_id][invite.code]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        invites = await member.guild.invites()
        for invite in invites:
            if invite.code not in self.index:
                self.index[guild_id][invite.code] = 0
            if invite.uses != self.index[guild_id][invite.code]:
                print(f"{invite.inviter} invited {member}")
                self.index[guild_id][invite.code] = invite.uses


def setup(bot):
    bot.add_cog(InviteManager(bot))
