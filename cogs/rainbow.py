from discord.ext import commands
import discord
import asyncio

CONFIG = {
    "USER_ID": 292840109072580618,
    "GUILDS": {
        459470568585035778: {
            "ROLE": "Thats Gross",
            "COLORS": [
                "#ff0000",
                "#ff002a",
                "#ff0055",
                "#ff007f",
                "#ff00aa",
                "#ff00d4",
                "#ff00ff",
                "#d500ff",
                "#aa00ff",
                "#8000ff",
                "#5500ff",
                "#2b00ff",
                "#0000ff",
                "#002aff",
                "#0055ff",
                "#007fff",
                "#00aaff",
                "#00d4ff",
                "#00ffff",
                "#00ffd5",
                "#00ffaa",
                "#00ff80",
                "#00ff55",
                "#00ff2b",
                "#00ff00",
                "#2aff00",
                "#55ff00",
                "#7fff00",
                "#aaff00",
                "#d4ff00",
                "#ffff00",
                "#ffd500",
                "#ffaa00",
                "#ff8000",
                "#ff5500",
                "#ff2b00",
            ],
            "CYCLE_DURATION": 50,
            "STOP_AFTER_N_SECONDS": 50
        },
        548461409810251776: {
            "ROLE": "Μεγαλύτερος",
            "COLORS": [
                "#ff0000",
                "#ff002a",
                "#ff0055",
                "#ff007f",
                "#ff00aa",
                "#ff00d4",
                "#ff00ff",
                "#d500ff",
                "#aa00ff",
                "#8000ff",
                "#5500ff",
                "#2b00ff",
                "#0000ff",
                "#002aff",
                "#0055ff",
                "#007fff",
                "#00aaff",
                "#00d4ff",
                "#00ffff",
                "#00ffd5",
                "#00ffaa",
                "#00ff80",
                "#00ff55",
                "#00ff2b",
                "#00ff00",
                "#2aff00",
                "#55ff00",
                "#7fff00",
                "#aaff00",
                "#d4ff00",
                "#ffff00",
                "#ffd500",
                "#ffaa00",
                "#ff8000",
                "#ff5500",
                "#ff2b00",
            ],
            "CYCLE_DURATION": 50,
            "STOP_AFTER_N_SECONDS": 50
        }
    }
}

class HopefulNoDiscordAPIRapeRainbowRoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cycling = False

    async def cycle_colors(self, guild_id: int, role_name: str, colors: list, duration: int, stop_after: int):
        delay = int(duration / len(colors))  # change color every n seconds
        try:
            guild = self.bot.get_guild(guild_id)
            if isinstance(guild, discord.Guild):
                role = None  # type: discord.Role
                for r_tmp in guild.roles:
                    if r_tmp.name == role_name:
                        role = r_tmp
                        break
                if role is not None:
                    index = 0
                    original = role.color
                    delay_counter = 0
                    self.cycling = True
                    for iterations in range(stop_after):
                        delay_counter += 1
                        if delay_counter <= delay:
                            await asyncio.sleep(1)
                            continue
                        delay_counter = 0

                        color = colors[index]  # type: str

                        index += 1
                        if index >= len(colors):
                            index = 0

                        await role.edit(color=discord.Color(int(color.replace("#", "0x"), 0)))

                        await asyncio.sleep(1)  # the loop is every 1 sec
                    await role.edit(color=original)  # revert to original
                    self.cycling = False
        except Exception as e:
            print(e)
            self.cycling = False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == CONFIG["USER_ID"] and not self.cycling:
            if message.guild.id in CONFIG["GUILDS"].keys():
                conf = CONFIG["GUILDS"][message.guild.id]
                self.bot.loop.create_task(
                    self.cycle_colors(
                        message.guild.id,
                        conf["ROLE"],
                        conf["COLORS"],
                        conf["CYCLE_DURATION"],
                        conf["STOP_AFTER_N_SECONDS"]
                    )
                )

def setup(bot):
    bot.add_cog(HopefulNoDiscordAPIRapeRainbowRoleCog(bot))
