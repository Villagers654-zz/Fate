"""
cogs.core.error_handler
~~~~~~~~~~~~~~~~~~~~~~~~

A cog for handling exceptions raised within commands

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import sys
import traceback
from time import time
from contextlib import suppress
from typing import *

import discord
from aiohttp import ClientConnectorError, ClientOSError, ServerDisconnectedError
from discord.ext import commands
from discord.http import DiscordServerError
from lavalink import NodeException
from pymongo.errors import DuplicateKeyError

from botutils import colors, split, Cooldown
from classes import checks, exceptions

class ErrorHandler(commands.Cog):
    notifs: Dict[int, str] = {}  # Who to notify when an errors fixed

    def __init__(self, bot):
        self.bot = bot
        self.response_cooldown = Cooldown(1, 10)
        self.reaction_cooldown = Cooldown(1, 4)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ensure the servers `currently running commands` index gets updated
        if ctx.command and ctx.command.cog.__class__.__name__ == "Moderation":
            module = self.bot.cogs["Moderation"]
            await module.cog_after_invoke(ctx)

        # Suppress spammy, or intentional errors
        error: Exception = getattr(error, "original", error)
        ignored = (
            commands.CommandNotFound,
            commands.NoPrivateMessage,
            discord.errors.DiscordServerError,
            exceptions.IgnoredExit
        )
        if isinstance(error, ignored) or not (error_to_send := str(error)):
            return

        # Don't bother if completely missing access
        if not isinstance(ctx.channel, discord.DMChannel):
            if not ctx.guild or not ctx.guild.me or not ctx.channel:
                return
            perms = ctx.channel.permissions_for(ctx.guild.me)
            if not perms.send_messages or not perms.add_reactions:
                return

        # Format the full traceback
        full_tb = "\n".join(traceback.format_tb(error.__traceback__))
        formatted_tb = f"```python\n{full_tb}\n{type(error).__name__}: {error}```"

        try:
            # Disabled globally in the code
            if isinstance(error, RuntimeError):
                return await ctx.send("Oop, I had an internal error. Rerun the command")
            elif isinstance(error, commands.DisabledCommand):
                return await ctx.send(f"`{ctx.command}` is disabled.")

            # Unaccepted, or improperly used arg was passed
            elif isinstance(error, commands.ExpectedClosingQuoteError):
                return await ctx.send("You can't include a `\"` in that argument")
            elif isinstance(error, (commands.BadArgument, commands.errors.BadUnionArgument)):
                msg = str(error).lstrip("http://").lstrip("https://").lstrip("www.")
                return await ctx.send(msg)

            # Lavalink
            elif isinstance(error, NodeException):
                self.bot.reload_extension("cogs.core.music")
                return await ctx.send("Error connecting to my moosic server, please retry")

            elif isinstance(error, DuplicateKeyError):
                self.bot.log.critical(full_tb)
                return await ctx.send("Error saving changes because to a duplicate entry, it's likely you ran the command twice at once")

            # Too fast, sMh
            elif isinstance(error, commands.CommandOnCooldown):
                user_id = ctx.author.id
                if self.response_cooldown.check(user_id):
                    if not self.reaction_cooldown.check(user_id):
                        await ctx.message.add_reaction("⏳")
                else:
                    await ctx.send(error)
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
            elif isinstance(error, discord.errors.NotFound):
                try:
                    await ctx.send(
                        f"Something I tried to do an operation on was removed or doesn't exist",
                        reference=ctx.message,
                        delete_after=5
                    )
                except discord.errors.HTTPException:
                    await ctx.send(
                        f"Something I tried to do an operation on was removed or doesn't exist",
                        delete_after=5
                    )
                return

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
                error_to_send = f"No Data: {error}"

            # Send a user-friendly error and state that it'll be fixed soon
            if not isinstance(error, discord.errors.NotFound):
                e = discord.Embed(color=colors.red)
                e.description = f"[{error_to_send}](https://www.youtube.com/watch?v=t3otBjVZzT0)"
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

        # Prepare to log the error to a dedicated error channel
        channel = self.bot.get_channel(self.bot.config["error_channel"])
        e = discord.Embed(color=colors.red)
        e.description = f"[{ctx.message.content}]({ctx.message.jump_url})"
        e.set_author(
            name=f"| Fatal Error | in {ctx.command}", icon_url=ctx.author.avatar.url
        )
        if ctx.guild and ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        enum = enumerate(split(formatted_tb, 980))
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
        self.notifs[message.id] = ctx.author.id

        if ctx.author.id in self.bot.owner_ids:
            e = discord.Embed(color=colors.fate)
            e.set_author(
                name=f"Here's the full traceback:", icon_url=ctx.author.avatar.url
            )
            e.set_thumbnail(url=self.bot.user.avatar.url)
            e.description = full_tb
            await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, data):
        """ Dismisses an error whence fixed """
        if str(data.emoji) == "✔" and data.channel_id == self.bot.config["error_channel"]:
            if (user := self.bot.get_user(data.user_id)) and not user.bot:
                delay = None
                try:
                    # Fetch the message object
                    channel = self.bot.get_channel(data.channel_id)
                    msg = await channel.fetch_message(data.message_id)  # type: discord.Message

                    # Check the embeds for exception embeds
                    for embed in msg.embeds:
                        dump_channel = self.bot.get_channel(self.bot.config["dump_channel"])
                        await dump_channel.send("Error Dismissed", embed=embed)

                        # If possible tell the author it was fixed
                        if author := self.bot.get_user(self.notifs.get(msg.id, None)):
                            e = discord.Embed(color=colors.green)
                            description = embed.description
                            if len(description) > 128:
                                description = description[:128] + "..."
                            e.description = f"**Command you used:** {description}"
                            with suppress(Exception):
                                await author.send(f"A problem you encountered was fixed", embed=e)
                                await channel.send(
                                    "DM'd the user that the problem was fixed",
                                    reference=msg,
                                    delete_after=5
                                )
                                delay = 5
                        self.notifs.pop(msg.id, None)
                except (AttributeError, discord.errors.NotFound):
                    pass
                else:
                    await msg.delete(delay=delay)


def setup(bot):
    bot.add_cog(ErrorHandler(bot), override=True)
