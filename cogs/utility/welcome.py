"""
cogs.utility.welcome
~~~~~~~~~~~~~~~~~~~~~

A cog for welcoming users to servers

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import random
import os

from discord.ext import commands
import discord

from botutils import colors, Conversation


mentions = discord.AllowedMentions(users=True, roles=True, everyone=False)


def welcome_help():
    e = discord.Embed(color=colors.tan)
    e.description = "Run `.leave` for a list of sub commands"
    e.add_field(
        name=".welcome config",
        value="This basically shows you your current configuration/settings for welcome messages",
        inline=False,
    )
    e.add_field(
        name=".welcome test",
        value="Send a fake leave message to test your current configuration",
        inline=False,
    )
    e.add_field(
        name=".welcome setchannel",
        value="Sets the welcome msg channel to the channel you use it in\n"
        "You can also use `.welcome setchannel #channel_mention` to set it elsewhere",
        inline=False,
    )
    e.add_field(
        name=".welcome toggleimages",
        value="Toggles the use of images. If you haven't added any custom ones with `.welcome addimages` "
        "then I'll use my own set of images until you add some",
    )
    e.add_field(
        name=".welcome addimages",
        value="Attach files while using this command to add them, or use the command, send the files, "
        "and reply with 'done' whence youve sent them all\nIf you have images added I won't use my own",
        inline=False,
    )
    e.add_field(
        name=".welcome delimages",
        value="Purges your current set of images",
        inline=False,
    )
    e.add_field(
        name=".welcome listimages",
        value="Sends you a list of the images you currently have added",
        inline=False,
    )
    e.add_field(
        name=".welcome format",
        value="Set the format using `.welcome format your_new_format` or run the cmd and send it after",
        inline=False,
    )
    e.add_field(
        name=".welcome wait-for-verify",
        value="This makes the bot wait till a user verifies through the .verification module before welcoming them",
        inline=False,
    )
    return e


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.utils.cache("welcome")
        self.welcome_usage = welcome_help()

    def is_enabled(self, guild_id):
        return guild_id in self.config

    @commands.group(name="welcome", usage=welcome_help())
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def _welcome(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = ctx.guild.id
            toggle = "disabled"
            if guild_id in self.config:
                toggle = "enabled"
            e = discord.Embed(color=colors.tan)
            e.set_author(name="Welcome Messages", icon_url=self.bot.user.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Welcomes users when they join"
            e.add_field(
                name="◈ Command Usage ◈",
                value="__**Core:**__\n"
                ".welcome enable\n"
                ".welcome disable\n"
                ".welcome config\n"
                ".welcome test\n"
                "__**Utils:**__\n"
                ".welcome setchannel\n"
                ".welcome toggleimages\n"
                ".welcome addimages\n"
                ".welcome delimages\n"
                ".welcome listimages\n"
                ".welcome format\n"
                ".welcome wait-for-verify",
                inline=False,
            )
            images = ""
            if guild_id in self.config and self.config[guild_id]["useimages"]:
                images = f" | Custom Images: {len(self.config[guild_id]['images'])}"
            e.set_footer(
                text=f"Current Status: {toggle}{images}",
                icon_url=ctx.guild.owner.display_avatar.url,
            )
            await ctx.send(embed=e)

    @_welcome.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def _enable(self, ctx):
        convo = Conversation(ctx, delete_after=True)
        guild_id = ctx.guild.id
        conf = {
            "enabled": True,
            "channel": None,
            "format": "Welcome !mention",
            "useimages": False,
            "images": [],
            "wait_for_verify": False
        }
        if guild_id in self.config:
            conf = self.config[guild_id]

        for _ in range(5):
            msg = await convo.ask("Mention the channel I should use")
            if not msg.channel_mentions:
                await convo.send("That's not a channel mention")
                continue
            conf["channel"] = msg.channel_mentions[0].id
            break
        else:
            return await convo.end()

        for _ in range(5):
            msg = await convo.ask("Should I use images/gifs?")
            if "ye" in msg.content.lower():
                conf["useimages"] = True
                await convo.send("Aight, I'll use images")
            elif "no" in msg.content.lower():
                conf["useimages"] = False
                await convo.send("kk")
            else:
                continue
            break
        else:
            return await convo.end()

        msg = await convo.ask("Now to set a message format:```css\nExample:\nWelcome !user to !server```")
        if "!inviter" in msg.content:
            await self.bot.invite_manager.init(ctx.guild)
        conf["format"] = msg.content

        self.config[guild_id] = conf
        await self.config.flush()

        e = discord.Embed(color=colors.tan)
        e.set_author(name="Enabled Welcome Messages", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=e)
        await convo.end()

    @_welcome.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def _disable(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config or not self.config[guild_id]["enabled"]:
            return await ctx.send("This module isn't enabled")
        self.config[guild_id]["enabled"] = False
        await self.config.flush()
        await ctx.send("Disabled welcome messages")

    @_welcome.command(name="config")
    async def _config(self, ctx):
        guild_id = ctx.guild.id
        toggle = "disabled"
        channel = "none"
        useimages = "disabled"
        images = 0
        form = "none"
        if guild_id in self.config:
            conf = self.config[guild_id]
            if conf["enabled"]:
                toggle = "enabled"
            channel = self.bot.get_channel(conf["channel"])
            channel = channel.mention if channel else "none"
            if conf["useimages"]:
                useimages = "enabled"
            form = conf["format"]
            images = len(conf["images"])
        e = discord.Embed(color=colors.tan)
        e.set_author(name="Welcome Config", icon_url=self.bot.user.display_avatar.url)
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.description = (
            f"**Toggle:** {toggle}\n"
            f"**Channel:** {channel}\n"
            f"**Images:** {useimages}\n"
            f"**Custom Images:** {images}\n"
            f"**Format:** {form}\n"
        )
        await ctx.send(embed=e)

    @_welcome.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def _test(self, ctx, user: discord.User=None):
        guild_id = ctx.guild.id
        channel = ctx.channel
        if not user:
            user = ctx.author
        if guild_id not in self.config:
            return await ctx.send("You need to enable the module first")
        msg = self.config[guild_id]["format"] \
            .replace("!server", ctx.guild.name) \
            .replace("!user", str(user)) \
            .replace("!name", user.name) \
            .replace("!mention", user.mention)
        if "!inviter" in msg and ctx.guild.id in self.bot.invite_manager.index:
            inviter = await self.bot.invite_manager.get_inviter(ctx.guild,user)
            msg = msg.replace("!inviter", inviter)
        path = (
            os.getcwd()
            + "/data/images/reactions/welcome/"
            + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/welcome/"))
        )
        if self.config[guild_id]["useimages"]:
            e = discord.Embed(color=colors.fate)
            if self.config[guild_id]["images"]:
                e.set_image(url=random.choice(self.config[guild_id]["images"]))
                try:
                    await channel.send(msg, embed=e, allowed_mentions=mentions)
                except discord.errors.Forbidden:
                    return
            else:
                e.set_image(url="attachment://" + os.path.basename(path))
                try:
                    await channel.send(
                        msg,
                        file=discord.File(path, filename=os.path.basename(path)),
                        embed=e, allowed_mentions=mentions
                    )
                except discord.errors.Forbidden:
                    return
        else:
            try:
                await channel.send(msg, allowed_mentions=mentions)
            except discord.errors.Forbidden:
                return

    @_welcome.command(name="setchannel")
    @commands.has_permissions(manage_guild=True)
    async def _setchannel(self, ctx, channel: discord.TextChannel = None):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Welcome messages aren't enabled")
        if not channel:
            channel = ctx.channel
        self.config[guild_id]["channel"] = channel.id
        await ctx.send(f"Set the welcome message channel to {channel.mention}")
        await self.config.flush()

    @_welcome.command(name="toggleimages")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(attach_files=True)
    async def _toggle_images(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Welcome messages aren't enabled")
        self.config[guild_id]["useimages"] = not self.config[guild_id]["useimages"]
        if self.config[guild_id]["useimages"]:
            if self.config[guild_id]["images"]:
                await ctx.send("Enabled Images")
            else:
                await ctx.send(
                    "Enabled Images. You have no custom "
                    "images so I'll just use my own for now"
                )
        else:
            await ctx.send("Disabled images")
        await self.config.flush()

    @_welcome.command(name="addimages")
    @commands.has_permissions(manage_guild=True)
    async def _addimages(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Welcome messages aren't enabled")
        if not ctx.message.attachments:
            complete = False
            await ctx.send(
                'Send the image(s) you\'d like to use\nReply with "done" when finished'
            )
            while complete is False:
                msg = await self.bot.utils.get_message(ctx)  # type: discord.Message
                if msg.content:
                    if "done" in msg.content.lower():
                        return await ctx.send("Added your images 👍")
                for attachment in msg.attachments:
                    self.config[guild_id]["images"].append(attachment.url)
        for attachment in ctx.message.attachments:
            self.config[guild_id]["images"].append(attachment.url)
        if len(self.config[guild_id]["images"]) > 0:
            await ctx.send("Added your image(s)")
        else:
            return await ctx.send("No worries, I'll just keep using my own gifs for now")
        await self.config.flush()

    @_welcome.command(name="delimages")
    @commands.has_permissions(manage_guild=True)
    async def _delimages(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config or not self.config[guild_id]["images"]:
            return await ctx.send("No images >:(")
        self.config[guild_id]["images"] = []
        await ctx.send("Purged images")
        await self.config.flush()

    @_welcome.command(name="listimages")
    @commands.has_permissions(manage_guild=True)
    async def _listimages(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config or not self.config[guild_id]["images"]:
            return await ctx.send("This guild has no images")
        await ctx.send("\n".join(self.config[guild_id]["images"]))

    @_welcome.command(name="format")
    @commands.has_permissions(manage_guild=True)
    async def _format(self, ctx, *, message=None):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Welcome messages aren't enabled")
        if message:
            if "!inviter" in message:
                await self.bot.invite_manager.init(ctx.guild)
            self.config[guild_id]["format"] = message
        else:
            await ctx.send(
                "What format should I use?:```css\nExample:\nWelcome !user to !server```"
            )
            msg = await self.bot.utils.get_message(ctx)
            if "!inviter" in msg.content:
                await self.bot.invite_manager.init(ctx.guild)
            self.config[guild_id]["format"] = msg.content
        await ctx.send("Set the welcome format 👍")
        await self.config.flush()

    @_welcome.command(name="wait-for-verify", aliases=["waitforverify"])
    @commands.has_permissions(manage_guild=True)
    async def _wait_for_verify(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Welcome messages aren't enabled")
        enabled = not self.config[guild_id]["wait_for_verify"]
        self.config[guild_id]["wait_for_verify"] = enabled
        r = "I'll now" if enabled else "I'll no longer"
        await ctx.send(f"{r} wait for users to verify before sending the welcome message")
        await self.config.flush()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member, just_verified=False):
        if isinstance(member.guild, discord.Guild):
            guild = member.guild
            guild_id = guild.id
            if guild_id in self.config and self.config[guild_id]["enabled"]:
                if not just_verified and self.config[guild_id]["wait_for_verify"]:
                    return
                conf = self.config[guild_id]
                channel = self.bot.get_channel(conf["channel"])
                if not channel:
                    self.config[guild_id]["enabled"] = False
                    return await self.config.flush()

                # Format the welcome message
                msg = conf["format"] \
                    .replace("!server", guild.name) \
                    .replace("!user", str(member)) \
                    .replace("!name", member.name) \
                    .replace("!mention", member.mention)
                if "!inviter" in msg and guild.id in self.bot.invite_manager.index:
                    inviter = await self.bot.invite_manager.get_inviter(guild, member)
                    msg = msg.replace("!inviter", inviter)

                # Attach images in an embed
                if conf["useimages"]:
                    e = discord.Embed(color=colors.fate)
                    if conf["images"]:
                        e.set_image(url=random.choice(conf["images"]))
                        try:
                            return await channel.send(msg, embed=e, allowed_mentions=mentions)
                        except discord.errors.Forbidden:
                            self.config[guild_id]["enabled"] = False
                            return await self.config.flush()

                    # Send with our own images
                    path = os.getcwd() + "/data/images/reactions/welcome/" + random.choice(
                        os.listdir(os.getcwd() + "/data/images/reactions/welcome/")
                    )
                    e.set_image(url="attachment://" + os.path.basename(path))
                    try:
                        return await channel.send(
                            msg,
                            file=discord.File(path, filename=os.path.basename(path)),
                            embed=e,
                            allowed_mentions=mentions,
                        )
                    except discord.errors.Forbidden:
                        self.config[guild_id]["enabled"] = False
                        return await self.config.flush()

                # Send without images
                try:
                    await channel.send(msg, allowed_mentions=mentions)
                except discord.errors.Forbidden:
                    self.config[guild_id]["enabled"] = False
                    return await self.config.flush()


def setup(bot):
    bot.add_cog(Welcome(bot), override=True)
