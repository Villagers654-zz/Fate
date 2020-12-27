
import discord
from discord.ext import commands


class QubeMC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 630178744908382219
        self.channel_id = 670366452003373108
        self.message_id = 792619753897459713

    @property
    def embed(self):
        guild = self.bot.get_guild(self.guild_id)
        e = discord.Embed()
        e.set_author(name="Server Statistics", icon_url=guild.icon_url)
        s = discord.Status
        emotes = self.bot.utils.emotes
        e.description = f"👥 {guild.member_count} members\n" \
                        f"{emotes.online} {len([m for m in guild.members if m.status is m.status is s.online])} " \
                        f"{emotes.idle} {len([m for m in guild.members if m.status is s.idle])} " \
                        f"{emotes.dnd} {len([m for m in guild.members if m.status is s.dnd])} " \
                        f"{emotes.offline} {len([m for m in guild.members if m.status is s.offline])}\n" \
                        f"{emotes.boost} {guild.premium_subscription_count} boosts\n" \
                        f"{emotes.booster} {len(guild.premium_subscribers)} boosters"
        return e

    async def update_embed(self):
        channel = self.bot.get_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)
        await message.edit(content=None, embed=self.embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == self.guild_id:
            await self.update_embed()

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        if member.guild.id == self.guild_id:
            await self.update_embed()


def setup(bot):
    bot.add_cog(QubeMC(bot))
