from random import randint, choice
from discord.ext import commands
from utils import colors
import requests
import discord
import json

class NSFW(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def get(self, filename):
		with open(f"./data/images/urls/{filename}", "r") as f:
			return choice(f.readlines())

	@commands.command(name="gel")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	@commands.is_nsfw()
	async def _gel(self, ctx, *, tag):
		blacklist = ['loli', 'shota']
		send_all = False
		if 'all ' in tag:
			if ctx.author.name == 'Luck':
				send_all = True
				tag = tag.replace('all ', '')
		tag = tag.replace(' ', '_')
		for x in blacklist:
			if x in tag:
				return await ctx.send('that tag is blacklisted')
		try:
			r = requests.get(f"https://gelbooru.com/index.php?page=dapi&s=post"
			    f"&q=index&tags={tag}&json=1&limit=100&pid={randint(1, 3)}")
			dat = json.loads(r.content)
			if send_all:
				try:
					for i in range(len(dat)):
						e = discord.Embed(color=colors.random())
						e.set_image(url=dat[i]['file_url'])
						await ctx.send(embed=e)
				except Exception as e:
					await ctx.send(e)
				return
			e = discord.Embed(color=colors.random())
			e.set_image(url=dat[randint(1, len(dat))]['file_url'])
			await ctx.send(embed=e)
		except:
			await ctx.send("error")

	@commands.command(name="trap")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	@commands.is_nsfw()
	async def _trap(self, ctx):
		e = discord.Embed(color=colors.purple())
		e.set_image(url=self.get("traps.txt"))
		await ctx.send(embed=e)

	@commands.command(name="yaoi")
	@commands.bot_has_permissions(embed_links=True)
	@commands.is_nsfw()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _yaoi(self, ctx):
		e = discord.Embed(color=colors.purple())
		e.set_image(url=self.get("yaoi.txt"))
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(NSFW(bot))
