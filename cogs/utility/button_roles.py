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

from botutils import Conversation
from fate import Fate


allowed_mentions = discord.AllowedMentions(everyone=False, roles=True, users=False)


class ButtonRoles(commands.Cog):
    def __init__(self, bot: Fate):
        self.bot = bot
        self.menus = bot.utils.cache("button_roles")
        for key in list(self.menus.keys()):
            self.menus.remove(key)
        self.global_cooldown = bot.utils.cooldown_manager(1, 5)
        if bot.is_ready():
            bot.loop.create_task(self.load_menus_on_start())

    @commands.Cog.listener("on_ready")
    async def load_menus_on_start(self):
        if not hasattr(self.bot, "menus_loaded"):
            self.bot.menus_loaded = False
        if not self.bot.menus_loaded:
            for guild_id, menus in self.menus.items():
                for msg_id, data in menus.items():
                    if data["style"] == "buttons":
                        self.bot.add_view(ButtonMenu(self, guild_id, msg_id))
                self.bot.menus_loaded = True

    @commands.group(name="role-menu", aliases=["rolemenu"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def role_menu(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Role Menus", icon_url=self.bot.user.avatar.url)
            if ctx.guild.icon:
                e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Create menus for users to self assign roles via buttons\n**NOTE:** this feature is in beta"
            p: str = ctx.prefix
            e.add_field(
                name="◈ Usage",
                value=f"{p}role-menu create\n"
                      f"{p}~~role-menu set-message `msg_id` `new message`~~\n"
                      f"{p}~~role-menu add-role `msg_id` `@role`~~\n"
                      f"{p}~~role-menu remove-role `msg_id` `@role`~~\n"
                      f"{p}~~role-menu set-style `msg_id` `button/dropdown`~~"
            )
            count = 0
            if ctx.guild.id in self.menus:
                count = len(self.menus[ctx.guild.id])
            e.set_footer(text=f"{count} Active Menu")
            if count == 0 or count > 1:
                e.footer.text += "s"
            await ctx.send(embed=e)

    @role_menu.command(name="create")
    @commands.has_permissions(administrator=True)
    async def create_menu(self, ctx):
        e = discord.Embed(color=self.bot.config["theme_color"])
        e.set_author(name="Instructions", icon_url=ctx.author.avatar.url)
        e.description = "> Send the name of the role you want me to add"
        e.set_footer(text="Reply with 'done' when complete")

        # Get the roles
        msg = await ctx.send(embed=e)
        data = []
        while True:
            reply = await self.bot.utils.get_message(ctx)
            if "cancel" in reply.content.lower():
                return await msg.delete()
            if reply.content.lower() == "done":
                await msg.delete()
                await reply.delete()
                break
            role = await self.bot.utils.get_role(ctx, reply.content)
            if not role:
                await ctx.send("Role not found", delete_after=5)
                await reply.delete()
                continue
            data.append(role)
            if e.fields:
                e.remove_field(0)
            e.add_field(
                name="◈ Selected Roles",
                value="\n".join([f"• {role.mention}" for role in data])
            )
            await msg.edit(embed=e)
            await reply.delete()

        # Set the style of the menu
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
        if ctx.guild.id not in self.menus:
            self.menus[ctx.guild.id] = {}
        self.menus[ctx.guild.id][str(msg.id)] = {
            "roles": [r.id for r in data],
            "text": "Select your role",
            "style": style,
        }
        view = ButtonMenu(cls=self, guild_id=ctx.guild.id, message_id=msg.id)
        await msg.edit(view=view)
        await self.menus.flush()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id in self.menus:
            if str(payload.message_id) in self.menus[payload.guild_id]:
                await self.menus.remove_sub(payload.guild_id, str(payload.message_id))


class ButtonMenu(ui.View):
    def __init__(self, cls: ButtonRoles, guild_id: int, message_id: int):
        self.bot = cls.bot
        self.menus = cls.menus
        self.guild_id = guild_id
        self.message_id = message_id

        self.buttons = {}
        self._index = {}
        self.style = self.menus[guild_id][str(message_id)]["style"]

        self.global_cooldown = cls.global_cooldown
        cd = [5, 25] if self.style == "buttons" else [5, 60]
        self.cooldown = cls.bot.utils.cooldown_manager(*cd)

        super().__init__(timeout=None)

        if self.style == "buttons":
            data = self.menus[guild_id][str(message_id)]
            guild = self.bot.get_guild(guild_id)
            for role_id in data["roles"]:
                role = guild.get_role(role_id)
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
    def index(self) -> List[discord.Role]:
        data = self.menus[self.guild_id][str(self.message_id)]
        guild = self.bot.get_guild(self.guild_id)
        self._index = {}
        for role_id in data["roles"]:
            role = guild.get_role(role_id)
            if not role:
                self.menus[self.guild_id]["roles"].remove(role_id)
                self.bot.loop.create_task(self.menus.flush())
                continue
            self._index[role.name] = role
        return list(self._index.values())

    async def on_error(self, _error, _item, _interaction) -> None:
        pass

    async def surface_callback(self, interaction) -> None:
        """ Suppress exceptions in the actual callback function """
        with suppress(discord.errors.NotFound):
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
                self.menus[self.guild_id][key]["roles"].remove(role_id)
            await self.menus.flush()
            await interaction.message.edit(view=self)
            return await interaction.response.send_message(reason, ephemeral=True)

        # Ensure the user isn't spamming buttons
        check1 = self.global_cooldown.check(interaction.user.id)
        check2 = self.cooldown.check(interaction.user.id)
        if check1 or check2:
            return await interaction.response.send_message(
                "You're on cooldown, try again in a moment", ephemeral=True
            )

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

        # Ensure the user isn't spamming buttons
        check1 = self.global_cooldown.check(interaction.user.id)
        check2 = self.cooldown.check(interaction.user.id)
        if check1 or check2:
            return await interaction.response.send_message(
                "You're on cooldown, try again in a moment", ephemeral=True
            )

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
                self.menus[self.guild_id]["roles"].remove(role.id)
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
    def __init__(self, cls: ButtonMenu, msg_id: int, roles: List[discord.Role]):
        self.cls = cls
        options = []
        for role in roles:
            options.append(discord.SelectOption(label=role.name[:25], value=str(role.id)))
        super().__init__(
            custom_id=f"select_{msg_id}",
            placeholder="Select a Role",
            min_values=1,
            max_values=2,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await self.cls.surface_callback(interaction)


def setup(bot: Fate):
    bot.add_cog(ButtonRoles(bot))
