from os.path import isfile
import json
from discord.ext import commands
import discord
from utils import colors


class RestoreRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = []
        self.allow_perms = []
        self.cache = {}
        self.path = './data/userdata/restore_roles.json'
        if isfile(self.path):
            with open(self.path, 'r') as f:
                dat = json.load(f)
                if 'guilds' in dat:
                    self.guilds = dat['servers']
                if 'allow_perms' in dat:
                    self.allow_perms = dat['allow_perms']

    def save_data(self):
        """ Saves any changes made """
        with open(self.path, 'w+') as f:
            json.dump({'guilds': self.guilds, 'allow_perms': self.allow_perms}, f)

    def disable_module(self, guild_id: str):
        """ Disables the module and resets guild data """
        self.guilds.pop(self.guilds.index(guild_id))
        if guild_id in self.guilds:
            del self.guilds[guild_id]
        self.save_data()

    @commands.group(name='restore-roles', aliases=['restore_roles'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def restore_roles(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate())
            e.set_author(name='Restore Roles', icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = 'Adds a users roles back if they leave and rejoin'
            usage = '.Restore-Roles enable\n• Enables the module\n' \
                '.Restore-Roles disable\n• Disables the module\n' \
                '.Restore-Roles allow-perms\n• Restores roles with mod perms'
            e.add_field(name='◈ Usage ◈', value=usage)
            await ctx.send(embed=e)

    @restore_roles.command(name='enable')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def _enable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.guilds:
            return await ctx.send('Restore-Roles is already enabled')
        self.guilds.append(guild_id)
        await ctx.send('Enabled Restore-Roles')

    @restore_roles.command(name='disable')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def _disable(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.guilds:
            return await ctx.send('Restore-Roles is not enabled')
        self.disable_module(guild_id)
        await ctx.send('Disabled Restore-Roles')

    @commands.command(name='allow-perms')
    @commands.is_owner()
    @commands.bot_has_permissions(manage_roles=True)
    async def _allow_perms(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.allow_perms:
            self.allow_perms.pop(self.allow_perms.index(guild_id))
            await ctx.send('Disabled Restore-Roles')
        else:
            self.allow_perms.append(guild_id)
            await ctx.send('Enabled Restore-Roles')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """ Restore roles on rejoin """
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        if guild_id in self.cache:
            if user_id in self.cache[guild_id]:
                roles = []
                for role_id in self.cache[guild_id][user_id]:
                    role = member.guild.guild.get_role(role_id)
                    if isinstance(role, discord.Role):
                        if role.position < member.guild.me.top_role.position:
                            roles.append(role)
                await member.add_roles(*roles, reason='.Restore-Roles')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """ Saves role id's when a member leaves """
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        if guild_id in self.guilds:
            for role in member.roles:
                notable = ['view_audit_log', 'manage_roles', 'manage_channels', 'manage_emojis',
                    'kick_members', 'ban_members', 'manage_messages', 'mention_everyone']
                if not any(perm in notable for perm in role.permissions) or guild_id in self.allow_perms:
                    if guild_id not in self.cache:
                        self.cache[guild_id] = {}
                    if user_id not in self.cache[guild_id]:
                        self.cache[guild_id][user_id] = []
                    self.cache[guild_id][user_id].append(role.id)
            self.save_data()

def setup(bot):
    bot.add_cog(RestoreRoles(bot))
