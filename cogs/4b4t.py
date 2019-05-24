from discord.ext import commands
from utils import checks, colors
from os.path import isfile
import discord
import asyncio
import random
import json

class Minecraft(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.motds = []
		self.old_motds = []
		if isfile("./data/4b4t/motds.json"):
			with open("./data/4b4t/motds.json", "r") as infile:
				dat = json.load(infile)
				if "motds" in dat and "old_motds" in dat:
					self.motds = dat["motds"]
					self.old_motds = dat["old_motds"]
		self.channel = self.bot.get_channel(580567603899269145)

	def save(self):
		with open("./data/4b4t/motds.json", "w") as outfile:
			json.dump({"motds": self.motds, "old_motds": self.old_motds}, outfile, ensure_ascii=False)

	async def motdshuffle(self):
		while True:
			with open("/home/legit/4b4t/data/server.properties", 'r') as f:
				get_all = f.readlines()
			with open("/home/legit/4b4t/data/server.properties", 'w') as f:
				for i, line in enumerate(get_all, 1):
					if i == 12:
						f.writelines(f"motd=4B4T - {random.choice(self.motds)}\n")
					else:
						f.writelines(line)
			await asyncio.sleep(1800)

	@commands.command(name="motdcount")
	async def motdcount(self, ctx):
		await ctx.send(len(self.motds))

	@commands.command(name='submitmotd', aliases=['motd'])
	@commands.cooldown(1, 60, commands.BucketType.user)
	@commands.guild_only()
	async def submitmotd(self, ctx, *, motd: commands.clean_content=None):
		motd = motd  # type: str
		if motd is None:
			return await ctx.send('motd is a required argument that is missing')
		if len(motd) > 35:
			return await ctx.send('too big ;-;')
		if len(motd) < 3:
			return await ctx.send('too small ;-;')
		for i in ["discord.gg", "discord,gg", ".gg", ",gg"]:
			if i in motd:
				return await ctx.send("No advertising, peasant")
		for i in self.motds:
			if str(i).lower() in motd.lower():
				return await ctx.send('That MOTD already exists')
		e = discord.Embed(description=f"`{motd}`", color=0x0000ff)
		e.set_author(name="{} | Submitted your MOTD:".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.author.avatar_url)
		await ctx.send(embed=e, delete_after=10)
		await ctx.message.delete()
		e = discord.Embed(color=ctx.author.color)
		e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = motd
		msg = await self.channel.send(embed=e)
		await msg.add_reaction('✔')
		await msg.add_reaction('❌')

	@commands.command(name="shufflemotd", aliases=["motdshuffle"])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	async def shufflemotd(self, ctx):
		guild = ctx.guild
		name = guild.name[:guild.name.find(' -')]
		motd = f"{random.choice(self.motds)}"
		await guild.edit(name=name + ' - ' + motd)
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name="{} shuffled the MOTD".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		e.description = f"New: {motd}"
		await ctx.send(embed=e, delete_after=10)
		await ctx.message.delete()
		if len(self.motds) > 1000:
			self.old_motds.append(self.motds[0])
			del self.motds[0]
			self.save()

	@commands.command(name='sendallmotds')
	@commands.check(checks.luck)
	async def sendall(self, ctx):
		for motd in self.motds:
			msg = await self.channel.send(embed=discord.Embed(description=motd))
			await msg.add_reaction('✔')
			await msg.add_reaction('❌')
		await ctx.message.delete()

	@commands.command(name='clearduplicates')
	async def clear_duplicates(self, ctx):
		motds = []
		for motd in self.motds:
			if motd not in motds:
				motds.append(motd)
		self.motds = motds
		self.save()
		await ctx.send('👍')

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member):
		if member.guild.id == 470961230362837002:
			guild = self.bot.get_guild(470961230362837002)
			motd = random.choice(self.motds)
			msg = await guild.edit(name=f"4B4T - {motd}")
			await msg.add_reaction('✔')
			await msg.add_reaction('❌')

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			if data.channel_id == self.channel.id:
				msg = await self.channel.fetch_message(data.message_id)
				motd = msg.embeds[0].description
				if str(data.emoji) == "✔":
					if all(m for m in self.motds if motd.lower() not in m.lower()):
						self.motds.append(motd)
					if len(self.motds) > 1000:
						self.old_motds.append(self.motds[0])
						del self.motds[0]
				else:
					if motd in self.motds:
						index = self.motds.index(motd)
						self.motds.pop(index)
						print('Removed: ' + motd)
				self.save()
				await msg.delete()

def setup(bot):
	bot.add_cog(Minecraft(bot))
