from discord.ext import commands
import discord


class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def configure(self, ctx):
        """ @everyone configuration """
        perms = ctx.guild.default_role.permissions
        perms.update(read_messages=False, mention_everyone=False)
        perms.update(embed_links=True, attach_files=True)
        await ctx.guild.default_role.edit(permissions=perms)
        await ctx.send("Completed default configuration")

    async def sync_roles(self, ctx):
        """ Makes the permissions of roles match @everyone """
        perms = ctx.guild.default_role.permissions
        roles = [
            r
            for r in ctx.guild.roles
            if r.permissions.value != perms.value and ctx.guild.default_role.id != r.id
        ]
        for role in sorted(roles, reverse=True):  # highest position to lowest
            if role.position < ctx.guild.me.top_role.position:
                await role.edit(permissions=perms)
        await ctx.send(f"Sync'd role permissions with `@everyone`")

    async def sync_channels(self, ctx):
        """ Sync's channel perms with their category """
        for category in ctx.guild.categories:
            for channel in category.channels:
                try:
                    await channel.edit(sync_permissions=True)
                except:
                    pass
        await ctx.send("Sync'd channel overwrites")

    async def strip_roles(self, ctx):
        """ Strips roles of every permission """
        perms = discord.Permissions(0)
        for role in sorted(ctx.guild.roles, reverse=True):
            if role.position < ctx.guild.me.top_role.position:
                try:
                    await role.edit(permissions=perms, hoist=False, mentionable=False)
                except:
                    pass
        await ctx.send("Stripped role permissions")

    async def strip_channels(self, ctx):
        """ Strips channel overwrites that don't effect read perms """
        for channel in ctx.guild.text_channels + ctx.guild.voice_channels:
            if ctx.guild.default_role in channel.overwrites:
                if ctx.channel.overwrites[ctx.guild.default_role].read_messages:
                    for overwrite in channel.overwrites:
                        if overwrite.id != ctx.guild.default_role.id:
                            if ctx.channel.overwrites[overwrite].read_messages:
                                await channel.set_permissions(overwrite, overwrite=None)
            for overwrite, perms in channel.overwrites.items():
                for perm, value in perms:
                    if value is not None:
                        if perms.read_messages:
                            if (
                                len(
                                    [
                                        (perm, value)
                                        for perm in perms
                                        if value is not None
                                    ]
                                )
                                > 1
                            ):
                                await channel.set_permissions(overwrite, overwrite=None)
                                await channel.set_permissions(
                                    overwrite, read_messages=True
                                )
                        else:
                            await channel.set_permissions(overwrite, overwrite=None)
        await ctx.send("Stripped channel overwrites")

    @commands.command(name="cleanup")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    async def cleanup(self, ctx):
        await self.configure(ctx)
        await self.sync_roles(ctx)
        await self.sync_channels(ctx)
        await ctx.send("Finished cleanup :)")

    @commands.command(name="sync")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    async def sync(self, ctx, arg=None):
        if not arg:  # sync everything
            await self.sync_roles(ctx)
            await self.sync_channels(ctx)
        elif arg.lower() == "roles":
            await self.sync_roles(ctx)
        elif arg.lower() == "channels":
            await self.sync_channels(ctx)
        else:
            await ctx.send("Unknown argument")

    @commands.command(name="strip")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    async def strip(self, ctx, arg=None):
        if not arg:  # strip everything
            await self.strip_roles(ctx)
            await self.strip_channels(ctx)
        elif arg.lower() == "roles":
            await self.strip_roles(ctx)
        elif arg.lower() == "channels":
            await self.strip_channels(ctx)
        else:
            await ctx.send("Unknown argument")


def setup(bot):
    bot.add_cog(ServerSetup(bot), override=True)
