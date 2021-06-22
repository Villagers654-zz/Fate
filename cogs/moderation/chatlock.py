from discord.ext import commands
from os.path import isfile
from botutils import colors
import discord
import asyncio
import json


class ChatLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.toggle = {}
        if isfile("./data/userdata/chatlock.json"):
            with open("./data/userdata/chatlock.json", "r") as f:
                self.toggle = json.load(f)

    async def save_data(self):
        await self.bot.utils.save_json("./data/userdata/chatlock.json", self.toggle)

    def is_enabled(self, guild_id):
        return str(guild_id) in self.toggle

    @commands.group(
        name="chatlock",
        description="Deletes messages by users without the manage_messages permission",
    )
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def _chatlock(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            toggle = "disabled"
            channel = None
            if guild_id in self.toggle:
                toggle = "enabled"
                channel = ""
                for _id in self.toggle[guild_id]:
                    if not channel:
                        channel += f"{self.bot.get_channel(_id).name}"
                    else:
                        channel += f", {self.bot.get_channel(_id).name}"
            e = discord.Embed(color=colors.fate)
            e.set_author(name="| Chatlock", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = (
                "Deletes messages by users without the manage_messages permission"
            )
            if channel:
                e.set_footer(text=f"| Toggle: {toggle} | Channels: {channel}")
            await ctx.send(embed=e)

    @_chatlock.command(name="enable")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.toggle[guild_id] = []
        if ctx.channel.id in self.toggle[guild_id]:
            return await ctx.send("Chatlock is already enabled")
        self.toggle[guild_id].append(ctx.channel.id)
        await ctx.message.add_reaction("👍")
        await self.save_data()

    @_chatlock.command(name="disable")
    @commands.has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            return await ctx.send("Chatlock isn't enabled")
        if ctx.channel.id not in self.toggle[guild_id]:
            return await ctx.send("Chatlock isn't enabled in this channel")
        self.toggle[guild_id].pop(self.toggle[guild_id].index(ctx.channel.id))
        if len(self.toggle[guild_id]) < 1:
            del self.toggle[guild_id]
        await ctx.send("Disabled chatlock")
        await self.save_data()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if isinstance(m.guild, discord.Guild):
            if not m.author.bot:
                guild_id = str(m.guild.id)
                channel_id = m.channel.id
                if guild_id in self.toggle:
                    if channel_id in self.toggle[guild_id]:
                        perms = list(
                            perm for perm, value in m.author.guild_permissions if value
                        )
                        if "manage_messages" not in perms:
                            await asyncio.sleep(0.5)
                            await m.delete()


def setup(bot):
    bot.add_cog(ChatLock(bot))
