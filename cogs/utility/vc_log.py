from time import time
import discord
import asyncio
from discord.ext import commands
from botutils import colors
from discord.http import DiscordServerError


class VcLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/VcLog.json"
        self.config = bot.utils.cache("vclog")
        self.join_cd = {}
        self.leave_cd = {}
        self.move_cd = {}

    @commands.group(name="vc-log", aliases=["vclog"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def _vclog(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Vc Logger", icon_url=ctx.author.avatar_url)
            if ctx.guild.icon_url:
                e.set_thumbnail(url=ctx.guild.icon_url)
            else:
                e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = "Logs actions in vc to a dedicated channel"
            e.add_field(
                name="◈ Usage ◈", value=".vclog enable\n.vclog disable", inline=False
            )
            toggle = "Enabled" if ctx.guild.id in self.config else "Disabled"
            e.set_footer(text=f"Current Status: {toggle}")
            await ctx.send(embed=e)

    @_vclog.command(name="enable")
    @commands.has_permissions(manage_channels=True)
    async def _enable(self, ctx):
        await ctx.send("Mention the channel I should use")
        msg = await self.bot.utils.get_message(ctx)
        if not msg.channel_mentions:
            return await ctx.send("That isn't a channel mention")
        channel = msg.channel_mentions[0]
        perms = channel.permissions_for(ctx.guild.me)
        if not perms.send_messages:
            return await ctx.send("I don't have access to that channel")
        await ctx.send("Would you like me to delete all non vc-log messages?")
        msg = await self.bot.utils.get_message(ctx)
        keep_clean = True if "yes" in msg.content.lower() else False
        if keep_clean and not perms.manage_messages:
            return await ctx.send("I'm missing manage_message permissions in the channel")
        if keep_clean:
            await ctx.send("Aight, i'll make sure it stays clean .-.")
        self.config[ctx.guild.id] = {
            "channel": channel.id,
            "keep_clean": keep_clean
        }
        await self.config.flush()
        await ctx.send("Enabled VcLog")

    @_vclog.command(name="disable")
    @commands.has_permissions(manage_channels=True)
    async def _disable(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("VcLog isn't enabled")
        self.config.remove(guild_id)
        await ctx.send("Disabled VcLog")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild and msg.author.id != self.bot.user.id:
            guild_id = msg.guild.id
            if guild_id in self.config and self.config[guild_id]["keep_clean"]:
                if msg.channel.id == self.config[guild_id]["channel"]:
                    if not msg.channel.permissions_for(msg.guild.me).manage_messages:
                        self.config.remove(guild_id)
                        return await self.config.flush()
                    await asyncio.sleep(20)
                    if not msg.channel.permissions_for(msg.guild.me).manage_messages:
                        return self.config.remove(guild_id)
                    ignored = (
                        discord.errors.NotFound,
                        discord.errors.Forbidden,
                        discord.errors.HTTPException
                    )
                    try:
                        await msg.delete()
                    except ignored:
                        pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = member.guild.id
        if guild_id in self.config:
            channel = self.bot.get_channel(self.config[guild_id]["channel"])
            if not channel:
                ignored = (
                    discord.errors.HTTPException,
                    DiscordServerError
                )
                handled = (
                    discord.errors.NotFound,
                    discord.errors.Forbidden
                )
                try:
                    channel = await self.bot.fetch_channel(self.config[guild_id]["channel"])
                except ignored:
                    return
                except handled:
                    self.config.remove(guild_id)
                    return await self.config.flush()
            if not channel.permissions_for(member.guild.me).send_messages:
                self.config.remove(guild_id)
                return await self.config.flush()

            user_id = member.id
            if not before.channel:
                if guild_id not in self.join_cd:
                    self.join_cd[guild_id] = {}
                if user_id not in self.join_cd[guild_id]:
                    self.join_cd[guild_id][user_id] = 0
                if self.join_cd[guild_id][user_id] < time():
                    await channel.send(
                        f"<:plus:548465119462424595> **{member.display_name} joined {after.channel.name}**"
                    )
                    self.join_cd[guild_id][user_id] = time() + 10
                    return

            elif not after.channel:
                if guild_id not in self.leave_cd:
                    self.leave_cd[guild_id] = {}
                if user_id not in self.leave_cd[guild_id]:
                    self.leave_cd[guild_id][user_id] = 0
                if self.leave_cd[guild_id][user_id] < time():
                    await channel.send(
                        f"❌ **{member.display_name} left {before.channel.name}**"
                    )
                    self.leave_cd[guild_id][user_id] = time() + 10
                    return

            elif before.channel.id != after.channel.id:
                now = int(time() / 10)
                if guild_id not in self.move_cd:
                    self.move_cd[guild_id] = {}
                if user_id not in self.move_cd[guild_id]:
                    self.move_cd[guild_id][user_id] = [now, 0]
                if self.move_cd[guild_id][user_id][0] == now:
                    self.move_cd[guild_id][user_id][1] += 1
                else:
                    self.move_cd[guild_id][user_id] = [now, 0]
                if self.move_cd[guild_id][user_id][1] > 2:
                    return
                return await channel.send(
                    f"🚸 **{member.display_name} moved to {after.channel.name}**"
                )

            elif before.mute is False and after.mute is True:
                return await channel.send(f"🔈 **{member.display_name} was muted**")
            elif before.mute is True and after.mute is False:
                return await channel.send(
                    f"🔊 **{member.display_name} was unmuted**"
                )
            elif before.deaf is False and after.deaf is True:
                return await channel.send(
                    f"🎧 **{member.display_name} was deafened**"
                )
            elif before.deaf is True and after.deaf is False:
                await channel.send(f"🎤 **{member.display_name} was undeafened**")


def setup(bot):
    bot.add_cog(VcLog(bot))
