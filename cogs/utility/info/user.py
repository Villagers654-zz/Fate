"""
cogs.utility.info.user
~~~~~~~~~~~~~~~~~~~~~~~

A coroutine function for generating a users profile embed

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from time import time
import asyncio

import discord

from botutils import colors, get_time, emojis


async def fetch_user_info(ctx, user):
    """|coro| generates a profile embed for a user"""
    e = discord.Embed(color=colors.fate)
    e.set_author(
        name="Here's what I got on them..", icon_url=ctx.bot.user.avatar.url
    )
    e.set_thumbnail(url=user.avatar.url)
    e.description = ""

    # Whether or not to hide information from other servers
    has_public_profile = True
    utility = ctx.bot.cogs["Utility"]
    if user.id in utility.settings:
        if not utility.settings[user.id]["public"]:
            has_public_profile = False

    # User Information
    guilds = []
    nicks = []
    if has_public_profile:
        guilds = user.mutual_guilds
        for guild in guilds:
            await asyncio.sleep(0)
            if guild and user in guild.members:
                member = guild.get_member(user.id)
                if member.display_name != user.display_name:
                    nicks = list(set(list([member.display_name, *nicks])))
    user_info = {
        "Profile": f"{user.mention}",
        "ID": user.id,
        "Created at": user.created_at.strftime("%m/%d/%Y %I%p"),
        "Shared Servers": str(len(guilds))
    }
    if nicks:
        user_info["Nicks"] = ", ".join(nicks[:5])

    # Member Information
    member_info = {}
    if isinstance(user, discord.Member):
        user_info["Profile"] = f"{user.mention}"

        if user.name != user.display_name:
            member_info["Display Name"] = user.display_name
        if user.activity:
            member_info["Activity"] = user.activity.name
        member_info["Top Role"] = user.top_role.mention

        text = len([
            c for c in ctx.guild.text_channels
            if c.permissions_for(user).read_messages
        ])
        voice = len([
            c for c in ctx.guild.voice_channels
            if c.permissions_for(user).read_messages
        ])

        notable = [
            "view_audit_log",
            "manage_roles",
            "manage_channels",
            "manage_emojis",
            "kick_members",
            "ban_members",
            "manage_messages",
            "mention_everyone",
        ]
        member_info["Access"] = f"{emojis.text_channel} {text} {emojis.voice_channel} {voice}"
        if any(k in notable and v for k, v in list(user.guild_permissions)):
            perms = [k for k, v in user.guild_permissions if k in notable and v]
            perms = (
                ["administrator"]
                if user.guild_permissions.administrator
                else perms
            )
            member_info["Notable Perms"] = f"`{', '.join(perms)}`"

        # Bot Information
        if user.bot:  # search the audit log to see who invited the bot
            inviter = "Unknown"
            if ctx.guild.me.guild_permissions.view_audit_log:
                async for entry in ctx.guild.audit_logs(limit=250, action=discord.AuditLogAction.bot_add):
                    if entry.target and entry.target.id == user.id:
                        inviter = entry.user
                        break
            user_info["Inviter"] = inviter

    # Activity Information
    activity_info = {}
    if guilds:
        user = guilds[0].get_member(user.id)  # type: discord.Member
        async with ctx.bot.utils.cursor() as cur:
            if user.status is discord.Status.offline:
                await cur.execute(
                    f"select format(last_online, 3) from activity "
                    f"where user_id = {user.id} "
                    f"and last_online is not null "
                    f"limit 1;"
                )
                if cur.rowcount:
                    r = await cur.fetchone()
                    if r and hasattr(r[0], "replace"):
                        seconds = round(time() - float(r[0].replace(',', '')))
                        activity_info["Last Online"] = f"{get_time(seconds)} ago"
                    else:
                        activity_info["Last Online"] = "Unknown"
                else:
                    activity_info["Last Online"] = "Unknown"
            await cur.execute(
                f"select format(last_message, 3) from activity "
                f"where user_id = {user.id} "
                f"and last_message is not null "
                f"limit 1;"
            )
            if cur.rowcount:
                r = await cur.fetchone()
                if r and hasattr(r[0], "replace"):
                    seconds = round(time() - float(r[0].replace(',', '')))
                    activity_info["Last Msg"] = f"{get_time(seconds)} ago"
                else:
                    activity_info["Last Msg"] = "Unknown"
            else:
                activity_info["Last Msg"] = "Unknown"

    if isinstance(user, discord.Member):
        if user.status is discord.Status.online:
            if user.is_on_mobile():
                activity_info["Active on Mobile 📱"] = None
            else:
                activity_info["Active on PC 🖥"] = None

    # Username history
    if has_public_profile:
        async with ctx.bot.utils.cursor() as cur:
            await cur.execute(f"select username from usernames where user_id = {user.id};")
            if cur.rowcount:
                results = await cur.fetchall()
                decoded_results = [ctx.bot.decode(r[0]) for r in results]
                names = [name for name in decoded_results if name != str(user)]
                if names:
                    user_info["Usernames"] = ",".join(names)

    e.description += (
        f"◈ User Information{ctx.bot.utils.format_dict(user_info)}\n\n"
    )
    if member_info:
        e.description += (
            f"◈ Member Information{ctx.bot.utils.format_dict(member_info)}\n\n"
        )
    if activity_info:
        e.description += f"◈ Activity Information{ctx.bot.utils.format_dict(activity_info)}\n\n"
    return e
