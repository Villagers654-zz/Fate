"""
cogs.utility.suggestions
~~~~~~~~~~~~~~~~~~~~~~~~~

A cog for users to make suggestions to the server mods

:copyright: (C) 2021-present FrequencyX4
:license: Proprietary and Confidential, see LICENSE for details
"""

from datetime import datetime, timezone, timedelta

from discord.ext import commands
import discord
from botutils import get_time, emojis


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.utils.cache("suggestions")

        self.required = (
            'read_messages',
            'read_message_history',
            'send_messages',
            'add_reactions',
            'embed_links',
            'manage_messages'
        )

        self.suggest_usage = f"> Make suggestions for your server. " \
                             f"This needs setup by mods via `.suggestions` first.\n" \
                             f"Usage: `.suggest [your suggestion]`"
        self.suggestions_usage = f"> Setup a channel to receive suggestions from server members via `.suggest`\n" \
                                 f"For full usage & how to setup run `.suggest`"

    def is_enabled(self, guild_id):
        return guild_id in self.config

    @commands.command(name="suggest", description="Makes a suggestion to the server")
    @commands.guild_only()
    async def suggest(self, ctx, *, suggestion):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("This server doesn't have a suggestions channel setup")

        # Ensure they have the required role if one's set
        if self.config[guild_id]["required_role_id"]:
            role = ctx.guild.get_role(self.config[guild_id]["required_role_id"])
            if role not in ctx.author.roles:
                return await ctx.send(f"You need the {role} role to make suggestions")

        # Ensure the channel is functional
        channel = self.bot.get_channel(self.config[guild_id]["channel_id"])
        if not channel:
            return await ctx.send(f"Failed to fetch the suggestions channel, maybe it was deleted?")
        perms = channel.permissions_for(ctx.guild.me)
        if not any(getattr(perms, perm) for perm in self.required):
            missing = [f"`{perm}`" for perm in self.required if not getattr(perms, perm)]
            return await ctx.send(f"I'm missing {', '.join(missing)} in the suggestions channel")

        # Check if the user has sent a suggestion within the cooldown
        lmt = datetime.now(tz=timezone.utc) - timedelta(seconds=self.config[guild_id]["cooldown"])
        async for msg in channel.history(limit=256, after=lmt):
            if msg.author.id == self.bot.user.id and msg.embeds and msg.embeds[0].author:
                e = msg.embeds[0]
                if e.author.icon and str(ctx.author.id) in e.author.icon.url:
                    since = get_time((datetime.now(tz=timezone.utc) - lmt).seconds)
                    return await ctx.send(
                        f"You've already sent a suggestion within the last {since}, you're on cooldown"
                    )

        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        e.description = suggestion
        e.set_footer(text="New Suggestion")
        msg = await channel.send(embed=e)
        await msg.add_reaction(emojis.approve)
        await msg.add_reaction(emojis.disapprove)
        await ctx.message.delete()


    @commands.group(name="suggestions", description="Shows how touse the module")
    @commands.bot_has_permissions(embed_links=True)
    async def suggestions(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Member Suggestions", icon_url=self.bot.user.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "> Set a channel in which to receive suggestions from your server members " \
                            "via the `.suggest` command"
            e.add_field(
                name="Usage",
                value="> `.suggestions enable`\nstart the setup process\n"
                      "> `.suggestions disable`\ndisable suggestions\n"
                      "> `.suggest [your suggestion]`\nmake a new suggestion"
            )
            await ctx.send(embed=e)

    @suggestions.command(name="enable", description="Enables the suggestions channel")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx):
        """Begin the setup process for a suggestions channel"""
        guild_id = ctx.guild.id
        if guild_id in self.config:
            return await ctx.send(f"Suggestions is already enabled. To disable them run `.suggestions disable`")

        # Get the channel they want to use
        await ctx.send(f"Mention the channel should I use for suggestions. (Ex: {ctx.channel.mention})")
        reply = await self.bot.utils.get_message(ctx)
        if not reply.channel_mentions:
            return await ctx.send(f"You didn't mention any channels. You'll have to rerun the command")
        channel = reply.channel_mentions[0]

        # Check the bots permissions in that channel
        perms = channel.permissions_for(ctx.guild.me)

        # Be more explanatory with needing read/send so the user can easily understand
        if not perms.read_messages:
            return await ctx.send("I don't have access to read that channel")
        if not perms.send_messages:
            return await ctx.send("I don't have access to send messages to that channel")

        # Throw everything at them :D
        if not any(getattr(perms, attr) for attr in self.required):
            missing = [f"`{perm}`" for perm in self.required if not getattr(perms, perm)]
            return await ctx.send(f"I need {', '.join(missing)} permissions in that channel")

        # See if they want to limit suggestions to a role
        await ctx.send(
            f"Should I require users to have a role in order to make suggestions? "
            f"If not reply with `skip`, otherwise send the role name, or ping"
        )
        reply = await self.bot.utils.get_message(ctx)
        if reply.content.lower() == "skip":
            await ctx.send("Aight, no required role set")
            role_id = None
        else:
            if reply.role_mentions:
                role = reply.role_mentions[0]
            else:
                role = await self.bot.utils.get_role(ctx, reply.content)
                if not role:
                    return await ctx.send("Couldn't find the role. Rerun the command with the proper name or mention")
            if role.position >= ctx.author.top_role.position:
                return await ctx.send("That role's above your paygrade, take a seat")
            role_id = role.id

        # Set a cooldown
        await ctx.send("How many minutes should the cooldown be between each users suggestions?")
        reply = await self.bot.utils.get_message(ctx)
        if not reply.content.isdigit():
            return await ctx.send("That's not a number. Rerun the command and use an integer")
        minutes = int(reply.content)
        if minutes <= 0:
            return await ctx.send("Didn't realize we were going as low as your iq")
        hours = minutes / 60
        days = hours / 24
        if days > 14:
            return await ctx.send("Why.. no")

        # Save the config
        self.config[guild_id] = {
            "channel_id": channel.id,
            "required_role_id": role_id,
            "cooldown": minutes * 60  # Store in seconds
        }
        await self.config.flush()
        await ctx.send(f"Successfully setup the suggestions channel in {channel.mention}")

    @suggestions.command(name="disable", description="Disables the module")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Suggestions aren't enabled. You can enable them via `.suggestions enable`")
        await self.config.remove(guild_id)
        await ctx.send("Disabled suggestions")


def setup(bot):
    bot.add_cog(Suggestions(bot), override=True)
