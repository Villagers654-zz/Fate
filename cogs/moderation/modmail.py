
import json
from time import time

from discord.ext import commands
import discord


class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="modmail", aliases=["mod-mail", "mod_mail"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def modmail(self, ctx):
        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name="Modmail", icon_url=self.bot.user.avatar_url)
        e.set_thumbnail(url="https://opal.place/public/captures/716209.png")
        await ctx.send(embed=e)

    @modmail.command(name="enable")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx):
        await ctx.send("What's the category ID I should use for modmail")
        async with self.bot.require("message", ctx) as msg:
            if not msg.content.isdigit():
                return await ctx.send("That's not a category ID. Rerun the command >:(")
            category_id = int(msg.content)
        channel = self.bot.get_channel(category_id)
        if not isinstance(channel, discord.CategoryChannel):
            return await ctx.send("I can't find a category with that ID. Rerun the command to try again")
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"insert into modmail "
                f"values ({ctx.guild.id}, {category_id}, '{self.bot.encode(json.dumps([]))}') "
                f"on duplicate key update channel_id = {category_id};"
            )
        await ctx.send(f"Set the modmail category to {channel}")

    @modmail.command(name="disable")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        async with self.bot.cursor() as cur:
            await cur.execute(f"delete from modlogs where guild_id = {ctx.guild.id} limit 1;")
        await ctx.send("Disabled modmail if it was enabled")

    @modmail.command(name="block")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def block(self, ctx, user: discord.User):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select blocked from modmail where guild_id = {ctx.guild.id} limit 1;")
            result = await cur.fetchone()
            if not result:
                return await ctx.send("Modmail isn't enabled in this server")
            blocked = json.loads(self.bot.decode(result[0]))
            if user.id in blocked:
                return await ctx.send(f"{user} is already blocked from using modmail")
            blocked.append(user.id)
            await cur.execute(
                f"update modmail "
                f"set blocked = {self.bot.encode(json.dumps(blocked))} "
                f"where guild_id = {ctx.guild.id};"
            )
        await ctx.send(f"Blocked {user} from using modmail")

    @modmail.command(name="unblock")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unblock(self, ctx, user: discord.User):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select blocked from modmail where guild_id = {ctx.guild.id} limit 1;")
            result = await cur.fetchone()
            if not result:
                return await ctx.send("Modmail isn't enabled in this server")
            blocked = json.loads(self.bot.decode(result[0]))
            if user.id not in blocked:
                return await ctx.send(f"{user} isn't blocked from using modmail")
            blocked.remove(user.id)
            await cur.execute(
                f"update modmail "
                f"set blocked = {self.bot.encode(json.dumps(blocked))} "
                f"where guild_id = {ctx.guild.id};"
            )
        await ctx.send(f"Unblocked {user} from using modmail")

    @commands.command(name="reply")
    @commands.dm_only()
    async def reply(self, ctx, case_number: int = None):
        async with self.bot.cursor() as cur:
            if case_number:
                await cur.execute(
                    f"select guild_id, case_number, reason from cases "
                    f"where case_number = {case_number};"
                )
                results = await cur.fetchall()
            else:
                await cur.execute(
                    f"select guild_id, case_number, reason from cases "
                    f"where user_id = {ctx.author.id} "
                    f"and created_at > {time() - 60 * 60 * 24 * 14};"
                )
                results = await cur.fetchall()
        if not results:
            if case_number:
                return await ctx.send("Couldn't find any cases for you with that case number")
            p = self.bot.utils.get_prefix(ctx)  # type: str
            return await ctx.send(
                f"Couldn't find any cases from you from within the last 14 days. "
                f"Use `{p}reply [case_number]` to specify which"
            )
        await ctx.send("This part of the command isn't developed yet")

    @commands.command(name="close")
    async def close(self, ctx):
        pass


def setup(bot):
    bot.add_cog(ModMail(bot))
