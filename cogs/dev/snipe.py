
"""
cogs.dev.snipe
~~~~~~~~~~~~~~~

Improved snipe command

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
from io import BytesIO

from discord.ext import commands
import discord
from PIL import Image, ImageDraw, ImageFont

from botutils.pillow import add_corners
from botutils import split


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = {}

    async def add(self, key, item):
        """ Only index items in the key for 15 seconds """
        if key not in self.index:
            self.index[key] = []
        self.index[key].append(item)
        await asyncio.sleep(15)
        self.index[key].remove(item)
        if not self.index[key]:
            del self.index[key]

    @commands.command(name=".snipe")
    @commands.is_owner()
    async def _snipe(self, ctx):
        """ Some snipe command idk """
        def generate():
            msgs = []
            last_user = None
            for msg in messages:
                fmt = "\n".join(split(msg.content, 50))
                if msg.author.id == last_user:
                    last = len(msgs) - 1  # The position of the last item in the list
                    msgs[last][1] += f"\n{fmt}"
                else:
                    msgs.append([msg, fmt])
                last_user = msg.author.id

            width, height = 750, 75 * len(msgs)
            image = Image.new("RGBA", (width, height), (255, 0, 0, 0))
            image.save("test.png", format="PNG")
            return "test.png"

        messages = list(self.index[ctx.channel.id])
        fp = await self.bot.loop.run_in_executor(None, generate)
        await ctx.send(file=discord.File("test.png"))


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id == 397415086295089155:
            await self.add(message.channel.id, message)


def setup(bot):
    bot.add_cog(Snipe(bot))
