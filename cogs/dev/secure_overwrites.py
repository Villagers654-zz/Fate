from discord.ext import commands

CONFIG = {
    579823772547153958: [264838866480005122],  # 2B2TBE
    502719548739551233: [264838866480005122, 261451679239634944],  # 2B2TBE Staff
    470961230362837002: [264838866480005122, 261451679239634944],  # 4B4T
}


class SecureOverwrites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = after.guild
        channel = after
        if guild.id in CONFIG:
            if before.overwrites != after.overwrites:
                async for entry in after.guild.audit_logs(limit=1):
                    if (
                        entry.user.id not in CONFIG[guild.id]
                        and entry.user.id != self.bot.user.id
                    ):
                        for target, overwrite in after.overwrites.items():
                            if target in before.overwrites:
                                if overwrite == before.overwrites[target]:
                                    continue
                            else:
                                await channel.set_permissions(target, overwrite=None)
                                continue
                            await channel.set_permissions(
                                target, overwrite=before.overwrites[target]
                            )
                            continue
                        for target, overwrite in before.overwrites.items():
                            if target not in after.overwrites:
                                await channel.set_permissions(
                                    target, overwrite=overwrite
                                )


def setup(bot):
    bot.add_cog(SecureOverwrites(bot), override=True)
