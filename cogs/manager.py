from discord.ext import commands
from random import random
import subprocess
import traceback
import discord
import asyncio
import os

class Defender:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def ips(ctx):
		return ctx.author.id in [264838866480005122, 355026215137968129]

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_manager(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	async def warn(self):
		while True:
			ips = ['75.107.232.117', '166.182.244', '90.240.5.35', '83.137.2']
			luck = self.bot.get_user(264838866480005122)
			legit = self.bot.get_user(261451679239634944)
			f = open('/home/luck/FateZero/data/warn.txt', 'r')
			users = [luck, legit]
			if f.read() == "empty":
				f.close()
				p = subprocess.Popen("last | head -1", stdout=subprocess.PIPE, shell=True)
				(output, err) = p.communicate()
				output = str(output)
				if "still logged in" in output:
					t = os.popen('date')
					timestamp = t.read()
					check = 0
					for i in ips:
						if i in output:
							check += 1
					if check == 0:
						e = discord.Embed(color=0xff0000)
						e.set_author(name='Login Notice', icon_url=self.bot.user.avatar_url)
						e.description = f'{timestamp}'
						e.add_field(name='Security Check', value=f'`{output}`')
						for i in users:
							await i.send(embed=e)
					f = open('/home/luck/FateZero/data/warn.txt', 'w')
					f.write("waiting")
					f.close()
			else:
				f = open('/home/luck/FateZero/data/warn.txt', 'r')
				if f.read() == "waiting":
					f.close()
					p = subprocess.Popen("last | head -1", stdout=subprocess.PIPE, shell=True)
					(output, err) = p.communicate()
					output = str(output)
					if "still logged in" in output:
						pass
					else:
						f.close()
						f = open('/home/luck/FateZero/data/warn.txt', 'w')
						t = os.popen('date')
						timestamp = t.read()
						p = subprocess.Popen("last | head -1", stdout=subprocess.PIPE, shell=True)
						(output, err) = p.communicate()
						output = str(output)
						e = discord.Embed(color=0xff0000)
						e.set_author(name='User logged out or disconnected', icon_url=self.bot.user.avatar_url)
						e.description = f'{timestamp}'
						e.add_field(name='Security Check', value=f'`{output}`')
						check = 0
						for i in ips:
							if i in output:
								check += 1
						if check == 0:
							for i in users:
								await i.send(embed=e)
						f.write("empty")
						f.close()
			await asyncio.sleep(5)

	@commands.command()
	@commands.check(luck)
	async def write(self, ctx, arg):
		f = open('/home/luck/FateZero/data/warn.txt', 'w')
		f.write(arg)
		f.close()
		await ctx.send('done')

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.warn())
		channel = self.bot.get_channel(514214974868946964)
		warning = self.bot.get_channel(502236124308307968)
		p = subprocess.Popen("last | head -1", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output)
		output = output.replace("b'", "'")
		t = os.popen('date')
		timestamp = t.read()
		h = '75.107.232.117'
		s = '166.182.244'
		if h in output:
			color = 0x39FF14
		else:
			if s in output:
				color = 0x39FF14
			else:
				color = 0xff0000
		e = discord.Embed(color=color)
		e.set_author(name='Login Notice', icon_url=self.bot.user.avatar_url)
		e.description = f'{timestamp}'
		e.add_field(name='Security Check', value=f'`{output}`')
		await channel.send(embed=e)
		h = ['75.107.232.117', '166.182.244']
		check = 0
		for i in h:
			if i in output:
				check += 1
		if check == 0:
			await self.bot.get_channel(514213558549217330).send("<@264838866480005122> someone might be tampering with my files")

def setup(bot):
	bot.add_cog(Defender(bot))
