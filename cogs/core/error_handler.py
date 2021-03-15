import sys
import traceback
from time import time
from contextlib import suppress

import discord
from aiohttp import ClientConnectorError, ClientOSError, ServerDisconnectedError
from discord.ext import commands
from discord.http import DiscordServerError

from botutils import colors, checks


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cd = {}

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"):
            return
        if ctx.command and ctx.command.cog.__class__.__name__ == "Moderation":
            module = self.bot.cogs["Moderation"]
            await module.cog_after_invoke(ctx)
        ignored = (commands.CommandNotFound, commands.NoPrivateMessage)
        if isinstance(error, ignored):
            return

        # Don't bother if completely missing access
        if not isinstance(ctx.channel, discord.DMChannel):
            if not ctx.guild or not ctx.guild.me or not ctx.channel:
                return
            perms = ctx.channel.permissions_for(ctx.guild.me)
            if not perms.send_messages or not perms.add_reactions:
                return

        # Parse the error object
        error = getattr(error, "original", error)
        if isinstance(error, str):
            self.bot.log(f"Error `{error}` was a string and not a object")
            formatted = f"```python\n{error}```"
        else:
            formatted = "\n".join(traceback.format_tb(error.__traceback__))
        error_str = str(error)
        full_traceback = f"```python\n{formatted}\n{type(error).__name__}: {error}```"
        if "EmptyException" in full_traceback or "NotFound" in full_traceback:
            return
        if "DiscordServerError" in full_traceback:
            with suppress(Exception):
                return await ctx.send(
                    "Oop-\nDiscord shit in the bed\nIt's not my fault, it's theirs"
                )

        try:
            # Disabled globally in the code
            if isinstance(error, commands.DisabledCommand):
                return await ctx.send(f"`{ctx.command}` is disabled.")

            # Unaccepted, or improperly used arg was passed
            elif isinstance(
                error, (commands.BadArgument, commands.errors.BadUnionArgument)
            ):
                return await ctx.send(error)

            # Too fast, sMh
            elif isinstance(error, commands.CommandOnCooldown):
                user_id = str(ctx.author.id)
                if user_id not in self.cd:
                    self.cd[user_id] = 0
                if self.cd[user_id] < time() - 10:
                    await ctx.message.add_reaction("⏳")
                    await ctx.send(error)
                self.cd[user_id] = time() + 10
                return

            # User forgot to pass a required argument
            elif isinstance(error, commands.MissingRequiredArgument):
                return await ctx.send(error)

            # Failed a decorator check
            elif isinstance(error, commands.CheckFailure):
                if not checks.command_is_enabled(ctx):
                    return await ctx.send(f"{ctx.command} is disabled here")
                elif "check functions" in str(error):
                    return await ctx.message.add_reaction("🚫")
                else:
                    return await ctx.send(error)

            # The bot tried to perform an action on a non existent or removed object
            elif "NotFound" in error_str:
                await ctx.send(
                    f"Something I tried to do an operation on was removed or doesn't exist"
                )

            # An action by the bot failed due to missing access or lack of required permissions
            elif isinstance(error, discord.errors.Forbidden):
                if not ctx.guild:
                    return
                if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                    return await ctx.send(error)
                if ctx.channel.permissions_for(ctx.guild.me).add_reactions:
                    return await ctx.message.add_reaction("⚠")
                return await ctx.author.send(
                    f"I don't have permission to reply to you in {ctx.guid.name}"
                )

            # The bot attempted to complete an invalid action
            elif isinstance(error, discord.HTTPException):
                if "Maximum number of guild roles reached" in str(error):
                    return await ctx.send("Can't operate due to this server reaching the max number of roles")

            # Discord shit the bed
            elif isinstance(error, DiscordServerError):
                return await ctx.send(
                        "Oop-\nDiscord shit in the bed\nIt's not my fault, it's theirs"
                    )

            # Failed while parsing an argument that contains a "'"
            elif isinstance(error, commands.UnexpectedQuoteError):
                return await ctx.send("You can't use quotes in that argument")

            # bAd cOdE, requires fix if occurs
            elif isinstance(error, KeyError):
                error_str = f"No Data: {error}"

            # Send a user-friendly error and state that it'll be fixed soon
            if not isinstance(error, discord.errors.NotFound):
                e = discord.Embed(color=colors.red())
                e.description = (
                    f"[{error_str}](https://www.youtube.com/watch?v=t3otBjVZzT0)"
                )
                e.set_footer(text="This error has been logged, and will be fixed soon")
                await ctx.send(embed=e)

            # Temporarily can't connect to discord
            if isinstance(error, (ClientConnectorError, ClientOSError, ServerDisconnectedError)):
                await ctx.send(
                    "Temporarily failed to connect to discord; please re-run your command"
                )
                return

        except (discord.errors.Forbidden, discord.errors.NotFound):
            return

        # Print everything to console to get the full traceback
        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )
        self.bot.last_traceback = full_traceback

        # Prepare to log the error to a dedicated error channel
        channel = self.bot.get_channel(self.bot.config["error_channel"])
        e = discord.Embed(color=colors.red())
        e.description = f"[{ctx.message.content}]({ctx.message.jump_url})"
        e.set_author(
            name=f"| Fatal Error | in {ctx.command}", icon_url=ctx.author.avatar_url
        )
        if ctx.guild:
            e.set_thumbnail(url=ctx.guild.icon_url)
        enum = enumerate(self.bot.utils.split(full_traceback, 980))
        for iteration, chunk in enum:
            e.add_field(
                name="◈ Error ◈",
                value=f"{chunk}" if not iteration else f"```python\n{chunk}```",
                inline=False,
            )

        # Check to make sure the error isn't already logged
        async for msg in channel.history(limit=16):
            for embed in msg.embeds:
                if not embed.fields or not e.fields:
                    continue
                if embed.fields[0].value == e.fields[0].value:
                    return

        # Send the logged error out
        message = await channel.send(embed=e)
        await message.add_reaction("✔")
        if ctx.author.id in self.bot.owner_ids:
            e = discord.Embed(color=colors.fate())
            e.set_author(
                name=f"Here's the full traceback:", icon_url=ctx.author.avatar_url
            )
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = full_traceback
            await ctx.send(embed=e)

    @commands.Cog.listener("on_raw_reaction_add")
    async def dismiss_error_on_fix(self, data):
        if not self.bot.get_user(data.user_id).bot:
            if data.channel_id == self.bot.config["error_channel"]:
                if str(data.emoji) == "✔":
                    channel = self.bot.get_channel(data.channel_id)
                    msg = await channel.fetch_message(data.message_id)
                    for embed in msg.embeds:
                        channel = self.bot.get_channel(self.bot.config["dump_channel"])
                        await channel.send("Error Dismissed", embed=embed)
                    await msg.delete()


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
