"""
cogs.utility.info.invite
~~~~~~~~~~~~~~~~~~~~~~~~~

A coroutine function for generating an invites information embed

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import discord
from botutils import colors


async def fetch_invite_info(ctx):
    e = discord.Embed(color=colors.fate)
    e.set_author(
        name="Alright, here's what I got..", icon_url=ctx.bot.user.avatar.url
    )
    inv = [arg for arg in ctx.message.content.split() if "discord.gg" in arg][0]
    code = discord.utils.resolve_invite(inv)
    try:
        invite = await ctx.bot.fetch_invite(code)
        e.set_author(
            name="Alright, here's what I got..", icon_url=invite.guild.icon.url
        )
        if invite.guild.splash:
            e.set_thumbnail(url=invite.guild.splash.url)
        if invite.guild.bannner:
            e.set_image(url=invite.guild.banner.url)
        data = {
            "Guild": invite.guild.name,
            "GuildID": invite.guild.id,
            "channel_name": invite.channel.name,
            "channel_id": invite.channel.id
        }
    except (discord.errors.NotFound, discord.errors.Forbidden):
        async with ctx.bot.utils.cursor() as cur:
            await cur.execute(
                f"select guild_id, guild_name, channel_id, channel_name "
                f"from invites "
                f"where code = {ctx.bot.encode(code)};"
            )
            if not cur.rowcount:
                return await ctx.send("Failed to query that invite")
            results = await cur.fetchone()
            data = {
                "guild_name": ctx.bot.decode(results[1]),
                "guild_id": results[0],
                "channel_name": ctx.bot.decode(results[3]),
                "channel_id": results[2],
            }
            e.set_footer(text="⚠ From Cache ⚠")

    inviters = []

    e.add_field(
        name="◈ Invite Information",
        value=ctx.bot.utils.format_dict(data),
        inline=False,
    )
    if inviters:
        e.add_field(
            name="◈ Inviters", value=", ".join(inviters[:16]), inline=False
        )

    return e
