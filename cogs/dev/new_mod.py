# quick moderation based commands

from os import path
import json
from typing import *

from discord.ext import commands
import discord
from discord.ext.commands import Greedy

from utils import utils


cache = {}  # keep track of what commands are still being ran


def check_if_running(fp):
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
                "mute": [],  # roles that can access
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
        """ index commands that are running """
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
        """ index commands that are running """
        # with open(self.fp, 'r') as f:
        #     cache = json.load(f)  # type: dict
        cmd = ctx.command.name
        cache[cmd].remove(ctx.guild.id)
        # with open(self.fp, 'w') as f:
        #     json.dump(cache, f, indent=2)

    @commands.command(name='kick')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(kick_members=True)
    @commands.bot_has_permissions(embed_links=True, kick_members=True)
    async def kick(self, ctx, members: Greedy[discord.Member], *, reason):
        pass

    @commands.command(name='ban')
    @commands.cooldown(*utils.default_cooldown())
    @has_required_permissions(ban_members=True)
    @commands.bot_has_permissions(embed_links=True, ban_members=True)
    async def ban(self, ctx, users: Greedy[discord.User], *, reason):
        pass

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


def setup(bot):
    bot.add_cog(Moderation(bot))
