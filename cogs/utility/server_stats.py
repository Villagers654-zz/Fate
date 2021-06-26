import asyncio
from discord.ext import commands
import discord
from botutils import get_prefix


class ServerStatistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.defaults = {
            "members": "👥 | {count} Members",
            "bots": "🤖 | {count} Bots",
            "boosts": "💎 | {count} Boosts"
        }
        self.configs = {}
        self.bot.loop.create_task(self.cache_configs())

    async def cache_configs(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        for _ in range(10):
            if self.bot.pool:
                break
            await asyncio.sleep(5)
        else:
            self.bot.log.critical("Can't cache server stat configs")
        async with self.bot.cursor()as cur:
            columns = [
                "guild_id", "members", "members_fmt", "bots", "bots_fmt", "boosts", "boosts_fmt"
            ]
            await cur.execute(
                f"select {', '.join(columns)} from server_stats;"
            )
            results = await cur.fetchall()
        for guild_id, members, members_fmt, bots, bots_fmt, boosts, boosts_fmt in results:
            self.configs[guild_id] = {
                "members": {
                    "channel_id": members,
                    "format": self.bot.decode(members_fmt) if members_fmt else self.defaults["members"]
                },
                "bots": {
                    "channel_id": bots,
                    "format": self.bot.decode(bots_fmt) if bots_fmt else self.defaults["bots"],
                },
                "boosts": {
                    "channel_id": boosts,
                    "format": self.bot.decode(boosts_fmt) if boosts_fmt else self.defaults["boosts"]
                }
            }
        self.bot.log.info("Cached server statistic configs")

    @commands.group(name="server-stats", aliases=["serverstats", "server_stats", "ss"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def server_statistics(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Server Stat Channels", icon_url=self.bot.user.avatar.url)
            e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
            e.description = "• Use voice channels to automatically update and show server statistics\n" \
                            "• Display things like the member count, bot count, and boost count"
            p = get_prefix(ctx)
            e.add_field(
                name="◈ Usage",
                value=f"{p}server-stats enable\n"
                      f"`helps you setup the module`\n"
                      f"{p}server-stats disable\n"
                      f"`completely disables the module`\n"
                      f"{p}server-stats config\n"
                      f"`send your current setup`",
                inline=False
            )
            e.add_field(
                name="◈ Formatting",
                value="You can alter the channel name format just by editing the actual channels name. "
                      "Just put `{count}` where you want it to put the count",
                inline=False
            )
            await ctx.send(embed=e)

    @server_statistics.command(name="enable")
    async def _enable(self, ctx):
        converter = commands.VoiceChannelConverter()
        types = ["members", "bots", "boosts"]
        results = {}

        for channel_type in types:
            await ctx.send(
                f"Should I show the count of {channel_type}? "
                f"Name the voice channel if you do, otherwise say `skip`"
            )
            reply = await self.bot.utils.get_message(ctx)
            if "skip" in reply.content:
                results[channel_type] = None
            else:
                if not any(reply.content == c.name for c in ctx.guild.voice_channels):
                    return await ctx.send("That voice channel doesn't exist")
                channel = await converter.convert(ctx, reply.content)
                results[channel_type] = channel.id

        if not any(value for value in results.values()):
            return await ctx.send("You didn't choose to use any of the channel types")

        values = f"{ctx.guild.id}"
        for ctype, channel_id in results.items():
            values += f", {channel_id}, null"

        sql = f"insert into server_stats values ({values}) " \
              f"on duplicate key update " \
              f"members = {results['members']}, " \
              f"bots = {results['bots']}, " \
              f"boosts = {results['boosts']};"

        async with self.bot.cursor() as cur:
            await cur.execute(
                sql.replace("None", "null")
            )

        self.configs[ctx.guild.id] = {
            ctype: {
                "channel_id": channel_id,
                "format": self.defaults[ctype]
            } for ctype, channel_id in results.items()
        }

        for ctype, channel_id in results.items():
            if not channel_id:
                continue
            channel = self.bot.get_channel(channel_id)
            fmt = lambda count: self.defaults[ctype].replace("{count}", str(count))

            if ctype == "members":
                await channel.edit(name=fmt(len([m for m in ctx.guild.members if not m.bot])))
            elif ctype == "bots":
                await channel.edit(name=fmt(len([m for m in ctx.guild.members if m.bot])))
            elif ctype == "boosts":
                await channel.edit(name=fmt(ctx.guild.premium_subscription_count))

        await ctx.send("Enabled server stats")

    @server_statistics.command(name="disable")
    async def _disable(self, ctx):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select * from server_stats where guild_id = {ctx.guild.id};")
            if not cur.rowcount:
                return await ctx.send("Server stats aren't enabled in this server")
            await cur.execute(f"delete from server_stats where guild_id = {ctx.guild.id};")
        if ctx.guild.id in self.configs:
            del self.configs[ctx.guild.id]
        await ctx.send("Disabled server stats")

    async def update_format(self, guild_id, ctype, format):
        async with self.bot.cursor() as cur:
            await cur.execute(
                f"update server_stats "
                f"set {ctype}_fmt = '{self.bot.encode(format)}' "
                f"where guild_id = {guild_id};"
            )
        if guild_id in self.configs:
            self.configs[guild_id][ctype]["format"] = format

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before and after and before.guild.id in self.configs and "{count}" in after.name:
            guild_id = before.guild.id
            for ctype, data in list(self.configs[guild_id].items()):
                if before.id == data["channel_id"]:
                    await self.update_format(guild_id, ctype, after.name)
                    if ctype == "members":
                        await self.update_members(before.guild)
                    elif ctype == "bots":
                        await self.update_bots(before.guild)
                    elif ctype == "boosts":
                        await self.update_boosts(before.guild)
                    break

    async def update_members(self, guild):
        conf = self.configs[guild.id]  # type: dict
        channel = self.bot.get_channel(conf["members"]["channel_id"])
        if not channel:
            return
        count = len([m for m in guild.members if not m.bot])
        name = conf["members"]["format"].replace("{count}", str(count))
        await channel.edit(name=name)

    async def update_bots(self, guild):
        conf = self.configs[guild.id]  # type: dict
        channel = self.bot.get_channel(conf["bots"]["channel_id"])
        if not channel:
            return
        count = len([m for m in guild.members if m.bot])
        name = conf["members"]["format"].replace("{count}", str(count))
        await channel.edit(name=name)

    async def update_boosts(self, guild):
        conf = self.configs[guild.id]
        channel = self.bot.get_channel(conf["boosts"]["channel_id"])
        if not channel:
            return
        count = guild.premium_subscription_count
        name = conf["boosts"]["format"].replace("{count}", str(count))
        await channel.edit(name=name)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.configs:
            conf = self.configs[member.guild.id]
            if not member.bot and conf["members"]["channel_id"]:
                await self.update_members(member.guild)
            elif member.bot and conf["bots"]["channel_id"]:
                await self.update_bots(member.guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before and after and before.id in self.configs:
            conf = self.configs[before.id]  # type: dict
            if conf["boosts"]["channel_id"]:
                if before.premium_subscription_count != after.premium_subscription_count:
                    await self.update_boosts(after)


def setup(bot):
    bot.add_cog(ServerStatistics(bot), override=True)
