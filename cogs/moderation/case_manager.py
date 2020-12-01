# Cog for managing case numbers in mod.py

from time import time
import asyncio

from discord.ext import commands
import discord


class CaseManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_case(self, guild_id: int, user_id, action: str, reason, link: str, created_by):
        if reason:
            reason = self.bot.encode(reason)
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select case_number from cases "
                f"where guild_id = {guild_id} "
                f"order by case_number desc "
                f"limit 1;"
            )
            results = await cur.fetchone()
            if results:
                case_number = results[0] + 1
            else:
                case_number = 1
            now = time()
            q = "'"
            sql = f"insert into cases " \
                  f"values (" \
                  f"{guild_id}, " \
                  f"{f'{q}{user_id}{q}' if user_id else 'null'}, " \
                  f"'{action}', " \
                  f"{f'{q}{reason}{q}' if reason else 'null'}, " \
                  f"'{link}', " \
                  f"{case_number}, " \
                  f"{f'{q}{created_by}{q}' if created_by else 'null'}, " \
                  f"{now}" \
                  f");"
            await cur.execute(
                sql
            )
        return case_number

    @commands.command(name="mod-logs", aliases=["mod_logs", "modlogs"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def mod_logs(self, ctx, *, args = None):
        guild_id = str(ctx.guild.id)
        has_value = lambda value: value and value != "None" and value != "Unspecified"
        any_large = lambda values: any(len(str(self.bot.get_user(v))) > 10 for v in values)
        nl = "\n"

        # Get logs from a specific user
        if ctx.message.raw_mentions or (args.isdigit() if args else False):
            usr_id = ctx.message.raw_mentions[0] if ctx.message.raw_mentions else int(args)
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, link, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id} and user_id = {usr_id} order by case_number desc;"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for that user")
            lines = [
                f"#{case_number}. [{action}]({link}) - from `{self.bot.get_user(created_by)}`" \
                f"{f'{nl}> {self.bot.decode(reason)}' if reason else ''}"
                for i, (user_id, action, reason, link, case_number, created_by, created_at) in enumerate(
                    results[:16]
                )
            ]

        # Get mod logs with a specific reason
        elif args:
            query = f"%{args}%"
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, link, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id} and reason like '{query}' order by case_number desc;"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs for that reason")
            lines = [
                f"#{case_number}. {f'`{self.bot.get_user(user_id)}` - ' if user_id else ''}" \
                f"[{action}]({link}){f' - from `{self.bot.get_user(created_by)}`' if created_by else ''}" \
                f"{f'{nl}> {self.bot.decode(reason)}' if reason else ''}"
                for i, (user_id, action, reason, link, case_number, created_by, created_at) in enumerate(
                    results[:16]
                )
            ]

        # Get all the mod logs
        else:
            async with self.bot.cursor() as cur:
                await cur.execute(
                    f"select user_id, case_action, reason, link, case_number, created_by, created_at "
                    f"from cases where guild_id = {guild_id} order by case_number desc;"
                )
                results = await cur.fetchall()
            if not results:
                return await ctx.send("There are no mod logs in this server")

            lines = [
                f"**Case #{case_number}.** {f'**`{str(self.bot.get_user(user_id))}`** - ' if user_id else ''}" \
                f"[{action}]({link}){f' - from **{self.bot.get_user(created_by)}**' if created_by else ''}" \
                f"\n> `{self.bot.decode(reason) if reason else 'unspecified reason'}`"
                # f"{f'{nl}> `{reason}`' if has_value(reason) else nl}"
                for i, (user_id, action, reason, link, case_number, created_by, created_at) in enumerate(
                    results[:16]
                )
            ]

        embeds = []
        e = discord.Embed(color=self.bot.theme_color)
        e.set_author(name="Moderation Logs", icon_url=ctx.guild.icon_url)
        e.description = ""
        for i, line in enumerate(lines):
            if i != 0 and i % 9 == 0:
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

    @commands.command(name="del-log", aliases=["del_log", "dellog", "del-modlog"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def del_log(self, ctx, case_number: int):
        guild_id = str(ctx.guild.id)
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select case_number from cases "
                f"where guild_id = {guild_id} "
                f"and case_number = {case_number} "
                f"limit 1;"
            )
            results = await cur.fetchone()
            if not results:
                return await ctx.send("There is no case by that number")
            await cur.execute(
                f"delete from cases "
                f"where guild_id = {guild_id} "
                f"and case_number = {case_number} "
                f"limit 1;"
            )
        await ctx.send(f"Deleted case #{case_number}")


def setup(bot):
    bot.add_cog(CaseManager(bot))
