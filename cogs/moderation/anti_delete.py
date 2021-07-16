"""
cogs.moderation.anti_delete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A cog for preventing users from deleting their messages
via resending it as a webhook replicating their profile

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from datetime import datetime, timedelta, timezone

from discord.ext import commands
import discord
from discord.errors import HTTPException, NotFound, Forbidden

from fate import Fate
from botutils import colors


action = discord.AuditLogAction.message_delete


class AntiDelete(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot

    @commands.group(name="anti-delete", aliases=["antidelete", "anti_delete"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(2, 5, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def anti_delete(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Anti Delete", icon_url=ctx.author.avatar.url)
            e.description = "Resend deleted messages as webhooks"
            p = ctx.prefix  # type: str
            e.add_field(
                name="◈ Usage",
                value=f"{p}anti-delete enable\n"
                      f"`enables in the channel you use it in`\n"
                      f"{p}anti-delete disable\n"
                      f"`disables in the channel you use it in`\n"
                      f"{p}anti-delete disable-all\n"
                      f"`disables all enabled channels`"
            )
            async with self.bot.utils.cursor() as cur:
                await cur.execute(f"select channel_id from anti_delete where guild_id = {ctx.guild.id};")
                results = await cur.fetchall()
                channels = []
                for channel_id in results:
                    channel = self.bot.get_channel(channel_id[0])
                    if channel:
                        channels.append(channel.mention)
                if channels:
                    e.add_field(
                        name="◈ Active In",
                        value=", ".join(channels)
                    )
            await ctx.send(embed=e)

    @anti_delete.command(name="enable")
    @commands.has_permissions(manage_messages=True, manage_webhooks=True)
    @commands.bot_has_permissions(manage_messages=True, manage_webhooks=True)
    async def _enable(self, ctx):
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from anti_delete where channel_id = {ctx.channel.id};")
            if cur.rowcount:
                return await ctx.send("This channel already has anti-delete enabled")
            await cur.execute(
                f"insert into anti_delete values ({ctx.guild.id}, {ctx.channel.id})"
            )
        await ctx.send(f"Enabled anti-delete in {ctx.channel.mention}")

    @anti_delete.command(name="disable")
    @commands.has_permissions(manage_messages=True, manage_webhooks=True)
    @commands.bot_has_permissions(manage_messages=True, manage_webhooks=True)
    async def _disable(self, ctx):
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from anti_delete where channel_id = {ctx.channel.id};")
            if not cur.rowcount:
                return await ctx.send("This channel doesn't have anti-delete enabled")
            await cur.execute(f"delete from anti_delete where channel_id = {ctx.channel.id};")
        await ctx.send("Disabled anti-delete")

    @anti_delete.command(name="disable-all", aliases=["disableall"])
    @commands.has_permissions(manage_messages=True, manage_webhooks=True)
    @commands.bot_has_permissions(manage_messages=True, manage_webhooks=True)
    async def _disable_all(self, ctx):
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from anti_delete where guild_id = {ctx.guild.id};")
            if not cur.rowcount:
                return await ctx.send("This server doesn't have anti-delete enabled anywhere")
            await cur.execute(f"delete from anti_delete where guild_id = {ctx.guild.id};")
        await ctx.send("Disabled anti-delete in all channels")

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if not isinstance(msg.author, discord.Member) or not msg.content:
            return
        async with self.bot.utils.cursor() as cur:
            await cur.execute(f"select * from anti_delete where channel_id = {msg.channel.id};")
            if cur.rowcount:
                print("Enabled")
                after = datetime.now(tz=timezone.utc) - timedelta(seconds=3)
                try:
                    async for entry in msg.guild.audit_logs(limit=1, action=action):
                        if entry.created_at > after:
                            return
                    webhook = await msg.channel.create_webhook(name=msg.author.display_name)
                    await webhook.send(
                        content=msg.content,
                        avatar_url=msg.author.avatar.url,
                        username=msg.author.display_name,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                    await webhook.delete()
                except (NotFound, Forbidden, HTTPException):
                    await cur.execute(f"delete from anti_delete where channel_id = {msg.channel.id};")


def setup(bot: Fate):
    bot.add_cog(AntiDelete(bot))
