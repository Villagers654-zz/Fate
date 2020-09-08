# Captcha human verification channels

import asyncio
from os import path
import json
from typing import Optional
from contextlib import suppress
from datetime import datetime, timedelta

from discord.ext import commands
import discord
from discord.errors import *

from fate import Fate
from utils import colors
from cogs.utils import Utils as utils


class Verification(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.path = "./data/userdata/verification.json"
        self.config = {}
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.config = json.load(f)
        for guild_id, config in list(self.config.items()):
            if "log_channel" not in config:
                config["log_channel"] = None
            if "kick_on_fail" not in config:
                config["kick_on_fail"] = True
            if "auto_start" not in config:
                config["auto_start"] = True
        self.queue = {}
        self.running_tasks = []

    @property
    def template_config(self):
        return {
            "channel_id": int,                    # Verification channel, required incase the bot can't dm
            "verified_role_id": int,              # Role to give whence verified
            "temp_role_id": Optional[None, int],  # Role to remove whence verified
            "delete_after": bool,                 # Delete captcha message after users are verified
            "log_channel": int,
            "kick_on_fail": bool,
            "auto_start": bool
        }

    async def save_data(self):
        """ Dump changes to the config to a file """
        async with self.bot.open(self.path, "w+") as f:
            await f.write(json.dumps(self.config))

    @commands.group(name="verification")
    @commands.cooldown(*utils.default_cooldown())
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
                      
                f"\n{p}verification disable"
                f"\n`wipes your current configuration`"
                      
                f"\n{p}verification set-channel #channel"
                f"\n`changes the linked channel`"
                      
                f"\n{p}verification set-verified-role @role"
                f"\n`change the role given whence verified`"
                      
                f"\n{p}verification set-temp-role @role"
                f"\n`set or change the role to remove whence verified. this is an optional feature, "
                f"and isn't required in order for verification to work`"
                      
                f"\n{p}verification delete-after"
                f"\n`toggles whether or not to delete the captcha after a user completes verification`"
                      
                f"\n{p}verification kick"
                f"\n`toggles whether or not to kick after failing verification`"
                      
                f"\n{p}verification auto-start"
                f"\n`toggles verification starting automatically when a new member joins instead of using .verify`"
                      
                f"\n{p}verification log-channel #channel"
                f"\n`sets the channel to log whether people succeeded or failed verification. use this without "
                f"the #channel argument to disable this feature`",
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
                log_channel = None
                if conf["log_channel"]:
                    log_channel = self.bot.get_channel(conf["log_channel"])
                log_channel = log_channel.mention if log_channel else "Not Set"
                e.add_field(
                    name="◈ Current Configuration",
                    value=self.bot.utils.format_dict({
                        "Channel":
                            channel.mention if channel else 'deleted-channel',
                        "Verified Role":
                            verified_role.mention
                            if verified_role else 'deleted-role',
                        "Temp Role":
                            temp_role,
                        "Log Channel":
                            log_channel,
                        "Delete captcha after":
                            str(conf["delete_after"]),
                        "Auto Start":
                            str(conf["auto_start"]),
                        "Kick on Fail":
                            str(conf["kick_on_fail"])
                    }))
            await ctx.send(embed=e)

    @verification.group(name="enable")
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)

        await ctx.send("Mention the channel I should use for each verification process")
        async with self.bot.require('message', ctx) as msg:
            if not msg.channel_mentions:
                return await ctx.send("m, that's an invalid response\nRerun the command and try again")
            channel = msg.channel_mentions[0]
        perms = channel.permissions_for(ctx.guild.me)
        if not perms.send_messages or not perms.embed_links or not perms.manage_messages:
            return await ctx.send("Before you can enable verification I need permissions in that channel to send "
                                  "messages, embed links, and manage messages")

        await ctx.send("Send the name, or mention of the role I should give whence someone completes verification")
        async with self.bot.require('message', ctx) as msg:
            role = await self.bot.utils.get_role(ctx, msg.content)
        if not role:
            return await ctx.send("m, that's not a valid role\nRerun the command and try again")
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's higher than I can access")

        await ctx.send("Send the name, or mention of the role I should remove whence someone completes verification"
                       "\nThis one's optional, so you can reply with `skip` if you don't wish to use one")
        async with self.bot.require('message', ctx) as msg:
            temp_role = None
            if str(msg.content).lower() != "skip":
                target = await self.bot.utils.get_role(ctx, msg.content)
                if not target:
                    return await ctx.send("m, that's not a valid role\nRerun the command and try again")
                if role.position >= ctx.guild.me.top_role.position:
                    return await ctx.send("That role's higher than I can access")
                temp_role = target.id

        await ctx.send("Should I delete the captcha message that shows if a user passed or failed verification after "
                       "completion? Reply with `yes` or `no`")
        async with self.bot.require('message', ctx) as msg:
            if 'ye' not in str(msg.content).lower() and 'no' not in str(msg.content).lower():
                return await ctx.send("Invalid response, please rerun the command")
            elif 'ye' in str(msg.content).lower():
                delete_after = True
            else:
                delete_after = False

        await ctx.send("Should I kick members if they fail verification? Reply with `yes` or `no`")
        async with self.bot.require('message', ctx) as msg:
            if 'ye' not in str(msg.content).lower() and 'no' not in str(msg.content).lower():
                return await ctx.send("Invalid response, please rerun the command")
            elif 'ye' in str(msg.content).lower():
                kick_on_fail = True
            else:
                kick_on_fail = False

        await ctx.send("Now, should I log whether or not someone passes, fails, or kick to a channel? "
                       "If so, #mention the channel I should use; otherwise send `skip`")
        async with self.bot.require('message', ctx) as msg:
            if msg.channel_mentions:
                log_channel = msg.channel_mentions[0].id
            else:
                log_channel = None

        await ctx.send("When a new member joins, should I start captcha verification on my own, or "
                       "wait until they run .verify. Reply with `yes` to start automatically, or `no` to not")
        async with self.bot.require("message", ctx) as msg:
            if 'ye' not in str(msg.content).lower() and 'no' not in str(msg.content).lower():
                return await ctx.send("Invalid response, please rerun the command")
            elif 'ye' in str(msg.content).lower():
                automatic = True
            else:
                automatic = False

        self.config[guild_id] = {
            "channel_id": channel.id,     # Verification channel, required incase the bot can't dm
            "verified_role_id": role.id,  # Role to give whence verified
            "temp_role_id": temp_role,    # Role to remove whence verified
            "delete_after": delete_after,
            "kick_on_fail": kick_on_fail,
            "log_channel": log_channel,
            "auto_start": automatic
        }
        await ctx.send("Successfully setup the verification system")
        await self.save_data()

    @verification.group(name="disable")
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        del self.config[guild_id]
        await ctx.send("Disabled verification")
        await self.save_data()

    @verification.group(name="setchannel", aliases=["set-channel"])
    @commands.has_permissions(administrator=True)
    async def _set_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        perms = channel.permissions_for(ctx.guild.me)
        if not perms.send_messages or not perms.embed_links or not perms.manage_messages:
            return await ctx.send("Before you can enable verification I need permissions in that channel to send "
                                  "messages, embed links, and manage messages")
        self.config[guild_id]["channel_id"] = channel.id
        await ctx.send("Set the verification channel")
        await self.save_data()

    @verification.group(name="set-verified-role")
    @commands.has_permissions(administrator=True)
    async def _set_verified_role(self, ctx, *, role):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        role = await self.bot.utils.get_role(ctx, role)
        if not role:
            return await ctx.send("Role not found")
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send("That role's higher than I can access")
        self.config[guild_id]["verified_role_id"] = role.id
        await ctx.send("Set the verified role")
        await self.save_data()

    @verification.group(name="set-temp-role")
    @commands.has_permissions(administrator=True)
    async def _set_temp_role(self, ctx, *, role=None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        if role is not None:
            role = await self.bot.utils.get_role(ctx, role)
            if not role:
                return await ctx.send("Role not found")
            if role.position >= ctx.guild.me.top_role.position:
                return await ctx.send("That role's higher than I can access")
            role = role.id
        self.config[guild_id]["temp_role_id"] = role
        await ctx.send("Set the temp role")
        await self.save_data()

    @verification.command(name="delete-after")
    @commands.has_permissions(administrator=True)
    async def _delete_after(self, ctx, toggle: bool = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        new_toggle = not self.config[guild_id]["delete_after"]
        if toggle:
            new_toggle = toggle
        self.config[guild_id]["delete_after"] = new_toggle
        await ctx.send(f"{'Enabled' if new_toggle else 'Disabled'} delete-after")
        await self.save_data()

    @verification.command(name="kick")
    @commands.has_permissions(administrator=True)
    async def _kick(self, ctx, toggle: Optional[bool]):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        if toggle:
            new_toggle = toggle
        else:
            new_toggle = not self.config[guild_id]["kick_on_fail"]
        self.config[guild_id]["kick_on_fail"] = new_toggle
        await ctx.send(f"{'Enabled' if new_toggle else 'Disabled'} kicking on fail")
        await self.save_data()

    @verification.command(name="auto", aliases=["automatic"])
    @commands.has_permissions(administrator=True)
    async def auto_start(self, ctx, toggle: Optional[bool]):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        if toggle:
            new_toggle = toggle
        else:
            new_toggle = not self.config[guild_id]["auto_start"]
        self.config[guild_id]["auto_start"] = new_toggle
        await ctx.send(f"{'Enabled' if new_toggle else 'Disabled'} automatically starting verification")
        await self.save_data()

    @verification.command(name="log-channel", aliases=["logchannel"])
    @commands.has_permissions(administrator=True)
    async def _log_channel(self, ctx, channel: Optional[discord.TextChannel]):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        self.config[guild_id]["log_channel"] = channel.id if channel else None
        await ctx.send(f"{'Set' if channel else 'Removed'} the log channel")
        await self.save_data()

    @commands.command(name="verify")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def verify(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("Verification isn't enabled")
        await self.init_verification_process(ctx.author)

    async def bulk_purge(self, channel: discord.TextChannel, collection_period: int = 5):
        """Collect messages for X seconds and bulk delete"""
        guild_id = str(channel.guild.id)
        await asyncio.sleep(collection_period)

        target_messages = list(set([msg for msg in self.queue[guild_id] if msg]))
        for message in target_messages:
            self.queue[guild_id].remove(message)

        try:  # Attempt to bulk delete the target messages
            await channel.delete_messages(target_messages)
        except NotFound:  # One, or more of the messages was already deleted
            for msg in target_messages:
                # Delete individually
                with suppress(NotFound):
                    await msg.delete()
        return None

    @commands.Cog.listener("on_message")
    async def channel_cleanup(self, msg):
        """Trigger the task for bulk deleting messages in verification channels"""
        if not isinstance(msg.channel, discord.DMChannel) and not msg.author.bot:
            if not msg.author.guild_permissions.administrator:
                guild_id = str(msg.guild.id)
                if guild_id in self.config and msg.channel.id == self.config[guild_id]["channel_id"]:
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
        if guild_id in self.config and not member.bot:
            conf = self.config[guild_id]  # type: Verification.template_config
            if member.joined_at > datetime.utcnow() - timedelta(seconds=2):
                if not conf["auto_start"]:
                    return
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
            log_channel = None
            if conf["log_channel"]:
                try:
                    log_channel = await self.bot.fetch_channel(conf["log_channel"])
                except (NotFound, HTTPException, Forbidden):
                    log_channel = None
                    self.config[guild_id]["log_channel"] = None
                    await self.save_data()
            if conf["kick_on_fail"]:
                bot = member.guild.me  # type: discord.Member
                if not bot.guild_permissions.kick_members or member.top_role > bot.top_role:
                    await channel.send("I'm missing kick permission(s) to properly manage verification")
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
            if verified_role in member.roles:
                return
            verified = await self.bot.verify_user(channel=channel, user=member, delete_after=conf["delete_after"])
            if verified:
                await member.add_roles(verified_role)
                if conf["temp_role_id"]:
                    temp_role = member.guild.get_role(conf["temp_role_id"])
                    if temp_role:
                        if temp_role in member.roles:
                            await member.remove_roles(temp_role)
                    else:
                        with suppress(Forbidden, HTTPException):
                            await channel.send(
                                f"Disabled verification in {member.guild} due to the verified role being deleted"
                            )
                        self.config[guild_id]["temp_role_id"] = None
                        await self.save_data()
                if log_channel:
                    await log_channel.send(f"{member} was verified")
            else:
                if verified_role not in member.roles and conf["kick_on_fail"]:
                    try:
                        await member.kick(reason="Failed Captcha Verification")
                    except Forbidden:
                        with suppress(Forbidden, HTTPException):
                            await member.guid.owner.send(
                                f"I'm missing permissions to kick unverified members in {member.guild}"
                            )
                    else:
                        if log_channel:
                            await log_channel.send(f"Kicked {member} for failing verification")
                else:
                    if log_channel:
                        await log_channel.send(f"{member} failed to complete the captcha")


def setup(bot):
    bot.add_cog(Verification(bot))
