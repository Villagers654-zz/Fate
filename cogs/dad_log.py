from datetime import datetime, timedelta
from discord.ext import commands
import discord


class DadLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.typing = {355026215137968129: None, 243182786909962251: None}
        self.msg = {355026215137968129: None, 243182786909962251: None}
        self.status = {355026215137968129: None, 243182786909962251: None}

    @commands.command(name='dad-log')
    async def dad_log(self, ctx):
        last = {}; log = ''
        for user_id, time in self.status.items():
            if time:
                time = round((datetime.now() - time).seconds / 60)
            last[user_id] = f'Last Online: {time} minutes ago'
        for user_id, time in self.msg.items():
            if time:
                time = round((datetime.now() - time).seconds / 60)
            last[user_id] += f'\nLast Msg: {time} minutes ago'
        for user_id, time in self.typing.items():
            if time:
                time = round((datetime.now() - time).seconds / 60)
            last[user_id] += f'\nLast Typed: {time} minutes ago'
        for user_id, data in last.items():
            user = self.bot.get_user(user_id)
            log += f'__**{user.name}:**__\n{data}\n\n'
        e = discord.Embed(description=log)
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if user.id in self.typing:
            self.typing[user.id] = datetime.now()

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id in self.msg:
            self.msg[msg.author.id] = datetime.now()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.id in self.status:
            self.status[before.id] = datetime.now()

def setup(bot):
    bot.add_cog(DadLog(bot))
