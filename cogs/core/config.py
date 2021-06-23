import asyncio

from discord.ext import commands
import discord

from botutils import colors
from botutils import get_prefixes_async


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_config(self, config):
        async with self.bot.utils.open("./data/userdata/config.json", "w") as f:
            await f.write(await self.bot.dump(config))

    @commands.group(name="config", aliases=["conf"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def _config(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=colors.fate)
            e.set_author(
                name="| 💎 Server Config 💎", icon_url=ctx.guild.owner.avatar_url
            )
            e.set_thumbnail(url=ctx.guild.icon_url)
            p = await get_prefixes_async(self.bot, ctx.message)
            e.description = f"**Prefix:** [`{p[2]}`]\n"

            cogs = ""
            for name, cog in self.bot.cogs.items():
                await asyncio.sleep(0)
                if hasattr(cog, "is_enabled"):
                    toggle = cog.is_enabled(ctx.guild.id)
                    if hasattr(toggle, "__await__"):
                        toggle = await toggle
                    toggle = "active" if toggle else "inactive"
                    cogs += f"\n**{name}:** [`{toggle}`]"

            e.add_field(name="◈ Modules ◈", value=cogs, inline=False)
            subcommands = f"{p[2]}config warns"
            e.add_field(name="◈ Editable Configs ◈", value=subcommands, inline=False)
            await ctx.send(embed=e)

    @_config.command(name="warns")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _warns(self, ctx):
        guild_id = str(ctx.guild.id)
        emojis = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣"]
        config = self.bot.utils.get_config()  # type: dict
        if "warns" not in config:
            config["warns"] = {}
        if "expire" not in config["warns"]:
            config["warns"]["expire"] = []
        if "punishments" not in config["warns"]:
            config["warns"]["punishments"] = {}
        await self.save_config(config)
        if guild_id not in config:
            config["warns"][guild_id] = {}

        async def wait_for_reaction():
            def check(reaction, user):
                return user == ctx.author

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=check
                )
            except asyncio.TimeoutError:
                await ctx.send("Timeout Error")
            else:
                return str(reaction.emoji)

        def emoji(index):
            return emojis[index - 1]

        def default():
            e = discord.Embed(color=colors.fate)
            e.set_author(name="Warn Config", icon_url=ctx.author.avatar_url)
            e.description = (
                f"{emoji(1)} : View Config\n"
                f"{emoji(2)} : Edit Config\n"
                f"{emoji(3)} : Cancel\n"
            )
            return e

        complete = False
        msg = await ctx.send(embed=default())
        while not complete:
            await msg.edit(embed=default())
            await msg.clear_reactions()
            await msg.add_reaction(emoji(1))
            await msg.add_reaction(emoji(2))
            await msg.add_reaction(emoji(3))
            reaction = await wait_for_reaction()
            if reaction == emoji(1):
                await msg.clear_reactions()
                config = self.bot.utils.get_config()  # type: dict
                if guild_id not in config["warns"]:
                    config["warns"][guild_id] = {}
                dat = config["warns"]
                expiring = False
                if guild_id in dat["expire"]:
                    expiring = True
                punishments = "None"
                if guild_id in dat["punishments"]:
                    punishments = ""
                    index = 1
                    for punishment in dat["punishments"][guild_id]:
                        punishments += f"**#{index}. `{punishment}`**\n"
                e = discord.Embed(color=colors.fate)
                e.set_author(name="Warn Config", icon_url=ctx.author.avatar_url)
                e.description = (
                    f"**Warns Expire: {expiring}\nCustom Punishments:**\n{punishments}"
                )
                await msg.edit(embed=e)
                await msg.add_reaction("⏹")
                await msg.add_reaction("🔄")
                reaction = await wait_for_reaction()
                if reaction == "⏹":
                    break
                if reaction == "🔄":
                    continue
            if reaction == emoji(2):
                await msg.clear_reactions()
                e = discord.Embed(color=colors.fate)
                e.description = "Should warns expire after a month?"
                await msg.edit(embed=e)
                await msg.add_reaction("✔")
                await msg.add_reaction("❌")
                reaction = await wait_for_reaction()
                config = self.bot.utils.get_config()  # type: dict
                if reaction == "✔":
                    if guild_id not in config["warns"]["expire"]:
                        config["warns"]["expire"].append(guild_id)
                        await self.save_config(config)
                else:
                    if guild_id in config["warns"]["expire"]:
                        index = config["warns"]["expire"].index(guild_id)
                        config["warns"]["expire"].pop(index)
                await msg.clear_reactions()
                e = discord.Embed(color=colors.fate)
                e.description = "Set custom punishments?"
                await msg.edit(embed=e)
                await msg.add_reaction("✔")
                await msg.add_reaction("❌")
                reaction = await wait_for_reaction()
                if reaction == "❌":
                    config = self.bot.utils.get_config()  # type: dict
                    if guild_id in config["warns"]["punishments"]:
                        del config["warns"]["punishments"][guild_id]
                        await self.save_config(config)
                else:
                    await msg.clear_reactions()
                    punishments = []

                    def dump():
                        config = self.bot.utils.get_config()  # type: dict
                        if guild_id not in config["warns"]:
                            config["warns"][guild_id] = {}
                        if punishments:
                            config["warns"]["punishments"][guild_id] = punishments
                        else:
                            config["warns"]["punishments"][guild_id] = ["None"]
                        self.save_config(config)

                    def pos(index):
                        positions = [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "4th",
                            "6th",
                            "7th",
                            "8th",
                        ]
                        return positions[index - 1]

                    index = 1
                    finished = False
                    while not finished:
                        if len(punishments) > 7:
                            dump()
                            break
                        e = discord.Embed(color=colors.fate)
                        e.description = (
                            f"**Punishments: {punishments}**\n\n"
                            f"Set the {pos(index)} punishment:\n"
                            f"1⃣: None\n2⃣ : Mute\n3⃣ : Kick\n"
                            f"4⃣ : Softban\n5⃣ : Ban\n"
                        )
                        index += 1
                        await msg.edit(embed=e)
                        for emoji in emojis:
                            await msg.add_reaction(emoji)
                        await msg.add_reaction("✔")
                        reaction = await wait_for_reaction()
                        if reaction == "✔":
                            dump()
                            break
                        options = ["None", "Mute", "Kick", "Softban", "Ban"]
                        try:
                            reaction_index = emojis.index(reaction)
                        except (discord.DiscordException, ValueError):
                            await ctx.send("Invalid reaction >:(")
                            continue
                        punishments.append(options[reaction_index])
            else:
                if reaction == emoji(3):
                    break
            break
        await ctx.message.delete()
        await msg.delete()


def setup(bot):
    bot.add_cog(Config(bot))
