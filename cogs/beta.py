# detailed information on users/channels/invites/etc

from os import path
import json
from time import time

from discord.ext import commands
import discord


class UtilityBeta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = './data/info.json'
        self.guild_logs = {}
        self.user_logs = {}
        self.misc_logs = {
            'invites': {}
        }
        if path.isfile(self.path):
            with open(self.path, 'r') as f:
                dat = json.load(f)  # type: dict
                self.guild_logs = dat['guild_logs']
                self.user_logs = dat['user_logs']
                self.misc_logs = dat['misc_logs']
        self.cache = {}

    def save_data(self):
        with open(self.path, 'w+') as f:
            json.dump(
                {'guild_logs': self.guild_logs, 'user_logs': self.user_logs, 'misc_logs': self.misc_logs},
                f, indent=2, sort_keys=True, ensure_ascii=False
            )

    def setup_if_not_exists(self, *args):
        for arg in args:
            if isinstance(arg, discord.Guild):
                guild_id = str(arg.id)
                if guild_id not in self.guild_logs:
                    self.guild_logs[guild_id] = {
                        'history': {
                            'growth': {},
                            'names': []
                        },
                        'bots': {
                            str(bot.id): None for bot in [m for m in arg.members if m.bot]
                        }
                    }
                    self.save_data()
            if isinstance(arg, discord.User):
                user_id = str(arg.id)
                if user_id not in self.user_logs:
                    self.user_logs[user_id] = {
                        'names': {str(arg): time()},
                        'last_online': None,
                        'duration': None
                    }
                    self.save_data()

    def cleanup_users(self):
        for user_id, data in self.user_logs.items():
            for name, changed_at in data['names'].items():
                if changed_at > time() - 60*60*24*60:
                    del self.user_logs[user_id]['names'][name]
        self.save_data()

    @commands.command(name='info')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        user_id = str(before.id)

        old_name = str(before)
        new_name = str(after)
        if old_name != new_name:
            self.setup_if_not_exists(before)
            if new_name not in self.user_logs[user_id]:
                self.user_logs[user_id][new_name] = time()

        if before.status != after.status:
            self.setup_if_not_exists(before)
            status = discord.Status
            if user_id not in self.cache and after.status != status.offline:
                self.cache[user_id] = time()
            elif before.status == status.offline and after.status != status.online:
                self.cache[user_id] = time()
            if before.status != status.offline and after.status == status.offline:
                if user_id not in self.cache:
                    return  # Prevents the code below from repeating
                self.user_logs[user_id]['last_online'] = self.cache[user_id]
                self.user_logs[user_id]['duration'] = time() - self.cache[user_id]
                del self.cache[user_id]
                self.save_data()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            guild = member.guild
            guild_id = str(guild.id)
            bot_id = str(member.id)

            self.setup_if_not_exists(guild, member)
            self.guild_logs[guild_id]['bots'][bot_id] = None

            if guild.permissions_for(guild.me).view_audit_log:
                audit = discord.AuditLogAction
                async for entry in guild.audit_logs(limit=1, action=audit.bot_add):
                    self.guild_logs[guild_id]['bots'][bot_id] = entry.user.id
            self.save_data()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.code not in self.misc_logs['invites']:
            guild = self.bot.get_guild(invite.guild.id)
            invite_info = {
                'deleted': False,
                'inviter': invite.inviter.id,
                'guild': {
                    'name': guild.name,
                    'id': guild.id
                }
            }
            try:
                invite = await self.bot.fetch_invite(invite.code, with_counts=True)
            except discord.errors.HTTPException:
                pass
            invite_info['member_count'] = invite.approximate_member_count
            invite_info['online_count'] = invite.approximate_presence_count
            invite_info['channel'] = {'name': None, 'id': invite.channel.id}
            if isinstance(invite.channel, (discord.TextChannel, discord.VoiceChannel, discord.PartialInviteChannel)):
                invite_info['channel']['name'] = invite.channel.name
            invite_info['temporary'] = invite.temporary
            invite_info['created_at'] = invite.created_at
            invite_info['uses'] = invite.uses
            invite_info['max_uses'] = invite.max_uses
            self.misc_logs['invites'][invite.code] = invite_info
            self.save_data()

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.code in self.misc_logs['invites']:
            self.misc_logs['invites'][invite.code]['deleted'] = True
            self.save_data()


def setup(bot):
    bot.add_cog(UtilityBeta)
