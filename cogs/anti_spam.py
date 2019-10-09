import asyncio
import os
import json
from time import time
from datetime import datetime
from discord.ext import commands
import discord
from utils import colors, utils


class AntiSpam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam_cd = {}  # sending messages in mass
        self.macro_cd = {}  # same interval between each msg
        self.ping_cd = {}  # mass pings
        self.dupes = {}
        self.dupez = {}
        self.toggle = {}
        self.sensitivity = {}
        self.blacklist = {}
        self.roles = {}
        self.status = {}
        self.mutes = {}
        self.msgs = {}
        self.path = './data/userdata/anti_spam.json'
        if not os.path.isdir('./data'):
            os.mkdir('data')
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                dat = json.load(f)
                self.toggle = dat['toggle']
                self.sensitivity = dat['sensitivity']
                self.blacklist = dat['blacklist']


    def save_data(self):
        with open(self.path, 'w+') as f:
            json.dump({'toggle': self.toggle, 'sensitivity': self.sensitivity, 'blacklist': self.blacklist}, f)


    def init(self, guild_id):
        if guild_id not in self.sensitivity:
            self.sensitivity[guild_id] = 'low'
        self.toggle[guild_id] = {
            'Rate-Limit': False,
            'Mass-Pings': False,
            'Anti-Macro': False,
            'Duplicates': False
        }


    @commands.group(name='anti-spam', aliases=['antispam'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def anti_spam(self, ctx):
        if not ctx.invoked_subcommand and 'help' not in ctx.message.content:
            e = discord.Embed(color=colors.fate())
            e.set_author(name='AntiSpam Usage', icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = '**.anti-spam enable**\n`• enables all anti-spam modules`\n' \
                '**.anti-spam enable module**\n`• enables a single module`\n' \
                '**.anti-spam disable**\n`• disables all anti-spam modules`\n' \
                '**.anti-spam disable module**\n`• disables a single module`\n' \
                '**.anti-spam alter-sensitivity**\n`• alters anti-spam sensitivity`\n' \
                '**.anti-spam ignore #channel**\n`• ignores spam in a channel`\n' \
                '**.anti-spam unignore #channel**\n`• no longer ignores a channels spam`'
            modules = '**Rate-Limit:** `sending msgs fast`\n' \
                '**Mass-Pings:** `mass mentioning users`\n' \
                '**Anti-Macro:** `using macros for bots`\n' \
                '**Duplicates:** `copying and pasting`'
            e.add_field(name='◈ Modules', value=modules, inline=False)
            guild_id = str(ctx.guild.id)
            if guild_id in self.toggle:
                conf = ''
                for key, value in self.toggle[guild_id].items():
                    conf += f'**{key}:** `{"enabled" if value else "disabled"}`\n'
                e.add_field(name='◈ Config', value=conf, inline=False)
            await ctx.send(embed=e)


    @anti_spam.group(name='enable')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, manage_roles=True, manage_channels=True)
    async def _enable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.sensitivity:
                self.sensitivity[guild_id] = 'low'
            self.toggle[guild_id] = {
                'Rate-Limit': True,
                'Mass-Pings': True,
                'Anti-Macro': True,
                'Duplicates': True
            }
            await ctx.send('Enabled all anti-spam modules')
            self.save_data()

    @_enable.command(name='rate-limit')
    async def _enable_rate_limit(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Rate-Limit'] = True
        await ctx.send('Enabled rate-limit module')
        self.save_data()

    @_enable.command(name='mass-pings', aliases=['mass-ping'])
    async def _enable_mass_pings(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Mass-Pings'] = True
        await ctx.send('Enabled mass-pings module')
        self.save_data()

    @_enable.command(name='anti-macro')
    async def _enable_anti_macro(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Anti-Macro'] = True
        await ctx.send('Enabled anti-macro module')
        self.save_data()

    @_enable.command(name='duplicates')
    async def _enable_duplicates(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Duplicates'] = True
        await ctx.send('Enabled duplicates module')
        self.save_data()


    @anti_spam.group(name='disable')
    async def _disable(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.toggle:
                return await ctx.send('Anti-Spam is\'nt enabled')
            del self.toggle[guild_id]
            del self.sensitivity[guild_id]
            await ctx.send('Disabled anti-spam')
            self.save_data()

    @_disable.command(name='rate-limit')
    async def _disable_rate_limit(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Rate-Limit'] = False
        await ctx.send('Disabled rate-limit module')
        self.save_data()

    @_disable.command(name='anti-macro')
    async def _disable_anti_macro(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Anti-Macro'] = False
        await ctx.send('Disabled anti-macro module')
        self.save_data()

    @_disable.command(name='mass-pings')
    async def _disable_mass_pings(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Mass-Pings'] = False
        await ctx.send('Disabled mass-pings module')
        self.save_data()

    @_disable.command(name='duplicates')
    async def _disable_duplicates(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.toggle:
            self.init(guild_id)
        self.toggle[guild_id]['Duplicates'] = False
        await ctx.send('Disabled duplicates module')
        self.save_data()


    @anti_spam.command(name='alter-sensitivity')
    async def _alter_sensitivity(self, ctx):
        guild_id = str(ctx.guild.id)
        if self.sensitivity[guild_id] == 'low':
            self.sensitivity[guild_id] = 'high'
        elif self.sensitivity[guild_id] == 'high':
            self.sensitivity[guild_id] = 'low'
        await ctx.send(f'Set the sensitivity to {self.sensitivity[guild_id]}')


    @anti_spam.command(name='ignore')
    @commands.has_permissions(manage_messages=True)
    async def _ignore(self, ctx, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.blacklist:
            self.blacklist[guild_id] = []
        if not channel:
            channel = ctx.channel
        if channel.id in self.blacklist[guild_id]:
            return await ctx.send('This channel is already ignored')
        self.blacklist[guild_id].append(channel.id)
        await ctx.send('👍')
        self.save_data()

    @anti_spam.command(name='unignore')
    @commands.has_permissions(manage_messages=True)
    async def _unignore(self, ctx, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.blacklist[guild_id]:
            return await ctx.send('This server has no ignored channels')
        if not channel:
            channel = ctx.channel
        if channel.id not in self.blacklist[guild_id]:
            return await ctx.send('This channel isn\'t ignored')
        index = self.blacklist[guild_id].index(channel.id)
        self.blacklist[guild_id].pop(index)
        await ctx.send('👍')
        self.save_data()


    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not isinstance(msg.guild, discord.Guild) or msg.author.bot:
            return
        guild_id = str(msg.guild.id)
        channel_id = str(msg.channel.id)
        user_id = str(msg.author.id)
        triggered = False
        if guild_id in self.toggle:
            if self.sensitivity[guild_id] == 'low':
                sensitivity_level = 3
            else:
                sensitivity_level = 2
            if guild_id in self.blacklist:
                if msg.channel.id in self.blacklist[guild_id]:
                    return

            # msgs to delete if triggered
            if user_id not in self.msgs:
                self.msgs[user_id] = []
            self.msgs[user_id].append([msg, time()])
            self.msgs[user_id] = self.msgs[user_id][-15:]

            # rate limit
            now = int(time() / 5)
            if guild_id not in self.spam_cd:
                self.spam_cd[guild_id] = {}
            if user_id not in self.spam_cd[guild_id]:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][0] == now:
                self.spam_cd[guild_id][user_id][1] += 1
            else:
                self.spam_cd[guild_id][user_id] = [now, 0]
            if self.spam_cd[guild_id][user_id][1] > sensitivity_level:
                if self.toggle[guild_id]['Rate-Limit']:
                    triggered = True

            # mass pings
            mentions = [*msg.mentions, *msg.role_mentions]
            if len(mentions) > sensitivity_level + 1 or msg.guild.default_role in mentions:
                if msg.guild.default_role in mentions:
                    if mentions.count(msg.guild.default_role) > 1 or len(mentions) > sensitivity_level + 1:
                        if self.toggle[guild_id]['Mass-Pings']:
                            triggered = True
                else:
                    if self.toggle[guild_id]['Mass-Pings']:
                        triggered = True

            # anti macro
            if user_id not in self.macro_cd:
                self.macro_cd[user_id] = {}
                self.macro_cd[user_id]['intervals'] = []
            if 'last' not in self.macro_cd[user_id]:
                self.macro_cd[user_id]['last'] = datetime.now()
            else:
                last = self.macro_cd[user_id]['last']
                self.macro_cd[user_id]['intervals'].append((datetime.now() - last).seconds)
                intervals = self.macro_cd[user_id]['intervals']
                self.macro_cd[user_id]['intervals'] = intervals[-sensitivity_level + 1:]
                if len(intervals) > 2:
                    if all(interval == intervals[0] for interval in intervals):
                        if self.toggle[guild_id]['Anti-Macro']:
                            triggered = True

            # duplicate messages
            if channel_id not in self.dupes:
                self.dupes[channel_id] = []
                self.dupez[channel_id] = []
            self.dupes[channel_id].append([msg, time()])
            self.dupes[channel_id] = self.dupes[channel_id][:10]
            self.dupez[channel_id].append([msg, time()])
            self.dupez[channel_id] = self.dupes[channel_id][:10]
            data = [(m, m.content) for m, m_time in self.dupes[channel_id] if m_time > time() - 7 and len(m.content) > 3]
            contents = [x[1] for x in data]
            duplicates = [m for m in contents if contents.count(m) > sensitivity_level]
            if msg.content in duplicates:
                data = [(m, m_time) for m, m_time in self.dupez[channel_id] if msg.content == m.content and [m, m_time] in data]
                for m, m_time in data:
                    self.dupez[channel_id].pop(self.dupez[channel_id].index([m, m_time]))
                    if m in self.msgs[str(m.author.id)]:
                        self.msgs[user_id].pop(self.msgs[user_id].index(m))
                await msg.channel.delete_messages([m[1] for m in data])
                if self.toggle[guild_id]['Duplicates']:
                    triggered = True

            if triggered:
                bot = msg.guild.me
                perms = [perm for perm, value in bot.guild_permissions]
                if "manage_roles" not in perms or "manage_messages" not in perms:
                    if msg.channel.permissions_for(bot).send_messages:
                        del self.toggle[guild_id]
                        del self.sensitivity[guild_id]
                        await msg.channel.send("Disabled anti spam, missing required permissions")
                        self.save_data()
                    return
                messages = [m for m, mtime in self.msgs[user_id] if mtime > time() - 15]
                self.msgs[user_id] = []  # removes deleted messages from the list
                if msg.author.top_role.position >= bot.top_role.position:
                    return await msg.channel.delete_messages(messages)
                await msg.channel.delete_messages(messages)
                if "send_messages" not in perms:
                    return
                async with msg.channel.typing():
                    with open("./data/userdata/mod.json", "r") as f:
                        dat = json.load(f)  # type: dict
                        if "timers" in dat:
                            if user_id in dat['timers']:
                                return
                    if guild_id not in self.status:
                        self.status[guild_id] = {}
                    if user_id in self.status[guild_id]:
                        return
                    self.status[guild_id][user_id] = "working"
                    mute_role = discord.utils.get(msg.guild.roles, name="Muted")
                    if not mute_role:
                        mute_role = discord.utils.get(msg.guild.roles, name="muted")
                    if not mute_role:
                        if "manage_channels" not in perms:
                            if msg.channel.permissions_for(bot).send_messages:
                                del self.toggle[guild_id]
                                del self.sensitivity[guild_id]
                                await msg.channel.send("Disabled anti spam, missing required permissions")
                                self.save_data()
                            return
                        mute_role = await msg.guild.create_role(name="Muted", color=discord.Color(colors.black()),
                                                              hoist=True)
                        for channel in msg.guild.text_channels:
                            await channel.set_permissions(mute_role, send_messages=False)
                        for channel in msg.guild.voice_channels:
                            await channel.set_permissions(mute_role, speak=False)
                    self.roles[user_id] = []
                    for role in msg.author.roles:
                        try:
                            await msg.author.remove_roles(role)
                            self.roles[user_id].append(role)
                            await asyncio.sleep(1)
                        except:
                            pass
                    multiplier = 0
                    if guild_id not in self.mutes:
                        self.mutes[guild_id] = {}
                    if user_id not in self.mutes[guild_id]:
                        self.mutes[guild_id][user_id] = []
                    self.mutes[guild_id][user_id].append(time())
                    for mute_time in self.mutes[guild_id][user_id]:
                        if mute_time > time() - 3600:
                            multiplier += 1
                        else:
                            index = self.mutes[guild_id][user_id].index(mute_time)
                            self.mutes[guild_id][user_id].pop(index)
                    timer = 150 * multiplier
                    timer_str = utils.get_time(timer)
                    await msg.author.add_roles(mute_role)
                    messages = [m for m, mtime in self.msgs[user_id]]
                    await msg.channel.delete_messages(messages)
                    self.msgs[user_id] = []
                    try:
                        await msg.author.send(f"You've been muted for spam in **{msg.guild.name}** for {timer_str}")
                    except:
                        pass
                    await msg.channel.send(f"Temporarily muted `{msg.author.display_name}` for spam")
                await asyncio.sleep(timer)
                if user_id in self.status[guild_id]:
                    user = msg.guild.get_member(int(user_id))
                    if isinstance(user, discord.Member):
                        with open("./data/userdata/mod.json", "r") as f:
                            dat = json.load(f)  # type: dict
                            if "timers" in dat:
                                if user_id in dat['timers']:
                                    return
                        if mute_role in msg.author.roles:
                            async with msg.channel.typing():
                                try:
                                    await msg.author.remove_roles(mute_role)
                                except:
                                    pass
                        for role in self.roles[user_id]:
                            if role not in msg.author.roles:
                                await asyncio.sleep(1)
                                try:
                                    await msg.author.add_roles(role)
                                except:
                                    pass
                        await msg.channel.send(f"Unmuted {msg.author.display_name}")
                    del self.status[guild_id][user_id]

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_id = str(before.guild.id)
        user_id = str(before.id)
        if user_id in self.roles:
            for role in before.roles:
                if 'muted' in str(role.name).lower():
                    if role not in after.roles:
                        for role in self.roles[user_id]:
                            await before.add_roles(role)
                        del self.roles[user_id]
                        del self.status[guild_id][user_id]
                        return

def setup(bot):
    bot.add_cog(AntiSpam(bot))
