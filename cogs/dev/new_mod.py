# quick moderation based commands

from os import path
import json
from typing import *

from discord.ext import commands
import discord
from discord.ext.commands import Greedy

from utils import utils, colors


cache = {}  # Keep track of what commands are still being ran
            # This should empty out as quickly as it's filled


def check_if_running():
    """ Checks if the command is already in progress """
    async def predicate(ctx):
        # with open(fp, 'r') as f:
        #     cache = json.load(f)  # type: dict
        cmd = ctx.command.name
        if cmd not in cache:
            cache[cmd] = []
        check_result = ctx.guild.id not in cache[cmd]
        if not check_result:
            await ctx.send('That command is already running >:(')
        return check_result
    return commands.check(predicate)


def has_required_permissions(**kwargs):
    """ Permission check with support for usermod, rolemod, and role specific cmd access """
    async def predicate(ctx):
        with open('./data/userdata/moderation.json', 'r') as f:
            config = json.load(f)  # type: dict
        config = config[str(ctx.guild.id)]  # type: dict
        if ctx.command.name in config['commands']:
            allowed = config['commands'][ctx.command.name]  # type: list
            if any(role.id in allowed for role in ctx.author.roles):
                return True
        if ctx.author.id in config['usermod']:
            return True
        if any(r.id in config['rolemod'] for r in ctx.author.roles):
            return True
        perms = ctx.author.guild_permissions
        return all((perm, value) in list(perms) for perm, value in kwargs.items())
    return commands.check(predicate)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fp = './static/mod-cache.json'
        self.template = {
            "usermod": [],
            "rolemod": [],
            "commands": {
                "warn": [],  # roles that have access
                "purge": [],
                "mute": [],
                "kick": [],
                "ban": []
            },
            "warns": {},
            "config": {},
            "timers": []
        }
        self.path = './data/userdata/moderation.json'
        self.config = {}
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.config = json.load(f)  # type: dict
        # Add or remove any missing/unused key/values
        # this is for ease of updating json as it's developed
        for guild_id, config in self.config.items():
            for key, values in self.template.items():
                if key not in config:
                    config[key] = values
            for key, values in config.items():
                if key not in self.template:
                    del config[key]
            self.config[guild_id] = config

    def save_data(self):
        with open(self.path, 'w') as f:
            json.dump(self.config, f)

    async def cog_before_invoke(self, ctx):
        """ Index commands that are running """
        # if not path.isfile(self.fp):
        #     with open(self.fp, 'w') as f:
        #         json.dump({}, f, indent=2)
        # with open(self.fp, 'r') as f:
        #     cache = json.load(f)  # type: dict
        cmd = ctx.command.name
        if cmd not in cache:
            cache[cmd] = []
        if ctx.guild.id not in cache[cmd]:
            cache[cmd].append(ctx.guild.id)
        # with open(self.fp, 'w') as f:
        #     json.dump(cache, f, indent=2)
        if str(ctx.guild.id) not in self.config:
            self.config[str(ctx.guild.id)] = self.template
            self.save_data()

    async def cog_after_invoke(self, ctx):
        """ Index commands that are running """
        # with open(self.fp, 'r') as f:
        #     cache = json.load(f)  # type: dict
        cmd = ctx.command.name
        cache[cmd].remove(ctx.guild.id)
        # with open(self.fp, 'w') as f:
        #     json.dump(cache, f, indent=2)

    def save_config(self, config):
        """ Save things like channel restrictions """
        with open('./data/userdata/config.json', 'w') as f:
            json.dump(config, f, ensure_ascii=False)

    @commands.command(name='restrict')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def restrict(self, ctx, args=None):
        if not args:
            e = discord.Embed(color=colors.fate())
            e.set_author(name='Channel Restricting')
            e.description = 'Prevents everyone except mods from using commands'
            e.add_field(name='Usage', value='.restrict #channel_mention\n'
                                            '.unrestrict #channel_mention\n.restricted')
            return await ctx.send(embed=e)
        guild_id = str(ctx.guild.id)
        config = self.bot.get_config  # type: dict
        if 'restricted' not in config:
            config['restricted'] = {}
        if guild_id not in config['restricted']:
            config['restricted'][guild_id] = {}
            config['restricted'][guild_id]['channels'] = []
            config['restricted'][guild_id]['users'] = []
        restricted = '**Restricted:**'
        dat = config['restricted'][guild_id]
        for channel in ctx.message.channel_mentions:
            if channel.id in dat['channels']:
                continue
            config['restricted'][guild_id]['channels'].append(channel.id)
            restricted += f'\n{channel.mention}'
        for member in ctx.message.mentions:
            if member.id in dat['users']:
                continue
            config['restricted'][guild_id]['users'].append(member.id)
            restricted += f'\n{member.mention}'
        e = discord.Embed(color=colors.fate(), description=restricted)
        await ctx.send(embed=e)
        self.save_config(config)

    @commands.command(name='unrestrict')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def unrestrict(self, ctx):
        guild_id = str(ctx.guild.id)
        config = self.bot.get_config  # type: dict
        if 'restricted' not in config:
            config['restricted'] = {}
        unrestricted = '**Unrestricted:**'
        dat = config['restricted'][guild_id]
        if guild_id not in config['restricted']:
            config['restricted'][guild_id] = {}
            config['restricted'][guild_id]['channels'] = []
            config['restricted'][guild_id]['users'] = []
        for channel in ctx.message.channel_mentions:
            if channel.id in dat['channels']:
                index = config['restricted'][guild_id]['channels'].index(channel.id)
                config['restricted'][guild_id]['channels'].pop(index)
                unrestricted += f'\n{channel.mention}'
        for member in ctx.message.mentions:
            if member.id in dat['users']:
                index = config['restricted'][guild_id]['users'].index(member.id)
                config['restricted'][guild_id]['users'].pop(index)
                unrestricted += f'\n{member.mention}'
        e = discord.Embed(color=colors.fate(), description=unrestricted)
        await ctx.send(embed=e)
        self.save_config(config)

    @commands.command(name='restricted')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def restricted(self, ctx):
        guild_id = str(ctx.guild.id)
        config = self.bot.get_config  # type: dict
        if guild_id not in config['restricted']:
            return await ctx.send('No restricted channels/users')
        dat = config['restricted'][guild_id]
        e = discord.Embed(color=colors.fate())
        e.set_author(name='Restricted:', icon_url=ctx.author.avatar_url)
        e.description = ''
        if dat['channels']:
            changelog = ''
            for channel_id in dat['channels']:
                channel = self.bot.get_channel(channel_id)
                if not isinstance(channel, discord.TextChannel):
                    position = config['restricted'][guild_id]['channels'].index(channel_id)
                    config['restricted'][guild_id]['channels'].pop(position)
                    self.save_config(config)
                else:
                    changelog += '\n' + channel.mention
            if changelog:
                e.description += changelog
        if dat['users']:
            changelog = ''
            for user_id in dat['users']:
                user = self.bot.get_user(user_id)
                if not isinstance(user, discord.User):
                    position = config['restricted'][guild_id]['users'].index(user_id)
                    config['restricted'][guild_id]['users'].pop(position)
                    self.save_config(config)
                else:
                    changelog += '\n' + user.mention
            if changelog:
                e.description += changelog
        await ctx.send(embed=e)

    @commands.command(name='purge')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(manage_messages=True)
    @commands.bot_has_permissions(read_message_history=True, manage_messages=True)
    async def purge(self, ctx, *args):
        pass

    @commands.command(name='mute', aliases=['shutup', 'fuckoff'])
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(mute_members=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mute(self, ctx, member: Greedy[discord.Member], *, reason):  # check for timers in reason.split()[0]
        pass

    @commands.command(name='kick')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(kick_members=True)
    @commands.bot_has_permissions(embed_links=True, kick_members=True)
    async def kick(self, ctx, members: Greedy[discord.Member], *, reason):
        pass

    @commands.command(name='ban')
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(embed_links=True, ban_members=True)
    async def ban(self, ctx, ids: Greedy[int], users: Greedy[discord.User], *, reason='Unspecified'):
        """ Ban cmd that supports more than just members """
        reason = f"{ctx.author}: {reason}"
        users_to_ban = len(ids if ids else []) + len(users if users else [])
        e = discord.Embed(color=colors.fate())
        if users_to_ban == 0:
            return await ctx.send("You need to specify who to ban")
        elif users_to_ban > 1:
            e.set_author(name=f"Banning {users_to_ban} user{'' if users_to_ban > 1 else ''}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url='https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif')
        msg = await ctx.send(embed=e)
        for id in ids:
            member = ctx.guild.get_member(id)
            if isinstance(member, discord.Member):
                if member.top_role.position >= ctx.author.top_role.position:
                    e.add_field(name=f'◈ Failed to ban {member}', value="This users is above your paygrade", inline=False)
                    await msg.edit(embed=e)
                    continue
                elif member.top_role.position >= ctx.guild.me.top_role.position:
                    e.add_field(name=f'◈ Failed to ban {member}', value="I can't ban this user", inline=False)
                    await msg.edit(embed=e)
                    continue
            try:
                user = await self.bot.fetch_user(id)
            except:
                e.add_field(name=f'◈ Failed to ban {id}', value="That user doesn't exist", inline=False)
            else:
                await ctx.guild.ban(user, reason=reason)
                e.add_field(name=f'◈ Banned {user}', value=f'Reason: {reason}', inline=False)
            await msg.edit(embed=e)
        for user in users:
            member = discord.utils.get(ctx.guild.members, id=user.id)
            if member:
                if member.top_role.position >= ctx.author.top_role.position:
                    e.add_field(name=f'◈ Failed to ban {member}', value="This users is above your paygrade", inline=False)
                    await msg.edit(embed=e)
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    e.add_field(name=f'◈ Failed to ban {member}', value="I can't ban this user", inline=False)
                    await msg.edit(embed=e)
                    continue
            await ctx.guild.ban(user, reason=reason)
            e.add_field(name=f'◈ Banned {user}', value=f'Reason: {reason}', inline=False)
        if not e.fields:
            e.colour = colors.red()
            e.set_author(name="Couldn't ban any of the specified user(s)")
            await msg.edit(embed=e)

    @commands.command(name='unban')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(embed_links=True, ban_members=True, view_audit_log=True)
    async def unban(self, ctx, users: Greedy[discord.User], *, reason=':author:'):
        if not users:
            async for entry in ctx.guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
               users = entry.target,
        if len(users) == 1:
            user = users[0]
            await ctx.guild.unban(user, reason=reason.replace(':author:', str(ctx.author)))
            e = discord.Embed(color=colors.red())
            e.set_author(name=f'{user} unbanned', icon_url=user.avatar_url)
            await ctx.send(embed=e)
        else:
            e = discord.Embed(color=colors.green())
            e.set_author(name=f'Unbanning {len(users)} users', icon_url=ctx.author.avatar_url)
            e.description = ''
            msg = await ctx.send(embed=e)
            index = 1
            for user in users:
                e.description += f'✅ {user}'
                if index == 5:
                    await msg.edit(embed=e)
                    index = 1
                else:
                    index += 1
            await msg.edit(embed=e)

    @commands.command(name='mass-nick', aliases=['massnick'])
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(manage_nicknames=True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    async def mass_nick(self, ctx, *, nick):
        pass

    @commands.command(name='mass-role', aliases=['massrole'])
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mass_role(self, ctx, *, role: Union[discord.Role, str]):
        pass

    @commands.command(name='warn')
    @commands.cooldown(*utils.default_cooldown())
    async def warn(self, ctx, user: Greedy[discord.User], *, reason):
        pass  # use a second special check for this with perm requirements based off of the set punishments


def setup(bot):
    bot.add_cog(Moderation(bot))
