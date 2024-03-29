"""
cogs.utility.farewell
~~~~~~~~~~~~~~~~~~~~~~

A cog that sends when a user leaves the server

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from discord.ext import commands
from os.path import isfile
from botutils import colors
import discord
import asyncio
import random
import json
import os
from botutils import Cooldown


def leave_help():
    e = discord.Embed(color=colors.tan)
    e.description = "Run `.leave` for a list of sub commands"
    e.add_field(
        name=".leave config",
        value="This basically shows you your current configuration/settings for leave messages",
        inline=False,
    )
    e.add_field(
        name=".leave test",
        value="Send a fake leave message to test your current configuration",
        inline=False,
    )
    e.add_field(
        name=".leave setchannel",
        value="Sets the leave msg channel to the channel you use it in\n"
        "You can also use `.leave setchannel #channel_mention` to set it elsewhere",
        inline=False,
    )
    e.add_field(
        name=".leave toggleimages",
        value="Toggles the use of images. If you haven't added any custom ones with `.leave addimages` "
        "then I'll use my own set of images until you add some",
    )
    e.add_field(
        name=".leave addimages",
        value="Attach files while using this command to add them, or use the command, send the files, "
        "and reply with 'done' whence youve sent them all\nIf you have images added I won't use my own",
        inline=False,
    )
    e.add_field(
        name=".leave delimages", value="Purges your current set of images", inline=False
    )
    e.add_field(
        name=".leave listimages",
        value="Sends you a list of the images you currently have added",
        inline=False,
    )
    e.add_field(
        name=".leave format",
        value="Set the format using `.leave format your_new_format` or run the cmd and send it after",
        inline=False,
    )
    return e


class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.toggle = {}
        self.channel = {}
        self.useimages = {}
        self.images = {}
        self.format = {}
        if isfile("./data/userdata/leave.json"):
            with open("./data/userdata/leave.json", "r") as f:
                dat = json.load(f)
                if "toggle" in dat:
                    self.toggle = dat["toggle"]
                    self.channel = dat["channel"]
                    self.useimages = dat["useimages"]
                    self.images = dat["images"]
                    self.format = dat["format"]
        self.cd = Cooldown(1, 300)
        self.global_cd = Cooldown(3, 5)

    async def save_data(self):
        data = {
            "toggle": self.toggle,
            "channel": self.channel,
            "useimages": self.useimages,
            "images": self.images,
            "format": self.format,
        }
        async with self.bot.utils.open("./data/userdata/leave.json", "w+") as f:
            await f.write(json.dumps(data))

    def is_enabled(self, guild_id):
        return str(guild_id) in self.toggle

    @commands.group(name="leave", aliases=["farewell"], usage=leave_help(), description="Shows how to use the module")
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def leave(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            toggle = "disabled"
            if guild_id in self.toggle:
                toggle = "enabled"
            e = discord.Embed(color=colors.tan)
            e.set_author(name="Leave Messages", icon_url=self.bot.user.display_avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Shows when members leave the server"
            e.add_field(
                name="◈ Command Usage ◈",
                value="__**Core:**__\n"
                ".leave enable\n"
                ".leave disable\n"
                ".leave config\n"
                ".leave test\n"
                "__**Utils:**__\n"
                ".leave setchannel\n"
                ".leave toggleimages\n"
                ".leave addimages\n"
                ".leave delimages\n"
                ".leave listimages\n"
                ".leave format\n",
                inline=False,
            )
            images = ""
            if guild_id in self.images:
                images = f" | Custom Images: {len(self.images[guild_id])}"
            e.set_footer(
                text=f"Current Status: {toggle}{images}",
                icon_url=ctx.guild.owner.display_avatar.url,
            )
            await ctx.send(embed=e)

    @leave.command(name="enable", description="Enables the module")
    @commands.has_permissions(manage_guild=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        messages = []
        if guild_id in self.toggle:
            return await ctx.send("This module is already enabled")

        async def cleanup():
            await ctx.message.delete()
            for msg in messages:
                await asyncio.sleep(1)
                await msg.delete()

        async def wait_for_msg():
            def pred(m):
                return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

            try:
                msg = await self.bot.wait_for("message", check=pred, timeout=30)
            except asyncio.TimeoutError:
                await cleanup()
            else:
                return msg

        msg = await ctx.send("Mention the channel I should use")
        messages.append(msg)
        completed = False
        while not completed:
            msg = await wait_for_msg()
            if not msg:
                return await cleanup()
            messages.append(msg)
            if "cancel" in msg.content.lower():
                return await cleanup()
            if len(msg.channel_mentions) < 1:
                msg = await ctx.send(
                    'That\'s not a channel mention, reply with "cancel" to stop'
                )
                messages.append(msg)
                continue
            self.channel[guild_id] = msg.channel_mentions[0].id
            break
        msg = await ctx.send("Should I use images/gifs?")
        messages.append(msg)
        while not completed:
            msg = await wait_for_msg()
            if not msg:
                return await cleanup()
            messages.append(msg)
            if "cancel" in msg.content.lower():
                return await cleanup()
            if "ye" in msg.content.lower():
                self.useimages[guild_id] = "enabled"
                msg = await ctx.send("Aight, I'll use my own for now")
                messages.append(msg)
                break
            else:
                msg = await ctx.send("kk")
                messages.append(msg)
                break
        msg = await ctx.send(
            "Now to set a message format:```css\nExample:\n**!user has left the chat**```"
        )
        messages.append(msg)
        while not completed:
            msg = await wait_for_msg()
            if not msg:
                return await cleanup()
            messages.append(msg)
            if "cancel" in msg.content.lower():
                return await cleanup()
            msg = await ctx.channel.fetch_message(msg.id)
            self.format[guild_id] = msg.content
            break
        self.toggle[guild_id] = "enabled"
        e = discord.Embed(color=colors.tan)
        e.set_author(name="Enabled Leave Messages", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=e, delete_after=10)
        await cleanup()
        await self.save_data()

    @leave.command(name="disable", description="Disables the module")
    @commands.has_permissions(manage_guild=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            return await ctx.send("This module isn't enabled")
        del self.toggle[guild_id]
        await ctx.send("Disabled leave messages")
        await self.save_data()

    @leave.command(name="config", description="Shows the current configuration")
    async def _config(self, ctx):
        guild_id = str(ctx.guild.id)
        toggle = "disabled"
        channel = "none"
        useimages = "disabled"
        images = 0
        form = "none"
        if guild_id in self.toggle:
            toggle = "enabled"
        if guild_id in self.channel:
            channel = self.bot.get_channel(self.channel[guild_id])
            channel = channel.mention if channel else "deleted-channel"
        if guild_id in self.useimages:
            useimages = self.useimages[guild_id]
        if guild_id in self.format:
            form = self.format[guild_id]
        if guild_id in self.images:
            images = len(self.images[guild_id])
        e = discord.Embed(color=colors.tan)
        e.set_author(name="Leave Config", icon_url=self.bot.user.display_avatar.url)
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

    @leave.command(name="test", description="Tests the current configuration")
    @commands.has_permissions(manage_guild=True)
    async def _test(self, ctx):
        guild_id = str(ctx.guild.id)
        m = ctx.author
        channel = ctx.channel
        if guild_id not in self.format:
            return await ctx.send("You need to set the leave msg format first")
        msg = self.format[guild_id]
        msg = msg.replace("$MENTION", m.mention).replace("$SERVER", m.guild.name)
        msg = msg.replace("!user", str(m.name)).replace("!server", m.guild.name)
        path = (
            os.getcwd()
            + "/data/images/reactions/farewell/"
            + random.choice(
                os.listdir(os.getcwd() + "/data/images/reactions/farewell/")
            )
        )
        if guild_id in self.useimages:
            e = discord.Embed(color=colors.fate)
            if guild_id in self.images:
                if self.images[guild_id]:
                    e.set_image(url=random.choice(self.images[guild_id]))
                    try:
                        await channel.send(msg, embed=e)
                    except discord.Forbidden:
                        del self.useimages[guild_id]
                        del self.images[guild_id]
                        await self.save_data()
            else:
                e.set_image(url="attachment://" + os.path.basename(path))
                try:
                    await channel.send(
                        msg,
                        file=discord.File(path, filename=os.path.basename(path)),
                        embed=e,
                    )
                except discord.Forbidden:
                    del self.useimages[guild_id]
                    await self.save_data()
        else:
            try:
                await channel.send(msg)
            except discord.Forbidden:
                del self.toggle[guild_id]
                await self.save_data()

    @leave.command(name="setchannel", description="Sets the leave channel")
    @commands.has_permissions(manage_guild=True)
    async def _setchannel(self, ctx, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        if not channel:
            channel = ctx.channel
        self.channel[guild_id] = channel.id
        await ctx.send(f"Set the leave message channel to {channel.mention}")
        await self.save_data()

    @leave.command(name="toggleimages", description="Toggles using images")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(attach_files=True)
    async def _toggle_images(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.useimages:
            del self.useimages[guild_id]
            await ctx.send("Disabled Images")
            return self.save_data()
        self.useimages[guild_id] = "enabled"
        if guild_id in self.images:
            await ctx.send("Enabled Images")
        else:
            await ctx.send(
                "Enabled Images. You have no custom "
                "images so I'll just use my own for now"
            )
        await self.save_data()

    @leave.command(name="addimages", description="Adds images to use")
    @commands.has_permissions(manage_guild=True)
    async def _addimages(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.images:
            self.images[guild_id] = []
        if not ctx.message.attachments:
            complete = False
            await ctx.send(
                'Send the image(s) you\'d like to use\nReply with "done" when finished'
            )
            while complete is False:
                msg = await self.bot.utils.get_message(ctx)  # type: discord.Message
                if msg:
                    if msg.content:
                        if "done" in msg.content.lower():
                            return await ctx.send("Added your images 👍")
                    for attachment in msg.attachments:
                        self.images[guild_id].append(attachment.url)
        for attachment in ctx.message.attachments:
            self.images[guild_id].append(attachment.url)
        if len(self.images[guild_id]) > 0:
            await ctx.send("Added your image(s)")
        else:
            await ctx.send("No worries, I'll just keep using my own gifs for now")
            del self.images[guild_id]
        await self.save_data()

    @leave.command(name="delimages", description="Removes all images")
    @commands.has_permissions(manage_guild=True)
    async def _delimages(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.images:
            return await ctx.send("No images >:(")
        del self.images[guild_id]
        await ctx.send("Purged images")
        await self.save_data()

    @leave.command(name="listimages", description="Shows all the current images")
    @commands.has_permissions(manage_guild=True)
    async def _listimages(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.images:
            return await ctx.send("This guild has no images")
        await ctx.send(self.images[guild_id])

    @leave.command(name="format", description="Sets the leave format")
    @commands.has_permissions(manage_guild=True)
    async def _format(self, ctx, *, message=None):
        guild_id = str(ctx.guild.id)
        if message:
            self.format[guild_id] = message
        else:
            await ctx.send(
                "What format should I use?:```css\nExample:\n**!user has left the chat**```"
            )
            msg = await self.bot.utils.get_message(ctx)
            self.format[guild_id] = msg.content
        await ctx.send("Set the welcome format 👍")
        await self.save_data()

    @commands.Cog.listener()
    async def on_member_remove(self, m: discord.Member):
        if self.cd.check(str(m.guild.id) + str(m.id)) or self.global_cd.check(m.guild.id):
            return
        if isinstance(m.guild, discord.Guild):
            guild_id = str(m.guild.id)
            if guild_id in self.toggle:
                channel = self.bot.get_channel(self.channel[guild_id])
                if not channel:
                    del self.toggle[guild_id]
                    return await self.save_data()
                msg = self.format[guild_id]
                msg = msg.replace("$MENTION", str(m)).replace("$SERVER", m.guild.name)
                msg = msg.replace("!user", str(m)).replace("!server", m.guild.name)
                await asyncio.sleep(0)
                path = (
                    os.getcwd()
                    + "/data/images/reactions/farewell/"
                    + random.choice(
                        os.listdir(os.getcwd() + "/data/images/reactions/farewell/")
                    )
                )
                await asyncio.sleep(0)
                if guild_id in self.useimages:
                    e = discord.Embed(color=colors.fate)
                    if guild_id in self.images and self.images[guild_id]:
                        e.set_image(url=random.choice(self.images[guild_id]))
                        try:
                            await channel.send(
                                msg,
                                embed=e,
                                allowed_mentions=self.bot.allow_user_mentions,
                            )
                        except discord.Forbidden:
                            del self.useimages[guild_id]
                            del self.images[guild_id]
                            await self.save_data()
                        else:
                            pass
                    else:
                        e.set_image(url="attachment://" + os.path.basename(path))
                        try:
                            await channel.send(
                                msg,
                                file=discord.File(
                                    path, filename=os.path.basename(path)
                                ),
                                embed=e,
                                allowed_mentions=self.bot.allow_user_mentions,
                            )
                        except discord.Forbidden:
                            del self.useimages[guild_id]
                            await self.save_data()
                        else:
                            pass
                else:
                    try:
                        await channel.send(
                            msg, allowed_mentions=self.bot.allow_user_mentions
                        )
                    except discord.Forbidden:
                        del self.toggle[guild_id]
                        await self.save_data()
                    else:
                        pass


def setup(bot):
    bot.add_cog(Leave(bot), override=True)
