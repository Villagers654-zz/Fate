# Cog for managing case numbers in mod.py

from time import time
import asyncio

from discord.ext import commands
import discord


class CaseManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_case(self, guild_id: int, user_id: int, action: str, reason: str, created_by: int):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select count(*) from cases where guild_id = {guild_id}")
            results = await cur.fetchone()
            case_number = results[0] + 1
            now = time()
            await cur.execute(
                f"insert into cases "
                f"values ("
                f"{guild_id}, "
                f"{user_id}, "
                f"'{action}', "
                f"'{reason}', "
                f"{case_number}, "
                f"{created_by}, "
                f"{now}"
                f");"
            )
        return case_number

    @commands.command(name="mod-logs", aliases=["mod_logs", "modlogs"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def mod_logs(self, ctx, *, args = None):
        guild_id = str(ctx.guild.id)

        # Get logs from a specific user
        if ctx.message.raw_mentions or (args.isdigit() if args else False):
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
                f"#{case_number}. {action} - from `{self.bot.get_user(created_by)}` - {reason}"
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
                    f"from cases where guild_id = {guild_id} and reason like '{query}';"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for this server")
            lines = [
                f"#{case_number}. `{self.bot.get_user(user_id)}` - {action} - from `{self.bot.get_user(created_by)}` - {reason}"
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
                f"#{case_number}. `{self.bot.get_user(user_id)}` - {action} - from `{self.bot.get_user(created_by)}` - {reason}"
                for i, (user_id, action, reason, case_number, created_by, created_at) in enumerate(sorted(
                    results[:16], key=lambda kv: kv[5], reverse=True
                ))
            ]

        embeds = []
        e = discord.Embed(color=self.bot.theme_color)
        e.set_author(name="Mod Logs", icon_url=ctx.guild.icon_url)
        e.description = ""
        for i, line in enumerate(lines):
            if i != 0 and i % 14 == 0:
                embeds.append(e)
                e = discord.Embed(color=self.bot.theme_color)
                e.set_author(name="Mod Logs", icon_url=ctx.guild.icon_url)
                e.description = ""
            e.description += f"\n{line}"
            if i + 1 == len(lines):
                embeds.append(e)

        if len(embeds) == 1:
            await ctx.send(embed=e)
            return None

        async def wait_for_reaction():
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=lambda r, u: u == ctx.author
                )
            except asyncio.TimeoutError:
                return [None, None]
            else:
                return [reaction, str(reaction.emoji)]

        def index_check(index):
            """ Ensures the index isn't too high or too low """
            if index > len(embeds) - 1:
                index = len(embeds) - 1
            if index < 0:
                index = 0
            return index

        async def add_emojis_task():
            """ So the bot can read reactions before all are added """
            for emoji in emojis:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.5)
            return

        index = 0
        emojis = ["🏡", "⏪", "⏩"]
        embeds[0].set_footer(
            text=f"Page {index + 1}/{len(embeds)}"
        )
        msg = await ctx.send(embed=embeds[0])
        self.bot.loop.create_task(add_emojis_task())

        while True:
            reaction, emoji = await wait_for_reaction()
            if not reaction:
                return await msg.clear_reactions()

            if emoji == emojis[0]:  # home
                index = 0

            if emoji == emojis[1]:
                index -= 1

            if emoji == emojis[2]:
                index += 1
                index = index_check(index)

            if index > len(embeds) - 1:
                index = len(embeds) - 1

            if index < 0:
                index = 0

            embeds[index].set_footer(
                text=f"Page {index + 1}/{len(embeds)}"
            )
            await msg.edit(embed=embeds[index])
            self.bot.loop.create_task(msg.remove_reaction(reaction, ctx.author))



def setup(bot):
    bot.add_cog(CaseManager(bot))
