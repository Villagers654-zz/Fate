import random
import os
from discord.ext import commands
import discord
from utils import colors


class Reactions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = ['.', '/']
        self.blocked = ['welcome', 'farewell']

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        for prefix in self.prefix:
            if prefix in msg.content:
                cmd = msg.content.split(prefix)[1].split(' ')[0].lower()
                if cmd in self.blocked:
                    return
                if any(cmd == directory for directory in os.listdir('./data/images/reactions')):
                    path = f'./data/images/reactions/{cmd}/'\
                          + random.choice(os.listdir(f'./data/images/reactions/{cmd}/'))
                    e = discord.Embed(color=colors.fate())
                    e.set_image(url="attachment://" + os.path.basename(path))
                    await msg.channel.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

def setup(bot):
    bot.add_cog(Reactions(bot))
