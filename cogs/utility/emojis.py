"""
cogs.utility.emojis
~~~~~~~~~~~~~~~~~~~~

A cog for viewing and managing emojis

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
import traceback
from typing import Union
from io import BytesIO
import sys

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Greedy
from discord.errors import HTTPException, Forbidden, InvalidArgument
from PIL import Image

from botutils import colors, download, update_msg


class Emojis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cleanup_text(self, text: str):
        """cleans text to avoid errors when creating emotes"""
        if isinstance(text, list):
            text = " ".join(text)
        if "." in text:
            text = text[: text.find(".") + 1]
        chars = "abcdefghijklmnopqrstuvwxyz"
        result = ""
        for char in list(text):
            if char.lower() in chars:
                result += char
        return result if result else "new_emoji"

    async def compress(self, img):
        def do_compress():
            image = Image.open(BytesIO(img)).convert("RGBA")
            for _attempt in range(10):
                width, height = image.size
                width -= width / 4
                height -= height / 4
                image = image.resize((round(width), round(height)))

                # Save the image to memory instead of the filesystem
                file = BytesIO()
                image.save(file, format="png")
                file.seek(0)
                file_in_bytes = file.read()
                if sys.getsizeof(file) < 256000:
                    break
                del file
            else:
                return None

            return file_in_bytes

        return await self.bot.loop.run_in_executor(
            None, do_compress
        )

    async def _upload_emoji(self, ctx, name, img, reason, roles=None) -> str:
        """ Creates a partial emoji and returns the result as str """
        async def upload(image):
            return await ctx.guild.create_custom_emoji(name=name, image=image, roles=roles, reason=reason)

        if sys.getsizeof(img) > 4000000:
            return f"{name} - File exceeds 4MB"

        try:
            emoji = await upload(img)

        # Missing permissions
        except Forbidden:
            return "I'm missing manage_emoji permission(s)"

        # Unsupported file type
        except (AttributeError, InvalidArgument):
            return f"{name} - Unsupported Image Type"

        # Varying causes to fail
        except HTTPException as err:
            error = traceback.format_exc().lower()

            # Emoji limit reached
            if "maximum" in error:
                return f"{name} - Emoji Limit Reached"

            if "256" not in error:
                return f"{name} - {err}"

            # Attempt to compress the image
            new_img = await self.compress(img)
            if not new_img:
                return f"{name} - Couldn't compress within 5 attempts"

            # Try uploading the compressed image
            try:
                emoji = await upload(new_img)
                return f"Compressed and added {emoji} - {name}"
            except HTTPException:
                return f"{name} - Couldn't compress, simply too large"

        return f"Added {emoji} - {name}"

    async def upload_emoji(self, ctx, *args, **kwargs):
        result = await self._upload_emoji(ctx, *args, **kwargs)
        await update_msg(ctx.msg, result)

    @commands.command(name="emoji", aliases=["emote", "jumbo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def _emoji(self, ctx, *emojis: Union[discord.Emoji, discord.PartialEmoji]):
        """Sends the emoji in image form"""
        if not emojis:
            return await ctx.send("Usage: `.emoji [custom emoji]`")
        if len(emojis) > 1 and all(e == emojis[0] for e in emojis):
            return await ctx.send("No")
        for emoji in emojis[:3]:
            e = discord.Embed(color=colors.fate)
            e.description = str(emoji.id)
            author_name = emoji.name
            author_url = ctx.author.avatar.url
            if isinstance(emoji, discord.Emoji):
                perms = ctx.author.guild_permissions
                bot_perms = emoji.guild.me.guild_permissions
                if (
                    perms.manage_emojis
                    and bot_perms.manage_emojis
                    and emoji.guild.id == ctx.guild.id
                ):
                    emoji = await emoji.guild.fetch_emoji(emoji.id)
                    author_name += f" by {emoji.user}"
                    e.description = f"ID: {emoji.id}"
                    author_url = emoji.user.avatar.url
                icon_url = emoji.guild.icon.url if emoji.guild.icon else None
                e.set_footer(text=emoji.guild.name, icon_url=icon_url)
            e.set_author(name=author_name, icon_url=author_url)
            e.set_image(url=emoji.url)
            await ctx.send(embed=e)
            await asyncio.sleep(1)

    @commands.command(name="emojis")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def emojis(self, ctx):
        e = discord.Embed(color=colors.orange)
        e.set_author(name="Emoji Count", icon_url=ctx.guild.icon.url)
        emojis = [e for e in ctx.guild.emojis if not e.animated]
        a_emojis = [e for e in ctx.guild.emojis if e.animated]
        _max = ctx.guild.emoji_limit
        e.description = (
            f"🆓 | {len(emojis)}/{_max} Normal emotes"
            f"\n💵 | {len(a_emojis)}/{_max} Animated emotes"
        )
        restricted = [e for e in ctx.guild.emojis if e.roles]
        if restricted:
            e.description += f"\n🛑 | {len(restricted)} Restricted emotes"
            index = {}
            for emoji in restricted:
                for role in emoji.roles:
                    if role not in index:
                        index[role] = []
                    index[role].append(emoji)
            for role, emojis in index.items():
                e.add_field(
                    name=f"◈ @{role}", value=" ".join(list(set(emojis))), inline=False
                )
        await ctx.send(embed=e)

    @commands.command(
        name="add-emoji",
        aliases=["add-emote", "addemoji", "addemote", "stealemoji", "stealemote"],
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def _add_emoji(
        self, ctx, custom: Greedy[discord.PartialEmoji], ids: Greedy[int], *args
    ):
        """ Uploads Emojis Via Various Methods """
        ctx.message = await ctx.channel.fetch_message(
            ctx.message.id
        )  # fix content being lowercase
        limit = ctx.guild.emoji_limit

        def at_emoji_limit() -> bool:
            return len(ctx.guild.emojis) >= limit * 2

        def total_emotes() -> int:
            return len([emote for emote in ctx.guild.emojis if not emoji.animated])

        def total_animated() -> int:
            return len([emote for emote in ctx.guild.emojis if emoji.animated])

        # Handle emoji limitations
        if at_emoji_limit():
            return await ctx.send(
                "You're at the limit for both emojis and animated emojis"
            )

        # initialization
        if not custom and not ids and not args and not ctx.message.attachments:
            return await ctx.send(
                "You need to include an emoji to steal, an image/gif, or an image/gif URL"
            )
        ids = list(ids)
        args = list(args)
        for arg in args:
            if arg.isdigit():
                ids.append(int(arg))
                args.remove(arg)
        ctx.msg = await ctx.send("Uploading emoji(s)..")

        # PartialEmoji objects
        for emoji in custom:
            if not at_emoji_limit():
                if emoji.animated and total_animated() == limit:
                    if "Animated Limit Reached" not in ctx.msg.content:
                        ctx.msg = await update_msg(
                            ctx.msg, f"Animated Limit Reached"
                        )
                    continue
                elif not emoji.animated and total_emotes() == limit:
                    if "Emote Limit Reached" not in ctx.msg.content:
                        ctx.msg = await update_msg(
                            ctx.msg, f"Emote Limit Reached"
                        )
                    continue
                name = emoji.name
                img = await download(emoji.url)
                await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author))

        # PartialEmoji IDS
        for emoji_id in ids:
            emoji = self.bot.get_emoji(emoji_id)
            if emoji:
                emoji = emoji.url
            else:
                emoji = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            img = await download(emoji)
            if not img:
                ctx.msg = await update_msg(
                    ctx.msg, f"{emoji_id} - Couldn't Fetch"
                )
                continue

            if not at_emoji_limit():
                if (
                    not isinstance(emoji, (str, discord.Asset))
                    and emoji.animated
                    and total_animated() == limit
                ):
                    if "Animated Limit Reached" not in ctx.msg.content:
                        ctx.msg = await update_msg(
                            ctx.msg, f"Animated Limit Reached"
                        )
                    continue
                elif (
                    not isinstance(emoji, (str, discord.Asset))
                    and not emoji.animated
                    and total_emotes() == limit
                ):
                    if "Emote Limit Reached" not in ctx.msg.content:
                        ctx.msg = await update_msg(
                            ctx.msg, f"Emote Limit Reached"
                        )
                    continue

                # Get any optional 'name' arguments
                argsv = ctx.message.content.split()
                index = argsv.index(str(emoji_id)) + 1
                name = f"new_emoji_{emoji_id}"
                if len(argsv) > index:
                    new_name = argsv[index]
                    if not new_name.isdigit():
                        name = new_name

                await self.upload_emoji(
                    ctx, name=str(name), img=img, reason=str(ctx.author)
                )

        # Image/GIF URLS
        def check(it):
            if it + 2 > len(args):
                return "."
            return args[it + 1]

        mappings = {}
        try:
            mappings = {
                await download(arg): check(it)
                if "." not in check(it)
                else "new_emoji"
                for it, arg in enumerate(args)
                if "." in arg
            }
            for img, name in mappings.items():
                if not img:
                    ctx.msg = await update_msg(
                        ctx.msg, f"{name} - Dead Link"
                    )
                    continue
                await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author))
        except aiohttp.InvalidURL as e:
            ctx.msg = await update_msg(ctx.msg, str(e))

        # Attached Images/GIFsK
        allowed_extensions = ["png", "jpg", "jpeg", "gif"]
        for attachment in ctx.message.attachments:
            file_is_allowed = any(
                not attachment.filename.endswith(ext) for ext in allowed_extensions
            )
            if not attachment.height or not file_is_allowed:
                ctx.msg = await update_msg(
                    ctx.msg, f"{attachment.filename} - Not an image or gif"
                )
                continue
            if "gif" in attachment.filename and total_animated == limit:
                if "Animated Limit Reached" not in ctx.msg:
                    ctx.msg = await update_msg(
                        ctx.msg, f"Animated Limit Reached"
                    )
                continue
            elif "gif" not in attachment.filename and total_emotes == limit:
                if "Emote Limit Reached" not in ctx.msg.content:
                    ctx.msg = await update_msg(
                        ctx.msg, f"Emote Limit Reached"
                    )
                continue

            name = attachment.filename[: attachment.filename.find(".")]
            try:
                file = await attachment.read()  # Raw bytes file
            except discord.errors.HTTPException:
                await update_msg(
                    ctx.msg, f"{name} - failed to read attachment"
                )
                continue
            if args and not custom and not ids and not mappings:
                name = args[0]

            await self.upload_emoji(ctx, name=name, img=file, reason=str(ctx.author))

        if not len(ctx.msg.content.split("\n")) > 1:
            ctx.msg = await update_msg(
                ctx.msg, "No proper formats I can work with were provided"
            )

    @commands.command(name="delemoji", aliases=["delemote"])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_emojis=True)
    async def _delemoji(self, ctx, *emoji: discord.Emoji):
        for emoji in emoji:
            if emoji.guild.id != ctx.guild.id:
                await ctx.send(f"{emoji} doesn't belong to this server")
                continue
            await emoji.delete(reason=ctx.author.name)
            await ctx.send(f"Deleted emote `{emoji.name}`")

    @commands.command(name="rename-emoji")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_emojis=True)
    async def _rename_emoji(self, ctx, emoji: discord.Emoji, name):
        clean_name = ""
        old_name = emoji.name
        for i in list(name):
            if i in list("abcdefghijklmnopqrstuvwxyz"):
                clean_name += i
        await emoji.edit(name=name, reason=ctx.author.name)
        await ctx.send(f"Renamed emote `{old_name}` to `{clean_name}`")


def setup(bot):
    bot.add_cog(Emojis(bot), override=True)
