import asyncio
import json
import os
import inspect
import discord
from discord.ext import commands


class CoggyCogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test-help")
    async def test_help(self, ctx):
        c = ConfigureModules(ctx)
        await c.setup()
        while True:
            await c.next()


class ConfigureModules:
    def __init__(self, ctx):
        self.super = ctx.bot.cogs["AntiSpam"]
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id

        self.cursor = {}

        self.row = 0
        self.config = self.key = None

        emojis = ctx.bot.utils.emotes
        self.emotes = [emojis.home, emojis.up, emojis.down, "⏬", emojis.yes]

        self.msg = self.reaction = self.user = None
        self.check = lambda r, u: r.message.id == self.msg.id and u.id == ctx.author.id

    async def setup(self):
        """Initialize the reaction menu"""
        self.cursor = await self.main()
        e = self.create_embed()
        e.add_field(name="◈ Modules", value=await self.get_description())
        self.msg = await self.ctx.send(embed=e)
        self.bot.loop.create_task(self.add_reactions())

    async def reset(self):
        """Go back to the list of enabled modules"""
        self.cursor = await self.main()
        self.row = 0
        self.config = None

    async def main(self):
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
            "Ranking": self.bot.cogs["Ranking"],
            "Fun": {
                "Factions": self.bot.cogs["FactionsRewrite"],
                "Actions": self.bot.cogs["Actions"],
                "Reactions": self.bot.cogs["Reactions"],
                "Misc": self.bot.cogs["Fun"]
            },
            "Music": self.bot.cogs["Music"]
        }

        for key, value in modules.items():
            await asyncio.sleep(0)
            if isinstance(value, commands.Cog):
                value = modules[key] = [value]
            if isinstance(value, list):
                modules[key] = []
                for cog in value:
                    value = modules[key] = [*cog.walk_commands(), *modules[key]]
            if not isinstance(value, dict):
                modules[key] = {cmd: None for cmd in value if "luck" not in str(cmd.checks) and "owner" not in cmd.checks}

            elif isinstance(value, dict):
               for k, v in value.items():
                   await asyncio.sleep(0)
                   if isinstance(v, commands.Cog):
                       v = modules[key][k] = [v]
                   if isinstance(v, list):
                       modules[key][k] = []
                       for cog in v:
                           v = modules[key][k] = [*cog.walk_commands(), *modules[key][k]]
                   if not isinstance(v, dict):
                       modules[key][k] = {cmd: None for cmd in v if "luck" not in str(cmd.checks) and "owner" not in cmd.checks}

        return modules

    def create_embed(self, **kwargs):
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
        keys = list(self.cursor.keys())

        for i, key in enumerate(keys):
            await asyncio.sleep(0)
            if i == self.row:
                description.append(f"{emojis.online} {key}")
            else:
                description.append(f"{emojis.offline} {key}")

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
        reaction, user = await self.bot.utils.get_reaction(self.check)
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
        elif reaction.emoji == "⏬":
            self.row += 5
        # Enter button
        elif str(reaction.emoji) == emojis.yes:
            key = list(self.cursor.keys())[self.row]
            if not self.cursor[key]:
                e.description = self.cursor[key]
                if key in self.config and self.config[key]:
                    await self.init_config(key)
                else:
                    await self.configure(key)
            else:
                e.set_author(name=f"~==🥂🍸🍷{key}🍷🍸🥂==~")
                await self.init_config(key)

        # Adjust row position
        if self.row < 0:
            self.row = len(self.cursor) - 1
        elif self.row > len(self.cursor) - 1:
            self.row = 0

        # Parse the message
        if not e.fields or e.fields[0].name == "◈ Basic Bot Usage":
            e.add_field(name="◈ Categories", value=await self.get_description())
        if self.config:
            if len(e.fields) == 2:
                e.remove_field(0)
            e.set_author(name=f"~==🥂🍸🍷{self.key}🍷🍸🥂==~")
            e.description = ""
            if len(self.cursor) == 1:
                e.set_field_at(0, name="◈ Command Help", value=await self.get_description())
            elif any(v is None for v in self.config.values()):
                e.set_field_at(0, name="◈ Commands", value=await self.get_description())
            else:
                e.set_field_at(0, name="◈ Modules", value=await self.get_description())
        await self.msg.edit(embed=e)

    async def add_reactions(self):
        """Add the reactions in the background"""
        for i, emote in enumerate(self.emotes):
            await self.msg.add_reaction(emote)
            if i != len(self.emotes) - 1:
                await asyncio.sleep(0.21)

    async def get_reply(self, message):
        """Get new values for a config"""
        m = await self.ctx.send(message)
        reply = await self.bot.utils.get_message(self.ctx)
        await m.delete()
        content = reply.content
        await reply.delete()
        return content

    async def update_data(self):
        """Update the cache and database"""
        return

    async def init_config(self, key):
        """Change where we're working at"""
        self.config = self.cursor[key]
        self.key = key
        self.row = 0
        self.cursor = self.cursor[key]

        # Add in options
        # if any(isinstance(v, bool) for v in dict(self.config).values()):
        #     self.cursor["Enable a mod"] = None
        #     self.cursor["Disable a mod"] = None
        # if "per_message" in self.config:
        #     self.cursor["Per-message threshold"] = None
        # if isinstance(self.config, list) or "thresholds" in self.config:
        #     self.cursor["Add a custom threshold"] = None
        #     self.cursor["Remove a custom threshold"] = None
        # self.cursor["Reset to default"] = None

    async def configure(self, key):
        """Alter a configs data"""
        if key == "Reset to default":
            # self.config = defaults[self.key]
            await self.update_data()
            self.reset()

        elif key == "Per-message threshold":
            # Get options to modify the per-message threshold
            self.cursor = {
                "Update": None,
                "Disable": None
            }

        elif key == "Update":
            # Change the per-message threshold
            question = "What's the new number I should set"
            reply = await self.get_reply(question)
            if not reply.isdigit():
                await self.ctx.send("Invalid format. Your reply must be a number", delete_after=5)
            else:
                if int(reply) > 16:
                    await self.ctx.send("At the moment you can't go above 16")
                    return self.reset()
                self.config["per_message"] = int(reply)
                await self.update_data()
            self.reset()

        elif key == "Disable":
            # Remove the per-message threshold
            if isinstance(self.config, dict):  # To satisfy pycharms warning
                self.config["per_message"] = None
            await self.update_data()
            self.reset()

        elif key == "Enable a mod":
            # Set a toggle to True
            question = "Which mod should I enable"
            reply = await self.get_reply(question)
            if reply.lower() not in self.config:
                await self.ctx.send("That's not a toggleable mod", delete_after=5)
            else:
                self.config[reply.lower()] = True
                await self.update_data()
            self.reset()

        elif key == "Disable a mod":
            # Set a toggle to False
            question = "Which mod should I disable"
            reply = await self.get_reply(question)
            if reply.lower() not in self.config:
                await self.ctx.send("That's not a toggleable mod", delete_after=5)
            else:
                self.config[reply.lower()] = False
                await self.update_data()
            self.reset()

        elif key == "Add a custom threshold":
            # Something something something
            if len(self.config) == 3 if isinstance(self.config, list) else len(self.config["thresholds"]) == 3:
                await self.ctx.send("You can't have more than 3 thresholds", delete_after=5)
                return self.reset()
            question = "Send the threshold and timespan to use. Format like " \
                       "`6, 10` to only allow 6 msgs within 10 seconds"
            reply = await self.get_reply(question)
            args = reply.split(", ")
            if not all(arg.isdigit() for arg in args) or len(args) != 2:
                await self.ctx.send("Invalid format", delete_after=5)
            else:
                if int(args[0]) > 60:
                    await self.ctx.send("You can't go above 60s for the timespan")
                    return self.reset()
                if int(args[1]) > 30:
                    await self.ctx.send("You can't go above 30 for the threshold")
                    return self.reset()
                new_threshold = {"timespan": int(args[0]), "threshold": int(args[1])}
                list_check = new_threshold in self.config if isinstance(self.config, list) else False
                dict_check = new_threshold in self.config["thresholds"] if isinstance(self.config, dict) else False
                if list_check or dict_check:
                    await self.ctx.send("That threshold already exists", delete_after=5)
                    return self.reset()
                if isinstance(self.config, list):
                    self.config.append(new_threshold)
                else:
                    self.config["thresholds"].append(new_threshold)
                await self.update_data()
            self.reset()

        elif key == "Remove a custom threshold":
            # Something something something
            question = "Send the threshold and timespan to remove. Format like " \
                       "`6, 10` to remove one with a threshold of 6 and timespan of 10"
            reply = await self.get_reply(question)
            args = reply.split(", ")
            if not all(arg.isdigit() for arg in args) or len(args) != 2:
                await self.ctx.send("Invalid format", delete_after=5)
            else:
                threshold = {"timespan": int(args[1]), "threshold": int(args[0])}
                list_check = threshold in self.config if isinstance(self.config, list) else False
                dict_check = threshold in self.config["thresholds"] if isinstance(self.config, dict) else False
                if not list_check and not dict_check:
                    await self.ctx.send("That threshold doesn't exist", delete_after=5)
                    return self.reset()
                if isinstance(self.config, list):
                    self.config.remove(threshold)
                else:
                    self.config["thresholds"].remove(threshold)
                await self.update_data()
            self.reset()

        else:
            # Something isn't fucking finished
            self.cursor = {"No information available": None}

def setup(bot):
    bot.add_cog(CoggyCogCog(bot))
