import requests
import json
import os
import codecs
import random
import asyncio

from discord.ext import commands
import discord

from utils import colors


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ritter-api", aliases=["2b2t", "ritter", "lolritter"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def ritter_api(self, ctx, player_name=None):
        if not player_name:
            e = discord.Embed(color=colors.green())
            e.set_author(
                name="2B2T Queue",
                icon_url="https://cdn.discordapp.com/avatars/79305800157233152/a_1d26f615a6271e4e15216b0a01c5e03e.gif?size=1024",
            )
            e.set_thumbnail(url="https://bot.2b2t.dev/img/2b2t.png")
            e.description = "Powered By [2b2t.dev](https://2b2t.dev)"
            e.set_image(url=f"https://tab.2b2t.dev/?{random.randint(1000, 99999)}")
            msg = await ctx.send(embed=e)
            return await msg.add_reaction("🔄")
        url = "https://api.2b2t.dev/stats?username=" + player_name
        content = requests.get(url).json()
        if not content:
            return await ctx.send(f"No data available for that user")
        dat = content[0]  # type: dict
        url = "https://minotar.net/avatar/" + player_name
        path = os.getcwd() + "/static/skin.png"
        with open(path, "wb") as f:
            f.write(requests.get(url).content)
        e = discord.Embed(color=colors.green())
        e.set_author(
            name=f"{player_name} Stats",
            icon_url="attachment://" + os.path.basename(path),
        )
        e.description = (
            f"Kills: {dat['kills']}"
            f"\nDeaths: {dat['deaths']}"
            f"\nJoins: {dat['joins']}"
        )
        await ctx.send(
            embed=e, file=discord.File(path, filename=os.path.basename(path))
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if str(payload.emoji) == "🔄":
            msg = await channel.fetch_message(payload.message_id)
            if msg.author.id == self.bot.user.id and msg.embeds:
                if "2b2t.dev" in str(msg.embeds[0].to_dict()):
                    for reaction in msg.reactions:
                        async for user in reaction.users():
                            if user.id != self.bot.user.id:
                                e = msg.embeds[0]
                                e.set_image(
                                    url=f"https://tab.2b2t.dev/?{random.randint(1000, 99999)}"
                                )
                                await msg.edit(embed=e)
                                await msg.remove_reaction(reaction, user)


def setup(bot):
    bot.add_cog(Minecraft(bot))
