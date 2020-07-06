import inspect
from datetime import datetime
import platform
import asyncio
import random
import json
import os

from discord.ext import commands
import discord
import psutil

from utils import bytes2human as p, config, colors
from help_embeds import HelpMenus


class Menus(commands.Cog, HelpMenus):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot)

    async def wait_for_dismissal(self, ctx, msg):
        def pred(m):
            return m.channel.id == ctx.channel.id and m.content.lower().startswith('k')

        try:
            reply = await self.bot.wait_for('message', check=pred, timeout=25)
        except asyncio.TimeoutError:
            pass
        else:
            await asyncio.sleep(0.21)
            await ctx.message.delete()
            await asyncio.sleep(0.21)
            await msg.delete()
            await asyncio.sleep(0.21)
            await reply.delete()

    @commands.command(name='help')
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def help(self, ctx, *, args=None):
        async def wait_for_reaction() -> list:
            def check(reaction, user):
                return user == ctx.author

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                try:
                    await msg.edit(content="Menu inactive due to timeout")
                except discord.errors.NotFound:
                    pass
                return [None, None]
            else:
                return [reaction, str(reaction.emoji)]

        if args:
            for cmd in self.bot.commands:
                if cmd.name.lower() == args.lower():
                    if not cmd.usage:
                        return await ctx.send("That command doesn't have extra help information. "
                                              f"Try using `.{cmd.name}` without any args for help")
                    if isinstance(cmd.usage, discord.Embed):
                        e = cmd.usage
                    elif inspect.isclass(cmd.usage):
                        help = cmd.usage(self.bot)
                        e = await help.embed() if help.coro else help.embed()
                    elif inspect.isfunction(cmd.usage):
                        e = cmd.usage()
                    else:
                        return await ctx.send("Oop, my help menu for that command is in an unknown format")
                    return await ctx.send(embed=e)

        emojis = ['🏡', '⏮', '⏪', '⏩', '⏭']
        index = 0; sub_index = None
        ems = [self.default, self.core, self.mod, self.utility, self.fun, self.music]
        embeds = [*[embed_func() for embed_func in ems]]  # call the functions to get their embeds
        if args:
            ems = [e.__name__ for e in ems]
            if args not in ems:
                return await ctx.send("I don't have any commands, or category pages under that name. "
                                      "Try locating it in the help menus then retry with its actual name")
            index = ems.index(args)
        msg = await ctx.send(embed=embeds[index])

        def index_check(index):
            if index > len(embeds) - 1:
                index = len(embeds) - 1
            if index < 0:
                index = 0
            return index

        for emoji in emojis:
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.5)
        while True:
            reaction, emoji = await wait_for_reaction()
            if not reaction:
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages and msg:
                    await msg.clear_reactions()
                return
            if emoji == emojis[0]:  # home
                index = 0; sub_index = None
            if emoji == emojis[1]:
                index -= 2; sub_index = None
                if isinstance(embeds[index], list):
                    sub_index = 0
            if emoji == emojis[2]:
                if isinstance(embeds[index], list):
                    if not isinstance(sub_index, int):
                        sub_index = len(embeds[index]) - 1
                    else:
                        if sub_index == 0:
                            index -= 1; sub_index = None
                            index = index_check(index)
                            if isinstance(embeds[index], list):
                                sub_index = len(embeds[index]) - 1
                        else:
                            sub_index -= 1
                else:
                    index -= 1
                    if isinstance(embeds[index], list):
                        sub_index = len(embeds[index]) - 1
            if emoji == emojis[3]:
                if isinstance(embeds[index], list):
                    if not isinstance(sub_index, int):
                        sub_index = 0
                    else:
                        if sub_index == len(embeds[index]) - 1:
                            index += 1; sub_index = None
                            index = index_check(index)
                            if isinstance(embeds[index], list):
                                sub_index = 0
                        else:
                            sub_index += 1
                else:
                    index += 1
                    index = index_check(index)
                    if isinstance(embeds[index], list):
                        sub_index = 0
            if emoji == emojis[4]:
                index += 2; sub_index = None
                index = index_check(index)
                if isinstance(embeds[index], list):
                    sub_index = 0
            if index > len(embeds) - 1:
                index = len(embeds) - 1
            if index < 0:
                index = 0
            if isinstance(embeds[index], list):
                embeds[index][sub_index].set_footer(text=f'Page {index + 1}/{len(embeds)}')
                if index == len(embeds) - 1:
                    embeds[index][sub_index].set_footer(text=f'Last Page! {index + 1}/{len(embeds)}')
                await msg.edit(embed=embeds[index][sub_index])
            else:
                embeds[index].set_footer(text=f'Page {index + 1}/{len(embeds)}')
                if index == len(embeds) - 1:
                    embeds[index].set_footer(text=f'Last Page! {index + 1}/{len(embeds)}')
                await msg.edit(embed=embeds[index])
            if ctx.channel.permissions_for(self if not ctx.guild else ctx.guild.me).manage_messages:
                await msg.remove_reaction(reaction, ctx.author)

        # Old help command
    # @commands.group(name="help")
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # @commands.bot_has_permissions(embed_links=True)
    # async def _help(self, ctx):
    #     if not ctx.invoked_subcommand:
    #         e = discord.Embed(title="~~~====🥂🍸🍷Help🍷🍸🥂====~~~", color=0x80b0ff)
    #         e.add_field(name="◈ Core ◈",
    #                     value="`leaderboard` `gleaderboard` `ggleaderboard` `mleaderboard` `gmleaderboard` `vcleaderboard` `gvcleaderboard` `changelog` `partners` `servers` `restrict` `unrestrict` `restricted` `config` `prefix` `invite` `realms` `ping` `info` `say`",
    #                     inline=False)
    #         e.add_field(name="◈ Responses ◈", value="`@Fate` `hello` `ree` `kys` `gm` `gn`", inline=False)
    #         e.add_field(name="◈ Music ◈",
    #                     value="`play` `playnow` `playat` `find` `stop` `skip` `previous` `repeat` `pause` `resume` `volume` `queue` `remove` `shuffle` `dc` `np`",
    #                     inline=False)
    #         e.add_field(name="◈ Utility ◈",
    #                     value="`membercount` `channelinfo` `servericon` `serverinfo` `userinfo` `makepoll` `welcome` `farewell` `logger` `color` `emoji` `addemoji` `stealemoji` `rename_emoji` `delemoji` `owner` `avatar` `topic` `timer` `note` `quicknote` `notes` `wiki` `find` `afk` `ud` `id`",
    #                     inline=False)
    #         e.add_field(name="◈ Reactions ◈",
    #                     value="`tenor` `intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `thonk` `shrug` `bite` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`",
    #                     inline=False)
    #         e.add_field(name="◈ Mod ◈",
    #                     value="`modlogs` `addmod` `delmod` `mods` `mute` `unmute` `vcmute` `vcunmute` `warn` `removewarn` `clearwarns` `addrole` `removerole` `restore_roles` `selfroles` `autorole` `limit` `audit` `lock` `lockb` `delete` `purge` `nick` `massnick` `kick` `mute` `ban` `pin`",
    #                     inline=False)
    #         e.add_field(name="◈ Fun ◈",
    #                     value="`personality` `liedetector` `chatbot` `fancify` `factions` `coffee` `encode` `decode` `choose` `notice` `snipe` `mock` `rate` `roll` `soul` `gay` `sue` `ask` `rps` `rr` `cookie` `shoot` `inject` `slice` `boop` `stab`",
    #                     inline=False)
    #         try:
    #             await ctx.author.send(embed=e)
    #             await ctx.send("Help menu sent to dm ✅")
    #         except:
    #             msg = await ctx.send("Failed to send help menu to dm ❎", embed=e)
    #             await self.wait_for_dismissal(ctx, msg)


def setup(bot):
    bot.add_cog(Menus(bot))
