"""
cogs.utility.info.channel
~~~~~~~~~~~~~~~~~~~~~~~~~~

A coroutine function for generating a users profile embed

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from datetime import datetime, timezone

import discord

from botutils import colors, get_time, split

async def fetch_channel_info(ctx, channel: discord.TextChannel):
    """|coro| Generates an information embed for a channel"""
    e = discord.Embed(color=colors.fate)
    e.set_author(
        name="Alright, here's what I got..", icon_url=ctx.bot.user.avatar.url
    )
    bot_has_audit_access = ctx.guild.me.guild_permissions.view_audit_log

    channel_info = {
        "Name": channel.name,
        "ID": channel.id,
        "Members": str(len(channel.members)),
    }

    if channel.category:
        channel_info["Category"] = f"`{channel.category}`"
    if channel.is_nsfw():
        channel_info["Marked as NSFW"] = None
    if channel.is_news():
        channel_info["Is the servers news channel"] = None
    channel_info["Created at"] = channel.created_at.strftime("%m/%d/%Y %I%p")

    e.add_field(
        name="◈ Channel Information",
        value=ctx.bot.utils.format_dict(channel_info),
        inline=False,
    )
    e.set_footer(text="🖥 Topic | ♻ History")

    msg = await ctx.send(embed=e)
    ems = ["🖥", "♻"]
    for emoji in ems:
        await msg.add_reaction(emoji)

    def predicate(r, u):
        return str(r.emoji) in ems and r.message.id == msg.id and not u.bot

    while True:
        await asyncio.sleep(0.5)
        try:
            reaction, user = await ctx.bot.wait_for(
                "reaction_add", check=predicate, timeout=60
            )
        except asyncio.TimeoutError:
            if (
                ctx.channel.permissions_for(ctx.guild.me).manage_messages
                and msg
            ):
                await msg.clear_reactions()
            return

        if str(reaction.emoji) == "🖥":  # Requested topic information
            topic = channel.topic
            if not topic:
                topic = "None set."
            for group in split(topic, 1024):
                e.add_field(name="◈ Channel Topic", value=group, inline=False)
            ems.remove("🖥")
        elif str(reaction.emoji) == "♻":  # Requested channel history
            if not bot_has_audit_access:
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await msg.remove_reaction(reaction, user)
                err = "Missing view_audit_log permission(s)"
                if any(field.value == err for field in e.fields):
                    continue
                e.add_field(name="◈ Channel History", value=err, inline=False)
            else:
                e.set_footer()
                history = {}
                e.add_field(
                    name="◈ Channel History", value="Fetching..", inline=False
                )
                await msg.edit(embed=e)

                action = discord.AuditLogAction.channel_create
                async for entry in ctx.guild.audit_logs(
                    limit=500, action=action
                ):
                    if channel.id == entry.target.id:
                        history["Creator"] = entry.user
                        break

                if channel.permissions_for(ctx.guild.me).read_messages:
                    async for m in channel.history(limit=1):
                        seconds = (
                            datetime.now(tz=timezone.utc) - m.created_at
                        ).total_seconds()
                        total_time = get_time(round(seconds))
                        history["Last Message"] = f"{total_time} ago\n"

                action = discord.AuditLogAction.channel_update
                async for entry in ctx.guild.audit_logs(
                    limit=750, action=action
                ):
                    if channel.id == entry.target.id:
                        if not hasattr(entry.before, "name") or not hasattr(
                            entry.after, "name"
                        ):
                            continue
                        if entry.before.name != entry.after.name:
                            minute = str(entry.created_at.minute)
                            if len(minute) == 1:
                                minute = "0" + minute
                            when = entry.created_at.strftime(
                                f"%m/%d/%Y %I:{minute}%p"
                            )
                            history[f"**Name Changed on {when}**"] = None
                            history[
                                f"**Old Name:** `{entry.before.name}`\n"
                            ] = None

                if not history:
                    history["None Found"] = None
                e.set_field_at(
                    index=len(e.fields) - 1,
                    name="◈ Channel History",
                    value=ctx.bot.utils.format_dict(
                        dict(list(history.items())[:6])
                    ),
                    inline=False,
                )
                ems.remove("♻")
        await msg.edit(embed=e)
