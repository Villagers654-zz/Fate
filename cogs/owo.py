# helper for OwO bot

from os import path
import json
import asyncio
from discord.ext import commands
import discord
import aiofiles
from utils import colors


bot_id = 408785106942164992


class HelpMenu:
    def __init__(self, bot):
        self.bot = bot
        self.coro = True

    async def embed(self):
        owo = await self.bot.fetch_user(408785106942164992)
        e = discord.Embed(color=colors.fate())
        e.set_author(name="OwO Helper - Usage", icon_url=owo.avatar_url)
        e.description = "None yet :]"
        return e


class OwOBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = "./data/userdata/owo_bot.json"
        self.enabled = [470961230362837002]
        self.owo_bot = 408785106942164992
        if path.isfile(self.path):
            with open(self.path, "r") as f:
                self.enabled = json.load(f)
        self.hunt_bot = {}
        self.hunt = {}
        self.battle = {}
        self.action = {}

    async def save_data(self):
        async with aiofiles.open("self.path", "w") as f:
            await f.write(json.dumps(self.enabled))

    @commands.Cog.listener()
    async def on_message(self, message):
        cooldown = 15
        if message.guild and message.guild.id in self.enabled:

            async def wait_for(user_id, *requires, timeout=5, has_embed=False):
                def pred(m) -> bool:  # predicate
                    if requires and not any(arg in m.content for arg in requires):
                        if has_embed and not m.embeds:
                            return False
                        if m.embeds:
                            author = m.embeds[0].author.name
                            if not any(arg in author for arg in requires):
                                return False
                            return True
                        else:
                            return False
                    return m.author.id == user_id and m.channel.id == message.channel.id

                try:
                    msg = await self.bot.wait_for(
                        "message", check=pred, timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return None
                else:
                    return msg

            def has(*arguments) -> bool:
                return any(
                    str(message.content).lower().startswith(arg) for arg in arguments
                )

            if has("owoh", "owohunt"):
                msg = await wait_for(self.owo_bot, message.author.name + "**, hunt")
                if msg:
                    if "increased" in msg.content:
                        cooldown += 15
                    await asyncio.sleep(round(cooldown))
                    await message.channel.send(
                        f"{message.author.mention}, you can hunt again"
                    )

            if has("owob", "owobattle"):
                msg = await wait_for(self.owo_bot, message.author.name, has_embed=True)
                if msg:
                    if "increased" in msg.content:
                        cooldown += 15
                    await asyncio.sleep(round(cooldown))
                    await message.channel.send(
                        f"{message.author.mention}, you can battle again"
                    )

        # async def get_user(name, cmds):
        #     async for m in msg.channel.history(limit=5):
        #         if name == m.author.name and any(m.content.startswith(cmd) for cmd in cmds):
        #             return m.author
        #     return None
        #
        # if msg.guild and msg.guild.id in self.enabled and msg.author.id == bot_id:
        #     cd = 0
        #     if msg.content and 'cooldown' in msg.content:
        #         cd += 15
        #     if msg.embeds and msg.embeds[0].author:
        #         em = msg.embeds[0]  # type: discord.Embed
        #         battle_end = ' goes into battle!'
        #         if em.author.name.endswith(battle_end):
        #             username = em.author.name.strip(battle_end)
        #             user = await get_user(username, ['b', 'battle'])
        #             await asyncio.sleep(15+cd)
        #             await msg.channel.send(f"{user.mention}, you can battle again")
        #     if msg.content and 'hunt is empowered' in msg.content:
        #         username = re.findall('|.*,', msg.content)[1].strip('|').strip(',')
        #         user = await get_user(username, ['h', 'hunt'])
        #         await asyncio.sleep(15+cd)
        #         await msg.channel.send(f"{user.mention}, you can hunt again")

    @commands.group(name="owobot")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def owo_bot(self, ctx):
        if not ctx.invoked_subcommand:
            help = HelpMenu(self.bot)
            e = await help.embed() if help.coro else help.embed()
            await ctx.send(embed=e)
            await self.save_data()

    @owo_bot.command(name="enable")
    @commands.has_permissions(manage_messages=True)
    async def enable(self, ctx):
        if ctx.guild.id in self.enabled:
            return await ctx.send("You already have this enabled")
        self.enabled.append(ctx.guild.id)
        await self.save_data()


def setup(bot):
    bot.add_cog(OwOBot(bot))
