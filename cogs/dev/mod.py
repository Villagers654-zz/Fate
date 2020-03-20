import asyncio

from discord.ext import commands
import discord
from discord.ext.commands import Greedy

from utils import colors


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(embed_links=True, ban_members=True)
    async def ban(
        self,
        ctx,
        ids: Greedy[int],
        users: Greedy[discord.User],
        *,
        reason="Unspecified",
    ):
        """ Ban cmd that supports more than just members """
        users_to_ban = len(ids) + len(users)
        e = discord.Embed(color=colors.fate())
        e.set_author(
            name=f"Banning {users_to_ban} user{'' if users_to_ban > 1 else ''}",
            icon_url=ctx.author.avatar_url,
        )
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif"
        )
        msg = await ctx.send(embed=e)
        for id in ids:
            member = ctx.guild.get_member(id)
            if isinstance(member, discord.Member):
                if member.top_role.position >= ctx.author.top_role.position:
                    if users_to_ban == 1:
                        return await ctx.send(
                            f"That users above your paygrade, take a seat"
                        )
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="This users is above your paygrade",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    if users_to_ban == 1:
                        return await ctx.send(f"I can't ban that user")
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="I can't ban this user",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
            try:
                user = await self.bot.fetch_user(id)
            except:
                if users_to_ban == 1:
                    return await ctx.send(f"That user doesn't exist")
                e.add_field(
                    name=f"◈ Failed to ban {id}",
                    value="That user doesn't exist",
                    inline=False,
                )
            else:
                await ctx.guild.ban(user, reason=reason)
                if users_to_ban == 1:
                    return await ctx.send(f"Banned {member}")
                e.add_field(
                    name=f"◈ Banned {user}", value=f"Reason: {reason}", inline=False
                )
            await msg.edit(embed=e)
        for user in users:
            member = discord.utils.get(ctx.guild.members, id=user.id)
            if member:
                if member.top_role.position >= ctx.author.top_role.position:
                    if users_to_ban == 1:
                        return await ctx.send(
                            f"That users above your paygrade, take a seat"
                        )
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="This users is above your paygrade",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    if users_to_ban == 1:
                        return await ctx.send(f"I can't ban that user")
                    e.add_field(
                        name=f"◈ Failed to ban {member}",
                        value="I can't ban this user",
                        inline=False,
                    )
                    await msg.edit(embed=e)
                    continue
            await ctx.guild.ban(user)
            if users_to_ban == 1:
                return await ctx.send(f"Banned {user}")
            e.add_field(
                name=f"◈ Banned {user}", value=f"Reason: {reason}", inline=False
            )


def setup(bot):
    bot.add_cog(Moderation(bot))
