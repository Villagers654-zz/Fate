from discord.ext import commands
import discord
import json
from utils import colors


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dir = "./data/userdata/config.json"

    def get_config(self):
        with open(self.dir, "r") as config:
            return json.load(config)

    def update_config(self, config):
        with open(self.dir, "w") as f:
            json.dump(config, f, ensure_ascii=False)

    @commands.command(name="changepresence", aliases=["cp"])
    @commands.is_owner()
    async def change_presence(self, ctx, *, presence):
        config = self.get_config()  # type: dict
        config["presence"] = presence
        self.update_config(config)
        await ctx.message.add_reaction("👍")

    @commands.command(name="block")
    @commands.is_owner()
    async def block(self, ctx, user):
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            if user.isdigit():
                user = await self.bot.fetch_user(int(user))
            else:
                return await ctx.send("user not found")
        config = self.get_config()  # type: dict
        if "blocked" not in config:
            await ctx.send("Odd, blocked key didnt exist")
            config["blocked"] = []
        config["blocked"].append(user.id)
        config["blocked"] = list(set(config["blocked"]))
        self.update_config(config)
        await ctx.send(f"Blocked {user}")

    @commands.command(name="unblock")
    @commands.is_owner()
    async def unblock(self, ctx, user):
        if ctx.message.mentions:
            user_id = ctx.message.mentions[0].id
        elif user.isdigit():
            user_id = int(user)
        else:
            return await ctx.send("user not found")
        config = self.get_config()  # type: dict
        index = config["blocked"].index(user_id)
        config["blocked"].pop(index)
        self.update_config(config)
        user = self.bot.get_user(user_id)
        user = user if isinstance(user, discord.User) else user_id
        await ctx.send(f"Unblocked {user}")

    @commands.command(name="blocked")
    @commands.is_owner()
    async def blocked(self, ctx):
        config = self.get_config()  # type: dict
        e = discord.Embed(color=colors.fate())
        e.set_author(name="Blocked Users", icon_url=self.bot.user.avatar_url)
        e.description = ""
        for user_id in config["blocked"]:
            user = await self.bot.fetch_user(int(user_id))
            e.add_field(name=str(user), value=str(user_id))
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(User(bot))
