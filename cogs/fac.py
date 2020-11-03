"""
Factions Game For Discord.Py
- Supports versions 1.1 - 1.3
- Create factions, group up, complete work tasks to earn money
- Raid other factions while they're not guarded
- Challenge enemys to minigame battles
- Rank up on the faction leaderboard
"""

import json
from os import path
import random
import asyncio
from time import time
from contextlib import suppress
import os

from discord.ext import commands
from discord.ext.commands import CheckFailure
import discord

from utils.colors import purple
from utils import checks


def is_faction_owner():
    async def predicate(ctx):
        self = ctx.cog  # type: Factions
        faction = self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if ctx.author.id != self.factions[guild_id][faction]["owner"]:
            raise CheckFailure("You aren't the owner of this faction")
        return True

    return commands.check(predicate)


def has_faction_permissions():
    async def predicate(ctx):
        self = ctx.cog  # type: Factions
        faction = self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if ctx.author.id == self.factions[guild_id][faction]["owner"]:
            return True
        if ctx.author.id in self.factions[guild_id][faction]["co-owners"]:
            return True
        raise CheckFailure("You don't have permission")

    return commands.check(predicate)


class Factions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = bot.get_fp_for("userdata/test_factions.json")
        self.icon = "https://cdn.discordapp.com/attachments/641032731962114096/641742675808223242/13_Swords-512.png"
        self.banner = ""
        self.boosts = {"extra-income": {}, "land-guard": [], "anti-raid": {}}
        self.game_data = {}
        self.pending = []
        self.factions = {}
        self.cooldowns = {}
        self.counter = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.factions = json.load(f)  # type: dict

    def cog_unload(self):
        with open(self.path + ".tmp", "w+") as f:
            f.write(self.__get_dump())
        os.rename(self.path + ".tmp", self.path)

    def __get_dump(self) -> str:
        return json.dumps({
            faction: data for faction, data in list(self.factions.items()) if data
        })

    async def save_data(self):
        """Save the current variables without blocking the event loop"""

        data = await self.bot.loop.run_in_executor(None, self.__get_dump)
        async with self.bot.open(self.path, "w+", cache=True) as f:
            await f.write(data)
        return None

    def init(self, guild_id: str):
        """Creates guild dictionary if it doesnt exist"""

        if guild_id not in self.factions:
            self.factions[guild_id] = {}

    def get_factions_icon(self, ctx, faction: str) -> str:
        """Returns an icon for the faction"""

        guild_id = str(ctx.guild.id)
        if "icon" in self.factions[guild_id][faction]:
            if self.factions[guild_id][faction]["icon"]:
                return self.factions[guild_id][faction]["icon"]

        owner_id = self.factions[guild_id][faction]["owner"]
        owner = self.bot.get_user(owner_id)
        return owner.avatar_url

    def get_users_faction(self, ctx, user=None):
        """fetch a users faction by context or partial name"""

        if not user:
            user = ctx.author
        if not isinstance(user, discord.Member):
            user = self.bot.utils.get_user(ctx, user)
        if not isinstance(user, discord.Member):
            return None

        guild_id = str(ctx.guild.id)
        if guild_id in self.factions:
            for faction, data in self.factions[guild_id].items():
                if user.id in data["members"]:
                    return faction

        return None

    def get_authors_faction(self, ctx):
        """ fetch a users faction by context or partial name """

        user = ctx.author
        guild_id = str(ctx.guild.id)
        if guild_id in self.factions:
            for faction, data in self.factions[guild_id].items():
                if user.id in data["members"]:
                    return faction
        raise CheckFailure("You're not currently in a faction")

    def get_owned_faction(self, ctx, user=None):
        """ returns a users owned faction if it exists """

        if not user:
            user = ctx.author.mention
        user = self.bot.utils.get_user(ctx, user)
        if not user:
            return
        guild_id = str(ctx.guild.id)
        for faction, data in self.factions[guild_id].items():
            if user.id == data["owner"]:
                return faction
            if user.id in data["co-owners"]:
                return faction
        return None

    async def get_faction_named(self, ctx, name):
        """ gets a faction via partial name """

        guild_id = str(ctx.guild.id)
        factions = [
            f
            for f in self.factions[guild_id].keys()
            if str(f).lower() == str(name).lower()
        ]
        if not factions:
            factions = [
                f
                for f in self.factions[guild_id].keys()
                if str(name).lower() in str(f).lower()
            ]
        if len(factions) > 1:
            choice = await self.bot.utils.get_choice(ctx, factions, user=ctx.author)
            if not choice:
                return
            return choice
        elif factions:
            return factions[0]
        raise commands.CheckFailure("I couldn't find that faction :[")

    def collect_claims(self, guild_id, faction=None) -> dict:
        """Fetches claims for the whole guild or a single faction
        for easy use when needing all the claims"""

        def claims(faction) -> dict:
            """ returns claims & their data """
            fac_claims = {}
            fac = self.factions[guild_id][faction]
            for claim in fac["claims"]:
                channel = self.bot.get_channel(int(claim))
                if not isinstance(channel, discord.TextChannel):
                    self.factions[guild_id]["balance"] += 250
                    self.factions[guild_id][faction]["claims"].remove(claim)
                    continue
                is_guarded = False
                if claim in self.boosts["land-guard"]:
                    is_guarded = True
                fac_claims[int(claim)] = {
                    "faction": faction,
                    "guarded": is_guarded,
                    "position": channel.position,
                }
            return fac_claims

        if faction:
            return claims(faction)
        global_claims = {}
        for faction in self.factions[guild_id].keys():
            fac_claims = claims(faction)  # type: dict
            for claim, data in fac_claims.items():
                global_claims[claim] = data
        return global_claims

    def get_faction_rankings(self, guild_id: str) -> dict:
        def get_value(kv, net=True):
            value = kv[1]["balance"]
            if net:
                for i in range(len(kv[1]["claims"])):
                    value += 500
            return value

        factions = []
        factions_net = []
        allies_bal = []
        allies_net = []

        for faction, data in self.factions[guild_id].items():
            factions_net.append([faction, get_value([faction, data], net=True)])
            factions.append([faction, get_value([faction, data], net=False)])
            if data["allies"] and not any(faction in List for List in allies_net):
                alliance_net = [(faction, get_value([faction, data], net=True))]
                alliance_bal = [(faction, get_value([faction, data], net=False))]
                for ally in data["allies"]:
                    fac, value = get_value(
                        [ally, self.factions[guild_id][ally]], net=True
                    )
                    alliance_net.append([fac, value])
                    fac, value = get_value(
                        [ally, self.factions[guild_id][ally]], net=False
                    )
                    alliance_bal.append([fac, value])
                allies_net.append(alliance_net)
                allies_bal.append(alliance_bal)

        factions_net = sorted(factions, key=lambda kv: kv[1], reverse=True)
        factions = sorted(factions, key=lambda kv: kv[1], reverse=True)
        allies_net = sorted(
            allies_net, key=lambda kv: sum(kv[1] for kv in allies_net), reverse=True
        )
        allies_bal = sorted(
            allies_bal, key=lambda kv: sum(kv[1] for kv in allies_bal), reverse=True
        )

        return {
            "net": factions_net,
            "bal": factions,
            "ally_net": allies_net,
            "ally_bal": allies_bal,
        }

    def update_income_board(self, guild_id, faction, **kwargs) -> None:
        for key, value in kwargs.items():
            self.factions[guild_id][faction]["income"][key] += value

    async def wait_for_msg(self, ctx, *user):
        def predicate(m):
            if "everyone" in user:
                return m.channel.id == ctx.channel.id
            else:
                return m.author.id in user and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for("message", check=predicate, timeout=60)
        except asyncio.TimeoutError:
            return None
        else:
            return msg

    @commands.command(name="convert-factions")
    @commands.check(checks.luck)
    async def convert_factions(self, ctx):
        new_dict = {}
        with open("./data/userdata/factions.json", "r") as f:
            dat = json.load(f)  # type: dict
        for guild_id, factions in dat["factions"].items():
            new_dict[guild_id] = {}
            for faction, metadata in factions.items():
                if faction == "category":
                    continue
                claims = []
                if guild_id in dat["land_claims"]:
                    if faction in dat["land_claims"][guild_id]:
                        claims = [
                            int(k) for k in dat["land_claims"][guild_id][faction].keys()
                        ]
                new_dict[faction] = {
                    "owner": metadata["owner"],
                    "co-owners": [],
                    "members": metadata["members"],
                    "balance": metadata["balance"],
                    "claims": claims,
                    "public": True,
                    "allies": [],
                    "limit": 15,
                    "income": {},
                    "bio": None,
                }
                if "limit" in metadata:
                    new_dict["limit"] = metadata["limit"]
                if "access" in metadata:
                    new_dict["public"] = (
                        True if metadata["access"] == "public" else False
                    )
                if "co-owners" in metadata:
                    new_dict["co-owners"] = metadata["co-owners"]
                if "bio" in metadata:
                    new_dict["bio"] = metadata["bio"] if metadata["bio"] else None
                if "icon" in metadata:
                    new_dict["icon"] = metadata["icon"]
                if "banner" in metadata:
                    new_dict["banner"] = metadata["banner"]
        await ctx.send("Conversion Would Succeed")

    @commands.group(name="fac")
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def factions(self, ctx):
        """ Information about the module """
        if not ctx.invoked_subcommand:
            p = self.bot.utils.get_prefix(ctx)  # type: str
            if len(ctx.message.content.split()) > 1:
                return await ctx.send(f"Unknown command\nTry using `{p}factions help`")
            e = discord.Embed(color=purple())
            e.set_author(name="Discord Factions", icon_url=self.icon)
            e.description = (
                "Create factions, group up, complete work tasks to earn "
                "your faction money, raid other factions while they're "
                "not guarded, challenge enemys to minigame battles, and "
                "rank up on the faction leaderboard"
            )
            await ctx.send(embed=e)

    @factions.command(name="help", aliases=["commands"])
    async def _help(self, ctx):
        """ Command usage and descriptions """
        e = discord.Embed(color=purple())
        e.set_author(name="Usage", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        p = self.bot.utils.get_prefix(ctx)  # type: str
        e.add_field(
            name="◈ Core ◈",
            value=f"{p}factions create [name]"
                  f"\n{p}factions rename [name]"
                  f"\n{p}factions disband"
                  f"\n{p}factions join [faction]"
                  f"\n{p}factions invite @user"
                  f"\n{p}factions promote @user"
                  f"\n{p}factions demote @user"
                  f"\n{p}factions kick @user"
                  f"\n{p}factions leave",
            inline=False,
        )
        e.add_field(
            name="◈ Utils ◈",
            value=f"{p}faction privacy"  # incomplete
                  f"\n{p}factions setbio [your new bio]"  # incomplete
                  f"\n{p}factions seticon [file | url]"  # incomplete
                  f"\n{p}factions setbanner [file | url]"  # incomplete
                  f"\n{p}factions togglenotifs",  # incomplete
            inline=False,
        )
        e.add_field(
            name="◈ Economy ◈",
            value=f"{p}faction work"
                  f"\n{p}factions balance"  # incomplete
                  f"\n{p}factions pay [faction] [amount]"  # incomplete
                  f"\n{p}factions raid [faction]"  # incomplete
                  f"\n{p}factions battle [faction]"  # incomplete
                  f"\n{p}factions annex [faction]"  # incomplete
                  f"\n{p}factions claim #channel"  # incomplete
                  f"\n{p}factions unclaim #channel"  # incomplete
                  f"\n{p}factions claims"
                  f"\n{p}factions boosts"  # incomplete
                  f"\n{p}factions info"
                  f"\n{p}factions members [faction]"
                  f"\n{p}factions top",  # incomplete
            inline=False,
        )
        await ctx.send(embed=e)

    @factions.command(name="create")
    async def create(self, ctx, *, name):
        """ Creates a faction """
        guild_id = str(ctx.guild.id)
        faction = self.get_users_faction(ctx)
        if faction:
            return await ctx.send(
                "You must leave your current faction to create a new one"
            )
        if (
            ctx.message.raw_mentions
            or ctx.message.raw_role_mentions
            or "@" in name
            or "#" in name
        ):
            return await ctx.send("biTcH nO")
        self.init(guild_id)  # make sure the key is setup properly
        if str(name).lower() in [
            str(f).lower() for f in self.factions[guild_id].keys()
        ]:
            return await ctx.send("That name is already taken")
        self.factions[guild_id][name] = {
            "owner": ctx.author.id,
            "co-owners": [],
            "members": [ctx.author.id],
            "balance": 500,
            "limit": 15,
            "public": True,
            "allies": [],
            "claims": [],
            "bio": None,
            "income": {},
        }
        await ctx.send("Created your faction")
        await self.save_data()

    @factions.command(name="disband")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @is_faction_owner()
    async def disband(self, ctx):
        """ Deletes the owned faction """
        guild_id = str(ctx.guild.id)
        faction = self.get_owned_faction(ctx)
        await ctx.send(
            "Are you sure you want to delete your faction?\nReply with 'yes' or 'no'"
        )
        async with self.bot.require("message", ctx) as msg:
            if "yes" in str(msg.content).lower():
                for fac, data in self.factions[guild_id].items():
                    if faction in data["allies"]:
                        self.factions[guild_id][fac]["allies"].remove(faction)
                del self.factions[guild_id][faction]
                await ctx.send("Ok.. deleted your faction")
                await self.save_data()
            else:
                await ctx.send("Ok, I won't delet")

    @factions.command(name="join")
    async def join(self, ctx, *, faction):
        """ Joins a public faction via name """
        is_in_faction = self.get_users_faction(ctx)  # type: str
        if is_in_faction:
            return await ctx.send("You're already in a faction")
        faction = await self.get_faction_named(ctx, faction)
        guild_id = str(ctx.guild.id)
        if not self.factions[guild_id][faction]["public"]:
            return await ctx.send("That factions not public :[")
        self.factions[guild_id][faction]["members"].append(ctx.author.id)
        e = discord.Embed(color=purple())
        e.set_author(name=faction, icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=self.get_factions_icon(ctx, faction))
        e.description = (
            f"{ctx.author.display_name} joined\nMember Count: "
            f"[`{len(self.factions[guild_id][faction]['members'])}`]"
        )
        await ctx.send(embed=e)
        await self.save_data()

    @factions.command(name="invite")
    async def invite(self, ctx, user: discord.Member):
        """ Invites a user to a private faction """

        def pred(msg):
            return (
                msg.channel.id == ctx.channel.id
                and msg.author.id == user.id
                and ("yes" in msg.content and "no" in msg.content)
            )

        faction = self.get_owned_faction(ctx)
        if not faction:
            return await ctx.send(
                "You need to have owner level permissions to use this cmd"
            )
        users_in_faction = self.get_users_faction(ctx, user)
        if users_in_faction:
            return await ctx.send("That users already in a faction :[")
        if user.id in self.pending:
            return await ctx.send("That user already has a pending invite")
        self.pending.append(user.id)

        request = await ctx.send(
            f"{user.mention}, {ctx.author.display_name} invited you to join {faction}\n"
            f"Reply with 'yes' to join, or 'no' to reject",
            allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
        )
        try:
            msg = await self.bot.wait_for("message", check=pred, timeout=60)
        except asyncio.TimeoutError:
            await request.edit(content=f"~~{request.content}~~\n\nRequest Expired")
            await ctx.message.delete()
        else:
            if "yes" in msg.content.lower():
                self.factions[str(ctx.guild.id)][faction]["members"].append(
                    ctx.author.id
                )
                await ctx.send(f"{user.display_name} joined {faction}")
                await self.save_data()
            else:
                await ctx.send("Alrighty then :[")
        self.pending.remove(user.id)

    @factions.command(name="leave")
    async def leave(self, ctx):
        """ Leaves a faction """
        faction = self.get_users_faction(ctx)
        if not faction:
            return await ctx.send("You're not currently in a faction")
        if self.get_owned_faction(ctx):
            return await ctx.send(
                "You cannot leave a faction you own, you must "
                "transfer ownership, or disband it"
            )
        guild_id = str(ctx.guild.id)
        self.factions[guild_id][faction]["members"].remove(ctx.author.id)
        if ctx.author.id in self.factions[guild_id]["co-owners"]:
            self.factions[guild_id]["co-owners"].remove(ctx.author.id)
        await ctx.send("👍")
        await self.save_data()

    @factions.command(name="kick")
    async def kick(self, ctx, *, user):
        """ Kicks a user from the faction """
        user = self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        faction = self.get_owned_faction(ctx)
        if not faction:
            return await ctx.send("You need to at least be co-owner to use this cmd")
        users_faction = self.get_users_faction(ctx, user)
        if not users_faction:
            return await ctx.send("That users not in a faction")
        if users_faction != faction:
            return await ctx.send("That user isn't in your faction :/")
        guild_id = str(ctx.guild.id)
        if user.id == self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You cant demote the owner ._.")
        if user.id in self.factions[guild_id][faction]["co-owners"] and (
            ctx.author.id != self.factions[guild_id][faction]["owner"]
        ):
            return await ctx.send("Only the owner can demote a co-owner!")
        self.factions[guild_id][faction]["members"].remove(user.id)
        if user.id in self.factions[guild_id]["co-owners"]:
            self.factions[guild_id]["co-owners"].remove(user.id)
        await ctx.send(f"Kicked {user.mention} from {faction}")
        await self.save_data()

    @factions.command(name="promote")
    async def promote(self, ctx, *, user):
        """ Promotes a faction member to Co-Owner"""
        user = await self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        guild_id = str(ctx.guild.id)
        faction = self.get_owned_faction(ctx)
        if not faction or ctx.author.id != self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        if user.id in self.factions[guild_id][faction]["co-owners"]:
            return await ctx.send("That users already a co-owner")
        self.factions[guild_id][faction]["co-owners"].append(user.id)
        await ctx.send(f"Promoted {user.mention} to co-owner")
        await self.save_data()

    @factions.command(name="demote")
    async def demote(self, ctx, *, user):
        """ Demotes a faction member from Co-Owner """
        user = await self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        faction = self.get_owned_faction(ctx)
        if not faction:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        guild_id = str(ctx.guild.id)
        if ctx.author.id != self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        if user.id not in self.factions[guild_id][faction]["co-owners"]:
            return await ctx.send("That users not co-owner")
        self.factions[guild_id][faction]["co-owners"].remove(user.id)
        await ctx.send(f"Demoted {user.mention} from co-owner")

    @factions.command(name="annex", enabled=False)
    @is_faction_owner()
    async def annex(self, ctx, *, faction):
        """ Merges a faction with another """
        authors_faction = self.get_owned_faction(ctx, user=ctx.author)
        other_faction = await self.get_faction_named(ctx, faction)
        guild_id = str(ctx.guild.id)
        dat = self.factions[guild_id][other_faction]
        await ctx.send(
            f"<@{dat['owner']} {ctx.author} would like to merge factions with them as the owner. "
            f"Reply with `.confirm annex` if you consent to giving up your faction",
            allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
        )

        def predicate(m):
            return m.channel.id == ctx.channel.id and m.author.id == dat["owner"]

        async with self.bot.require("message", predicate) as msg:
            if ".confirm annex" not in str(msg.content).lower():
                return await ctx.send("Alright, merge has been rejected")

        for member_id in dat["members"]:
            if member_id not in self.factions[guild_id][authors_faction]["members"]:
                self.factions[guild_id][authors_faction]["members"].append(member_id)
        for member_id in dat["co-owners"]:
            if member_id not in self.factions[guild_id][authors_faction]["members"]:
                self.factions[guild_id][authors_faction]["members"].append(member_id)
        if dat["owner"] not in self.factions[guild_id][authors_faction]["members"]:
            self.factions[guild_id][authors_faction]["members"].append(dat["owner"])
        with suppress(ValueError):
            del self.factions[guild_id][other_faction]

        await ctx.send(f"Successfully annexed {other_faction}")

    @factions.command(name="rename")
    async def rename(self, ctx, *, name):
        """ Renames their faction """
        faction = self.get_owned_faction(ctx)
        if not faction:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        guild_id = str(ctx.guild.id)
        if ctx.author.id != self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        if str(name).lower() in [
            str(fac).lower() for fac in self.factions[guild_id].keys()
        ]:
            return await ctx.send("That names already taken")
        if (
            ctx.message.raw_mentions
            or ctx.message.raw_role_mentions
            or "@" in name
            or "#" in name
        ):
            return await ctx.send("biTcH nO")
        for fac, data in self.factions[guild_id].items():
            if faction in data["allies"]:
                self.factions[guild_id][fac]["allies"].remove(faction)
                self.factions[guild_id][fac]["allies"].append(name)
        self.factions[guild_id][name] = self.factions[guild_id].pop(faction)
        await ctx.send(f"Changed your factions name from {faction} to {name}")
        await self.save_data()

    @factions.command(name="info")
    async def info(self, ctx, *, faction=None):
        """ Bulk information on a faction """
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = self.get_authors_faction(ctx)

        guild_id = str(ctx.guild.id)
        dat = self.factions[guild_id][faction]  # type: dict
        owner = self.bot.get_user(dat["owner"])
        icon_url = self.get_factions_icon(ctx, faction)
        rankings = self.get_faction_rankings(guild_id)["net"]  # type: list
        rank = 1
        for fac, value in rankings:
            if fac == faction:
                break
            rank += 1

        e = discord.Embed(color=purple())
        e.set_author(name=faction, icon_url=owner.avatar_url)
        e.set_thumbnail(url=icon_url)
        e.description = (
            f"__**Owner:**__ `{owner}`"
            f"\n__**Members:**__ [`{len(dat['members'])}`] "
            f"__**Public:**__ [`{dat['public']}`]"
            f"\n__**Balance:**__ [`${dat['balance']}`]\n"
        )
        if dat["bio"]:
            e.description += f"__**Bio:**__ [`{dat['bio']}`]"
        if "banner" in dat:
            if dat["banner"]:
                e.set_image(url=dat["banner"])
        e.set_footer(text=f"Leaderboard Rank: #{rank}")
        await ctx.send(embed=e)

    @factions.command(name="members")
    async def members(self, ctx, *, faction=None):
        """ lists a factions members """
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = self.get_users_faction(ctx)

        guild_id = str(ctx.guild.id)
        owner_id = self.factions[guild_id][faction]["owner"]
        owner = self.bot.get_user(owner_id)
        users = []
        co_owners = []
        for user_id in self.factions[guild_id][faction]["members"]:  # type: int
            user = self.bot.get_user(user_id)
            if not isinstance(user, discord.User):
                self.factions[guild_id][faction].remove(user_id)
                await self.save_data()
                continue

            income = 0
            if user_id in self.factions[guild_id][faction]["income"]:
                income = self.factions[guild_id][faction][income][user_id]
            if user_id in self.factions[guild_id][faction]["co-owners"]:
                co_owners.append([user, income])
            else:
                users.append([user, income])

        e = discord.Embed(color=purple())
        e.set_author(name=f"{faction}'s members", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.get_factions_icon(ctx, faction))
        e.description = ""
        for user, income in users:
            if user.id in self.factions[guild_id][faction]["co-owners"]:
                e.description += f"Co: "
            e.description += f"{user.mention} - ${income}\n"
        await ctx.send(embed=e)

    @factions.command(name="claim")
    @has_faction_permissions()
    async def claim(self, ctx, channel: discord.TextChannel = None):
        """Claim a channel"""
        if not channel:
            channel = ctx.channel
        faction = self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        claims = self.collect_claims(guild_id)  # type: dict
        cost = 500
        if channel.id in claims:
            if claims[channel.id]["guarded"]:
                return await ctx.send("That claim is currently guarded")
            cost += 250
        if cost > self.factions[guild_id][faction]["balance"]:
            needed = cost - self.factions[guild_id][faction]['balance']
            return await ctx.send(f"Your faction doesn't have enough money to claim "
                                  f"this channel. You need ${needed} more")
        await ctx.send(f"Claiming that channel will cost you ${cost}, "
                       f"reply with `.confirm` to claim it")
        async with self.bot.require("message", ctx) as msg:
            if ".confirm" not in str(msg.content).lower():
                return await ctx.send("Alright.. maybe next time")
        if channel.id in claims:
            fac = claims[channel.id]["faction"]
            self.factions[guild_id][fac]["claims"].remove(channel.id)
        self.factions[guild_id][faction]["claims"].append(channel.id)
        await ctx.send(f"Claimed {channel.mention} for {faction}")
        await self.save_data()

    @factions.command(name="claims")
    async def claims(self, ctx, *, faction = None):
        """ Returns a factions sorted claims """
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        e = discord.Embed(color=purple())
        e.set_author(
            name=f"{faction}'s claims", icon_url=self.get_factions_icon(ctx, faction)
        )
        claims = self.collect_claims(guild_id, faction)
        claims = {
            self.bot.get_channel(chnl_id): data for chnl_id, data in claims.items()
        }
        for channel, data in sorted(
            claims.items(), reverse=True, key=lambda kv: kv[1]["position"]
        ):
            e.description = (
                f"• {channel.mention} {'- guarded' if data['guarded'] else ''}\n"
            )
        await ctx.send(embed=e)

    @factions.command(name="battle")
    async def battle(self, ctx, *args):
        """ Battle other factions in games like scrabble """
        await ctx.send("This command isn't developed yet")

    @factions.command(name="raid")
    @has_faction_permissions()
    async def raid(self, ctx, *, faction):
        """ Starts a raid against another faction """
        attacker = self.get_authors_faction(ctx)
        defender = await self.get_faction_named(ctx, faction)
        if not attacker:
            return await ctx.send("You need to be in a faction to use this cmd")
        if not defender:
            return await ctx.send("Faction not found")

        guild_id = str(ctx.guild.id)
        attacker_bal = self.factions[guild_id][attacker]["balance"]
        defender_bal = self.factions[guild_id][defender]["balance"]

        if attacker_bal > defender_bal:
            highest_fac = attacker
            lowest_fac = defender
            lowest_bal = defender_bal
        else:
            highest_fac = defender
            lowest_fac = attacker
            lowest_bal = attacker_bal
        if lowest_bal <= 250:
            return await ctx.send("You're too weak to raid. Try again when you at least have $250")

        if defender_bal > attacker_bal:
            await ctx.send("The odds are against us. Are you sure you wish to attempt a raid?")
            async with self.bot.require("message", ctx) as msg:
                if "ye" not in str(msg.content).lower():
                    return await ctx.send("Wise choice")


        max_range = round(lowest_bal / 4)
        loot = random.randint(50, max_range)
        if loot > 500:
            loot = 500
        if random.randint(1, 100) > 60:
            winner = lowest_fac
            loser = highest_fac
        else:
            winner = highest_fac
            loser = lowest_fac
        self.factions[guild_id][winner] += loot
        self.factions[guild_id][loser] -= loot

        e = discord.Embed(color=purple())
        if winner == attacker:
            e.description = f"You raided {defender} and gained ${loot}. GG"
        else:
            e.description = f"You attempted to raid {defender} and lost ${loot}"
        await ctx.send(embed=e)
        await self.save_data()

    @factions.command(name="work")
    async def work(self, ctx):
        """ Get money for your faction """
        guild_id = str(ctx.guild.id)
        faction = self.get_authors_faction(ctx)

        if guild_id not in self.cooldowns:
            self.cooldowns[guild_id] = {}
        if ctx.author.id in self.cooldowns[guild_id]:
            remainder = round(self.cooldowns[guild_id][ctx.author.id] - time())
            return await ctx.send(f"You're on cooldown! You have {remainder}s left")
        self.cooldowns[guild_id][ctx.author.id] = time() + 60

        e = discord.Embed(color=purple())
        pay = random.randint(15, 25)
        e.description = f"You earned {faction} ${pay}"
        if faction in self.boosts["extra-income"]:
            e.set_footer(
                text="With Bonus: $5", icon_url=self.get_factions_icon(ctx, faction)
            )
            pay += 5

        self.factions[guild_id][faction]["balance"] += pay
        if ctx.author.id in self.factions[guild_id][faction]["income"]:
            self.factions[guild_id][faction]["income"][ctx.author.id] += pay
        else:
            self.factions[guild_id][faction]["income"][ctx.author.id] = pay

        await ctx.send(embed=e)
        await self.save_data()

        await asyncio.sleep(self.cooldowns[guild_id][ctx.author.id] - time())
        del self.cooldowns[guild_id][ctx.author.id]

    @factions.command(name="balance", aliases=["bal"], enabled=False)
    async def balance(self, ctx, *, faction=None):
        """ Sends a factions balance """
        guild_id = str(ctx.guild.id)
        if guild_id not in self.factions:
            return await ctx.send("This server has no factions")
        if not faction:
            faction = self.get_users_faction(ctx, user=ctx.author)
        else:
            faction = self.get_faction_named(ctx, name=faction)
        if not faction:
            return await ctx.send(
                "You need to either be in a faction or specify a faction"
            )
        guild_id = str(ctx.guild.id)
        e = discord.Embed(color=purple())
        e.set_author(name=str(faction), icon_url=self.get_factions_icon(ctx, str(faction)))
        e.description = f"${self.factions[guild_id][faction]['balance']}"
        await ctx.send(embed=e)

    @factions.command(name="pay", enabled=False)
    @commands.cooldown(2, 240, commands.BucketType.user)
    @is_faction_owner()
    async def pay(self, ctx, faction, amount: int):
        """ Pays a faction from the author factions balance """
        authors_fac = self.get_authors_faction(ctx)
        target_fac = self.get_faction_named(ctx, faction)
        guild_id = str(ctx.guild.id)
        bal = self.factions[guild_id][authors_fac]["balance"]
        if amount > bal / 5:
            return await ctx.send(
                f"You can't pay another faction more than 1/5th your balance, (${round(bal / 5)})."
            )
        self.factions[guild_id][target_fac]["balance"] += amount
        self.factions[guild_id][authors_fac]["balance"] -= amount
        return await ctx.send(f"Paid {target_fac} ${amount}")

    @factions.command(name="top", aliases=["leaderboard", "lb"])
    @commands.bot_has_permissions(manage_messages=True)
    async def top(self, ctx):
        def predicate(r, u) -> bool:
            m = r.message  # type: discord.Message
            return m.id == msg.id and str(r.emoji) in emojis and not u.bot

        async def add_emojis_task():
            for emoji in emojis:
                await msg.add_reaction(emoji)

        guild_id = str(ctx.guild.id)
        dat = self.get_faction_rankings(guild_id)
        e = discord.Embed(description="Collecting Leaderboard Data..")
        msg = await ctx.send(embed=e)
        emojis = ["💰", "⚔"]
        self.bot.loop.create_task(add_emojis_task())

        net_leaderboard = discord.Embed(color=purple())
        net_leaderboard.set_author(name="Net Worth Leaderboard")
        net_leaderboard.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png"
        )
        net_leaderboard.description = ""
        for i, (faction, value) in enumerate(dat["net"][:9]):
            net_leaderboard.description += f"#{i}. {faction} - ${value}"

        bal_leaderboard = discord.Embed(color=purple())
        bal_leaderboard.set_author(name="Balance Leaderboard")
        bal_leaderboard.set_thumbnail(url=ctx.guild.icon_url)
        bal_leaderboard.description = ""
        for i, (faction, balance) in enumerate(dat["bal"][:9]):
            bal_leaderboard.description += f"#{i}. {faction} - ${balance}"

        alliance_net_leaderboard = discord.Embed(color=purple())
        alliance_net_leaderboard.set_author(name="Alliance Net Leaderboard")
        alliance_net_leaderboard.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/501871950260469790/505198377412067328/20181025_215740.png"
        )
        alliance_net_leaderboard.description = ""
        for alliance in dat["ally_net"][:9]:
            factions = ", ".join(f[0] for f in alliance)
            value = sum(f[1] for f in alliance)
            alliance_net_leaderboard.description += f"\n\n${value} from {factions}"

        alliance_bal_leaderboard = discord.Embed(color=purple())
        alliance_bal_leaderboard.set_author(name="Alliance Bal Leaderboard")
        alliance_bal_leaderboard.set_thumbnail(url=ctx.guild.icon_url)
        alliance_bal_leaderboard.description = ""
        for alliance in dat["ally_bal"][:9]:
            factions = ", ".join(f[0] for f in alliance)
            value = sum(f[1] for f in alliance)
            alliance_bal_leaderboard.description += f"\n\n${value} from {factions}"

        leaderboards = {
            True: {True: net_leaderboard, False: alliance_net_leaderboard},
            False: {True: bal_leaderboard, False: alliance_bal_leaderboard},
        }
        net = True
        normal_lb = True
        while True:
            await msg.edit(embed=leaderboards[net][normal_lb])
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=predicate, timeout=60
                )
            except asyncio.TimeoutError:
                return await msg.clear_reactions()
            if str(reaction.emoji) == "💰":
                net = False if net else True
            elif str(reaction.emoji) == "⚔":
                normal_lb = False if normal_lb else True
            await msg.remove_reaction(reaction, user)

    @factions.command(name="ally")
    @is_faction_owner()
    async def ally(self, ctx, *, target_faction):
        ally_name = self.get_faction_named(ctx, name=target_faction)
        faction_name = self.get_owned_faction(ctx, user=ctx.author)

        guild_id = str(ctx.guild.id)
        if faction_name in self.factions[guild_id][ally_name]["allies"]:
            return await ctx.send(f"You're already allied with `{ally_name}`")
        if len(self.factions[guild_id][faction_name]["allies"]) == 3:
            return await ctx.send(f"At the moment, you can't exceed 3 alliances")
        if len(self.factions[guild_id][ally_name]["allies"]) == 3:
            return await ctx.send(
                "That faction has already reached its limit of alliances"
            )

        def predicate(m):
            return m.channel.id == ctx.channel.id and ".accept" in str(m.content)

        await ctx.send(
            "Someone with ownership level permissions in {ally_name} "
            "reply with `.accept` to agree to the alliance"
        )
        while True:
            async with self.bot.require("message", predicate) as msg:
                if self.get_owned_faction(ctx, user=msg.author) == ally_name:
                    self.factions[guild_id][faction_name]["allies"].append(ally_name)
                    self.factions[guild_id][ally_name]["allies"].append(faction_name)
                    await ctx.send(
                        f"Successfully created an alliance between `{faction_name}` and `{ally_name}`"
                    )
                    return await self.save_data()

    @commands.Cog.listener()
    async def on_message(self, msg):
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.factions:
                claims = self.collect_claims(guild_id)  # type: dict
                channel_id = str(msg.channel.id)
                if channel_id in claims:
                    faction = claims[channel_id]["faction"]
                    pay = random.randint(1, 5)
                    self.factions[guild_id][faction]["balance"] += pay
                    self.update_income_board(guild_id, faction, land_claims=pay)
                    ally_pay = round(pay / 2) if pay > 1 else 0
                    for ally in self.factions[guild_id][faction]["allies"]:
                        self.factions[guild_id][ally]["balance"] += ally_pay
                        self.update_income_board(guild_id, ally, alliances=ally_pay)


def setup(bot):
    bot.add_cog(Factions(bot))
