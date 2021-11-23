"""
cogs.fun.reactions
~~~~~~~~~~~~~~~~~~~

A cog for adding reaction gifs to your msgs

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

import aiohttp
import os
import random
import asyncio
from contextlib import suppress
from typing import *

from discord.ext import commands
from discord import Webhook
import discord


class Reactions(
    commands.Cog,
    command_attrs=dict(
        cooldown=commands.CooldownMapping(commands.Cooldown(1, 5), commands.BucketType.user)
    )
):
    required_permissions = [
        "add_reactions",
        "manage_messages",
        "manage_webhooks"
    ]

    def __init__(self, bot):
        self.bot = bot
        self.webhook = {}
        self.sent = {}

    def cog_check(self, ctx):
        perms = ctx.guild.me.guild_permissions
        missing = []
        for permission in self.required_permissions:
            if not getattr(perms, permission):
                missing.append(permission)
        if missing:
            raise commands.MissingPermissions(missing)
        return True

    async def cog_before_invoke(self, ctx):
        if isinstance(ctx.channel, discord.Thread):
            raise commands.CheckFailure("You can't use this module in threads")

    async def queue(self, ctx, reaction, path):
        await asyncio.sleep(60 * 5)
        if path in self.sent[reaction][ctx.guild.id]:
            del self.sent[reaction][ctx.guild.id][path]
        if not self.sent[reaction][ctx.guild.id]:
            del self.sent[reaction][ctx.guild.id]

    async def send_webhook(self, ctx, reaction: str, args: str, action: str = None):
        # Prevent roles from being mentioned
        if args and ("<@&" in args or "@everyone" in args or "@here" in args):
            return await ctx.send("biTcH nO")

        # Format the message
        if action and ctx.message.mentions:
            argsv: List[str] = args.split()
            if len(argsv) == 1:
                args = f"*{action} {args}*"
            elif args.startswith("<@"):
                user = argsv[0]  # The target users mention
                text = " ".join(argsv[1:])  # The message to send
                args = f'*{action} {user}* {text}'

        options = os.listdir(f"./data/images/reactions/{reaction}/")

        if reaction not in self.sent:
            self.sent[reaction] = {}
        if ctx.guild.id not in self.sent[reaction]:
            self.sent[reaction][ctx.guild.id] = {}
        if len(self.sent[reaction][ctx.guild.id]) >= len(options):
            for task in self.sent[reaction][ctx.guild.id].values():
                if not task.done():
                    task.cancel()
            self.sent[reaction][ctx.guild.id] = {}

        # Remove sent gifs from possible options and choose which GIF to send
        for sent_path in self.sent[reaction][ctx.guild.id].keys():
            with suppress(ValueError):
                options.remove(sent_path)
        filename = random.choice(options)
        path = os.getcwd() + f"/data/images/reactions/{reaction}/" + filename

        # Add and wait 5mins to remove the sent path
        self.sent[reaction][ctx.guild.id][filename] = self.bot.loop.create_task(
            self.queue(ctx, reaction, filename)
        )

        created_webhook = False
        if ctx.channel.id not in self.webhook:
            webhooks = await ctx.channel.webhooks()
            for webhook in webhooks:
                if webhook.name == "Reaction":
                    self.webhook[ctx.channel.id] = webhook
                    break
            else:
                if len(webhooks) == 10:
                    raise commands.BadArgument("This channel has too many webhooks (There's a max of 10)")
                self.webhook[ctx.channel.id] = await ctx.channel.create_webhook(
                    name="Reaction"
                )
            created_webhook = True

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                self.webhook[ctx.channel.id].url, session=session
            )
            name = ctx.author.name
            if "clyde" in name.lower():
                name = name.lower().replace("clyde", "🚫")
            await webhook.send(
                content=args,
                username=name,
                avatar_url=ctx.author.display_avatar.url,
                file=discord.File(
                    path, filename=reaction + path[-(len(path) - path.find(".")) :]
                ),
            )
            with suppress(Exception):
                await ctx.message.delete()
            if created_webhook:
                await asyncio.sleep(120)
                if ctx.channel.id in self.webhook:
                    if self.webhook[ctx.channel.id]:
                        await self.webhook[ctx.channel.id].delete()
                        del self.webhook[ctx.channel.id]

    @commands.command(name="intimidate")
    async def intimidate(self, ctx, *, content=None):
        await self.send_webhook(ctx, "apple", content)

    @commands.command(name="observe")
    async def observe(self, ctx, *, content=None):
        await self.send_webhook(ctx, "observe", content)

    @commands.command(name="disgust")
    async def disgust(self, ctx, *, content=None):
        await self.send_webhook(ctx, "disgust", content)

    @commands.command(name="snuggle")
    async def snuggle(self, ctx, *, content):
        await self.send_webhook(ctx, "snuggle", content, action="snuggles")

    @commands.command(name="admire")
    async def admire(self, ctx, *, content=None):
        await self.send_webhook(ctx, "admire", content)

    @commands.command(name="waste")
    async def waste(self, ctx, *, args):
        await self.send_webhook(ctx, "waste", args, action="wastes")

    @commands.command(name="shrug")
    async def shrug(self, ctx, *, content=None):
        await self.send_webhook(ctx, "shrug", content)

    @commands.command(name="yawn")
    async def yawn(self, ctx, *, content=None):
        await self.send_webhook(ctx, "yawn", content)

    @commands.command(name="sigh")
    async def sigh(self, ctx, *, content=None):
        await self.send_webhook(ctx, "sigh", content)

    @commands.command(name="bite")
    async def bite(self, ctx, *, args):
        await self.send_webhook(ctx, "bite", args, action="bites")

    @commands.command(name="wine")
    async def wine(self, ctx, *, content=None):
        await self.send_webhook(ctx, "wine", content)

    @commands.command(name="hide")
    async def hide(self, ctx, *, content=None):
        await self.send_webhook(ctx, "hide", content)

    @commands.command(name="slap")
    async def slap(self, ctx, *, args):
        await self.send_webhook(ctx, "slap", args, action="slaps")

    @commands.command(name="kiss")
    async def kiss(self, ctx, *, args):
        await self.send_webhook(ctx, "kiss", args, action="kisses")

    @commands.command(name="kill")
    async def kill(self, ctx, *, args):
        await self.send_webhook(ctx, "kill", args, action="kills")

    @commands.command(name="teasip", aliases=["tea", "st", "siptea"])
    async def teasip(self, ctx, *, content=None):
        await self.send_webhook(ctx, "tea", content)

    @commands.command(name="lick")
    async def lick(self, ctx, *, args):
        await self.send_webhook(ctx, "lick", args, action="licks")

    @commands.command(name="hug")
    async def hug(self, ctx, *, args):
        await self.send_webhook(ctx, "hug", args, action="hugs")

    @commands.command(name="cry")
    async def cry(self, ctx, *, content=None):
        await self.send_webhook(ctx, "cry", content)

    @commands.command(name="cuddle")
    async def cuddle(self, ctx, *, content=None):
        await self.send_webhook(ctx, "cuddle", content, action="cuddles")

    @commands.command(name="pat")
    async def pat(self, ctx, *, args):
        await self.send_webhook(ctx, "pat", args, action="pats")

    @commands.command(name="homo")
    @commands.is_owner()
    async def _homo(self, ctx):
        path = (
            os.getcwd()
            + "/data/images/reactions/homo/"
            + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/homo/"))
        )
        e = discord.Embed()
        e.set_image(url="attachment://" + os.path.basename(path))
        await ctx.message.delete()
        await ctx.send(
            file=discord.File(path, filename=os.path.basename(path)), embed=e
        )


def setup(bot):
    bot.add_cog(Reactions(bot), override=True)
