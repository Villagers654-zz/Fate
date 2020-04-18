# quick moderation based commands
"""
Notes
- make sure commands work in unison with each other with muting
"""

from os import path
import json
from typing import *
from datetime import datetime, timedelta
import asyncio

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

    @property
    def template(self):
        return {
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
            "timers": [],
            "mute_timers": {}
        }

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
            config['restricted'][guild_id] = {
                'channels': [],
                'users': []
            }
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
            config['restricted'][guild_id] = {
                'channels': [],
                'users': []
            }
        for channel in ctx.message.channel_mentions:
            if channel.id in dat['channels']:
                config['restricted'][guild_id]['channels'].remove(channel.id)
                unrestricted += f'\n{channel.mention}'
        for member in ctx.message.mentions:
            if member.id in dat['users']:
                config['restricted'][guild_id]['users'].remove(member.id)
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
    async def mute(self, ctx, members: Greedy[discord.Member], *, reason):  # check for timers with regex
        for user in list(members):
            async with ctx.typing():
                if not user:
                    return await ctx.send("**Format:** `.mute {@user} {timer: 2m, 2h, or 2d}`")
                if user.top_role.position >= ctx.author.top_role.position:
                    return await ctx.send("That user is above your paygrade, take a seat")
                guild_id = str(ctx.guild.id)
                user_id = str(user.id)
                mute_role = None
                for role in ctx.guild.roles:
                    if role.name.lower() == "muted":
                        mute_role = role
                        for channel in ctx.guild.text_channels:
                            if not channel.permissions_for(ctx.guild.me).manage_channels:
                                continue
                            if mute_role not in channel.overwrites:
                                await channel.set_permissions(mute_role, send_messages=False)
                                await asyncio.sleep(0.5)
                        for channel in ctx.guild.voice_channels:
                            if not channel.permissions_for(ctx.guild.me).manage_channels:
                                continue
                            if mute_role not in channel.overwrites:
                                await channel.set_permissions(mute_role, speak=False)
                                await asyncio.sleep(0.5)
                if not mute_role:
                    perms = [perm for perm, value in ctx.guild.me.guild_permissions if value]
                    if 'manage_channels' not in perms:
                        return await ctx.send('No muted role found, and I\'m missing manage_channel permissions to set one up')
                    mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color(colors.black()))
                    for channel in ctx.guild.text_channels:
                        try:
                            await channel.set_permissions(mute_role, send_messages=False)
                        except:
                            await ctx.send(f"Couldn't modify mute role in {channel.mention}s overwrites")
                        await asyncio.sleep(0.5)
                    for channel in ctx.guild.voice_channels:
                        try:
                            await channel.set_permissions(mute_role, speak=False)
                        except:
                            await ctx.send(f"Couldn't modify mute role in {channel.name}s overwrites")
                        await asyncio.sleep(0.5)
                if mute_role in user.roles:
                    return await ctx.send(f'{user.display_name} is already muted')
                if not timer:
                    await user.add_roles(mute_role)
                    return await ctx.send(f'Muted {user.display_name}')
                for x in list(timer):
                    if x not in '1234567890dhms':
                        return await ctx.send("Invalid character used in timer field")
                timer, time = self.convert_timer(timer)
                if not isinstance(timer, float):
                    return await ctx.send("Invalid character used in timer field")
                await user.add_roles(mute_role)
                if not timer:
                    await ctx.send(f"**Muted:** {user.name}")
                else:
                    await ctx.send(f"Muted **{user.name}** for {time}")
                removed_roles = []
                for role in [role for role in sorted(user.roles, reverse=True) if role is not mute_role]:
                    try:
                        await user.remove_roles(role)
                        removed_roles.append(role.id)
                        await asyncio.sleep(0.5)
                    except:
                        pass
            try:
                timer_info = {
                    'channel': ctx.channel.id,
                    'user': user.id,
                    'end_time': str(datetime.now() + timedelta(seconds=round(timer))),
                    'mute_role': mute_role.id,
                    'roles': removed_roles
                }
            except OverflowError:
                return await ctx.send("No way in hell I'm waiting that long to unmute")
            if guild_id not in self.config:
                self.config[guild_id] = self.template
            self.config[guild_id]['mute_timers'][user_id] = timer_info
            self.save_data()
            await asyncio.sleep(timer)
            if user_id in self.config[guild_id]['mute_timers']:
                user = ctx.guild.get_member(int(user_id))
                if user:
                    if mute_role in user.roles:
                        await user.remove_roles(mute_role)
                        await ctx.send(f"**Unmuted:** {user.name}")
                    del self.config[guild_id]['mute_timers'][user_id]

    @commands.command(name='kick')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(kick_members=True)
    @commands.bot_has_permissions(embed_links=True, kick_members=True)
    async def kick(self, ctx, members: Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("Member(s) not found")

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
        def gen_embed(iteration):
            e = discord.Embed(color=colors.fate())
            e.set_author(name="Mass Updating Nicknames", icon_url=ctx.author.avatar_url)
            e.description = f"{iteration}/{len(members)} complete" \
                            f"\nETA of {self.bot.utils.get_time(len(members))}"
            return e

        members = [
            m for m in ctx.guild.members if m.top_role.position < ctx.author.top_role.position
                                            and m.author.top_role.position < ctx.guild.me.top_role.position
                                            and m.display_name != nick
        ]
        if len(members) > 3600:
            async with ctx.typing():
                await asyncio.sleep(1)
            msg = await ctx.send("Bruh.. you get ONE hour, but that's it.", embed=gen_embed(0))
        else:
            msg = await ctx.send(embed=gen_embed(0))
        async with ctx.typing():
            await msg.add_reaction("❌")
            for i, member in enumerate(members[:3600]):
                for reaction in [r for r in msg.reactions if str(reaction.emoji) == "❌"] and reaction.count > 1:
                    async for user in reaction.users():
                        if not user.guild_permissions.manage_nicknames:
                            await msg.remove_reaction(reaction.emoji, user)
                            continue
                        return await msg.edit(content="Message Inactive: Operation Cancelled")
                if (i + 1) % 5 == 0:
                    await msg.edit(embed=gen_embed(i))
                try:
                    await member.edit(nick=nick)
                except discord.errors.Forbidden:
                    if not ctx.guild.me.guild_permissions.manage_nicknames:
                        await msg.edit(content="Message Inactive: Missing Permissions")
                        return await ctx.send("I'm missing permissions to manage nicknames. Canceling the operation :[")
                await asyncio.sleep(1)
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "❌" and reaction.count > 1:
                        async for user in reaction.users():
                            if not user.guild_permissions.manage_nicknames:
                                await msg.remove_reaction(reaction.emoji, user)
                                continue
                            return await msg.edit(content="Message Inactive: Operation Cancelled")

    @commands.command(name='mass-role', aliases=['massrole'])
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mass_role(self, ctx, *, role: Union[discord.Role, str]):
        pass

    async def warn_user(self, channel, user, reason):
        guild = channel.guild
        guild_id = str(guild.id)
        user_id = str(user.id)
        if guild_id not in self.config:
            self.config[guild_id] = self.template
        warns = self.config[guild_id]["warns"]
        config = self.bot.utils.get_config()  # type: dict
        punishments = ['None', 'None', 'Mute', 'Kick', 'Softban', 'Ban']
        if guild_id in config['warns']['punishments']:
            punishments = config['warns']['punishments'][guild_id]
        if user_id not in warns:
            warns[user_id] = []
        if not isinstance(warns[user_id], list):
            warns[user_id] = []

        warns[user_id].append([reason, str(datetime.now())])
        total_warns = 0
        for reason, time in warns[user_id]:
            time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
            if (datetime.now() - time).days > 30:
                if guild_id in config['warns']['expire']:
                    warns[user_id].remove([reason, str(time)])
                    continue
            total_warns += 1
        self.save_data()

        if warns > len(punishments):
            punishment = punishments[-1:][0]
        else:
            punishment = punishments[warns - 1]
        if warns >= len(punishments):
            next_punishment = punishments[-1:][0]
        else:
            next_punishment = punishments[warns]

        e = discord.Embed(color=colors.fate())
        url = self.bot.user.avatar_url
        if user.avatar_url:
            url = user.avatar_url
        e.set_author(name=f'{user.name} has been warned', icon_url=url)
        e.description = f'**Warns:** [`{warns}`] '
        if punishment != 'None':
            e.description += f'**Punishment:** [`{punishment}`]'
        if punishment == 'None' and next_punishment != 'None':
            e.description += f'**Next Punishment:** [`{next_punishment}`]'
        else:
            if punishment == 'None' and next_punishment == 'None':
                e.description += f'**Reason:** [`{reason}`]'
            if next_punishment != 'None':
                e.description += f'\n**Next Punishment:** [`{next_punishment}`]'
        if punishment != 'None' and next_punishment != 'None':
            e.add_field(name='Reason', value=reason, inline=False)
        await channel.send(embed=e)
        try:
            await user.send(f"You've been warned in **{channel.guild}** for `{reason}`")
        except:
            pass
        if punishment == 'Mute':
            mute_role = None
            for role in channel.guild.roles:
                if role.name.lower() == "muted":
                    mute_role = role
            if not mute_role:
                bot = discord.utils.get(guild.members, id=self.bot.user.id)
                perms = list(perm for perm, value in bot.guild_permissions if value)
                if "manage_channels" not in perms:
                    return await channel.send("No muted role found, and I'm missing manage_channel permissions to set one up")
                mute_role = await guild.create_role(name="Muted", color=discord.Color(colors.black()))
                for channel in guild.text_channels:
                    await channel.set_permissions(mute_role, send_messages=False)
                for channel in guild.voice_channels:
                    await channel.set_permissions(mute_role, speak=False)
            if mute_role in user.roles:
                return await channel.send(f"{user.display_name} is already muted")
            user_roles = []
            for role in user.roles:
                try:
                    await user.remove_roles(role)
                    user_roles.append(role.id)
                    await asyncio.sleep(0.5)
                except:
                    pass
            await user.add_roles(mute_role)
            timer_info = {
                'action': 'mute',
                'channel': channel.id,
                'user': user.id,
                'end_time': str(datetime.now() + timedelta(seconds=7200)),
                'mute_role': mute_role.id,
                'roles': user_roles}
            if user_id not in self.config[guild_id]['timers']:
                self.config[guild_id]['timers'][user_id] = []
            self.config[guild_id]['timers'][user_id].append(timer_info)
            self.save_data()
            await asyncio.sleep(7200)
            if mute_role in user.roles:
                await user.remove_roles(mute_role)
                await channel.send(f"**Unmuted:** {user.name}")
            if user_id in self.config[guild_id]['timers'] and timer_info in self.config[guild_id]['timers'][user_id]:
                self.config[guild_id]['timers'][user_id].remove(timer_info)
            if not self.config[guild_id]['timers'][user_id]:
                del self.config[guild_id]['timers'][user_id]
            self.save_data()
        if punishment == 'Kick':
            try:
                await guild.kick(user, reason='Reached Sufficient Warns')
            except:
                await channel.send('Failed to kick this user')
        if punishment == 'Softban':
            try:
                await guild.kick(user, reason='Softban - Reached Sufficient Warns')
                await guild.unban(user, reason='Softban')
            except:
                await channel.send('Failed to softban this user')
        if punishment == 'Ban':
            try:
                await guild.ban(user, reason='Reached Sufficient Warns')
            except:
                await channel.send('Failed to ban this user')

    def has_warn_permission(self):
        async def predicate(ctx):
            config = self.template
            guild_id = str(ctx.guild.id)
            if guild_id in self.config:
                config = self.config[guild_id]
            if ctx.author.id in config['commands']['warn']:
                return True
            elif ctx.author.guild_permissions.administrator:
                return True
        return commands.check(predicate)

    @commands.command(name='warn')  # use a second special check for this with perm requirements based off of the set punishments
    @has_warn_permission()
    @commands.cooldown(*utils.default_cooldown())
    async def warn(self, ctx, user: Greedy[discord.User], *, reason):
        for user in list(user):
            await self.warn_user(ctx.channel, user, reason)


def setup(bot):
    bot.add_cog(Moderation(bot))
