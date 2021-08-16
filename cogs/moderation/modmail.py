"""
cogs.moderation.modmail
~~~~~~~~~~~~~~~~~~~~~~~~

A cog for users to interact with cases

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from time import time
from contextlib import suppress

from discord.errors import *
from discord.ext import commands
from discord import User, Guild, Thread, TextChannel, Embed, Message, AllowedMentions
from discord.ext.commands import Context

from fate import Fate
from botutils.colors import *


class ModMail(commands.Cog):
    def __init__(self, bot: Fate) -> None:
        self.bot = bot
        self.config = bot.utils.cache("modmail")

    def is_enabled(self, guild_id: int) -> bool:
        return guild_id in self.config

    @commands.group(name="modmail", aliases=["mod-mail", "mod_mail"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def modmail(self, ctx: Context):
        if not ctx.invoked_subcommand:
            e = Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Modmail", icon_url=self.bot.user.avatar.url)
            p = ctx.prefix
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
    @commands.bot_has_permissions(view_audit_log=True)
    async def enable(self, ctx: Context):
        await ctx.send("Mention the channel I should use for modmail")
        msg = await self.bot.utils.get_message(ctx)
        if not msg.channel_mentions:
            return await ctx.send("That's not a category ID. Rerun the command >:(")
        channel = msg.channel_mentions[0]
        self.config[ctx.guild.id] = {
            "channel_id": channel.id,
            "references": {},
            "blocked": []
        }
        await ctx.send(f"Set the modmail channel to {channel.mention}")
        await self.config.flush()

    @modmail.command(name="disable")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx: Context):
        if ctx.guild.id not in self.config:
            return await ctx.send("Modmail isn't enabled")
        await self.config.remove(ctx.guild.id)
        await ctx.send("Disabled modmail")

    @commands.command(name="block", aliases=["unblock"])
    async def aliases(self, ctx: Context):
        await getattr(self, ctx.invoked_with.lower()).invoke(ctx)

    @modmail.command(name="block")
    @commands.guild_only()
    async def block(self, ctx: Context, user: User):
        if not self.bot.attrs.is_moderator(ctx.author):
            return await ctx.send("Only moderators can use this command")
        if ctx.author.id == user.id:
            return await ctx.send(f"<:waitThatsIllegal:590584708174184448> that's illegal")
        if ctx.guild.id not in self.config:
            return await ctx.send("Modmail isn't enabled in this server")
        if user.id in self.config[ctx.guild.id]["blocked"]:
            return await ctx.send(f"{user} is already blocked from using modmail")
        self.config[ctx.guild.id]["blocked"].append(user.id)
        await ctx.send(f"Blocked {user} from using modmail")
        await self.config.flush()

    @modmail.command(name="unblock")
    @commands.guild_only()
    async def unblock(self, ctx: Context, user: User):
        if not self.bot.attrs.is_moderator(ctx.author):
            return await ctx.send("Only moderators can use this command")
        if ctx.guild.id not in self.config:
            return await ctx.send("Modmail isn't enabled in this server")
        if user.id not in self.config[ctx.guild.id]["blocked"]:
            return await ctx.send(f"{user} is already blocked from using modmail")
        self.config[ctx.guild.id]["blocked"].remove(user.id)
        await ctx.send(f"Unblocked {user} from using modmail")
        await self.config.flush()

    async def reference(self, guild_id: int, case: int, color: int, message: str) -> Message:
        """ Format a message into the thread channel to notify of an update """
        channel_id: int = self.config[guild_id]["channel_id"]
        channel: TextChannel = self.bot.get_channel(channel_id)  # type: ignore

        # If a thread exists, reference its parent message
        reference = None
        if message_id := self.config[ctx.guild.id]["references"].get(str(case)):
            with suppress(NotFound, Forbidden):
                msg = await channel.fetch_message(message_id)
                reference = msg

        e = Embed(color=color)
        e.description = message
        msg = await channel.send(
            embed=e,
            reference=reference,
            allowed_mentions=AllowedMentions(users=True, roles=False, everyone=False)
        )

        # If a new thread, save the parent message id for future updates
        if not reference:
            self.config[guild_id]["references"][str(case)] = msg.id
            await self.config.flush()

        return msg

    async def mod_reply(self, ctx: Context) -> None:
        case_number = int(ctx.message.channel.name.split()[1])
        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select user_id "
                f"from cases "
                f"where guild_id = {ctx.guild.id} "
                f"and case_number = {case_number};"
            )
            if result := await cur.fetchone():
                user_id = result[0]
            else:
                await ctx.send("Can't find the case for this thread")
                return None
            user = self.bot.get_user(user_id)
            if not user:
                await ctx.message.channel.send(
                    f"I no longer share any servers with this user, therefore cannot dm them"
                )
                return None

            e = Embed(color=self.bot.config["theme_color"])
            e.set_author(name=f"Case #{case_number}", icon_url=ctx.guild.icon.url)
            e.description = f"Reply from {ctx.message.author} in {ctx.guild}"
            if ctx.message.content:
                e.add_field(
                    name="◈ Message",
                    value=ctx.message.content[:1024],
                    inline=False
                )
            if ctx.message.attachments:
                e.set_image(url=ctx.message.attachments[0].url)
            e.set_footer(text=f"Use .reply {case_number} to make a reply")
            try:
                await user.send(embed=e)
            except Forbidden:
                await ctx.message.channel.send(
                    "Failed to reply to the user. Either their dms are closed "
                    "or I no longer share any servers with them"
                )
            else:
                e.set_footer(text=f"Use .reply to respond again")
                await ctx.send(embed=e)
                await ctx.message.delete()

    @commands.command(name="reply", aliases=["appeal"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def reply(self, ctx: Context, *, case_number=None):
        if isinstance(ctx.guild, Guild) and "Case " in ctx.channel.name:
            if not ctx.channel.name.split()[1].isdigit():
                await ctx.send("Error parsing the channel name")
                return None
            ctx.message.content = ctx.message.content.replace(ctx.message.content.split()[0] + " ", "")
            return await self.mod_reply(ctx)

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

        async with self.bot.utils.cursor() as cur:
            if isinstance(case_number, str) and case_number.isdigit():
                case_number = int(case_number)
            if case_number and isinstance(case_number, int):
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
                    f"and created_at > {time() - 60 * 60 * 24 * 14};"
                )
                results = await cur.fetchall()

        if not results:
            if case_number:
                await ctx.send("Couldn't find any cases for you with that case number")
                return None
            await ctx.send(
                f"Couldn't find any cases from you from within the last 14 days. "
                f"Use `{ctx.prefix}reply [case_number]` to specify which"
            )
            return None

        if len(results) == 1 and results[0][1] == case_number:
            result = results[0]
        else:
            sorted_results = sorted(results, key=lambda lst: lst[4])[:5]
            formatted_results = [
                f"[Case #{case} from {self.bot.get_guild(guild_id)}]({link})"
                f"\n> For {self.bot.decode(reason) if reason else None}"
                for guild_id, case, reason, link, created_at in sorted_results
            ]
            choice = await self.bot.utils.get_choice(ctx, *formatted_results, user=ctx.author, timeout=15)
            if not choice:
                await ctx.send("Timed out waiting for choice")
                return None
            result = sorted_results[formatted_results.index(choice)]
        guild_id, case, reason, link, created_at = result

        guild = self.bot.get_guild(guild_id)
        if not guild or guild.id not in self.config:
            await ctx.send("Modmail isn't enabled in that server")
            return None
        if ctx.author.id in self.config[guild.id]["blocked"]:
            return await ctx.send("You're blocked from using modmail in that server")

        channel: TextChannel = self.bot.get_channel(self.config[guild.id]["channel_id"])  # type: ignore
        if not channel or not guild:
            await ctx.send("Couldn't get the modmail channel in that guild, sorry")
            return None
        if not channel.guild.me.guild_permissions.view_audit_log:
            return await ctx.send(
                "I'm missing view_audit_log permissions in that "
                "server at the moment. Try again later"
            )

        async for thread in channel.archived_threads():
            if f"Case {case}" in thread.name and thread.name.endswith("(Closed)"):
                return await ctx.send("That thread is currently closed. Try again another time")

        if not message and not attachment:
            await ctx.send("What's the message you'd like to send?")
            msg = await self.bot.utils.get_message(ctx)
            if msg.content:
                message = msg.content
            if msg.attachments:
                attachment = msg.attachments[0].url

        threads = []
        async for thread in channel.archived_threads():
            threads.append(thread)
        for thread in [*threads, *await channel.active_threads()]:
            if f"Case {case} " in thread.name:
                if thread.name.endswith("(Closed)"):
                    return await ctx.send("That thread's currently closed")
                await self.reference(guild_id, case, pink, f"New Reply on **Case #{case}**")
                break
        else:
            try:
                msg = await channel.send(f"Thread Created by **{ctx.author}** for **Case #{case}**")
                self.config[guild.id]["references"][str(case)] = msg.id
                thread = await channel.start_thread(name=f"Case {case} - {ctx.author}", message=msg)
                await self.config.flush()
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            e = Embed(color=self.bot.config["theme_color"])
            e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar.url)
            e.set_footer(text="Use .reply to respond")
            e.description = f"**Case #{case}:**\n**UserID:** {ctx.author.id}\n"
            reason = self.bot.decode(reason) if reason else None
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
                await thread.send(embed=e)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            e.set_footer(text="Use .reply to respond")
            return await ctx.send("Created your thread 👍")

        e = Embed(color=self.bot.config["theme_color"])
        e.set_author(name="New Reply", icon_url=ctx.author.avatar.url)
        if message:
            e.description = message
        if attachment:
            e.set_image(url=attachment)
        try:
            await thread.send(embed=e)
        except Forbidden:
            await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
            return None
        await ctx.send("Replied to your thread 👍")

    @commands.command(name="close-thread", aliases=["close"])
    async def close_thread(self, ctx: Context):
        if not isinstance(ctx.channel, Thread):
            return await ctx.send("You can only run this in modmail threads")
        if not ctx.channel.name.startswith("Case "):
            return await ctx.send("Unable to parse the channel name")
        if ctx.channel.name.endswith("(Closed)"):
            if not ctx.channel.archived:
                return await ctx.channel.edit(archived=True)
            return await ctx.send("This thread's already closed")
        case = ctx.channel.name.split()[1]
        if not case.isdigit():
            return await ctx.send("Unable to parse the channel name")

        if not ctx.channel.permissions_for(ctx.guild.me).manage_channels:
            return await ctx.send(
                f"To close the thread, delete the channel, or give me permissions to and rerun the cmd"
            )
        case_number = int(case)
        async with self.bot.utils.cursor() as cur:
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
        await ctx.channel.edit(name=f"{ctx.channel.name} (Closed)", archived=True)
        await self.reference(ctx.guild.id, case, red, f"**Case #{case}** was closed by **{ctx.author.mention}**")


def setup(bot: Fate) -> None:
    bot.add_cog(ModMail(bot), override=True)
