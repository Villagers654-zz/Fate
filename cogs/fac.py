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
from discord.errors import Forbidden
import discord

from utils.colors import purple, pink
from utils import checks


def is_faction_owner():
    async def predicate(ctx):
        self = ctx.cog
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if ctx.author.id != self.factions[guild_id][faction]["owner"]:
            raise CheckFailure("You aren't the owner of this faction")
        return True

    return commands.check(predicate)


def has_faction_permissions():
    async def predicate(ctx):
        self = ctx.cog
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if ctx.author.id == self.factions[guild_id][faction]["owner"]:
            return True
        if ctx.author.id in self.factions[guild_id][faction]["co-owners"]:
            return True
        raise CheckFailure("You don't have permission")

    return commands.check(predicate)


class FactionsRewrite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = bot.get_fp_for("userdata/test_factions.json")
        self.icon = "https://cdn.discordapp.com/attachments/641032731962114096/641742675808223242/13_Swords-512.png"
        self.banner = ""
        self.boosts = {"extra-income": {}, "land-guard": {}, "anti-raid": {}}
        self.game_data = {}
        self.pending = []
        self.factions = {}
        self.notifs = []
        self.cooldowns = {}
        self.blocked = []
        self.work_counter = {}
        self.counter = {}
        self.claim_counter = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                dat = json.load(f)  # type: dict
                if "main" in dat:
                    self.factions = dat["main"]  # type: dict
                    for guild_id, factions in list(self.factions.items()):
                        for faction, data in list(factions.items()):
                            self.factions[guild_id][faction]["members"] = list(set(data["members"]))
                if "boosts" in dat:
                    self.boosts = dat["boosts"]  # type: dict
                    for key, values in list(self.boosts.items()):
                        for guild_id, data in list(values.items()):
                            for faction, end_time in list(data.items()):
                                if time() > end_time:
                                    del self.boosts[key][guild_id][faction]
                if "notifs" in dat:
                    self.notifs = dat["notifs"]  # type: list

    @property
    def extra_income(self):
        return self.boosts["extra-income"]

    @property
    def land_guard(self):
        return self.boosts["land-guard"]

    @property
    def anti_raid(self):
        return self.boosts["anti-raid"]

    def cog_unload(self):
        with open(self.path + ".tmp", "w+") as f:
            f.write(self.__get_dump())
        # os.rename is atomic and won't be interrupted
        os.rename(self.path + ".tmp", self.path)

    def __get_dump(self) -> str:
        return json.dumps({
            "main": {
                faction: data for faction, data in list(self.factions.items()) if data
            },
            "boosts": self.boosts,
            "notifs": self.notifs
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
        if self.factions[guild_id][faction]["icon"]:
            return self.factions[guild_id][faction]["icon"]

        owner_id = self.factions[guild_id][faction]["owner"]
        owner = self.bot.get_user(owner_id)
        return owner.avatar_url

    async def get_users_faction(self, ctx, user=None):
        """fetch a users faction by context or partial name"""

        if not user:
            user = ctx.author
        if not isinstance(user, (discord.User, discord.Member)):
            user = self.bot.utils.get_user(ctx, user)
        if not isinstance(user, (discord.User, discord.Member)):
            return None

        guild_id = str(ctx.guild.id)
        if guild_id in self.factions:
            for faction, data in self.factions[guild_id].items():
                await asyncio.sleep(0)
                if user.id in data["members"]:
                    return faction

        return None

    async def get_authors_faction(self, ctx):
        """ fetch a users faction by context or partial name """

        user = ctx.author
        guild_id = str(ctx.guild.id)
        if guild_id in self.factions:
            for faction, data in list(self.factions[guild_id].items()):
                await asyncio.sleep(0)
                if user.id in data["members"]:
                    return faction
        raise CheckFailure("You're not currently in a faction")

    async def get_owned_faction(self, ctx, user=None):
        """ returns a users owned faction if it exists """

        if not user:
            user = ctx.author
        elif not isinstance(user, (discord.User, discord.Member)):
            user = self.bot.utils.get_user(ctx, user)
        if not user:
            return None
        guild_id = str(ctx.guild.id)
        if guild_id not in self.factions:
            raise CheckFailure("You're not currently in a faction")
        for faction, data in list(self.factions[guild_id].items()):
            await asyncio.sleep(0)
            if user.id == data["owner"]:
                return faction
            if user.id in data["co-owners"]:
                return faction
        return None

    async def get_faction_named(self, ctx, name):
        """ gets a faction via partial name """

        guild_id = str(ctx.guild.id)
        if guild_id not in self.factions:
            raise CheckFailure("This server has no factions")
        factions = [
            f
            for f in list(self.factions[guild_id].keys())
            if str(f).lower() == str(name).lower()
        ]
        if not factions:
            factions = [
                f
                for f in list(self.factions[guild_id].keys())
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

    async def collect_claims(self, guild_id, faction=None) -> dict:
        """Fetches claims for the whole guild or a single faction
        for easy use when needing all the claims"""

        async def claims(faction) -> dict:
            """ returns claims & their data """
            fac_claims = {}
            if faction not in self.factions[guild_id]:
                return fac_claims
            fac = self.factions[guild_id][faction]
            for claim in fac["claims"]:
                await asyncio.sleep(0)
                channel = self.bot.get_channel(int(claim))
                if not isinstance(channel, discord.TextChannel):
                    self.factions[guild_id][faction]["balance"] += 250
                    self.factions[guild_id][faction]["claims"].remove(claim)
                    continue

                is_guarded = False
                if guild_id in self.land_guard and faction in self.land_guard[guild_id]:
                    if time() > self.land_guard[guild_id][faction]:
                        del self.land_guard[guild_id][faction]
                    else:
                        for f in list(self.land_guard[guild_id].keys()):
                            await asyncio.sleep(0)
                            if f not in self.factions[guild_id]:
                                del self.land_guard[guild_id][f]
                                continue
                            if int(claim) in self.factions[guild_id][f]["claims"]:
                                is_guarded = True
                                break

                fac_claims[int(claim)] = {
                    "faction": faction,
                    "guarded": is_guarded,
                    "position": channel.position,
                }

            return fac_claims

        if faction:
            return await claims(faction)
        global_claims = {}
        for faction in list(self.factions[guild_id].keys()):
            fac_claims = await claims(faction)  # type: dict
            for claim, data in fac_claims.items():
                global_claims[claim] = data
        return global_claims

    async def get_faction_rankings(self, guild_id: str) -> dict:
        def get_value(kv, net=True):
            value = kv[1]["balance"]
            if net:
                for _claim in kv[1]["claims"]:
                    value += 500
            return value

        factions = []
        factions_net = []
        allies_bal = []
        allies_net = []

        for faction, data in self.factions[guild_id].items():
            await asyncio.sleep(0)
            factions_net.append([faction, get_value([faction, data], net=True)])
            factions.append([faction, get_value([faction, data], net=False)])
            if data["allies"] and not any(any(faction in _ for _ in List) for List in allies_net):
                alliance_net = [(faction, get_value([faction, data], net=True))]
                alliance_bal = [(faction, get_value([faction, data], net=False))]
                for ally in data["allies"]:
                    await asyncio.sleep(0)
                    value = get_value(
                        [ally, self.factions[guild_id][ally]], net=True
                    )
                    alliance_net.append([ally, value])
                    value = get_value(
                        [ally, self.factions[guild_id][ally]], net=False
                    )
                    alliance_bal.append([ally, value])
                allies_net.append(alliance_net)
                allies_bal.append(alliance_bal)

        factions_net = sorted(factions_net, key=lambda kv: kv[1], reverse=True)
        factions = sorted(factions, key=lambda kv: kv[1], reverse=True)
        allies_net = sorted(
            allies_net, key=lambda kv: sum(kv[0][1] for kv in allies_net), reverse=True
        )
        allies_bal = sorted(
            allies_bal, key=lambda kv: sum(kv[0][1] for kv in allies_bal), reverse=True
        )

        return {
            "net": factions_net,
            "bal": factions,
            "ally_net": allies_net,
            "ally_bal": allies_bal,
        }

    async def update_income_board(self, guild_id, faction, **kwargs) -> None:
        for key, value in kwargs.items():
            if key not in self.factions[guild_id][faction]["income"]:
                self.factions[guild_id][faction]["income"][key] = 0
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
        await ctx.send(f"Converting {len(dat['factions'].items())}")
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
                new_dict[guild_id][faction] = {
                    "owner": metadata["owner"],
                    "co-owners": metadata["co-owners"],
                    "members": metadata["members"],
                    "balance": metadata["balance"],
                    "claims": claims,
                    "public": True,
                    "allies": [],
                    "slots": 15,
                    "income": {},
                    "bio": None,
                    "icon": None,
                    "banner": None
                }
                if "limit" in metadata:
                    new_dict[guild_id][faction]["slots"] = metadata["limit"]
                if "access" in metadata:
                    new_dict[guild_id][faction]["public"] = (
                        True if metadata["access"] == "public" else False
                    )
                if "co-owners" in metadata:
                    new_dict[guild_id][faction]["co-owners"] = metadata["co-owners"]
                if "bio" in metadata:
                    new_dict[guild_id][faction]["bio"] = metadata["bio"] if metadata["bio"] else None
                if "icon" in metadata:
                    new_dict[guild_id][faction]["icon"] = metadata["icon"]
                if "banner" in metadata:
                    new_dict[guild_id][faction]["banner"] = metadata["banner"]
        self.factions = new_dict
        await ctx.send(f"Converted {len(new_dict)} factions")

    @commands.group(name="factions", aliases=["f"])
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
                "not guarded, challenge enemies to minigame battles, and "
                "rank up on the faction leaderboard."
            )
            e.set_footer(text=f"For help use {p}f help")
            await ctx.send(embed=e)

    @factions.command(name="help", aliases=["commands"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    @commands.cooldown(2, 120, commands.BucketType.channel)
    async def _help(self, ctx):
        """ Command usage and descriptions """
        e = discord.Embed(color=purple())
        e.set_author(name="Usage", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=ctx.guild.icon_url)
        p = self.bot.utils.get_prefix(ctx)  # type: str
        e.add_field(
            name="◈ Core ◈",
            value=f"  {p}f create [name]"
                  f"\n{p}f rename [name]"
                  f"\n{p}f disband"
                  f"\n{p}f join [faction]"
                  f"\n{p}f invite @user"
                  f"\n{p}f promote @user"
                  f"\n{p}f demote @user"
                  f"\n{p}f kick @user"
                  f"\n{p}f leave",
            inline=False,
        )
        e.add_field(
            name="◈ Utils - Incomplete ◈",
            value=f"  {p}f privacy"
                  f"\n{p}f setbio [your new bio]"
                  f"\n{p}f seticon [file | url]"
                  f"\n{p}f setbanner [file | url]"
                  f"\n{p}f togglenotifs",
            inline=False,
        )
        e.add_field(
            name="◈ Economy ◈",
            value=f"  {p}f work"
                  f"\n{p}f vote"
                  f"\n{p}f forage"
                  f"\n{p}f scrabble"
                  f"\n{p}f balance"
                  f"\n{p}f pay [faction] [amount]"
                  f"\n{p}f raid [faction]"
                  f"\n~~{p}f battle [faction]~~"  # incomplete
                  f"\n{p}f annex [faction]"
                  f"\n{p}f claim #channel"
                  f"\n{p}f unclaim #channel"
                  f"\n{p}f claims"
                  f"\n{p}f boosts"
                  f"\n{p}f info"
                  f"\n{p}f members [faction]"
                  f"\n{p}f top"
                  f"\n~~{p}f shop~~",  # incomplete
            inline=False,
        )
        await ctx.send(embed=e)

    @factions.command(name="create")
    async def create(self, ctx, *, name):
        """ Creates a faction """
        guild_id = str(ctx.guild.id)
        faction = await self.get_users_faction(ctx)
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
        if len(name) > 25:
            return await ctx.send("That name's too long")
        self.factions[guild_id][name] = {
            "owner": ctx.author.id,
            "co-owners": [],
            "members": [ctx.author.id],
            "balance": 0,
            "slots": 15,
            "public": True,
            "allies": [],
            "claims": [],
            "bio": "",
            "icon": None,
            "banner": None,
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
        faction = await self.get_authors_faction(ctx)
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
        is_in_faction = await self.get_users_faction(ctx)  # type: str
        if is_in_faction:
            return await ctx.send("You're already in a faction")
        faction = await self.get_faction_named(ctx, faction)
        guild_id = str(ctx.guild.id)
        if not self.factions[guild_id][faction]["public"]:
            return await ctx.send("That factions not public :[")
        if len(self.factions[guild_id][faction]["members"]) == self.factions[guild_id][faction]["slots"]:
            p = self.bot.utils.get_prefix(ctx)
            return await ctx.send(f"Your faction is currently full. Buy more slots for $250 with {p}f buy slots")
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
    @has_faction_permissions()
    async def invite(self, ctx, user: discord.Member):
        """ Invites a user to a private faction """

        def pred(msg):
            return (
                msg.channel.id == ctx.channel.id
                and msg.author.id == user.id
                and ("yes" in msg.content and "no" in msg.content)
            )

        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if len(self.factions[guild_id][faction]["members"]) == self.factions[guild_id][faction]["slots"]:
            p = self.bot.utils.get_prefix(ctx)
            return await ctx.send(f"Your faction is currently full. Buy more slots for $250 with {p}f buy slots")
        if not faction:
            return await ctx.send(
                "You need to have owner level permissions to use this cmd"
            )
        users_in_faction = await self.get_users_faction(ctx, user)
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
                self.factions[guild_id][faction]["members"].append(
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
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if ctx.author.id == self.factions[guild_id][faction]["owner"]:
            return await ctx.send(
                "You cannot leave a faction you own, you must "
                "transfer ownership, or disband it"
            )
        self.factions[guild_id][faction]["members"].remove(ctx.author.id)
        if ctx.author.id in self.factions[guild_id][faction]["co-owners"]:
            self.factions[guild_id][faction]["co-owners"].remove(ctx.author.id)
        await ctx.send("👍")
        await self.save_data()

    @factions.command(name="kick")
    async def kick(self, ctx, *, user: discord.User):
        """ Kicks a user from the faction """
        faction = await self.get_authors_faction(ctx)
        users_faction = await self.get_users_faction(ctx, user)
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
        if user.id in self.factions[guild_id][faction]["co-owners"]:
            self.factions[guild_id][faction]["co-owners"].remove(user.id)
        await ctx.send(f"Kicked {user.mention} from {faction}")
        await self.save_data()

    @factions.command(name="promote")
    @is_faction_owner()
    async def promote(self, ctx, *, user):
        """ Promotes a faction member to Co-Owner"""
        user = self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        guild_id = str(ctx.guild.id)
        faction = await self.get_authors_faction(ctx)
        if not faction or ctx.author.id != self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        if user.id in self.factions[guild_id][faction]["co-owners"]:
            return await ctx.send("That users already a co-owner")
        self.factions[guild_id][faction]["co-owners"].append(user.id)
        await ctx.send(f"Promoted {user.mention} to co-owner")
        await self.save_data()

    @factions.command(name="demote")
    @is_faction_owner()
    async def demote(self, ctx, *, user):
        """ Demotes a faction member from Co-Owner """
        user = self.bot.utils.get_user(ctx, user)
        if not user:
            return await ctx.send("User not found")
        faction = await self.get_authors_faction(ctx)
        if not faction:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        guild_id = str(ctx.guild.id)
        if ctx.author.id != self.factions[guild_id][faction]["owner"]:
            return await ctx.send("You need to be owner of a faction to use this cmd")
        if user.id not in self.factions[guild_id][faction]["co-owners"]:
            return await ctx.send("That users not co-owner")
        self.factions[guild_id][faction]["co-owners"].remove(user.id)
        await ctx.send(f"Demoted {user.mention} from co-owner")

    @factions.command(name="privacy")
    @has_faction_permissions()
    async def privacy(self, ctx):
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        toggle = self.factions[guild_id][faction]["public"]
        self.factions[guild_id][faction]["public"] = not toggle
        await ctx.send(f"Made {faction} {'public' if (not toggle) else 'private'}")
        await self.save_data()

    @factions.command(name="set-bio", aliases=["set_bio", "setbio"])
    @has_faction_permissions()
    async def set_bio(self, ctx, *, bio):
        faction = await self.get_authors_faction(ctx)
        if len(bio) > 256:
            return await ctx.send("Your bio cannot exceed more than 256 characters")
        self.factions[str(ctx.guild.id)][faction]["bio"] = bio
        await ctx.send("Set your factions bio")
        await self.save_data()

    @factions.command(name="set-icon", aliases=["seticon", "set_icon"])
    @has_faction_permissions()
    async def set_icon(self, ctx, url = None):
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if self.factions[guild_id][faction]["icon"] is None:
            if self.factions[guild_id][faction]["balance"] < 250:
                return await ctx.send("Buying access to icons costs $250 and you currently don't have enough")
            await ctx.send(
                "Buying access to icons will cost you $250. Reply with `yes` to confirm. "
                "Note this is a one time transaction, and you can set the icon as many times "
                "as you want after without having to buy this again"
            )
            async with self.bot.require("message", ctx) as msg:
                if "ye" not in str(msg.content).lower():
                    return await ctx.send("Aight.. maybe next time")
            self.factions[guild_id][faction]["balance"] -= 250
            self.factions[guild_id][faction]["icon"] = ""
        if not url and not ctx.message.attachments:
            self.factions[guild_id][faction]["icon"] = ""
            return await ctx.send(
                "Reset your factions icon. Attach a file or add a link when running the command, "
                "(example: `.f set-icon http://url.to.image/`) to set it back."
            )
        if not url:
            url = ctx.message.attachments[0].url
        e = discord.Embed(color=discord.Color.red())
        e.set_author(name="Ensuring the image works", icon_url=url)
        try:
            await ctx.send(embed=e, delete_after=5)
        except discord.errors.HTTPException:
            return await ctx.send("Discord won't let me set that as the icon, sorry")
        self.factions[guild_id][faction]["icon"] = url
        await ctx.send("Set your factions icon")
        await self.save_data()

    @factions.command(name="set-banner", aliases=["setbanner", "set_banner"])
    @has_faction_permissions()
    async def set_banner(self, ctx, url=None):
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if self.factions[guild_id][faction]["banner"] is None:
            if self.factions[guild_id][faction]["balance"] < 500:
                return await ctx.send("Buying access to banners costs $500 and you currently don't have enough")
            await ctx.send(
                "Buying access to banners will cost you $500. Reply with `yes` to confirm. "
                "Note this is a one time purchase, and you can set the banner as many times "
                "as you want after without having to buy this again"
            )
            async with self.bot.require("message", ctx) as msg:
                if "ye" not in str(msg.content).lower():
                    return await ctx.send("Aight.. maybe next time")
            self.factions[guild_id][faction]["balance"] -= 500
            self.factions[guild_id][faction]["banner"] = ""
        if not url and not ctx.message.attachments:
            self.factions[guild_id][faction]["banner"] = ""
            return await ctx.send(
                "Reset your factions banner. Attach a file or add a link when running the command, "
                "(example: `.f set-icon http://url.to.image/`) to set it back."
            )
        if not url:
            url = ctx.message.attachments[0].url
        e = discord.Embed(color=discord.Color.red())
        e.set_author(name="Ensuring the image works", icon_url=url)
        try:
            await ctx.send(embed=e, delete_after=5)
        except discord.errors.HTTPException:
            return await ctx.send("Discord won't let me set that as the banner, sorry")
        self.factions[guild_id][faction]["banner"] = url
        await ctx.send("Set your factions banner")
        await self.save_data()

    @factions.command(name="annex")
    @is_faction_owner()
    async def annex(self, ctx, *, faction):
        """ Merges a faction with another """
        authors_faction = await self.get_owned_faction(ctx, user=ctx.author)
        other_faction = await self.get_faction_named(ctx, faction)
        if authors_faction == other_faction:
            return await ctx.send("You must think you're slick..")
        guild_id = str(ctx.guild.id)
        dat = self.factions[guild_id][other_faction]
        await ctx.send(
            f"<@{dat['owner']}> {ctx.author} would like to merge factions with them as the owner. "
            f"Reply with `.confirm annex` if you consent to giving up your faction",
            allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
        )

        def predicate(m):
            return m.channel.id == ctx.channel.id and m.author.id == dat["owner"]

        async with self.bot.require("message", predicate, handle_timeout=True) as msg:
            if ".confirm annex" not in str(msg.content).lower():
                return await ctx.send("Alright, merge has been rejected")

        self.factions[guild_id][authors_faction]["balance"] += dat["balance"]
        for member_id in dat["members"]:
            if member_id not in self.factions[guild_id][authors_faction]["members"]:
                self.factions[guild_id][authors_faction]["members"].append(member_id)
        for member_id in dat["co-owners"]:
            if member_id not in self.factions[guild_id][authors_faction]["members"]:
                self.factions[guild_id][authors_faction]["members"].append(member_id)
        if dat["owner"] not in self.factions[guild_id][authors_faction]["members"]:
            self.factions[guild_id][authors_faction]["members"].append(dat["owner"])
        for faction, data in list(self.factions[guild_id].items()):
            if other_faction in data["allies"]:
                self.factions[guild_id][faction]["allies"].remove(other_faction)
        with suppress(ValueError):
            del self.factions[guild_id][other_faction]

        await ctx.send(f"Successfully annexed {other_faction}")

    @factions.command(name="rename")
    @is_faction_owner()
    async def rename(self, ctx, *, name):
        """ Renames their faction """
        faction = await self.get_authors_faction(ctx)
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
        if len(name) > 25:
            return await ctx.send("That name's too long")
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
            faction = await self.get_authors_faction(ctx)

        guild_id = str(ctx.guild.id)
        dat = self.factions[guild_id][faction]  # type: dict
        owner = self.bot.get_user(dat["owner"])
        icon_url = self.get_factions_icon(ctx, faction)
        rankings = await self.get_faction_rankings(guild_id)  # type: dict
        rankings = rankings["net"]  # type: list
        rank = 1
        for fac, value in rankings:
            if fac == faction:
                break
            rank += 1

        e = discord.Embed(color=purple())
        e.set_author(name=faction, icon_url=owner.avatar_url)
        e.set_thumbnail(url=icon_url)
        e.description = (
            f"**Owner:** **`@{owner}`**"
            f"\n**Members:** [`{len(dat['members'])}`] "
            f"**Public:** [`{dat['public']}`]"
            f"\n**Balance:** [`${dat['balance']}`]\n"
        )
        if dat["bio"]:
            e.add_field(
                name="◈ Biography",
                value=dat["bio"]
            )
        if dat["allies"]:
            allies = ""
            for ally in dat["allies"]:
                allies += f"\n• {ally}"
            e.add_field(
                name="◈ Allies",
                value=allies
            )
        if "banner" in dat:
            if dat["banner"]:
                e.set_image(url=dat["banner"])
        e.set_footer(text=f"Leaderboard Rank: #{rank}")
        await ctx.send(embed=e)

    @factions.command(name="income")
    async def income(self, ctx):
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        dat = self.factions[guild_id][faction]["income"]
        info = ""
        if "land_claims" in dat:
            info += f"Land-Claims: ${dat['land_claims']}"
        if "alliances" in dat:
            info += f"\nAlliances: ${dat['alliances']}"
        # for key, income in sorted(dat.items(), key=lambda kv: kv[1], reverse=True):
        #     if key.isdigit():
        #         user = self.bot.get_user(int(key))
        #         if user:
        #             info += f"\n{user.name}: ${income}"
        e = discord.Embed(color=purple())
        e.set_author(name="Income History", icon_url=self.get_factions_icon(ctx, faction))
        e.description = info
        await ctx.send(embed=e)

    @factions.command(name="members")
    async def members(self, ctx, *, faction=None):
        """ lists a factions members """
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = await self.get_authors_faction(ctx)

        guild_id = str(ctx.guild.id)
        owner_id = self.factions[guild_id][faction]["owner"]
        owner = self.bot.get_user(owner_id)
        owner_income = 0
        if str(owner.id) in self.factions[guild_id][faction]["income"]:
            owner_income = self.factions[guild_id][faction]["income"][str(owner_id)]
        users = []
        co_owners = []
        for user_id in self.factions[guild_id][faction]["members"]:  # type: int
            user = self.bot.get_user(user_id)
            if not isinstance(user, discord.User):
                self.factions[guild_id][faction].remove(user_id)
                await ctx.send(f"Can't find {await self.bot.fetch_user(user_id)}, kicked them from the faction")
                await self.save_data()
                continue

            income = 0
            if str(user_id) in self.factions[guild_id][faction]["income"]:
                income = self.factions[guild_id][faction]["income"][str(user_id)]
            if user_id in self.factions[guild_id][faction]["co-owners"]:
                co_owners.append([user, income])
            else:
                users.append([user, income])

        e = discord.Embed(color=purple())
        e.set_author(name=f"{faction}'s members", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.get_factions_icon(ctx, faction))
        e.description = f"**O:** `{owner.name}` - ${owner_income}\n"
        for user, income in sorted(co_owners, key=lambda kv: kv[1], reverse=True):
            e.description += f"**Co:** `{user.name}` - ${income}\n"
        for user, income in sorted(users, key=lambda kv: kv[1], reverse=True):
            e.description += f"**M:** `{user.name}` - ${income}\n"
        await ctx.send(embed=e)

    @factions.command(name="boosts")
    async def boosts(self, ctx, *, faction=None):
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = await self.get_authors_faction(ctx)
            if not faction:
                return await ctx.send("Faction not found")
        active = {}
        guild_id = str(ctx.guild.id)
        if guild_id in self.extra_income:
            if faction in self.extra_income[guild_id]:
                end_time = self.extra_income[guild_id][faction]  # type: float
                active["Extra-Income"] = end_time - time()  # Remaining time
        if guild_id in self.land_guard:
            if faction in self.land_guard[guild_id]:
                end_time = self.land_guard[guild_id][faction]
                active["Land-Guard"] = end_time - time()
        if guild_id in self.anti_raid:
            if faction in self.anti_raid[guild_id]:
                end_time = self.anti_raid[guild_id][faction]
                active["Anti-Raid"] = end_time - time()
        if active:
            boosts = "\n".join([
                f"• {boost} - {self.bot.utils.get_time(remaining_seconds)}"
                for boost, remaining_seconds in active.items()
            ])
        else:
            boosts = "None Active"
        e = discord.Embed(color=pink())
        e.set_author(name=f"{faction}s boosts", icon_url=self.get_factions_icon(ctx, faction))
        e.description = boosts
        await ctx.send(embed=e)

    @factions.command(name="claim")
    @has_faction_permissions()
    async def claim(self, ctx, channel: discord.TextChannel = None):
        """Claim a channel"""
        if not channel:
            channel = ctx.channel
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        claims = await self.collect_claims(guild_id)  # type: dict
        cost = 500
        if channel.id in claims:
            if claims[channel.id]["guarded"]:
                end_time = self.bot.utils.get_time(
                    self.land_guard[guild_id][claims[channel.id]["faction"]] - time()
                )
                return await ctx.send(
                    f"That claim is currently guarded. Try again in {end_time}"
                )
            cost += 250
        if cost > self.factions[guild_id][faction]["balance"]:
            needed = cost - self.factions[guild_id][faction]['balance']
            return await ctx.send(f"Your faction doesn't have enough money to claim "
                                  f"this channel. You need ${needed} more")
        await ctx.send(f"Claiming that channel will cost you ${cost}, "
                       f"reply with `.confirm` to claim it")
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            if ".confirm" not in str(msg.content).lower():
                return await ctx.send("Alright.. maybe next time")
        if channel.id in claims:
            fac = claims[channel.id]["faction"]
            self.factions[guild_id][fac]["claims"].remove(channel.id)
        self.factions[guild_id][faction]["claims"].append(channel.id)
        self.factions[guild_id][faction]["balance"] -= cost
        await ctx.send(f"Claimed {channel.mention} for {faction}")
        await self.save_data()

    @factions.command(name="unclaim")
    @has_faction_permissions()
    async def unclaim(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        if channel.id not in self.factions[guild_id][faction]["claims"]:
            return await ctx.send(f"You don't have {channel.mention} claimed")
        await ctx.send("Unclaiming this channel will give you $250, are you sure?")
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            if "ye" not in str(msg.content).lower():
                return await ctx.send("Aight, maybe next time")
        self.factions[guild_id][faction]["claims"].remove(channel.id)
        self.factions[guild_id][faction]["balance"] += 250
        await ctx.send(f"Unclaimed {channel.mention} and returned $250")

    @factions.command(name="claims")
    async def claims(self, ctx, *, faction = None):
        """ Returns a factions sorted claims """
        if faction:
            faction = await self.get_faction_named(ctx, faction)
        else:
            faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        e = discord.Embed(color=purple())
        e.set_author(
            name=f"{faction}'s claims", icon_url=self.get_factions_icon(ctx, faction)
        )
        claims = [
            self.bot.get_channel(chnl_id) for chnl_id in self.factions[guild_id][faction]["claims"]
        ]
        e.description = ""
        for channel in claims:
            e.description += f"• {channel.mention}\n"
        await ctx.send(embed=e)

    @factions.command(name="battle")
    async def battle(self, ctx, *args):
        """ Battle other factions in games like scrabble """
        await ctx.send("This command isn't developed yet")

    @factions.command(name="raid")
    @has_faction_permissions()
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.cooldown(2, 480, commands.BucketType.user)
    async def raid(self, ctx, *, faction):
        """ Starts a raid against another faction """
        attacker = await self.get_authors_faction(ctx)
        defender = await self.get_faction_named(ctx, faction)
        if not attacker:
            return await ctx.send("You need to be in a faction to use this cmd")
        if not defender:
            return await ctx.send("Faction not found")

        guild_id = str(ctx.guild.id)
        if guild_id in self.anti_raid:
            if defender in self.anti_raid[guild_id]:
                if time() > self.anti_raid[guild_id][defender]:
                    del self.boosts["anti-raid"][guild_id][defender]
                else:
                    end_time = self.bot.utils.get_time(
                        self.boosts["anti-raid"][guild_id][defender] - time()
                    )
                    return await ctx.send(
                        f"{defender} is currently guarded by anti-raid. Try again in {end_time}"
                    )
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
            return await ctx.send("One of you is too weak to raid. Try again when you at least have $250")

        if defender_bal > attacker_bal:
            await ctx.send("The odds are against us. Are you sure you wish to attempt a raid?")
            async with self.bot.require("message", ctx, handle_timeout=True) as msg:
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
        self.factions[guild_id][winner]["balance"] += loot
        self.factions[guild_id][loser]["balance"] -= loot

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
        faction = await self.get_authors_faction(ctx)

        if ctx.author.id in self.blocked:
            passed_verification = await self.bot.verify_user(ctx, user=ctx.author)
            if passed_verification:
                self.blocked.remove(ctx.author.id)
            else:
                return

        if ctx.author.id not in self.work_counter:
            self.work_counter[ctx.author.id] = 0
        self.work_counter[ctx.author.id] += 1
        if self.work_counter[ctx.author.id] >= 45:
            passed_verification = await self.bot.verify_user(ctx, user=ctx.author)
            if not passed_verification:
                self.blocked.append(ctx.author.id)
                self.work_counter[ctx.author.id] = 30
                return
            self.work_counter[ctx.author.id] = 0

        if guild_id not in self.cooldowns:
            self.cooldowns[guild_id] = {}
        if ctx.author.id in self.cooldowns[guild_id]:
            remainder = round(self.cooldowns[guild_id][ctx.author.id] - time())
            return await ctx.send(f"You're on cooldown! You have {remainder}s left")
        self.cooldowns[guild_id][ctx.author.id] = time() + 60

        e = discord.Embed(color=purple())
        pay = random.randint(15, 25)
        e.description = f"You earned {faction} ${pay}"
        if guild_id in self.extra_income:
            if faction in self.extra_income[guild_id]:
                if time() > self.extra_income[guild_id][faction]:
                    del self.boosts["extra-income"][guild_id][faction]
                else:
                    e.set_footer(
                        text="With Bonus: $5", icon_url=self.get_factions_icon(ctx, faction)
                    )
                    pay += 5

        self.factions[guild_id][faction]["balance"] += pay
        if str(ctx.author.id) in self.factions[guild_id][faction]["income"]:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] += pay
        else:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] = pay

        await ctx.send(embed=e)
        await self.save_data()

        await asyncio.sleep(self.cooldowns[guild_id][ctx.author.id] - time())
        del self.cooldowns[guild_id][ctx.author.id]
        if ctx.author.id in self.notifs:
            await ctx.send(
                f"{ctx.author.mention}, your work cooldowns up", delete_after=5,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
            )

    @factions.command(name="toggle-notifs")
    async def _toggle_notifs(self, ctx):
        if ctx.author.id in self.notifs:
            self.notifs.remove(ctx.author.id)
            await ctx.send("Disabled work notifications")
        else:
            self.notifs.append(ctx.author.id)
            await ctx.send("Enabled work notifications")
        await self.save_data()

    @factions.command(name="scrabble")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _scrabble(self, ctx):
        faction = await self.get_authors_faction(ctx)

        def pred(m):
            return (
                m.channel.id == ctx.channel.id
                and m.author.id == ctx.author.id
                and (str(m.content).lower() == word)
            )

        words = [
            "fate",
            "bait",
            "rock",
            "water",
            "server",
            "toast",
            "based"
        ]  # stay wholesome uwu
        word = random.choice(words)
        scrambled_word = list(str(word).lower())
        random.shuffle(scrambled_word)

        e = discord.Embed(color=purple())
        e.description = f"Scrambled word: `{''.join(scrambled_word)}`"
        e.set_footer(text="You have 25 seconds..", icon_url=ctx.bot.user.avatar_url)
        await ctx.send(embed=e)

        try:
            await ctx.bot.wait_for("message", check=pred, timeout=25)
        except asyncio.TimeoutError:
            return await ctx.send("You failed. Maybe next time :/")

        guild_id = str(ctx.guild.id)
        paycheck = random.randint(3, 7)
        e = discord.Embed(color=purple())
        e.description = f"You earned {faction} ${paycheck}"
        if guild_id in self.extra_income:
            if faction in self.extra_income[guild_id]:
                if time() > self.extra_income[guild_id][faction]:
                    del self.boosts["extra-income"][guild_id][faction]
                else:
                    e.set_footer(
                        text="With Bonus: $2", icon_url=self.get_factions_icon(ctx, faction)
                    )
                    paycheck += 2
        self.factions[guild_id][faction]["balance"] += paycheck
        if str(ctx.author.id) in self.factions[guild_id][faction]["income"]:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] += paycheck
        else:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] = paycheck
        await ctx.send(embed=e)
        await self.save_data()

    @factions.command(name="vote")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _vote(self, ctx):
        faction = await self.get_authors_faction(ctx)
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select vote_time from votes "
                f"where user_id = {ctx.author.id} "
                f"order by vote_time asc;"
            )
            results = await cur.fetchall()
        if not results:
            return await ctx.send(f"Vote at http://vote.fatebot.xyz to earn $250."
                                  f"\nRerun the command after to redeem")
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"delete from votes "
                f"where user_id = {ctx.author.id} "
                f"order by vote_time asc "
                f"limit 1;"
            )
        self.factions[str(ctx.guild.id)][faction]['balance'] += 250
        guild_id = str(ctx.guild.id)
        if str(ctx.author.id) in self.factions[guild_id][faction]["income"]:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] += 250
        else:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] = 250
        additional = ""
        if len(results) > 1:
            additional += f". You have {len(results) - 1} redeemable votes remaining"
        await ctx.send(f"Redeemed $250 for your faction" + additional)
        await self.save_data()

    @factions.command(name="forage")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _forage(self, ctx):
        faction = await self.get_authors_faction(ctx)

        places = [
            "You checked inside a shoe and found $", "You creeped through an abandoned mineshaft and stumbled across $",
            "You rummaged through a burnt down walmart and found some silverware you sold for $",
            "You found fates code and sold it on the black market for $",
            "You tripped and found $", "You stumbled apon a chest and found $",
            "Your madusa looking headass sold a picture of yourself for $ to a mysterious agency"
        ]

        pay = random.randint(3, 7)
        e = discord.Embed(color=purple())
        e.description = random.choice(places).replace("$", f"${pay}")
        guild_id = str(ctx.guild.id)
        if guild_id in self.extra_income:
            if faction in self.extra_income[guild_id]:
                if time() > self.extra_income[guild_id][faction]:
                    del self.boosts["extra-income"][guild_id][faction]
                else:
                    e.set_footer(
                        text="With Bonus: $2", icon_url=self.get_factions_icon(ctx, faction)
                    )
                    pay += 5
        self.factions[str(ctx.guild.id)][faction]["balance"] += pay
        guild_id = str(ctx.guild.id)
        if str(ctx.author.id) in self.factions[guild_id][faction]["income"]:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] += pay
        else:
            self.factions[guild_id][faction]["income"][str(ctx.author.id)] = pay
        await ctx.send(embed=e)
        await self.save_data()

    @factions.command(name="balance", aliases=["bal"])
    async def balance(self, ctx, *, faction=None):
        """ Sends a factions balance """
        if faction:
            faction = await self.get_faction_named(ctx, name=faction)
        else:
            faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)
        e = discord.Embed(color=purple())
        e.set_author(name=str(faction), icon_url=self.get_factions_icon(ctx, str(faction)))
        e.description = f"${self.factions[guild_id][faction]['balance']}"
        await ctx.send(embed=e)

    @factions.command(name="pay")
    @commands.cooldown(2, 240, commands.BucketType.user)
    @is_faction_owner()
    async def pay(self, ctx, faction, amount: int):
        """ Pays a faction from the author factions balance """
        authors_fac = await self.get_authors_faction(ctx)
        target_fac = await self.get_faction_named(ctx, faction)
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
    @commands.bot_has_permissions(manage_messages=True, add_reactions=True)
    async def top(self, ctx):
        def predicate(r, u) -> bool:
            m = r.message  # type: discord.Message
            return m.id == msg.id and str(r.emoji) in emojis and not u.bot

        async def add_emojis_task():
            with suppress(Forbidden):
                for emoji in emojis:
                    await msg.add_reaction(emoji)

        guild_id = str(ctx.guild.id)
        if guild_id not in self.factions:
            return await ctx.send("This server currently has no rankings")
        dat = await self.get_faction_rankings(guild_id)
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
            net_leaderboard.description += f"\n#{i + 1}. {faction} - ${value}"

        bal_leaderboard = discord.Embed(color=purple())
        bal_leaderboard.set_author(name="Balance Leaderboard")
        bal_leaderboard.set_thumbnail(url=ctx.guild.icon_url)
        bal_leaderboard.description = ""
        for i, (faction, balance) in enumerate(dat["bal"][:9]):
            bal_leaderboard.description += f"\n#{i + 1}. {faction} - ${balance}"

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
        ally_name = await self.get_faction_named(ctx, target_faction)
        faction_name = await self.get_owned_faction(ctx)

        guild_id = str(ctx.guild.id)
        if faction_name in self.factions[guild_id][ally_name]["allies"]:
            return await ctx.send(f"You're already allied with `{ally_name}`")
        if len(self.factions[guild_id][faction_name]["allies"]) == 2:
            return await ctx.send(f"At the moment, you can't exceed 3 alliances")
        if len(self.factions[guild_id][ally_name]["allies"]) == 2:
            return await ctx.send(
                "That faction has already reached its limit of alliances"
            )

        def predicate(m):
            return m.channel.id == ctx.channel.id and ".accept" in str(m.content)

        await ctx.send(
            f"Someone with ownership level permissions in {ally_name} "
            "reply with `.accept` to agree to the alliance"
        )
        while True:
            async with self.bot.require("message", predicate, handle_timeout=True) as msg:
                if await self.get_owned_faction(ctx, user=msg.author) == ally_name:
                    self.factions[guild_id][faction_name]["allies"].append(ally_name)
                    self.factions[guild_id][ally_name]["allies"].append(faction_name)
                    await ctx.send(
                        f"Successfully created an alliance between `{faction_name}` and `{ally_name}`"
                    )
                    return await self.save_data()

    @factions.command(name="shop")
    async def shop(self, ctx):
        e = discord.Embed(color=purple())
        e.set_author(name="Factions Shop", icon_url=self.bot.user.avatar_url)
        e.add_field(
            name="◈ Attributes",
            value="》 +5 member slots\n"
                  "• $250",
            inline=False
        )
        e.add_field(
            name="◈ Boosts",
            value="》2h extra-income\n"
                  "• $50\n"
                  "》24h anti-raid\n"
                  "• $75\n"
                  "》2h land-guard\n"
                  "• $100",
            inline=False
        )
        p = self.bot.utils.get_prefix(ctx)
        e.set_footer(text=f"Usage | {p}f buy item_name")
        await ctx.send(embed=e)

    @factions.command(name="buy")
    @has_faction_permissions()
    async def buy(self, ctx, item_name: lambda arg: arg.lower()):
        def has_money(amount: int):
            return self.factions[guild_id][faction]["balance"] >= amount

        faction = await self.get_authors_faction(ctx)
        guild_id = str(ctx.guild.id)

        if "slots" in item_name:
            if self.factions[guild_id][faction]["slots"] == 25:
                return await ctx.send("You're at the max number of slots")
            if not has_money(250):
                return await ctx.send("You need $250 to buy this")
            self.factions[guild_id][faction]["balance"] -= 250
            self.factions[guild_id][faction]["slots"] += 5
            await ctx.send(f"Upped the slots to {self.factions[guild_id][faction]['slots']}")

        elif "income" in item_name:
            if not has_money(50):
                return await ctx.send("You need $50 to buy this")
            if guild_id not in self.extra_income:
                self.boosts["extra-income"][guild_id] = {}
            self.factions[guild_id][faction]["balance"] -= 50
            self.boosts["extra-income"][guild_id][faction] = time() + 60 * 60 * 2
            await ctx.send("Purchased 2h extra-income")

        elif "raid" in item_name:
            if not has_money(75):
                return await ctx.send("You need $75 to buy this")
            if guild_id not in self.anti_raid:
                self.boosts["anti-raid"][guild_id] = {}
            self.boosts["anti-raid"][guild_id][faction] = time() + 60 * 60 * 12
            await ctx.send("Purchased 12h anti-raid")

        elif "guard" in item_name:
            if not has_money(100):
                return await ctx.send("You need $100 to buy this")
            if guild_id not in self.land_guard:
                self.boosts["land-guard"][guild_id] = {}
            self.boosts["land-guard"][guild_id][faction] = time() + 60 * 60 * 2
            await ctx.send("Purchased 2h land-guard")

        else:
            p = self.bot.utils.get_prefix(ctx)
            await ctx.send(f"That's not an item in the shop, use {p}f shop")

        await self.save_data()

    @commands.Cog.listener()
    async def on_message(self, msg):
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.factions and "annex" not in msg.content.lower():
                claims = await self.collect_claims(guild_id)  # type: dict
                if msg.channel.id in claims:
                    if msg.channel.id not in self.claim_counter:
                        self.claim_counter[msg.channel.id] = 0
                    self.claim_counter[msg.channel.id] += 1
                    if self.claim_counter[msg.channel.id] == 5:
                        self.claim_counter[msg.channel.id] = 0
                        faction = claims[msg.channel.id]["faction"]
                        pay = random.randint(1, 5)
                        self.factions[guild_id][faction]["balance"] += pay
                        await self.update_income_board(guild_id, faction, land_claims=pay)
                        ally_pay = round(pay / 2) if pay > 1 else 0
                        for ally in list(self.factions[guild_id][faction]["allies"]):
                            if ally not in self.factions[guild_id]:
                                self.factions[guild_id][faction]["allies"].remove(ally)
                                continue
                            self.factions[guild_id][ally]["balance"] += ally_pay
                            await self.update_income_board(guild_id, ally, alliances=ally_pay)


def setup(bot):
    bot.add_cog(FactionsRewrite(bot))
