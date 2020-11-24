# Cog for managing case numbers in mod.py

from time import time

from discord.ext import commands
import discord


class CaseManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_case(self, guild_id: int, user_id: int, action: str, reason: str, created_by: int):
        async with self.bot.cursor() as cur:
            now = time()
            await cur.execute(
                f"insert into cases "
                f"values ("
                f"guild_id = {guild_id}, "
                f"user_id = {user_id}, "
                f"case_action = {action}, "
                f"reason = {reason}, "
                f"case_number = count(*) from cases where guild_id = {guild_id} + 1, "
                f"created_by = {created_by}, "
                f"created_at = {now}"
                f");"
            )
            await cur.execute(f"select case_number from cases where created_at = {now};")
            result = await cur.fetchone()
        return result[0][0]

    @commands.command(name="mod-logs", aliases=["mod_logs", "modlogs"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def mod_logs(self, ctx, *, args):
        guild_id = str(ctx.guild.id)

        # Get logs from a specific user
        if ctx.message.raw_mentions or args.isdigit():
            usr_id = ctx.message.raw_mentions[0] if ctx.message.raw_mentions else int(args)
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id} and user_id = {usr_id};"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for this server")
            lines = [
                f"#{i + 1}. {action} - from `{self.bot.get_user(created_by)}` - {reason}"
                for i, (user_id, action, reason, case_number, created_by, created_at) in enumerate(sorted(
                    results[:16], key=lambda kv: kv[5], reverse=True
                ))
            ]

        # Get mod logs with a specific reason
        elif args:
            query = f"%{args}%"
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id} and Keywords like {query};"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for this server")
            lines = [
                f"#{i + 1}. `{self.bot.get_user(user_id)}` - {action} - from `{self.bot.get_user(created_by)}` - {reason}"
                for i, (user_id, action, reason, case_number, created_by, created_at) in enumerate(sorted(
                    results[:16], key=lambda kv: kv[5], reverse=True
                ))
            ]

        # Get all the mod logs
        else:
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id};"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for this server")
            lines = [
                f"#{i + 1}. `{self.bot.get_user(user_id)}` - {action} - from `{self.bot.get_user(created_by)}` - {reason}"
                for i, (user_id, action, reason, case_number, created_by, created_at) in enumerate(sorted(
                    results[:16], key=lambda kv: kv[5], reverse=True
                ))
            ]

        e = discord.Embed(color=self.bot.theme_color)
        e.description = "\n".join(lines)[:2000]
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(CaseManager(bot))
