"""
cogs.utility.buttonroles
~~~~~~~~~~~~~~~~~~~~~~~~~

A selfroles module using buttons instead of reactions

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from contextlib import suppress
from typing import *

from discord.ext import commands
from discord import ui, Interaction
import discord

from botutils import GetChoice
from fate import Fate


allowed_mentions = discord.AllowedMentions(everyone=False, roles=True, users=False)


class ButtonRoles(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.config = bot.utils.cache("button_roles")
        self.global_cooldown = bot.utils.cooldown_manager(1, 5)
        if bot.is_ready():
            bot.loop.create_task(self.load_menus_on_start())

    @commands.Cog.listener("on_ready")
    async def load_menus_on_start(self):
        if not hasattr(self.bot, "menus_loaded"):
            self.bot.menus_loaded = False
        if not self.bot.menus_loaded:
            for guild_id, menus in self.config.items():
                for msg_id, data in menus.items():
                    if data["style"] == "buttons":
                        self.bot.add_view(RoleView(self, guild_id, msg_id))
                self.bot.menus_loaded = True

    async def refresh_menu(self, guild_id: int, message_id: str):
        """ Re-initiates the View and updates the message content """
        meta: dict = self.config[guild_id][message_id]
        channel = self.bot.get_channel(meta["channel_id"])
        message = await channel.fetch_message(int(message_id))  # type: ignore
        new_view = RoleView(self, guild_id, int(message_id))
        await message.edit(content=meta["text"], view=new_view)

    @commands.group(name="role-menu", aliases=["rolemenu"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    async def role_menu(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Role Menus", icon_url=self.bot.user.avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Create menus for users to self assign roles via buttons or " \
                            "select menus\n**NOTE:** The bot will have you choose which menu to apply a" \
                            "setting to **after** running commands that edit an existing menu"
            p: str = ctx.prefix
            e.add_field(
                name="◈ Usage",
                value=f"**{p}role-menu create**\n"
                      f"{p}role-menu add-role `@role`\n"
                      f"{p}role-menu remove-role `@role`\n"
                      f"{p}edit-message `new message`\n"
                      f"{p}change-emoji `new_emoji`\n"
                      f"{p}set-description `new description`"
            )
            count = 0
            if ctx.guild.id in self.config:
                count = len(self.config[ctx.guild.id])
            e.set_footer(text=f"{count} Active Menu{'s' if count == 0 or count > 1 else ''}")
            await ctx.send(embed=e)

    @role_menu.command(name="create")
    @commands.has_permissions(administrator=True)
    async def create_menu(self, ctx):
        """ The command for interactively setting up a new menu """
        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name="Instructions", icon_url=ctx.author.avatar.url)
        e.description = "> **Send the name of the role you want me to add**\nOr here's an example message " \
                        "with advanced formatting:\n```💚 | SomeDisplayLabel | [role_id, role name, or ping]\n" \
                        "some description on what it does```"
        e.set_footer(text="Reply with 'done' when complete")

        # Get the roles
        msg = await ctx.send(embed=e)
        selected_roles = {}
        while True:
            reply = await self.bot.utils.get_message(ctx)
            if "cancel" in reply.content.lower():
                return await msg.delete()
            if reply.content.lower() == "done":
                await msg.delete()
                await reply.delete()
                break

            name: Optional[str] = reply.content
            emoji: Optional[str] = None
            label: Optional[str] = None
            description: Optional[str] = None

            args = list(reply.content.split("\n")[0].split(" | "))
            if len(args) > 1:
                # Set the emoji
                if all(c.lower() == c.upper() for c in args[0]) or "<" in args[0]:
                    emoji = args[0]
                    args.pop(0)

                # Set the label
                if len(args) > 1:
                    label = args[0]
                    args.pop(0)

                # Get the role with the remaining args instead of msg content
                if emoji or label:
                    name = " ".join(args)

            # Set the description
            if "\n" in reply.content:
                description = reply.content.split("\n")[1]

            role = await self.bot.utils.get_role(ctx, name or reply.content)
            if not role:
                await ctx.send("Role not found", delete_after=5)
                await reply.delete()
                continue

            selected_roles[role] = {
                "emoji": emoji,
                "label": label,
                "description": description
            }

            if e.fields:
                e.remove_field(0)
            e.add_field(
                name="◈ Selected Roles",
                value="\n".join([f"• {role.mention}" for role in selected_roles.keys()])
            )
            await msg.edit(embed=e)
            await reply.delete()

            if len(selected_roles) == 25:
                break

        # Set the style of the menu
        if len(selected_roles) == 1:
            style = "buttons"
        else:
            m = await ctx.send("Should I use a select menu or buttons. Reply with 'select' or 'buttons'")
            reply = await self.bot.utils.get_message(ctx)
            if "button" in reply.content.lower():
                style = "buttons"
            else:
                style = "select"
            await ctx.send(f"Alright, I'll use a {style} menu", delete_after=5)
            await m.delete()
            await reply.delete()

        # Set the channel
        m = await ctx.send("#Mention the channel you want me to use")
        reply = await self.bot.utils.get_message(ctx)
        if not reply.channel_mentions:
            return await ctx.send("You didn't #mention a channel, rerun the command")
        channel = reply.channel_mentions[0]
        await m.delete()
        await reply.delete()

        msg = await channel.send("Choose your role")
        if ctx.guild.id not in self.config:
            self.config[ctx.guild.id] = {}
        self.config[ctx.guild.id][str(msg.id)] = {
            "channel_id": channel.id,
            "label": "Select your role",
            "roles": {
                str(role.id): metadata for role, metadata in selected_roles.items()
            },
            "text": "Choose your role",
            "style": style,
            "limit": 1
        }
        view = RoleView(cls=self, guild_id=ctx.guild.id, message_id=msg.id)
        await msg.edit(view=view)
        await self.config.flush()

    async def get_menu_id(self, ctx) -> str:
        """ Gets the message_id of the wanted menu """
        menus = {
            meta["text"].split("\n")[0]: message_id
            for message_id, meta in self.config[ctx.guild.id].items()
        }
        if len(menus) == 1:
            choice: str = list(menus.keys())[0]
        else:
            choice: str = await GetChoice(ctx, menus.keys())
        return menus[choice]

    @role_menu.command(name="add-role")
    @commands.has_permissions(administrator=True)
    async def add_role(self, ctx, *, role):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("There arent any active role menus in this server")
        message_id = await self.get_menu_id(ctx)
        if len(self.config[guild_id][message_id]["roles"]) == 25:
            return await ctx.send("You can't have more than 25 roles in a menu")

        name: Optional[str] = role
        emoji: Optional[str] = None
        label: Optional[str] = None
        description: Optional[str] = None

        args = list(role.split("\n")[0].split(" | "))
        if len(args) > 1:
            # Set the emoji
            if all(c.lower() == c.upper() for c in args[0]) or "<" in args[0]:
                emoji = args[0]
                args.pop(0)

            # Set the label
            if len(args) > 1:
                label = args[0]
                args.pop(0)

            # Get the role with the remaining args instead of msg content
            if emoji or label:
                name = " ".join(args)

        # Set the description
        if "\n" in role:
            description = role.split("\n")[1]

        role = await self.bot.utils.get_role(ctx, name)
        if not role:
            return await ctx.send("Role not found")
        if str(role.id) in self.config[guild_id][message_id]["roles"]:
            return await ctx.send("That role's already added")

        self.config[guild_id][message_id]["roles"][str(role.id)] = {
            "emoji": emoji,
            "label": label,
            "description": description
        }

        await self.refresh_menu(guild_id, message_id)
        await ctx.send(f"Added {role.mention}", allowed_mentions=discord.AllowedMentions.none())
        await self.config.flush()

    @role_menu.command(name="remove-role")
    @commands.has_permissions(administrator=True)
    async def remove_role(self, ctx, *, role):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("There arent any active role menus in this server")
        message_id = await self.get_menu_id(ctx)

        role = await self.bot.utils.get_role(ctx, role)
        if not role:
            return await ctx.send("Role not found")
        if str(role.id) not in self.config[guild_id][message_id]["roles"]:
            return await ctx.send(
                f"{role.mention} role isn't in that menu",
                allowed_mentions=discord.AllowedMentions.none()
            )

        del self.config[guild_id][message_id]["roles"][str(role.id)]
        await self.refresh_menu(guild_id, message_id)

        await ctx.send(f"Removed {role.mention}", allowed_mentions=discord.AllowedMentions.none())
        await self.config.flush()

    @commands.command(name="edit-message")
    @commands.has_permissions(administrator=True)
    async def edit_message(self, ctx, *, new_message):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("There arent any active role menus in this server")

        message_id = await self.get_menu_id(ctx)
        self.config[guild_id][message_id]["text"] = new_message

        await self.refresh_menu(guild_id, message_id)
        await ctx.send(f"Successfully edited the content 👍")
        await self.config.flush()

    @commands.command(name="change-emoji")
    @commands.has_permissions(administrator=True)
    async def change_emoji(self, ctx, *, new_emoji):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("There arent any active role menus in this server")
        message_id = await self.get_menu_id(ctx)

        roles = {}
        for role_id, meta in self.config[guild_id][message_id]["roles"].items():
            role = ctx.guild.get_role(int(role_id))
            if not role:
                continue
            roles[meta["label"] or role.name] = role_id

        if len(roles) == 1:
            choice: str = list(roles.values())[0]
        else:
            choice: str = await GetChoice(ctx, roles.keys())
        self.config[guild_id][message_id]["roles"][roles[choice]]["emoji"] = new_emoji

        await self.refresh_menu(guild_id, message_id)
        await ctx.send(f"Successfully set the emoji 👍")
        await self.config.flush()

    @commands.command(name="set-description")
    @commands.has_permissions(administrator=True)
    async def set_description(self, ctx, *, new_description):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("There arent any active role menus in this server")
        message_id = await self.get_menu_id(ctx)

        roles = {}
        for role_id, meta in self.config[guild_id][message_id]["roles"].items():
            role = ctx.guild.get_role(int(role_id))
            if not role:
                continue
            roles[meta["label"] or role.name] = role_id

        if len(roles) == 1:
            choice: str = list(roles.values())[0]
        else:
            choice: str = await GetChoice(ctx, roles.keys())
        self.config[guild_id][message_id]["roles"][roles[choice]]["description"] = new_description

        await self.refresh_menu(guild_id, message_id)
        await ctx.send(f"Successfully set the description 👍")
        await self.config.flush()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id in self.config:
            if str(payload.message_id) in self.config[payload.guild_id]:
                await self.config.remove_sub(payload.guild_id, str(payload.message_id))
                if not self.config[payload.guild_id]:
                    await self.config.remove(payload.guild_id)


class RoleView(ui.View):
    def __init__(self, cls: ButtonRoles, guild_id: int, message_id: int):
        self.bot = cls.bot
        self.config = cls.config
        self.guild_id = guild_id
        self.message_id = message_id

        # Replacing existing instances to refresh information
        if guild_id not in self.bot.views:
            self.bot.views[guild_id] = {}
        if message_id in self.bot.views[guild_id]:
            self.bot.views[guild_id][message_id].stop()
        self.bot.views[guild_id][message_id] = self

        conf: Dict[str, Optional[Any]] = cls.config[guild_id][str(message_id)]
        self.style: str = cls.config[guild_id][str(message_id)]["style"]
        self.limit: int = conf["limit"]

        self.buttons = {}

        # Setup cooldowns for interactions
        self.global_cooldown = cls.global_cooldown
        cd = [5, 25]
        if self.style == "buttons":
            cd = [5, 60]
        self.cooldown = cls.bot.utils.cooldown_manager(*cd)

        super().__init__(timeout=None)

        if self.style == "buttons":
            data = self.config[guild_id][str(message_id)]
            guild = self.bot.get_guild(guild_id)
            for role_id in data["roles"].keys():
                role = guild.get_role(int(role_id))
                if not role:
                    continue

                # Add a new button to the class
                button = ui.Button(
                    label=role.name,
                    style=discord.ButtonStyle.blurple,
                    custom_id=f"{role_id}@{message_id}"
                )
                button.callback = self.surface_callback
                self.buttons[button.custom_id] = button
                self.add_item(button)
        else:
            self.menu = Select(self, message_id, self.index)
            self.add_item(self.menu)

    @property
    def index(self) -> dict:
        index = {}
        guild = self.bot.get_guild(self.guild_id)
        for role_id, meta in self.config[self.guild_id][str(self.message_id)]["roles"].items():
            role = guild.get_role(int(role_id))
            if role:
                index[role] = meta
        return index

    async def on_error(self, _error, _item, _interaction) -> None:
        pass

    async def surface_callback(self, interaction) -> None:
        """ Handle cooldowns and suppress exceptions in the actual callback function """
        with suppress(discord.errors.NotFound):
            check1 = self.global_cooldown.check(interaction.user.id)
            check2 = self.cooldown.check(interaction.user.id)
            if check1 or check2:
                return await interaction.response.send_message(
                    "You're on cooldown, try again in a moment", ephemeral=True
                )
            if self.style == "buttons":
                await self.button_callback(interaction)
            else:
                await self.select_callback(interaction)

    async def button_callback(self, interaction: Interaction) -> Optional[discord.Message]:
        """ The callback function for when a buttons pressed """

        async def remove_button(reason) -> discord.Message:
            """ Remove a button that can no longer be used """
            self.remove_item(self.buttons[custom_id])
            with suppress(KeyError):
                self.config[self.guild_id][key]["roles"].remove(role_id)
            await self.config.flush()
            await interaction.message.edit(view=self)
            return await interaction.response.send_message(reason, ephemeral=True)

        # Parse the key and get its relative data
        custom_id = interaction.data["custom_id"]
        key = custom_id.split("@")[1]
        role_id = int(custom_id.split("@")[0])

        # Fetch required variables
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id)
        role = guild.get_role(role_id)
        name = self.buttons[custom_id].label

        if not guild or not member:
            return  # Cache isn't properly established
        if not role:
            return await remove_button(f"{name} doesn't seem to exist anymore")
        if role.position >= guild.me.top_role.position:
            return await remove_button(f"{name} is too high for me to manage")

        if role in member.roles:
            await member.remove_roles(role)
            action = "Removed"
        else:
            action = "Gave you"
            await member.add_roles(role)
        await interaction.response.send_message(
            f"{action} {role.mention}",
            ephemeral=True
        )

    async def select_callback(self, interaction: Interaction) -> Optional[discord.Message]:
        """ The callback function for when a buttons pressed """

        async def adjust_options(reason) -> discord.Message:
            """ Remove a button that can no longer be used """
            self.clear_items()
            self.menu = Select(self, self.message_id, self.index)
            await interaction.message.edit(view=self)
            return await interaction.response.send_message(reason, ephemeral=True)

        # Fetch required variables
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id)
        if not guild or not member:
            return  # Cache isn't properly established

        # Give selected roles
        for role_id in interaction.data["values"]:
            role = guild.get_role(int(role_id))
            if not role:
                return await adjust_options(f"{role_id} doesn't seem to exist anymore")

            if role.position >= guild.me.top_role.position:
                self.config[self.guild_id]["roles"].remove(role.id)
                return await adjust_options(f"{role_id} is too high for me to manage")

            if role not in member.roles:
                await member.add_roles(role)

        # Take away unselected roles
        for role in self.index:
            if str(role.id) not in interaction.data["values"]:
                if role in member.roles:
                    await member.remove_roles(role)

        await interaction.response.send_message(
            "Successfully set your roles",
            ephemeral=True
        )


class Select(discord.ui.Select):
    def __init__(self, cls: RoleView, msg_id: int, roles: dict):
        self.cls = cls

        # Prepare the components for the dropdown menu
        options = []
        for role, meta in roles.items():
            meta = dict(meta)
            label = meta.pop("label")
            option = discord.SelectOption(
                label=label or role.name[:25],
                value=str(role.id),
                **meta
            )
            options.append(option)

        super().__init__(
            custom_id=f"select_{msg_id}",
            placeholder="Select a Role",
            min_values=1,
            max_values=self.cls.limit,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """ Let the main View class handle the interaction """
        await self.cls.surface_callback(interaction)


def setup(bot: Fate):
    bot.add_cog(ButtonRoles(bot))
