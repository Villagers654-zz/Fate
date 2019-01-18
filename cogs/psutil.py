from data.utils import converter as c
from discord.ext import commands
import discord
import psutil
import os

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def devstats(self, ctx):
		p = psutil.Process(os.getpid())
		luck = self.bot.get_user(264838866480005122)
		ramused = psutil.virtual_memory().used
		ramtotal = psutil.virtual_memory().total
		rampercent = psutil.virtual_memory().percent
		try:
			cpufreqcurrent = c.bytes2human(psutil.cpu_freq().current)
		except:
			cpufreqcurrent = "unavailable"
		try:
			cpufreqmax = c.bytes2human(psutil.cpu_freq().max)
		except:
			cpufreqmax = "unavailable"
		storageused = psutil.disk_usage('/').used
		storagetotal = psutil.disk_usage('/').total
		try:
			batterypercent = psutil.sensors_battery().percent
		except:
			batterypercent = "unavailable"
		try:
			if psutil.sensors_battery().power_plugged:
				ischarging= "charging"
		except:
			ischarging = " "
		e = discord.Embed()
		e.set_author(name='| Memory | ', icon_url=luck.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
		e.description = f'__**Storage**__: [{c.bytes2human(storageused)}/{c.bytes2human(storagetotal)}]\n' \
			f'__**RAM**__: [{c.bytes2human(ramused)}/{c.bytes2human(ramtotal)}] ({rampercent}%)\n' \
			f'__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%\n' \
			f'__**CPU Frequency**__: [{cpufreqcurrent}/{cpufreqmax}]\n' \
			f'__**battery**__: {batterypercent}% {ischarging}'
		e.set_footer(text=f'{psutil.cpu_percent(interval=1, percpu=True)}')
		await ctx.send(embed=e)

	@commands.command()
	async def freq(self, ctx):
		await ctx.send(psutil.cpu_freq())

	@commands.command()
	async def pids(self, ctx):
		await ctx.send(psutil.pids())

	@commands.command()
	async def temp(self, ctx):
		await ctx.send(psutil.sensors_temperatures())

	@commands.command()
	async def net(self, ctx):
		await ctx.send(psutil.net_if_stats())

	@commands.command(name='ram', aliases=['wam'])
	async def ram(self, ctx):
		ramused = psutil.virtual_memory().used
		ramtotal = psutil.virtual_memory().total
		await ctx.send(f'[{c.bytes2human(ramused)}, {c.bytes2human(ramtotal)}]')

	@commands.command()
	async def cpu(self, ctx):
		await ctx.send(f"{psutil.cpu_percent(interval=1)}")

def setup(bot):
	bot.add_cog(Owner(bot))
