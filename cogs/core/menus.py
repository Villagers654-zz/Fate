import asyncio
import inspect
from contextlib import suppress

import discord
from discord.ext import commands
from discord.errors import NotFound, Forbidden, HTTPException


command_attrs = (commands.core.Command, commands.core.Group)


class Menus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.cooldown(1, 3, commands.BucketType.channel)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def help(self, ctx, *, args=None):
        if args:
            for cmd in self.bot.commands:
                await asyncio.sleep(0)
                if cmd.name.lower() == args.lower():
                    if not cmd.usage:
                        return await ctx.send(
                            "That command doesn't have extra help information. "
                            f"Try using `.{cmd.name}` without any args for help"
                        )
                    if isinstance(cmd.usage, discord.Embed):
                        e = cmd.usage
                    elif inspect.isclass(cmd.usage):
                        _help = cmd.usage(self.bot)
                        e = await _help.embed() if _help.coro else _help.embed()
                    elif inspect.isfunction(cmd.usage):
                        e = cmd.usage()
                    else:
                        return await ctx.send(
                            "Oop, my help menu for that command is in an unknown format"
                        )
                    return await ctx.send(embed=e)

        c = ConfigureModules(ctx)
        await c.setup()
        while True:
            await c.next()


class ConfigureModules:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id

        self.cursor = {}
        self.row = 0
        self.config = self.key = self.command = None

        emojis = ctx.bot.utils.emotes
        self.emotes = [
            getattr(emojis, name) for name in [
                "home", "up", "down", "double_down", "yes"
            ]
        ]

        self.msg = self.reaction = self.user = None
        self.check = lambda r, u: r.message.id == self.msg.id and u.id == ctx.author.id

    async def setup(self):
        """Initialize the reaction menu"""
        self.cursor = await self.main()
        e = self.create_embed()
        e.add_field(name="◈ Categories", value=await self.get_description())
        self.msg = await self.ctx.send(embed=e)
        self.bot.loop.create_task(self.add_reactions())

    async def reset(self):
        """Go back to the list of enabled modules"""
        self.cursor = await self.main()
        self.row = 0
        self.config = None

    async def main(self):
        """The structure of the help menu"""
        sort = ["Mod Cmds", "Misc"]
        modules = {
            "Core": [
                self.bot.cogs["Core"],
                self.bot.cogs["Statistics"],
                self.bot.cogs["ServerList"]
            ],
            "Moderation": {
                "Mod Cmds": [
                    self.bot.cogs["Moderation"],
                    self.bot.cogs["Lock"]
                ],
                "Modmail": [
                    self.bot.cogs["ModMail"],
                    self.bot.cogs["CaseManager"]
                ],
                "Logger": self.bot.cogs["Logger"],
                "AntiSpam": self.bot.cogs["AntiSpam"],
                "AntiRaid": self.bot.cogs["AntiRaid"],
                "Chatfilter": self.bot.cogs["ChatFilter"],
                "Verification": self.bot.cogs["Verification"]
            },
            "Utility": {
                "Welcome Messages": self.bot.cogs["Welcome"],
                "Leave Messages": self.bot.cogs["Leave"],
                "AutoRole": self.bot.cogs["AutoRole"],
                "Self-Roles": self.bot.cogs["SelfRoles"],
                "Restore-Roles": self.bot.cogs["RestoreRoles"],
                "Emojis": self.bot.cogs["Emojis"],
                "Vc-Log": self.bot.cogs["VcLog"],
                "Chat Bridges": self.bot.cogs["ChatBridges"],
                "Suggestions": self.bot.cogs["Suggestions"],
                "Misc": [
                    self.bot.cogs["SafePolls"],
                    self.bot.cogs["Audit"],
                    self.bot.cogs["Embeds"],
                    self.bot.cogs["Notepad"],
                    self.bot.cogs["Utility"]
                ]
            },
            "Ranking": self.bot.cogs["Ranking"],
            "Fun": {
                "Factions": self.bot.cogs["FactionsRewrite"],
                "Actions": self.bot.cogs["Actions"],
                "Reactions": self.bot.cogs["Reactions"],
                "Misc": self.bot.cogs["Fun"]
            },
            "Music": self.bot.cogs["Music"]
        }

        # Iterate through the help menu and convert values
        can_run = lambda cmd: "luck" not in str(cmd.checks) and "owner" not in str(cmd.checks)
        for key, value in modules.items():
            await asyncio.sleep(0)
            if isinstance(value, commands.Cog):
                value = modules[key] = [value]
            if isinstance(value, list):
                modules[key] = []
                for cog in value:
                   value = modules[key] = [*cog.walk_commands(), *modules[key]]
            if not isinstance(value, dict):
                modules[key] = {
                    cmd: None for cmd in value if can_run(cmd)
                }

            elif isinstance(value, dict):
                for k, v in value.items():
                    await asyncio.sleep(0)
                    if isinstance(v, commands.Cog):
                        v = modules[key][k] = [v]
                    if isinstance(v, list):
                        modules[key][k] = []
                        for cog in v:
                            if k in sort:
                                v = modules[key][k] = [
                                    *sorted(cog.walk_commands(), key=lambda c: c.name),
                                    *modules[key][k]
                                ]
                            else:
                                v = modules[key][k] = [*cog.walk_commands(), *modules[key][k]]
                    if not isinstance(v, dict):
                        if k in sort:
                            modules[key][k] = {
                                cmd: None for cmd in sorted(v, key=lambda c: c.name) if can_run(cmd)
                            }
                        else:
                            modules[key][k] = {
                                cmd: None for cmd in v if can_run(cmd)
                            }

        return modules

    def create_embed(self):
        """Get default embed style"""
        e = discord.Embed(color=8433919)
        owner = self.bot.get_user(264838866480005122)
        e.set_author(name="~==🥂🍸🍷Help🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            f"[Support Server]({self.bot.config['support_server']}) | "
            f"[Bot Invite]({self.bot.invite_url})"
        )
        usage = (
            "• using a cmd with no args will usually send its help menu\n"
            "• try using `.module enable` instead of `.enable module`"
        )
        e.add_field(name="◈ Basic Bot Usage", value=usage, inline=False)
        return e

    async def get_description(self):
        # Format the current options
        emojis = self.bot.utils.emotes
        description = []
        keys = [k for k in list(self.cursor.keys()) if k != "command_help"]

        for i, key in enumerate(keys):
            await asyncio.sleep(0)
            if i == self.row:
                description.append(f"{emojis.online} {key}")
            else:
                description.append(f"{emojis.offline} {key}")

        # Show only the 9 options above and below the selected row if there's
        # more than 18 options, and if the current row is at the top or bottom
        # of the options list only show the first or last 18 to keep the amount
        # of options showing the same
        if len(keys) > 18:
            max_scroll = len(keys) - 9
            if self.row > 9 and self.row < max_scroll:
                l = self.row - 9
                r = len(keys) - (l + 18)
                description = description[l:-r]
                description = [emojis.up * 5, *description]
            else:
                if self.row < max_scroll:
                    description = description[:18]
                else:
                    description = [emojis.up * 5, *description[-18:]]

            if self.row < max_scroll:
                description.append(emojis.down * 5)

        return "\n".join(description)[:1024]

    async def next(self):
        """Wait for the next reaction"""
        try:
            reaction, user = await self.bot.utils.get_reaction(self.check, ignore_timeout=False)
        except asyncio.TimeoutError:
            with suppress(NotFound, Forbidden, HTTPException):
                await self.msg.clear_reactions()
            raise self.bot.ignored_exit
        if reaction:
            self.bot.loop.create_task(self.msg.remove_reaction(reaction, user))
        e = self.create_embed()
        emojis = self.bot.utils.emotes

        # Home button
        if reaction.emoji == emojis.home:
            await self.reset()
        # Up button
        elif reaction.emoji == emojis.up:
            self.row -= 1
        # Down button
        elif reaction.emoji == emojis.down:
            self.row += 1
        # Double down button
        elif reaction.emoji == emojis.double_down:
            self.row += 5
        # Enter button
        elif str(reaction.emoji) == emojis.yes:
            row = int(self.row)
            if "command_help" in self.cursor:
                if row != len(self.cursor.keys()) - 1:
                    row += 1
            key = list(self.cursor.keys())[row]
            if not self.cursor[key]:
                e.description = self.cursor[key]
                if key in self.config and self.config[key]:
                    await self.init_config(key)
                else:
                    await self.configure(key)
            elif isinstance(self.cursor[key], discord.Embed):
                await self.configure(key)
            elif inspect.iscoroutine(self.cursor[key]):
                await self.configure(key)
            else:
                e.set_author(name=f"~==🥂🍸🍷{key}🍷🍸🥂==~")
                await self.init_config(key)

        # Adjust row position
        if self.row < 0:
            self.row = len(self.cursor.keys()) - 1
        elif self.row > len(self.cursor.keys()) - 1:
            self.row = 0

        # Parse the message
        if not e.fields or e.fields[0].name == "◈ Basic Bot Usage":
            e.add_field(name="◈ Categories", value=await self.get_description())
        if self.config:
            if len(e.fields) == 2:
                e.remove_field(0)
            e.set_author(name=f"~==🥂🍸🍷{self.key}🍷🍸🥂==~")
            e.description = ""
            description = await self.get_description()

            # Operating on an individual command
            if "command_help" in self.cursor or "Command Help" in self.cursor:
                cmd_name = self.command[0].upper() + self.command[1:]
                if "command_help" in self.cursor:
                    usage = self.cursor["command_help"]
                    e.set_field_at(0, name=f"◈ {cmd_name} Help", value=usage, inline=False)
                    e.add_field(name="◈ Toggles", value=description, inline=False)
                else:
                    e.set_field_at(0, name="◈ Options", value=description, inline=False)

                index = 1
                if len(e.fields) == 1:
                    index = 0
                    e.description = f"> {cmd_name} Help"
                cmd = self.bot.get_command(self.command)
                if cmd and cmd.aliases:
                    aliases = ", ".join(f"`{alias}`" for alias in cmd.aliases)
                    e.insert_field_at(index, name="◈ Aliases", value=aliases, inline=False)

            # Showing a list of commands inside a category
            elif any(v is None for v in self.config.values()):
                e.set_field_at(0, name="◈ Commands", value=description)

            # Showing all the categories
            else:
                e.set_field_at(0, name="◈ Modules", value=description)

        await self.msg.edit(embed=e)

    async def add_reactions(self):
        """Add the reactions in the background"""
        with suppress(NotFound, Forbidden):
            for i, emote in enumerate(self.emotes):
                await self.msg.add_reaction(emote)
                if i != len(self.emotes) - 1:
                    await asyncio.sleep(0.21)

    async def init_config(self, key):
        """Change where we're working at"""
        self.row = 0
        if isinstance(self.cursor[key], discord.Embed) or inspect.iscoroutine(self.cursor[key]):
            return
        self.config = self.cursor = self.cursor[key]
        self.key = key

    async def configure(self, key):
        """Alter a configs data"""

        # Enable the command
        if key == "Enable":
            cmd = self.bot.get_command("enable-command")
            if await cmd.can_run(self.ctx):
                await cmd.__call__(ctx=self.ctx, command=self.command)
            else:
                await self.ctx.send("You can't run this command")

        # Disable the command
        elif key == "Disable":
            cmd = self.bot.get_command("disable-command")
            if await cmd.can_run(self.ctx):
                await cmd.__call__(ctx=self.ctx, command=self.command)
            else:
                await self.ctx.send("You can't run this command")

        # Select the commands help embed
        elif key == "Command Help":
            usage = self.cursor[key]
            if isinstance(usage, discord.Embed):
                await self.ctx.send(embed=usage)
            elif inspect.iscoroutine(usage):
                with suppress(RuntimeError):
                    await usage

        # Viewing a commands help
        else:
            self.command = str(key)
            cmd = self.bot.get_command(str(key))
            cog = cmd.cog  # type: commands.Cog
            self.cursor = {}
            help = "No help"

            usage_attr = str(key).split()[0].replace("-", "_") + "_usage"
            if hasattr(cog, usage_attr):
                usage = getattr(cog, usage_attr)

                # Do conversion from function to value/awaitable
                if hasattr(usage, "__call__"):
                    if isinstance(usage, command_attrs):
                        usage = usage(self.ctx)
                    elif "ctx" in usage.__code__.co_varnames:
                        usage = usage(self.ctx)
                    else:
                        usage = usage()

                if isinstance(usage, str):
                    help = usage
                elif isinstance(usage, discord.Embed):
                    self.cursor["Command Help"] = usage
                elif inspect.iscoroutine(usage):
                    self.cursor["Command Help"] = usage

            if not self.cursor:
                self.cursor["command_help"] = help
            self.cursor = {
                **self.cursor,
                "Enable": None,
                "Disable": None
            }


def setup(bot):
    bot.add_cog(Menus(bot))
