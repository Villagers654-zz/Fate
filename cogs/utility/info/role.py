"""
cogs.utility.info.role
~~~~~~~~~~~~~~~~~~~~~~~

A coroutine function for generating a roles information embed

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from datetime import datetime

import discord

from botutils import colors


async def fetch_role_info(ctx, role):
    e = discord.Embed(color=colors.fate)
    e.set_author(
        name="Alright, here's what I got..", icon_url=ctx.bot.user.avatar.url
    )

    core = {
        "Name": role.name,
        "Mention": role.mention,
        "ID": role.id,
        "Members": len(role.members) if role.members else "None",
        "Created at": role.created_at.strftime("%m/%d/%Y %I%p"),
    }

    extra = {
        "Mentionable": str(role.mentionable),
        "HEX Color": role.color,
        "RGB Color": role.colour.to_rgb(),
    }
    if role.hoist:
        extra["**Shows Above Other Roles**"] = None
    if role.managed:
        extra["**And Is An Integrated Role**"] = None

    e.add_field(
        name="◈ Role Information",
        value=ctx.bot.utils.format_dict(core),
        inline=False,
    )
    e.add_field(
        name="◈ Extra", value=ctx.bot.utils.format_dict(extra), inline=False
    )
    e.set_footer(text="React With ♻ For History")

    msg = await ctx.send(embed=e)
    ems = ["♻"]

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
        if not ctx.guild.me.guild_permissions.view_audit_log:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await msg.remove_reaction(reaction, user)
            err = "Missing view_audit_log permission(s)"
            if any(field.value == err for field in e.fields):
                continue
            e.add_field(name="◈ Role History", value=err, inline=False)
        else:
            e.set_footer()
            history = {}
            e.add_field(name="◈ Role History", value="Fetching..", inline=False)
            await msg.edit(embed=e)

            action = discord.AuditLogAction.role_create
            async for entry in ctx.guild.audit_logs(limit=500, action=action):
                if role.id == entry.target.id:
                    history["Creator"] = f"{entry.user}\n"
                    break

            action = discord.AuditLogAction.role_update
            async for entry in ctx.guild.audit_logs(limit=500, action=action):
                if role.id == entry.target.id and hasattr(entry.after, "name"):
                    minute = str(entry.created_at.minute)
                    if len(minute) == 1:
                        minute = "0" + minute
                    when = datetime.date(entry.created_at).strftime(
                        f"%m/%d/%Y %I:{minute}%p"
                    )
                    if not hasattr(entry.before, "name"):
                        if entry.before.name != role.name:
                            history[f"**Name Changed on {when}**"] = None
                            history[f"**Changed to:** `{entry.before.name}`\n"] = None
                    elif entry.before.name != entry.after.name:
                        history[f"**Name Changed on {when}**"] = None
                        history[f"**Old Name:** `{entry.before.name}`\n"] = None

            if not history:
                history["None Found"] = None
            e.set_field_at(
                index=len(e.fields) - 1,
                name="◈ Role History",
                value=ctx.bot.utils.format_dict(
                    dict(list(history.items())[:6])
                ),
                inline=False,
            )
            ems.remove("♻")
            return await msg.edit(embed=e)
        await msg.edit(embed=e)
