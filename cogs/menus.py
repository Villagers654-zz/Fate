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
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    async def help(self, ctx, *, args=None):
        async def wait_for_reaction() -> list:
            def check(reaction, user):
                return user == ctx.author

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
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
                return await msg.clear_reactions()
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

    @commands.command(name='stats', description="Provides information relevant to the bots stats")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def stats(self, ctx):
        guilds = len(list(self.bot.guilds))
        users = len(list(self.bot.users))
        path = os.getcwd() + "/data/images/banners/" + random.choice(os.listdir(os.getcwd() + "/data/images/banners/"))
        bot_pid = psutil.Process(os.getpid())
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Fate [Zerø]: Core Info", icon_url=self.bot.get_user(config.owner_id()).avatar_url)
        stats = self.bot.get_stats  # type: dict
        commands = 0;
        lines = 0
        for command_date in stats['commands']:
            date = datetime.strptime(command_date, '%Y-%m-%d %H:%M:%S.%f')
            if (datetime.now() - date).days < 7:
                commands += 1
            else:
                index = stats['commands'].index(command_date)
                stats['commands'].pop(index)
                with open('./data/stats.json', 'w') as f:
                    json.dump(stats, f, ensure_ascii=False)
        with open('fate.py', 'r') as f:
            lines += len(f.readlines())
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                with open(f'./cogs/{file}', 'r') as f:
                    lines += len(f.readlines())
        e.description = f'Weekly Commands Used: {commands}\n' \
                        f'Total lines of code: {lines}'
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.set_image(url="attachment://" + os.path.basename(path))
        e.add_field(name="◈ Summary ◈", value="Fate is a ~~multipurpose~~ hybrid bot created for fun", inline=False)
        e.add_field(name="◈ Statistics ◈",
                    value=f'Commands: [{len(self.bot.commands)}]\nModules: [{len(self.bot.extensions)}]\nServers: [{guilds}]\nUsers: [{users}]')
        e.add_field(name="◈ Credits ◈", value="• Tothy ~ `rival`\n• Cortex ~ `teacher`\n• Discord.py ~ `existing`")
        e.add_field(name="◈ Memory ◈", value=
        f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
        f"__**RAM**__: [{p.bytes2human(psutil.virtual_memory().used)}/{p.bytes2human(psutil.virtual_memory().total)}] ({psutil.virtual_memory().percent}%)\n"
        f"__**Bot RAM**__: {p.bytes2human(bot_pid.memory_full_info().rss)} ({round(bot_pid.memory_percent())}%)\n"
        f"__**CPU**__: **Global**: {psutil.cpu_percent()}% **Bot**: {bot_pid.cpu_percent()}%\n")
        uptime = (datetime.now() - self.bot.start_time)
        e.add_field(name="◈ Uptime ◈",
                    value=f'{uptime.days} days {round(uptime.seconds / 60 / 60)} hours and {round(uptime.seconds / 60)} minutes')
        e.set_footer(text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}",
                     icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png")
        msg = await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
        await self.wait_for_dismissal(ctx, msg)

    @commands.command(name="realms")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def realms(self, ctx):
        e = discord.Embed(title="~~~====🥂🍸🍷Realms🍷🍸🥂====~~~", color=0x80b0ff)
        e.add_field(name="• Anarchy Realms",
                    value="Jappie Anarchy\n• https://realms.gg/pmElWWx5xMk\nAnarchy Realm\n• https://realms.gg/GyxzF5xWnPc\n2c2b Anarchy\n• https://realms.gg/TwbBfe0jGDc\nFraughtian Anarchy\n• https://realms.gg/rdK57KvnA8o\nChaotic Realm\n• https://realms.gg/nzDX1drovu4",
                    inline=False)
        e.add_field(name="• Misc", value=".", inline=False)
        msg = await ctx.send(embed=e)
        await self.wait_for_dismissal(ctx, msg)

    @commands.command(name="partners")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.bot_has_permissions(embed_links=True)
    async def partners(self, ctx):
        luck = self.bot.get_user(264838866480005122)
        bottest = self.bot.get_guild(501868216147247104)
        fourbfourt = "https://discord.gg/BQ23Z2E"
        totherbot = "https://discordapp.com/api/oauth2/authorize?client_id=452289354296197120&permissions=0&scope=bot"
        spookiehotel = "https://discord.gg/DVcF6Yn"
        threadysserver = "https://discord.gg/6tcqMUt"
        e = discord.Embed(color=0xffffff)
        e.set_author(name=f'🥃🥂🍸🍷Partners🍷🍸🥂🥃', icon_url=luck.avatar_url)
        e.description = "Wanna partner? dm Luck#1574"
        e.set_thumbnail(url=bottest.icon_url)
        e.add_field(name="◈ Servers ◈",
                    value=f'• [Threadys Server]({threadysserver})\n• [Spookie Hotel]({spookiehotel})\n• [4b4t]({fourbfourt})',
                    inline=False)
        e.add_field(name="◈ Bots ◈", value=f'• [TotherBot]({totherbot})', inline=False)
        msg = await ctx.send(embed=e)
        await self.wait_for_dismissal(ctx, msg)


def setup(bot):
    bot.add_cog(Menus(bot))
