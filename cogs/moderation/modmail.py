
import json
from time import time
from contextlib import suppress

from discord.ext import commands
import discord
from discord.errors import Forbidden


class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="modmail", aliases=["mod-mail", "mod_mail"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def modmail(self, ctx):
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

    @commands.command(name="reply")
    async def reply(self, ctx, case_number: int = None, *, message=None):
        async with self.bot.cursor() as cur:
            if case_number:
                await cur.execute(
                    f"select guild_id, case_number, reason, link, created_at from cases "
                    f"where case_number = {case_number} and user_id = {ctx.author.id}"
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
            f"select channel_id from modmail "
            f"where guild_id = {guild_id} "
            f"limit 1;"
        )
        results = await cur.fetchone()
        if not results:
            await ctx.send("Modmail isn't enabled in that server")
            return None

        category = self.bot.get_channel(results[0])
        if not category:
            await ctx.send("Couldn't get the modmail channel in that guild, sorry")
            return None

        thread_id = f"case-{case}"
        no_content = not message and not ctx.message.attachments
        if no_content and any(thread_id == channel.name for channel in category.channels):
            return await ctx.send("There's already an active thread in that server")

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
            if link:
                e.description += f"Reason: [{reason}]({link})\n"
            else:
                e.description += f"Reason: `{reason}`"
            try:
                await channel.send(embed=e)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            await ctx.send("Created your thread 👍")
        else:
            channel = matches[0]  # type: discord.TextChannel
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="New Reply", icon_url=ctx.author.avatar_url)
            if message:
                e.description = message
            if ctx.message.attachments:
                e.set_image(url=ctx.message.attachments[0].url)
            try:
                await channel.send(embed=e)
            except Forbidden:
                await ctx.send("Failed to create a thread due to my lacking manage_channel perms in that server")
                return None
            await ctx.send("Replied to your thread 👍")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if (msg.content or msg.attachments) and isinstance(msg.guild, discord.Guild) and "case-" in msg.channel.name:
            name = msg.channel.name.replace("case-", "")
            if name.isdigit() and int(name) in self.bot.modmail_threads:
                case_number = int(name)
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
                        return None
                    user = self.bot.get_user(user_id)

                    if ".close" in msg.content.lower():
                        if msg.channel.permissions_for(msg.guild.me).read_messages:
                            pass
                            # history = await msg.channel.history(limit=75).flatten()
                        if user:
                            with suppress(Forbidden):
                                await user.send(f"Case #{case_number} was closed in {msg.guild}")
                        try:
                            await msg.channel.delete()
                        except:
                            await msg.channel.send(
                                f"To close the thread, delete the channel"
                            )
                        return None

                    elif not user:
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
                    e.set_footer(text=f"Use .reply {case_number} [your message]")
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


def setup(bot):
    bot.add_cog(ModMail(bot))
