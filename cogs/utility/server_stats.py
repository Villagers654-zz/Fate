import json
from discord.ext import commands
import discord


class ServerStatistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="server-stats", aliases=["serverstats", "server_stats", "ss"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def server_statistics(self, ctx):
        if not ctx.invoked_subcommand:
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="Server Stat Channels", icon_url=self.bot.user.avatar_url)
            e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
            e.description = "• Use voice channels to automatically update and show server statistics\n" \
                            "• Display things like the member count, bot count, and boost count"
            p = self.bot.utils.get_prefix(ctx)
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
                channel = await converter.convert(ctx, reply.content)
                results[channel_type] = channel.id

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

        await ctx.send("Enabled member_count")

    @server_statistics.command(name="disable")
    async def _disable(self, ctx):
        async with self.bot.cursor() as cur:
            await cur.execute(f"select guild_id from server_stats where guild_id = {ctx.guild.id};")
            if not cur.rowcount:
                return await ctx.send("Server stats aren't enabled in this server")
            await cur.execute(f"delete from server_stats where guild_id = {ctx.guild.id};")
        await ctx.send("Disabled server stats")


def setup(bot):
    bot.add_cog(ServerStatistics(bot))
