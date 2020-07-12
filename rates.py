from time import time, monotonic
import asyncio
import traceback
import sys
from discord.ext import commands
import discord
import logging


def check_if_user_has_access():
	async def predicate(ctx):
		if ctx.author.id in [264838866480005122, 79305800157233152, 611108193275478018]:
			return True
		return await ctx.send("You don't have permission to use " + str(ctx.command))

	return commands.check(predicate)


class Rates(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.msgs = []
		self.index = {}
		self.rate_limited = []
		bot.loop.create_task(self.monit_task())

	# async def update_embed_task(self):
	# 	log_channel = await self.bot.fetch_channel(668472416917258270)
	# 	msg = await log_channel.fetch_message('set the message id here')             # take look at this line
	# 	if not msg.embeds:
	# 		e = discord.Embed()
	# 		await msg.edit(embed=e)
	# 		del e
	# 	while True:
	# 		await asyncio.sleep(5)
	# 		e = discord.Embed(color=0x39ff14)
	# 		e.description = '\n'.join(self.rate_limited)
	# 		await msg.edit(embed=e)

	async def monit_task(self):
		while True:
			await asyncio.sleep(1)
			if any(len(msgs) >= 5 for channel, msgs in self.index.items()):
				channels = [channel for channel, msgs in self.index.items() if len(msgs) >= 5]
				e = discord.Embed()
				e.description = ''
				fields = []
				for channel in channels:
					field = f'{channel.mention} in {channel.guild}'
					if field not in self.rate_limited:
						self.rate_limited.append(field)
						fields.append(field)
				await asyncio.sleep(5)
				for field in fields:
					self.rate_limited.remove(field)

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.bot:
			return
		self.msgs.append([msg, time()])
		self.msgs = self.msgs[-5000:]
		if msg.channel not in self.index:
			self.index[msg.channel] = []
		current_time = time()
		self.index[msg.channel].append(current_time)
		await asyncio.sleep(5)
		self.index[msg.channel].remove(current_time)
		if len(self.index[msg.channel]) == 0:
			del self.index[msg.channel]

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if hasattr(ctx.command, 'on_error'):
			return
		ignored = (commands.CommandNotFound, commands.NoPrivateMessage, discord.errors.NotFound)
		error = getattr(error, 'original', error)
		if isinstance(error, ignored):
			return
		elif isinstance(error, commands.DisabledCommand):
			await ctx.send(str(ctx.command) + ' has been disabled.')
		elif isinstance(error, commands.CheckFailure):
			await ctx.message.add_reaction('⚠')
		elif isinstance(error, discord.errors.Forbidden):
			print("I'm missing perms to reply in " + str(ctx.channel.mention))
		else:
			print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await ctx.send(error)

	@commands.command(name='rates')
	@check_if_user_has_access()
	async def rates(self, ctx, timeframe: int = 60):
		e = discord.Embed(color=0x39ff14)
		lists = [
			len([
				msg for msg, msg_time in self.msgs if msg_time < time() - timeframe * i and (
						msg_time > time() - timeframe * (i + 1)
				) or (i + 1 == 1 and msg_time > time() - timeframe)
			]) for i in range(3)
		]
		e.description = "{0} msgs within last {1}s\n{2} average msgs per {3}s".format(round(lists[0]), timeframe,
		                                                                              round(sum(lists) / len(lists)),
		                                                                              timeframe)
		await ctx.send(embed=e)

	@commands.command(name='c-rates')
	@check_if_user_has_access()
	async def channel_rates(self, ctx):
		e = discord.Embed(color=0x39ff14)
		e.description = ''
		for channel, msgs in self.index.items():
			e.description += '\n• `{0}` - {1}/5 msgs per second'.format(channel.guild.name, len(msgs))
			# if len(msgs) == 5:
			# 	e.set_footer(text="Seems I've hit a rate limit..")
		e.description = e.description[:1000]
		await ctx.send(embed=e)

	@commands.command(name='ping')
	async def ping(self, ctx):
		before = monotonic()
		msg = await ctx.send("Measuring ping")
		ping = round((monotonic() - before) * 1000)
		await msg.edit(content=f"Message Trip: {ping}ms"
		                       f"\nHeartbeat: {round(bot.latency * 1000)}ms")


logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='f.!', case_insensitive=True, max_messages=100)  # 100 cuz no need to keep em
bot.add_cog(Rates(bot))
bot.remove_command('help')
token = "NTA2NzM1MTExNTQzMTkzNjAx.XvYsHQ.FUGTOxyFOJO82-IexbOl6Yutmdo"


@bot.event
async def on_ready():
	print('Internal cache is ready\nIve got websocket heartbeat of')
	print(str(round(bot.latency * 1000)) + 'ms')
	cog = bot.get_cog('Rates')
	bot.loop.create_task(cog.update_embed_task())


bot.run(token)

