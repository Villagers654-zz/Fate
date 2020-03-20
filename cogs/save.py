import os
import json
import discord
import requests
from datetime import datetime
from discord.ext import commands


class ServerSave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def luck(ctx):
        return ctx.message.author.id == 264838866480005122

    @commands.command(pass_context=True, aliases=["ss"])
    @commands.check(luck)
    async def serversave(self, ctx, *, server=""):
        if server:
            ctx.guild = self.bot.get_guild(int(server))
        if not ctx.guild:
            return await ctx.send("That server couldn't be found.")

        await ctx.message.delete()
        await self.bot.get_user(264838866480005122).send(
            "Saving server `{}`...".format(ctx.guild.name)
        )

        if not os.path.exists("server_save"):
            os.makedirs("server_save")

        date = datetime.now().strftime("%Y-%m-%d")
        filename = "server_save/{}_{}_{}.json".format(
            ctx.guild.name, ctx.guild.id, date
        )

        saved_guild = {
            "name": str(ctx.guild.name),
            "region": str(ctx.guild.region),
            "afk_timeout": int(ctx.guild.afk_timeout),
            "afk_channel": str(ctx.guild.afk_channel.name)
            if ctx.guild.afk_channel
            else None,
            "icon": str(ctx.guild.icon_url),
            "mfa_level": str(ctx.guild.mfa_level),
            "verification_level": ["none", "low", "medium", "high", "extreme"].index(
                str(ctx.guild.verification_level)
            ),
            "roles": [],
            "categories": [],
            "text_channels": [],
            "voice_channels": [],
            "emojis": [],
        }

        for role in ctx.guild.roles:
            role_dict = {
                "name": str(role.name),
                "permissions": list(role.permissions),
                "colour": tuple(role.colour.to_rgb()),
                "hoist": role.hoist,
                "position": int(role.position),
                "mentionable": 0 if role.mentionable else 1,
            }

            saved_guild["roles"].append(role_dict)

        for category in ctx.guild.categories:
            category_dict = {
                "name": str(category.name),
                "position": int(category.position),
                "nsfw": category.nsfw,
                "channels": [],
                "overwrites": [],
            }

            for channel in category.channels:
                category_dict["channels"].append(channel.name)

            try:
                for overwrite, perms in category.overwrites.items():
                    overwrite_dict = {
                        "name": str(overwrite.name),
                        "permissions": list(perms),
                        "type": "member"
                        if type(overwrite) == discord.Member
                        else "role",
                    }

                    category_dict["overwrites"].append(overwrite_dict)
                saved_guild["categories"].append(category_dict)
            except:
                pass

        for channel in ctx.guild.text_channels:
            channel_dict = {
                "name": str(channel.name),
                "topic": str(channel.topic),
                "position": int(channel.position),
                "nsfw": channel.is_nsfw(),
                "overwrites": [],
                "category": str(channel.category.name) if channel.category else None,
            }
            try:
                for overwrite, perms in channel.overwrites.items():
                    overwrite_dict = {
                        "name": str(overwrite.name),
                        "permissions": list(perms),
                        "type": "member"
                        if type(overwrite) == discord.Member
                        else "role",
                    }

                    channel_dict["overwrites"].append(overwrite_dict)
                saved_guild["text_channels"].append(channel_dict)
            except:
                pass

        for channel in ctx.guild.voice_channels:
            channel_dict = {
                "name": str(channel.name),
                "position": str(channel.position),
                "user_limit": int(channel.user_limit),
                "bitrate": int(channel.bitrate),
                "overwrites": [],
                "category": str(channel.category.name) if channel.category else None,
            }
            channel_dict["category"] = channel.category.name
            for overwrite, perms in channel.overwrites.items():
                overwrite_dict = {
                    "name": str(overwrite.name),
                    "permissions": list(perms),
                    "type": "member" if type(overwrite) == discord.Member else "role",
                }
                channel_dict["overwrites"].append(overwrite_dict)
            saved_guild["voice_channels"].append(channel_dict)

        for emoji in ctx.guild.emojis:
            emoji_dict = {"name": str(emoji.name), "url": str(emoji.url)}

            saved_guild["emojis"].append(emoji_dict)

        with open(filename, "w+") as f:
            json.dump(saved_guild, f)
            await self.bot.get_user(264838866480005122).send(
                "Successfully saved `{}` to `{}`!".format(ctx.guild.name, filename)
            )

    @commands.command(pass_context=True, aliases=["sl"])
    @commands.check(luck)
    async def serverload(
        self, ctx, server=":"
    ):  # filenames cannot contain : so I'm using this as a workaround to make it only use the current server ID if no server is given
        """Load an entire server?!?!?!??!
		Loads in the saved data from a previously saved server.
		Usage:
		[p]serverload - Attempt to find a save of the current server and load it.
		[p]serverload <filename> - Find a saved server by filename (if a whole filename is not given, the latest save from all of the filenames that contain the given filename is used)
		"""
        if not os.path.exists("server_save") or not os.listdir("server_save"):
            return await ctx.send("You have no servers saved!")

        saves = os.listdir("server_save")
        guild_saves = [x for x in saves if server in x or str(ctx.guild.id) in x]

        if not guild_saves:
            return await ctx.send("That server couldn't be found in your saves.")

        parsed_guild_saves = [
            datetime.strptime(x.split("_")[2].split(".")[0], "%Y-%m-%d")
            for x in guild_saves
        ]

        server_save = guild_saves[parsed_guild_saves.index(max(parsed_guild_saves))]

        await ctx.send(
            "Loading server... (this may take a few minutes, check console for progress)"
        )

        await self.bot.get_user(264838866480005122).send(
            "Beginning server load process..."
        )

        with open("server_save/" + server_save, "r") as f:
            g = json.load(f)

        await self.bot.get_user(264838866480005122).send("Loading roles...")
        try:
            for role in ctx.guild.roles[:]:
                try:
                    if role.name not in [x["name"] for x in g["roles"]]:
                        if "Fate" in role.name or "temp" in role.name:
                            pass
                        else:
                            await role.delete(reason="Loading saved server")
                except Exception as e:
                    pass
            for role in g["roles"]:
                if "Fate" in role.name:
                    continue
                try:
                    permissions = discord.Permissions()
                    permissions.update(**dict(role["permissions"]))
                    if role["name"] not in [x.name for x in ctx.guild.roles]:
                        await ctx.guild.create_role(
                            name=role["name"],
                            colour=discord.Colour.from_rgb(*role["colour"]),
                            hoist=role["hoist"],
                            mentionable=role["mentionable"],
                            permissions=permissions,
                            reason="Loading saved server",
                        )
                    else:
                        await [x for x in ctx.guild.roles if x.name == role["name"]][
                            0
                        ].edit(
                            name=role["name"],
                            colour=discord.Colour.from_rgb(*role["colour"]),
                            hoist=role["hoist"],
                            mentionable=role["mentionable"],
                            permissions=permissions,
                            reason="Loading saved server",
                        )
                except Exception as e:
                    pass
        except Exception as e:
            pass

        await self.bot.get_user(264838866480005122).send("Loading categories...")

        for category in ctx.guild.categories:
            if category.name not in [x["name"] for x in g["categories"]]:
                try:
                    await category.delete(reason="Loading saved server")
                except:
                    pass
        for category in g["categories"]:
            overwrites = []
            for overwrite in category["overwrites"]:
                try:
                    if overwrite["type"] == "role":
                        if overwrite["name"] not in [x.name for x in ctx.guild.roles]:
                            pass
                        else:
                            role = [
                                x
                                for x in ctx.guild.roles
                                if x.name == overwrite["name"]
                            ][0]
                            permissions = discord.PermissionOverwrite()
                            permissions.update(**dict(overwrite["permissions"]))
                            overwrites.append((role, permissions))
                    else:
                        if overwrite["name"] not in [x.name for x in ctx.guild.members]:
                            pass
                        else:
                            member = [
                                x
                                for x in ctx.guild.members
                                if x.name == overwrite["name"]
                            ][0]
                            permissions = discord.PermissionOverwrite()
                            permissions.update(**dict(overwrite["permissions"]))
                            overwrites.append((member, permissions))
                except:
                    pass
            if category["name"] in [x.name for x in ctx.guild.categories]:
                try:
                    category_obj = [
                        x for x in ctx.guild.categories if x.name == category["name"]
                    ][0]
                    await category_obj.edit(
                        name=category["name"], reason="Loading saved server"
                    )
                    overwrites_dict = dict(overwrites)
                    for overwrite in overwrites_dict:
                        await category_obj.set_permissions(
                            overwrite,
                            overwrite=overwrites_dict[overwrite],
                            reason="Loading saved server",
                        )
                except:
                    pass
            else:
                new_cat = await ctx.guild.create_category(
                    category["name"],
                    overwrites=dict(overwrites),
                    reason="Loading saved server",
                )
                await new_cat.edit(nsfw=category["nsfw"], reason="Loading saved server")

        await self.bot.get_user(264838866480005122).send("Loading text channels...")

        for channel in ctx.guild.text_channels:
            if channel.name not in [x["name"] for x in g["text_channels"]]:
                await channel.delete(reason="Loading saved server")
        for channel in g["text_channels"]:
            category = None
            try:
                category = [
                    x for x in ctx.guild.categories if x.name == channel["category"]
                ][0]
            except:
                pass
            overwrites = []
            for overwrite in channel["overwrites"]:
                if overwrite["type"] == "role":
                    if overwrite["name"] not in [x.name for x in ctx.guild.roles]:
                        pass
                    else:
                        role = [
                            x for x in ctx.guild.roles if x.name == overwrite["name"]
                        ][0]
                        permissions = discord.PermissionOverwrite()
                        permissions.update(**dict(overwrite["permissions"]))
                        overwrites.append((role, permissions))
                else:
                    if overwrite["name"] not in [x.name for x in ctx.guild.members]:
                        pass
                    else:
                        member = [
                            x for x in ctx.guild.members if x.name == overwrite["name"]
                        ][0]
                        permissions = discord.PermissionOverwrite()
                        permissions.update(**dict(overwrite["permissions"]))
                        overwrites.append((member, permissions))
            if channel["name"] in [x.name for x in ctx.guild.text_channels]:
                channel_obj = [
                    x for x in ctx.guild.text_channels if x.name == channel["name"]
                ][0]
                await channel_obj.edit(
                    name=channel["name"],
                    topic=channel["topic"],
                    category=category,
                    reason="Loading saved server",
                )
                overwrites_dict = dict(overwrites)
                for overwrite in overwrites_dict:
                    await channel_obj.set_permissions(
                        overwrite,
                        overwrite=overwrites_dict[overwrite],
                        reason="Loading saved server",
                    )
            else:
                new_chan = await ctx.guild.create_text_channel(
                    channel["name"],
                    overwrites=dict(overwrites),
                    reason="Loading saved server",
                )
                await new_chan.edit(
                    topic=channel["topic"],
                    nsfw=channel["nsfw"],
                    category=category,
                    reason="Loading saved server",
                )

        await self.bot.get_user(264838866480005122).send("Loading voice channels...")

        for channel in ctx.guild.voice_channels:
            if channel.name not in [x["name"] for x in g["voice_channels"]]:
                await channel.delete(reason="Loading saved server")
        for channel in g["voice_channels"]:
            overwrites = []
            category = None
            try:
                category = [
                    x for x in ctx.guild.categories if x.name == channel["category"]
                ][0]
            except:
                pass
            for overwrite in channel["overwrites"]:
                if overwrite["type"] == "role":
                    if overwrite["name"] not in [x.name for x in ctx.guild.roles]:
                        pass
                    else:
                        role = [
                            x for x in ctx.guild.roles if x.name == overwrite["name"]
                        ][0]
                        permissions = discord.PermissionOverwrite()
                        permissions.update(**dict(overwrite["permissions"]))
                        overwrites.append((role, permissions))
                else:
                    if overwrite["name"] not in [x.name for x in ctx.guild.members]:
                        pass
                    else:
                        members = [
                            x for x in ctx.guild.members if x.name == overwrite["name"]
                        ][0]
                        permissions = discord.PermissionOverwrite()
                        permissions.update(**dict(overwrite["permissions"]))
                        overwrites.append((member, permissions))
            try:
                if channel["name"] in [x.name for x in ctx.guild.voice_channels]:
                    channel_obj = [
                        x for x in ctx.guild.voice_channels if x.name == channel["name"]
                    ][0]
                    await channel_obj.edit(
                        name=channel["name"],
                        topic=channel["topic"],
                        category=category,
                        reason="Loading saved server",
                    )
                    overwrites_dict = dict(overwrites)
                    for overwrite in overwrites_dict:
                        await channel_obj.set_permissions(
                            overwrite,
                            overwrite=overwrites_dict[overwrite],
                            reason="Loading saved server",
                        )
                else:
                    new_chan = await ctx.guild.create_voice_channel(
                        channel["name"],
                        overwrites=dict(overwrites),
                        reason="Loading saved server",
                    )
                    await new_chan.edit(
                        bitrate=channel["bitrate"]
                        if channel["bitrate"] <= 96000
                        else 96000,
                        user_limit=channel["user_limit"],
                        category=category,
                        reason="Loading saved server",
                    )
            except Exception as e:
                pass

        await self.bot.get_user(264838866480005122).send("Loading emotes...")

        for emoji in ctx.guild.emojis:
            await emoji.delete(reason="Loading saved server")
        for emoji in g["emojis"]:
            try:
                await ctx.guild.create_custom_emoji(
                    name=emoji["name"],
                    image=requests.get(emoji["url"]).content,
                    reason="Loaded saved server",
                )
            except Exception as e:
                pass

        await self.bot.get_user(264838866480005122).send(
            "Positioning channels and roles..."
        )

        # set up channel and role positions
        for channel in g["text_channels"]:
            await [x for x in ctx.guild.text_channels if x.name == channel["name"]][
                0
            ].edit(
                position=channel["position"]
                if channel["position"] < len(ctx.guild.text_channels)
                else len(ctx.guild.text_channels) - 1
            )

        for channel in g["voice_channels"]:
            await [x for x in ctx.guild.voice_channels if x.name == channel["name"]][
                0
            ].edit(
                position=channel["position"]
                if channel["position"] < len(ctx.guild.voice_channels)
                else len(ctx.guild.voice_channels) - 1
            )

        for category in g["categories"]:
            await [x for x in ctx.guild.categories if x.name == category["name"]][
                0
            ].edit(
                position=category["position"]
                if category["position"] < len(ctx.guild.categories)
                else len(ctx.guild.categories) - 1
            )

        for role in g["roles"]:
            if role["name"] != "@everyone":
                await [x for x in ctx.guild.roles if x.name == role["name"]][0].edit(
                    position=role["position"]
                    if role["position"] < len(ctx.guild.roles)
                    else len(ctx.guild.roles) - 1
                )

        await self.bot.get_user(264838866480005122).send("Editing server settings...")

        await ctx.guild.edit(
            name=g["name"],
            icon=requests.get(g["icon"].rsplit(".", 1)[0] + ".png").content
            if g["icon"]
            else None,
            region=discord.VoiceRegion(g["region"]),
            afk_channel=[
                x for x in ctx.guild.voice_channels if x.name == g["afk_channel"]
            ][0]
            if g["afk_channel"]
            else None,
            afk_timeout=g["afk_timeout"],
            verification_level=discord.VerificationLevel(g["verification_level"]),
            reason="Loading saved server",
        )

        await self.bot.get_user(264838866480005122).send(
            "Finished loading server backup!"
        )
        await self.bot.get_user(264838866480005122).send("Finished loading.")


def setup(bot):
    bot.add_cog(ServerSave(bot))
