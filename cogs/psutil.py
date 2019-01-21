from data.utils import psutil as p
from discord.ext import commands
import discord

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def devstats(self, ctx):
		luck = self.bot.get_user(264838866480005122)
		e = discord.Embed()
		e.set_author(name='| Memory | ', icon_url=luck.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
		e.description = f'__**Storage**__: [{p.bytes2human(p.storageused)}/{p.bytes2human(p.storagetotal)}]\n' \
			f'__**RAM**__: [{p.bytes2human(p.ramused)}/{p.bytes2human(p.ramtotal)}] ({p.rampercent}%)\n' \
			f'__**CPU**__: **Global**: {p.cpu}% **Bot**: {p.botcpu}%\n' \
			f'__**CPU Frequency**__: [{p.freq}/{p.freqmax}]\n' \
			f'__**battery**__: {p.batterypercent}% {p.ischarging}'
		e.set_footer(text=f'{p.percpu}')
		await ctx.send(embed=e)

	@commands.command()
	async def freq(self, ctx):
		await ctx.send(p.freq)

	@commands.command()
	async def pids(self, ctx):
		await ctx.send(p.pids)

	@commands.command()
	async def temp(self, ctx):
		await ctx.send(p.temp)

	@commands.command()
	async def net(self, ctx):
		await ctx.send(p.net)

	@commands.command(name='ram', aliases=['wam'])
	async def ram(self, ctx):
		await ctx.send(f'[{p.ramused}, {p.bytes2human(p.ramtotal)}]')

	@commands.command()
	async def cpu(self, ctx):
		await ctx.send(f"{p.cpu}")

def setup(bot):
	bot.add_cog(Owner(bot))
