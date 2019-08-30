from discord.ext import commands
import discord
import asyncio
from utils import checks
from utils.colors import ColorSets

CONFIG = {
    264838866480005122: {
        'GUILDS': {
            579823772547153958: {
                'TOGGLE': False,
                'ROLE': '◈𝓛𝓾𝓬𝓴 ◈',
                'COLORS': ColorSets().rainbow(),
                'CYCLE_DURATION': 50,
                'STOP_AFTER_N_SECONDS': 50
            },
            598386553894600705: {
                'TOGGLE': False,
                'ROLE': '🍀𝓛𝓾𝓬𝓴 🍀',
                'COLORS': ColorSets().rainbow(),
                'CYCLE_DURATION': 50,
                'STOP_AFTER_N_SECONDS': 50
            },
        }
    },
    598386553894600705: {
        'GUILDS': {
            579823772547153958: {
                'TOGGLE': False,
                'ROLE': '◈𝓛𝓾𝓬𝓴 ◈',
                'COLORS': ColorSets().rainbow(),
                'CYCLE_DURATION': 50,
                'STOP_AFTER_N_SECONDS': 50
            }
        }
    },
    292840109072580618: {
        'GUILDS': {
            548461409810251776: {
                'TOGGLE': True,
                'ROLE': 'Μεγαλύτερος',
                'COLORS': ColorSets().rainbow(),
                'CYCLE_DURATION': 50,
                'STOP_AFTER_N_SECONDS': 50
            },
            616048390517686278: {
                'TOGGLE': True,
                'ROLE': 'Rainbow',
                'COLORS': ColorSets().rainbow(),
                'CYCLE_DURATION': 50,
                'STOP_AFTER_N_SECONDS': 50
            }
        }
    }
}


class Rainbow(commands.Cog):
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

                        await role.edit(color=discord.Color(int(str(color).replace("#", "0x"), 0)))

                        await asyncio.sleep(1)  # the loop is every 1 sec
                    await role.edit(color=original)  # revert to original
                    self.cycling = False
        except Exception as e:
            print(e)
            self.cycling = False

    @commands.command(name='rainbowembed', aliases=['rembed'])
    @commands.check(checks.luck)
    async def rainbow_embed(self, ctx, text):
        e = discord.Embed()
        e.description = text
        msg = await ctx.send(embed=e)
        await ctx.message.delete()
        colors = ColorSets().rainbow()
        for color in colors:
            e.colour = discord.Color(int(color.replace("#", "0x"), 0))
            await msg.edit(embed=e)
            await asyncio.sleep(1)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.id in CONFIG and not self.cycling:
            if msg.guild.id in CONFIG[msg.author.id]["GUILDS"].keys():
                conf = CONFIG[msg.author.id]['GUILDS'][msg.guild.id]
                if conf['TOGGLE']:
                    self.bot.loop.create_task(
                        self.cycle_colors(
                            msg.guild.id,
                            conf['ROLE'],
                            conf['COLORS'],
                            conf['CYCLE_DURATION'],
                            conf['STOP_AFTER_N_SECONDS']
                        )
                    )

def setup(bot):
    bot.add_cog(Rainbow(bot))
