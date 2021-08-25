# AioMySQL invite indexer Cog for Discord.Py v1.3

import base64
from typing import Optional
import json

from discord.ext import commands
import discord

from botutils import colors


class BetterInviteManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def config(self, guild_id: int, get_invites=False) -> Optional[None, dict]:
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select channel, format "
                f"from invite_manager "
                f"where guild_id = {guild_id} "
                f"limit 1;"
            )
            result = await cur.fetchone()
            if not result:
                return None
            data = {"channel": result[0], "format": result[1]}
            if get_invites:
                await cur.execute(
                    f"select code, inviters "
                    f"from invites "
                    f"where guild_id = {guild_id};"
                )
                results = await cur.fetchall()
                data["invites"] = {
                    self.decrypt(code): json.loads(self.decrypt(inviters))
                    for code, inviters in results
                }
            return data

    def encrypt(self, string) -> str:
        return base64.b64encode(string.encode()).decode()

    def decrypt(self, string) -> str:
        return base64.b64decode(string.encode()).decode()

    def dump(self, data: dict):
        return self.encrypt(json.dumps(data))

    async def update_index(self, guild_id, index: dict):
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"update invites "
                f"set index = {self.dump(index)} "
                f"where guild_id = {guild_id};"
            )

    async def add_invite(self, invite: discord.Invite):
        guild_id = invite.guild.id  # type: int
        data = self.dump({"inviter": invite.inviter.id, "joins": [], "leaves": []})
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into invite_index "
                f"values ({guild_id}, {invite.code}, {data});"
            )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        config = await self.config(invite.guild.id)
        if isinstance(config, dict):  # Management is enabled
            await self.add_invite(invite)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if not member.bot and await self.config(guild.id):
            config = await self.config(guild.id, get_invites=True)
            invites = await guild.invites()
            code = None
            for invite in invites:
                code = invite.code
                if code not in config["invites"]:
                    config["invites"][code] = {
                        "inviter": invite.inviter.id,
                        "joins": [],
                        "leaves": [],
                    }
                    if invite.uses:
                        if member.id not in config["invites"][code]:
                            config["invites"][code]["joins"].append(member.id)
                        break
                if invite.uses > config["invites"]:
                    if member.id not in config["invites"][code]:
                        config["invites"][code]["joins"].append(member.id)
            else:
                self.bot.log.debug(f"Couldn't index {member} in {guild}")
            channel = self.bot.get_channel(config["channel"])
            if channel:
                joins = len(
                    list(
                        filter(
                            lambda dat: member.id in dat["joins"],
                            config["invites"].values(),
                        )
                    )
                )
                leaves = len(
                    list(
                        filter(
                            lambda dat: member.id in dat["leaves"],
                            config["invites"].values(),
                        )
                    )
                )
                inviter = self.bot.get_user(config["invites"][code]["invites"])
                if not inviter:
                    inviter = await self.bot.fetch_user(
                        config["invites"][code]["inviter"]
                    )
                e = discord.Embed(color=colors.fate)
                e.set_author(name=f"{member} has joined", icon_url=member.display_avatar.url)
                e.set_thumbnail(url=inviter.display_avatar.url)
                e.description = (
                    f"**Inviter:** @{inviter}"
                    f"\n**Joins:** `{joins}` **Leaves:** `{leaves}`"
                )
                await channel.send(
                    f"{member} has joined, invited by {inviter if inviter else 'Unknown'}"
                )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if not invite.uses:
            config = await self.config(invite.guild.id, get_invites=True)
            if isinstance(config, dict):
                if (
                    invite.code in config["invites"]
                    and not config["invites"][invite.code]["joins"]
                ):
                    del config["invites"][invite.code]
                    await self.update_index(invite.guild.id, config["invites"])


def setup(bot):
    bot.add_cog(BetterInviteManager(bot), override=True)
