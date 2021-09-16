"""
cogs.core.cc
~~~~~~~~~~~~~

A cog for configuring per-server custom commands

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from os.path import isfile
import json
from time import time

from discord.ext import commands, tasks
from discord import Message, Embed, AllowedMentions

from botutils import sanitize, get_prefixes_async, GetChoice
from fate import Fate


m = AllowedMentions.none()


class CustomCommands(commands.Cog):
    fp = "./data/userdata/cc.json"
    cache = {}
    guilds = []
    def __init__(self, bot: Fate):
        self.bot = bot
        if isfile(self.fp):
            with open(self.fp, "r") as f:
                self.guilds = json.load(f)
        self.cd = self.bot.utils.cooldown_manager(1, 10)
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    async def save_config(self):
        async with self.bot.utils.open(self.fp, "w+") as f:
            await f.write(await self.bot.dump(self.guilds))

    @tasks.loop(minutes=1)
    async def cleanup_task(self):
        for guild_id, commands in list(self.cache.items()):
            for command, (_resp, cached_at) in list(commands.items()):
                await asyncio.sleep(0)
                if time() - cached_at > 60 * 10:
                    del self.cache[guild_id][command]
            if not self.cache[guild_id]:
                del self.cache[guild_id]
        changed = False
        async with self.bot.utils.cursor() as cur:
            for guild_id in list(self.guilds):
                await asyncio.sleep(0)
                await cur.execute(f"select * from cc where guild_id = {guild_id} limit 1;")
                if not cur.rowcount:
                    self.guilds.remove(guild_id)
                    changed = True
        if changed:
            await self.save_config()

    @commands.group(name="cc", description="Shows help for custom commands")
    @commands.cooldown(2, 5, commands.BucketType.channel)
    async def cc(self, ctx):
        if not ctx.invoked_subcommand:
            e = Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Custom Commands", icon_url=self.bot.user.display_avatar.url)
            e.description = "Create commands with custom responses"
            p: str = ctx.prefix
            e.add_field(
                name="◈ Usage",
                value=f"{p}cc add [command] [the cmds response]\n"
                      f"{p}cc remove [command, or pick which after running the command]"
            )
            return await ctx.send(embed=e)

    @cc.group(name="add", description="Creates a custom command")
    async def add(self, ctx, command, *, response):
        if not self.bot.attrs.is_moderator(ctx.author):
            return await ctx.send("You need to be a moderator to manage custom commands")
        if len(command) > 16:
            return await ctx.send("Command names can't be longer than 16 characters")
        if self.bot.get_command(command):
            return await ctx.send(f"Command `{command}` already exists")
        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select * from cc "
                f"where guild_id = {ctx.guild.id} "
                f"and command = %s;", command
            )
            if cur.rowcount:
                return await ctx.send(
                    f"There's already a registered command under that. "
                    f"You can remove it via `{ctx.prefix}cc remove {command}`"
                )
            await cur.execute(
                f"insert into cc values (%s, %s, %s);", (ctx.guild.id, command, response)
            )
        if ctx.guild.id not in self.guilds:
            self.guilds.append(ctx.guild.id)
            await self.save_config()
        if ctx.guild.id in self.cache:
            del self.cache[ctx.guild.id]
        await ctx.send(f"Added {command} as a custom command")

    @cc.command(name="remove", description="Deletes a custom command")
    async def remove(self, ctx, command):
        if not self.bot.attrs.is_moderator(ctx.author):
            return await ctx.send("You need to be a moderator to manage custom commands")
        async with self.bot.utils.cursor() as cur:
            if not command:
                await cur.execute(f"select command from cc where guild_id = {ctx.guild.id};")
                if not cur.rowcount:
                    return await ctx.send("This server has no custom commands")
                commands = [result[0] for result in await cur.fetchall()]
                choices = await GetChoice(ctx, commands, limit=len(commands))
                for choice in choices:
                    await cur.execute(
                        f"delete from cc "
                        f"where guild_id = {ctx.guild.id} "
                        f"and command = %s;", (choice)
                    )
                    await ctx.send(f"Removed `{choice}`")
            else:
                await cur.execute(
                    f"select * from cc "
                    f"where guild_id = {ctx.guild.id} "
                    f"and command = %s;", (command)
                )
                if not cur.rowcount:
                    return await ctx.send(f"`{command}` isn't registered as a custom command")
                await cur.execute(
                    f"delete from cc "
                    f"where guild_id = {ctx.guild.id} "
                    f"and command = %s;", (command)
                )
                await ctx.send(f"Removed `{command}`")
        if ctx.guild.id in self.cache:
            del self.cache[ctx.guild.id]

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if not msg.guild or not msg.guild.owner:
            return
        if msg.guild.id not in self.guilds:
            return
        if len(msg.content.split()) > 1:
            return
        p: list = await get_prefixes_async(self.bot, msg)
        if not msg.content.startswith(p[2]):
            return

        command: str = msg.content.lstrip(p[2]).lower()  # Remove the prefix
        if self.bot.get_command(command):
            return

        if msg.guild.id not in self.cache:
            self.cache[msg.guild.id] = {}
        if command in self.cache[msg.guild.id]:
            response = self.cache[msg.guild.id][command][0]
            if response:
                if self.cd.check(msg.guild.id):
                    if msg.channel.permissions_for(msg.guild.me).add_reactions:
                        await msg.add_reaction("⏳")
                    return
                self.cache[msg.guild.id][command][1] = time()
                if msg.channel.permissions_for(msg.guild.me).send_messages:
                    return await msg.channel.send(response)

        async with self.bot.utils.cursor() as cur:
            await cur.execute(
                f"select response from cc "
                f"where guild_id = {msg.guild.id} "
                f"and command = '{command}' "
                f"limit 1;"
            )
            if cur.rowcount:
                r: tuple = await cur.fetchone()
                response: str = r[0]
                self.cd.check(msg.author.id)
                self.cache[msg.guild.id][command] = [response, time()]
                if msg.channel.permissions_for(msg.guild.me).send_messages:
                    await msg.channel.send(response)
            else:
                self.cache[msg.guild.id][command] = [None, time()]


def setup(bot: Fate):
    bot.add_cog(CustomCommands(bot))
