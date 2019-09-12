import random
import os
import json
from discord.ext import commands
import discord
from utils import checks, colors


class Reactions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = '/'
        self.reactions = {}
        self.dir = './data/reactions.json'
        if os.path.isfile(self.dir):
            with open(self.dir, 'r') as f:
                self.data = json.load(f)

    def save_data(self):
        with open(self.dir, 'w+') as f:
            json.dump(self.reactions, f)

    @commands.group(name='reactions')
    @commands.check(checks.luck)
    async def reactions(self, ctx):
        pass

    @reactions.command(name='add')
    async def _add(self, ctx, reaction, action: bool):
        self.reactions[reaction] = action
        await ctx.send(f'Added {reaction} {"as an action" if action else ""}')
        self.save_data()

    @reactions.command(name='remove')
    async def _remove(self, ctx, reaction):
        del self.reactions[reaction]
        await ctx.send(f'Removed {reaction}')
        self.save_data()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if self.prefix in msg.content:
            cmd = msg.content.split(self.prefix)[1].split(' ')[0].lower()
            dat = self.reactions
            if any(cmd == key or any(cmd == sub for sub in dat[key]['sub']) for key in self.reactions.keys()):
                path = f'./data/images/reactions/{cmd}/'\
                      + random.choice(os.listdir(f'./data/images/reactions/{cmd}/'))
                e = discord.Embed(color=colors.fate())
                e.set_image(url="attachment://" + os.path.basename(path))
                await msg.channel.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

def setup(bot):
    bot.add_cog(Reactions(bot))
