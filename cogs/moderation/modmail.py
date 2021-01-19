
import json
from time import time
from contextlib import suppress
import asyncio

from discord.ext import commands
import discord
from discord.errors import NotFound, Forbidden


class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="modmail", aliases=["mod-mail", "mod_mail"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def modmail(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Modmail", icon_url=self.bot.user.avatar_url)
            p = self.bot.utils.get_prefix(ctx)  # type: str
            e.add_field(
                name="◈ Usage",
                value=f"  {p}modmail enable"
                      f"\n`helps you set a category`"
                      f"\n{p}modmail disable"
                      f"\n`disables modmail`"
                      f"\n{p}modmail block [user_id]"
                      f"\n`blocks a user from using modmail`"
                      f"\n{p}modmail unblock [user_id]"
                      f"\n`unblocks a user from using modmail`"
                      f"\n{p}reply [case_number]"
                      f"\n`send modmail for appeals etc`"
                      f"\n{p}close-thread"
                      f"\n`closes a modmail channel`",
                inline=False
            )
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

    async def mod_reply(self, ctx, msg):
        case_number = int(msg.channel.name.replace("case-", ""))
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select user_id "
                f"from cases "
                f"where guild_id = {msg.guild.id} "
                f"and case_number = {case_number};"
            )
            result = await cur.fetchone()
            if result:
                user_id = result[0]
            else:
                await msg.channel.send("Can't find the case for this thread")
                return None
            user = self.bot.get_user(user_id)
            if not user:
                await msg.channel.send(
                    f"I no longer share any servers with this user, therefore cannot dm them"
                )
                return None

            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name=f"Case #{case_number} in {msg.guild}", icon_url=msg.guild.icon_url)
            e.description = f"Reply from {msg.author}"
            if msg.content:
                e.add_field(
                    name="◈ Message",
                    value=msg.content[:1024],
                    inline=False
                )
            if msg.attachments:
                e.set_image(url=msg.attachments[0].url)
            e.set_footer(text=f"Use .reply {case_number} to make a reply")
            user = self.bot.get_user(user_id)
            if not user:
                await msg.channel.send(f"I no longer share any servers with this user, therefore cannot dm them")
                return None
            try:
                await user.send(embed=e)
            except Forbidden:
                await msg.channel.send(
                    "Failed to reply to the user. Either their dms are closed "
                    "or I no longer share any servers with them"
                )
            else:
                e.set_footer(text=f"Use .reply to respond again")
                await msg.channel.send(embed=e)
                await ctx.message.delete()

    @commands.command(name="reply", aliases=["appeal"])
    async def reply(self, ctx, *, case_number = None):
        if isinstance(ctx.guild, discord.Guild) and "case-" in ctx.channel.name:
            if not ctx.channel.name.replace("case-", "").isdigit():
                await ctx.send("Error parsing the channel name")
                return None
            ctx.message.content = ctx.message.content.replace(ctx.message.content.split()[0] + " ", "")
            return await self.mod_reply(ctx, ctx.message)

        message = None
        if case_number and not case_number.isdigit() and " " not in case_number:
            message = case_number
            case_number = None
        elif case_number and not case_number.isdigit():
            args = case_number.split()
            if args[0].isdigit():
                case_number = int(args[0])
                args.remove(args[0])
            else:
                case_number = None
            message = " ".join(args)
        attachment = None
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0].url

        async with self.bot.cursor() as cur:
            if case_number and case_number.isdigit():
                await cur.execute(
                    f"select guild_id, case_number, reason, link, created_at from cases "
                    f"where case_number = {int(case_number)} and user_id = {ctx.author.id} "
                    f"limit 1;"
                )
                results = await cur.fetchall()
            else:
                await cur.execute(
                    f"select guild_id, case_number, reason, link, created_at from cases "
                    f"where user_id = {ctx.author.id} "
                    f"and created_at > {time() - 60 * 60 * 24 * 14} "
                    f"limit 1;"
                )
                results = await cur.fetchall()

        if not results:
            if case_number:
                await ctx.send("Couldn't find any cases for you with that case number")
                return None
            p = self.bot.utils.get_prefix(ctx)  # type: str
            await ctx.send(
                f"Couldn't find any cases from you from within the last 14 days. "
                f"Use `{p}reply [case_number]` to specify which"
            )
            return None

        if len(results) == 1 and results[0][1] == case_number:
            result = results[0]
        else:
            sorted_results = sorted(results, key=lambda lst: lst[4])[:5]
            formatted_results = [
                f"[Case #{case} from {self.bot.get_guild(guild_id)}]({link})" \
                f"\n> For {self.bot.decode(reason)}"
                for guild_id, case, reason, link, created_at in sorted_results
            ]
            choice = await self.bot.utils.get_choice(ctx, *formatted_results, user=ctx.author)
            if not choice:
                await ctx.send("Timed out waiting for choice")
                return None
            result = sorted_results[formatted_results.index(choice)]
        guild_id, case, reason, link, created_at = result

        await cur.execute(
            f"select channel_id, blocked from modmail "
            f"where guild_id = {guild_id} "
            f"limit 1;"
        )
        results = await cur.fetchone()
        if not results:
            await ctx.send("Modmail isn't enabled in that server")
            return None
        if ctx.author.id in json.loads(self.bot.decode(results[1])):
            return await ctx.send("You're blocked from using modmail in that server")

        if not message and not attachment:
            await ctx.send("What's the message you'd like to send?")
            async with self.bot.require("message", ctx) as msg:
                if msg.content:
                    message = msg.content
                if msg.attachments:
                    attachment = msg.attachments[0].url

        category = self.bot.get_channel(results[0])
        if not category:
            await ctx.send("Couldn't get the modmail channel in that guild, sorry")
            return None

        thread_id = f"case-{case}"
        matches = [channel for channel in category.channels if thread_id == channel.name]
        if not matches:
            try:
                channel = await category.create_text_channel(name=thread_id)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            e.description = f"**Case #{case}:**\n"
            reason = self.bot.decode(reason)
            if link:
                e.description += f"Reason: [{reason}]({link})\n"
            else:
                e.description += f"Reason: `{reason}`"
            if message:
                e.add_field(
                    name="◈ Message",
                    value=message,
                    inline=False
                )
            if attachment:
                e.set_image(url=attachment)
            try:
                await channel.send(embed=e)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            e.set_footer(text="Use .reply to respond")
            await ctx.send("Created your thread 👍")
        else:
            channel = matches[0]  # type: discord.TextChannel
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="New Reply", icon_url=ctx.author.avatar_url)
            if message:
                e.description = message
            if attachment:
                e.set_image(url=attachment)
            try:
                await channel.send(embed=e)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            await ctx.send("Replied to your thread 👍")

    @commands.command(name="close-thread")
    async def close(self, ctx):
        if "case-" not in ctx.channel.name:
            return await ctx.send("Unable to parse the channel name")
        case = ctx.channel.name.replace("case-", "")
        if not case.isdigit():
            return await ctx.send("Unable to parse the channel name")

        if not ctx.channel.category.permissions_for(ctx.guild.me).manage_channels:
            return await ctx.send(
                f"To close the thread, delete the channel, or give me permissions to and rerun the cmd"
            )
        case_number = int(case)
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"select user_id from cases "
                f"where guild_id = {ctx.guild.id} "
                f"and case_number = {case_number};"
            )
            r = await cur.fetchone()
        if r:
            with suppress(NotFound, Forbidden):
                await self.bot.get_user(r[0]).send(
                    f"The thread for case #{case_number} in {ctx.guild} was closed"
                )
        await ctx.send("Closing the thread in 10 seconds")
        await asyncio.sleep(10)
        await ctx.channel.delete()


def setup(bot):
    bot.add_cog(ModMail(bot))
