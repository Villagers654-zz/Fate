from utils.utils import bytes2human
from discord.ext import commands
import discord
import psutil
import os

class Psutil(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def devstats(self, ctx):
		luck = self.bot.get_user(264838866480005122)
		f = psutil.Process(os.getpid())
		try: cpufreq = bytes2human(psutil.cpu_freq())
		except: cpufreq = "unavailable"
		try: cpufreqmax = bytes2human(psutil.cpu_freq().max)
		except: cpufreqmax = "unavailable"
		e = discord.Embed()
		e.set_author(name='| Memory | ', icon_url=luck.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
		e.description = f"__**Storage**__: [{bytes2human(psutil.disk_usage('/').used)}/{bytes2human(psutil.disk_usage('/').total)}]\n" \
			f"__**RAM**__: [{bytes2human(psutil.virtual_memory().used)}/{bytes2human(psutil.virtual_memory().total)}] ({psutil.virtual_memory().percent}%)\n" \
			f"__**CPU**__: **Global**: {psutil.cpu_percent()}% **Bot**: {f.cpu_percent()}%\n" \
			f'__**CPU Frequency**__: [{cpufreq}/{cpufreqmax}]\n'
		e.set_footer(text=f'{[round(i) for i in psutil.cpu_percent(interval=1, percpu=True)]}')
		await ctx.send(embed=e)

	@commands.command()
	async def freq(self, ctx):
		await ctx.send(bytes2human(psutil.cpu_freq()))

	@commands.command()
	async def pids(self, ctx):
		await ctx.send(psutil.pids())

	@commands.command()
	async def temp(self, ctx):
		await ctx.send(psutil.sensors_temperatures(fahrenheit=True))

	@commands.command(name='ram', aliases=['wam'])
	async def ram(self, ctx):
		await ctx.send(f'[{bytes2human(psutil.virtual_memory())}, {p.bytes2human(psutil.virtual_memory().total)}]')

	@commands.command()
	async def cpu(self, ctx):
		await ctx.send(f"{psutil.cpu_percent(interval=1)}")

def setup(bot):
	bot.add_cog(Psutil(bot))
