from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json

class mainclass:
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

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_4b4t(self, ctx):
		await ctx.send('working')

	@commands.command()
	async def motdcount(self, ctx):
		await ctx.send(len(self.motds))

# ~== Main ==~

	async def motdshuffle(self):
		while True:
			try:
				f = open('/home/legit/4b4t/data/server.properties', 'w')
			except:
				await self.bot.get_channel(534608853300412416).send("Unable to find server.properties")
				break
			f.write(
				f"player-idle-timeout=0.000000\n"
				f"online-mode=true\n"
				f"server-port=19132\n"
				f"difficulty=2\n"
				f"view-distance=22\n"
				f"server-port-v6=19133\n"
				f"force-gamemode=true\n"
				f"level-name=world\n"
				f"level-dir=world\n"
				f"max-players=999\n"
				f"level-generator=1\n"
				f"motd=4B4t - {random.choice(self.motds)}\n"
				f"level-seed=4b4t\n"
				f"gamemode=0\n"
				f"edu-mode=false\n"
				f"experiment-mode=false\n"
				f"texturepack-required=true")
			f.close()
			await asyncio.sleep(1800)

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.motdshuffle())

	@commands.command()
	@commands.check(luck)
	async def cleanup(self, ctx):
		async for msg in ctx.channel.history():
			if msg.author.id == 529287770233896961:
				pass
			else:
				await msg.delete()

	@commands.command()
	async def playercount(self, ctx):
		await ctx.send(self.count)

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

def setup(bot):
	bot.add_cog(mainclass(bot))
