from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json

class Minecraft:
	def __init__(self, bot):
		self.bot = bot
		self.motds = []
		if isfile("./data/4b4t/motds.json"):
			with open("./data/4b4t/motds.json", "r") as infile:
				dat = json.load(infile)
				if "motds" in dat:
					self.motds = dat["motds"]

	def fourbeefourtee(ctx):
		return ctx.author.id in [264838866480005122, 264838866480005122]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def tothy(ctx):
		return ctx.message.author.id == 355026215137968129

	def puffy(ctx):
		return ctx.message.author.id == 257560165488918529

	@commands.command()
	async def motdcount(self, ctx):
		await ctx.send(len(self.motds))

	@commands.command()
	@commands.check(luck)
	async def cleanup(self, ctx):
		async for msg in ctx.channel.history():
			if msg.author.id == 529287770233896961:
				pass
			else:
				await msg.delete()

	@commands.command(aliases=["pc"])
	async def playercount(self, ctx):
		await ctx.send(self.bot.get_guild(470961230362837002).get_member(529287770233896961).game)

	@commands.command(name='submitmotd', aliases=['motd'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def submitmotd(self, ctx, *, motd=None):
		if motd is None:
			await ctx.send('motd is a required argument that is missing')
		else:
			if len(motd) > 35:
				await ctx.send('too big ;-;')
			else:
				if len(motd) > 3:
					check = 0
					for i in self.motds:
						if motd.lower() in i.lower():
							check += 1
					if check >= 1:
						await ctx.send('That MOTD already exists')
					else:
						self.motds.append(motd)
						e = discord.Embed(description=f"`{motd}`", color=0x0000ff)
						e.set_author(name="{} | Submitted your MOTD:".format(ctx.author.name), icon_url=ctx.author.avatar_url)
						e.set_thumbnail(url=ctx.author.avatar_url)
						await ctx.send(embed=e, delete_after=10)
						await ctx.message.delete()
						with open("./data/4b4t/motds.json", "w") as outfile:
							json.dump({"motds": self.motds}, outfile, ensure_ascii=False)
				else:
					await ctx.send('too small ;-;')

	@commands.command(name="shufflemotd", aliases=["motdshuffle"])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def shufflemotd(self, ctx):
		guild = self.bot.get_guild(470961230362837002)
		motd = f"{random.choice(self.motds)}"
		await guild.edit(name=f"4B4T - {motd}")
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name="{} shuffled the MOTD".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		e.description = f"New: {motd}"
		await ctx.send(embed=e, delete_after=10)
		await ctx.message.delete()

	async def motdshuffle(self):
		while True:
			with open("/home/legit/4b4t/data/server.properties", 'r') as f:
				get_all = f.readlines()
			with open("your_file.txt", 'w') as f:
				for i, line in enumerate(get_all, 1):
					if i == 12:
						f.writelines(f"motd=4B4T - {random.choice(self.motds)}")
					else:
						f.writelines(line)
			await asyncio.sleep(1800)

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.motdshuffle())

def setup(bot):
	bot.add_cog(Minecraft(bot))
