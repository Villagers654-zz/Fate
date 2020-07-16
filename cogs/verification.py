# Captcha human verification channels

from time import time
import asyncio
from os import path
import json
from typing import Optional
from contextlib import suppress

from discord.ext import commands
import discord
from discord.errors import *

from fate import Fate
from utils import utils, colors


class Verification(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.path = "./data/userdata/verification.json"
        self.config = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)
        self.queue = {}
        self.running_tasks = []

    @property
    def template_config(self):
        return {
            "channel_id": int,  # Verification channel, required incase the bot can't dm
            "verified_role_id": int,  # Role to give whence verified
            "temp_role_id": Optional[None, int]  # Role to remove whence verified
        }

    async def save_data(self):
        """ Dump changes to the config to a file """
        await self.bot.save_json(fp=self.path, data=self.config)

    @commands.group(name="verification")
    @commands.cooldown(2, 5, *utils.default_cooldown())
    async def verification(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="User Verification")
            e.description = f"Require new members to complete a captcha when they join to prove they're human"
            p = utils.get_prefix(ctx)
            e.add_field(
                name="◈ Usage",
                value=f"{p}verification enable"
                f"\n`start a simple and guided setup process`"
                f"{p}verification disable"
                f"\n`wipes your current configuration`"
                f"\n~~{p}verification set-verified-role @role"
                f"\n`change the role given whence verified`"
                f"\n{p}verification set-temp-role @role"
                f"\n`set or change the role to remove whence verified. this is an optional feature, "
                f"and isn't required in order for verification to work`~~",
                inline=False)
            guild_id = str(ctx.guild.id)
            if guild_id in self.config:
                conf = self.config[guild_id]
                channel = self.bot.get_channel(conf['channel_id'])
                verified_role = ctx.guild.get_role(conf['verified_role_id'])
                temp_role = "Not Set"
                if conf['temp_role_id']:
                    temp_role = ctx.guild.get_role(conf['temp_role_id'])
                    if temp_role:
                        temp_role = temp_role.mention
                    else:
                        temp_role = "deleted-role"
                e.add_field(
                    name="◈ Current Configuration",
                    value=self.bot.utils.format_dict({
                        "Channel":
                            channel.mention if channel else 'deleted-channel',
                        "Verified Role":
                            verified_role.mention
                            if verified_role else 'deleted-role',
                        "Temp Role":
                            temp_role
                    }))
            await ctx.send(embed=e)

    @verification.group(name="disable")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        del self.config[guild_id]
        await ctx.send("Disabled verification")
        await self.save_data()

    async def bulk_purge(self, channel: discord.TextChannel, collection_period: int = 5):
        guild_id = str(channel.guild.id)
        await asyncio.sleep(collection_period)
        target_messages = [msg for msg in self.queue[guild_id] if msg]
        for message in target_messages:
            self.queue[guild_id].remove(message)
        try:
            await channel.delete_messages(target_messages)
        except NotFound:
            for msg in target_messages:
                with suppress(NotFound):
                    await msg.delete()

    @commands.Cog.listener("on_message")
    async def channel_cleanup(self, msg):
        guild_id = str(msg.guild.id)
        if not msg.author.bot and guild_id in self.config:
            if msg.channel.id == self.config[guild_id]["channel_id"]:
                if guild_id not in self.queue:
                    self.queue[guild_id] = []
                self.queue[guild_id].append(msg)
                if guild_id not in self.running_tasks:
                    self.running_tasks.append(guild_id)
                    with suppress(IndexError, NotFound, Forbidden, HTTPException):
                        await self.bulk_purge(msg.channel, collection_period=5)
                    self.running_tasks.remove(guild_id)

    @commands.Cog.listener("on_member_join")
    async def init_verification_process(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.config:
            conf = self.config[guild_id]  # type: Verification.template_config
            try:
                channel = await self.bot.fetch_channel(conf["channel_id"])
            except (NotFound, HTTPException, Forbidden):
                with suppress(Forbidden, HTTPException):
                    await member.guild.owner.send(
                        f"Disabled verification in {member.guild} due to the channel being deleted"
                    )
                del self.config[guild_id]
                await self.save_data()
                return
            verified_role = member.guild.get_role(conf["verified_role_id"])
            if not verified_role:
                with suppress(Forbidden, HTTPException):
                    await channel.send(
                        f"Disabled verification in {member.guild} due to the verified role being deleted"
                    )
                del self.config[guild_id]
                await self.save_data()
                return
            msg = await channel.send(
                f"{member.mention} complete this captcha to be verified",
                delete_after=45
            )
            ctx = await self.bot.get_context(msg)
            verified = await self.bot.verify_user(ctx, user=member)
            if verified:
                await member.add_roles(verified_role)
                if conf["temp_role_id"]:
                    temp_role = ctx.guild.get_role(conf["temp_role_id"])
                    if not temp_role:
                        with suppress(Forbidden, HTTPException):
                            await channel.send(
                                f"Disabled verification in {member.guild} due to the verified role being deleted"
                            )
                        self.config[guild_id]["temp_role_id"] = None
                        await self.save_data()
                    else:
                        if temp_role in member.roles:
                            await member.remove_roles(temp_role)
            else:
                try:
                    await member.kick(reason="Failed Captcha Verification")
                except Forbidden:
                    with suppress(Forbidden, HTTPException):
                        await member.guid.owner.send(
                            f"I'm missing permissions to kick unverified members in {member.guild}"
                        )
            with suppress(NotFound):
                await msg.delete()


def setup(bot):
    bot.add_cog(Verification(bot))
