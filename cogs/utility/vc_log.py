from discord.ext import commands
from botutils import colors
from os.path import isfile
from time import time
import discord
import asyncio
import json


class VcLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/VcLog.json"
        self.channel = {}
        self.keep_clean = {}
        self.join_cd = {}
        self.leave_cd = {}
        self.move_cd = {}
        if isfile(self.path):
            with open(self.path, "r") as f:
                dat = json.load(f)
                if "channel" in dat:
                    self.channel = dat["channel"]
                if "keep_clean" in dat:
                    self.keep_clean = dat["keep_clean"]

    async def save_json(self):
        data = {"channel": self.channel, "keep_clean": self.keep_clean}
        await self.bot.save_json(self.path, data)

    async def ensure_permissions(self, guild_id, channel_id=None):
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                bot = channel.guild.get_member(self.bot.user.id)
                if channel.permissions_for(bot).send_messages:
                    return True
            return False
        channel = self.bot.get_channel(self.channel[guild_id])
        bot = channel.guild.get_member(self.bot.user.id)
        if guild_id in self.channel:
            if not channel:
                del self.channel[guild_id]
                await self.save_json()
                return False
            send_messages = channel.permissions_for(bot).send_messages
            manage_messages = channel.permissions_for(bot).manage_messages
            if not send_messages or not manage_messages:
                del self.channel[guild_id]
                await self.save_json()
                return False
        return True

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
            if str(ctx.guild.id) in self.channel:
                status = "Current Status: enabled"
            else:
                status = "Current Status: disabled"
            e.set_footer(text=status)
            await ctx.send(embed=e)

    @_vclog.command(name="enable")
    @commands.has_permissions(manage_channels=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send("Mention the channel I should use")
        msg = await self.bot.utils.wait_for_msg(ctx)
        if not msg.channel_mentions:
            return await ctx.send("That isn't a channel mention")
        channel_id = msg.channel_mentions[0].id
        channel_access = await self.ensure_permissions(guild_id, channel_id)
        if not channel_access:
            return await ctx.send("Sry, I don't have access to that channel")
        await ctx.send("Would you like me to delete all non vc-log messages?")
        async with self.bot.require("message", ctx, handle_timeout=True) as msg:
            reply = msg.content.lower()
        self.channel[guild_id] = channel_id
        channel_access = await self.ensure_permissions(guild_id)
        if not channel_access:
            del self.channel[guild_id]
            del self.keep_clean[guild_id]
            return await ctx.send(
                "Sry, I'm missing either manage message(s) or send message(s) permissions in there"
            )
        if "yes" in reply or "sure" in reply or "yep" in reply or "ye" in reply:
            self.keep_clean[guild_id] = "enabled"
            await ctx.send("Aight, i'll make sure it stays clean .-.")
        await ctx.send("Enabled VcLog")
        await self.save_json()

    @_vclog.command(name="disable")
    @commands.has_permissions(manage_channels=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.channel:
            return await ctx.send("VcLog isn't enabled")
        del self.channel[guild_id]
        if guild_id in self.keep_clean:
            del self.keep_clean[guild_id]
        await ctx.send("Disabled VcLog")
        await self.save_json()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if isinstance(msg.guild, discord.Guild):
            guild_id = str(msg.guild.id)
            if guild_id in self.keep_clean:
                if msg.channel.id == self.channel[guild_id]:
                    if msg.author.id == self.bot.user.id:
                        chars = [
                            "<:plus:548465119462424595>",
                            "❌",
                            "🔈",
                            "🔊",
                            "🚸",
                            "🎧",
                            "🎤",
                        ]
                        for x in chars:
                            if msg.content.startswith(x):
                                return
                    bot_has_permissions = await self.ensure_permissions(guild_id)
                    if bot_has_permissions:
                        await asyncio.sleep(20)
                        try:
                            await msg.delete()
                        except:
                            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        if guild_id in self.channel:
            channel = self.bot.get_channel(self.channel[guild_id])
            bot_has_permissions = await self.ensure_permissions(guild_id)
            if bot_has_permissions:
                user_id = str(member.id)
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
