from discord.ext import commands
from os.path import isfile
from contextlib import suppress
from botutils import colors
import discord
from discord.errors import NotFound, Forbidden
import json


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles = {}
        if isfile("./data/userdata/autorole.json"):
            with open("./data/userdata/autorole.json", "r") as infile:
                dat = json.load(infile)
                if "roles" in dat:
                    self.roles = dat["roles"]

    async def save_data(self):
        await self.bot.utils.save_json("./data/userdata/autorole.json", {"roles": self.roles})

    def is_enabled(self, guild_id):
        return str(guild_id) in self.roles

    @commands.command(
        name="autorole", description="Adds x roles to a user when they join"
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def _autorole(self, ctx, item: commands.clean_content = None):
        item = item  # type: str
        guild_id = str(ctx.guild.id)
        e = discord.Embed(color=colors.fate)
        if item is None:
            e.set_author(name="Auto-Role Help", icon_url=self.bot.user.avatar_url)
            e.set_thumbnail(url=ctx.author.avatar_url)
            e.add_field(
                name="◈ Usage ◈",
                value=".autorole {role}\n" ".autorole list\n" ".autorole clear",
                inline=False,
            )
            return await ctx.send(embed=e)
        if item.lower() == "clear":
            if guild_id not in self.roles:
                return await ctx.send("Auto role is not active")
            del self.roles[guild_id]
            await self.save_data()
            return await ctx.send("Cleared list of roles")
        if item.lower() == "list":
            if guild_id not in self.roles:
                return await ctx.send("Auto role is not active")
            e.set_author(name="Auto Roles", icon_url=self.bot.user.avatar_url)
            e.description = ""
            for role_id in self.roles[guild_id]:
                role = ctx.guild.get_role(role_id)
                if not role:
                    self.roles[guild_id].remove(role_id)
                    await self.save_data()
                    continue
                e.description += f"• {role.name}\n"
            return await ctx.send(embed=e)
        item = item.replace("@", "").lower()
        if guild_id not in self.roles:
            self.roles[guild_id] = []
        for role in ctx.message.role_mentions:
            if ctx.author.id != ctx.guild.owner.id:
                if role.position > ctx.author.top_role.position:
                    return await ctx.send("That roles above your paygrade, take a seat")
                if role.id in self.roles[guild_id]:
                    return await ctx.send("That roles already in use")
            self.roles[guild_id].append(role.id)
            await self.save_data()
            return await ctx.send(f"Added `{role.name}` to the list of auto roles")
        for role in ctx.guild.roles:
            if item == role.name.lower():
                if role.position > ctx.author.top_role.position:
                    return await ctx.send("That roles above your paygrade, take a seat")
                if role.id in self.roles[guild_id]:
                    return await ctx.send("That roles already in use")
                self.roles[guild_id].append(role.id)
                await self.save_data()
                return await ctx.send(f"Added `{role.name}` to the list of auto roles")
        for role in ctx.guild.roles:
            if item in role.name.lower():
                if role.position > ctx.author.top_role.position:
                    return await ctx.send("That roles above your paygrade, take a seat")
                if role.id in self.roles[guild_id]:
                    return await ctx.send("That roles already in use")
                self.roles[guild_id].append(role.id)
                await self.save_data()
                return await ctx.send(f"Added `{role.name}` to the list of auto roles")
        await ctx.send("Role not found")

    @commands.Cog.listener()
    async def on_member_join(self, m: discord.Member):
        guild_id = str(m.guild.id)
        if guild_id in self.roles:
            if not m.guild.me.guild_permissions.manage_roles:
                try:
                    dm = m.guild.owner.dm_channel
                    if not dm:
                        dm = await m.guild.owner.create_dm()
                    history = await dm.history(limit=1).flatten()
                    if history and "AutoRole" in history[0].content:
                        return
                except (Forbidden, NotFound, AttributeError):
                    return
                try:
                    await m.guild.owner.send(
                        f"**[AutoRole - {m.guild.name}] I'm missing manage_roles permissions "
                        f"in order to add roles to new users"
                    )
                except (Forbidden, NotFound, AttributeError):
                    pass
                return
            for role_id in self.roles[guild_id]:
                role = m.guild.get_role(role_id)
                if not role:
                    self.roles[guild_id].remove(role_id)
                    await self.save_data()
                    continue
                if role.position >= m.guild.me.top_role.position:
                    try:
                        await m.guild.owner.send(
                            f"**[AutoRole - {m.guild.name}] can't add {role.name} to user. "
                            f"Its position is higher than mine. You'll need to re-add it"
                        )
                    except discord.errors.Forbidden:
                        pass
                    self.roles[guild_id].remove(role_id)
                else:
                    try:
                        await m.add_roles(role)
                    except discord.errors.NotFound:
                        pass

    @commands.Cog.listener()
    async def on_role_delete(self, role):
        guild_id = str(role.guild.id)
        if role.id in self.roles[guild_id]:
            self.roles[guild_id].pop(self.roles[guild_id].index(role.id))
            await self.save_data()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_id = str(guild.id)
        if guild_id in self.roles:
            del self.roles[guild_id]
            await self.save_data()


def setup(bot):
    bot.add_cog(AutoRole(bot))
