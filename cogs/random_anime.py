from os.path import isfile
import json
import asyncio
import random
import requests
from discord.ext import commands
import discord
from utils import colors


class RandomAnime(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = {}
		self.path = './data/userdata/random_anime.json'
		if isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)

	def save_data(self):
		with open(self.path, 'w') as f:
			json.dump(self.config, f, ensure_ascii=False)

	async def start_random_image_task(self, guild_id: str):
		"""Starts the task that sends a random img at the configured interval"""
		while True:
			if self.config[guild_id]['toggle'] == 'enabled':
				channel = self.bot.get_channel(self.config[guild_id]['channel'])
				if not isinstance(channel, discord.TextChannel):
					del self.config[guild_id]
					return self.save_data()
				anime = random.choice(self.config[guild_id]['anime'])
				interval = self.config[guild_id]['interval']
				apikey = "LIWIXISVM3A7"
				lmt = 50
				r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
				if r.status_code == 200:
					anon_id = json.loads(r.content)["anon_id"]
				else:
					anon_id = ""
				r = requests.get("https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s" % (anime, apikey, lmt, anon_id))
				if r.status_code == 200:
					try:
						dat = json.loads(r.content)
						e = discord.Embed(color=colors.random())
						e.set_image(url=dat['results'][random.randint(0, len(dat['results']) - 1)]['media'][0]['gif']['url'])
						await channel.send(embed=e)
					except Exception as e:
						await channel.send(e)
				await asyncio.sleep(interval)

	@commands.command(name='randomanime', aliases=['random-anime'])
	@commands.has_permissions(manage_channels=True)
	@commands.bot_has_permissions(embed_links=True)
	async def random_anime(self, ctx, *, anime=None):
		if not anime:
			return
		guild_id = str(ctx.guild.id)
		if guild_id not in self.config:
			self.config[guild_id] = {'toggle': 'disabled', 'anime': [], 'interval': 3600, 'channel': ctx.channel.id}
		if ctx.message.channel_mentions:
			channel = ctx.message.channel_mentions[0]
			self.config[guild_id]['channel'] = channel.id
			await ctx.send('Set the channel')
			return self.save_data()
		if 'setinterval' in ctx.message.content:
			interval = int([arg for arg in anime.split(' ') if arg.isdigit()][0])
			self.config[guild_id]['interval'] = interval
			await ctx.send('Set the interval')
			return self.save_data()
		if 'reset' in anime:
			self.config[guild_id]['anime'] = []
			await ctx.send('Reset 👍')
			return self.save_data()
		if 'enable' in ctx.message.content:
			self.config[guild_id]['toggle'] = 'enabled'
			self.bot.loop.create_task(self.start_random_image_task(guild_id))
			await ctx.send('Enabled random anime')
			return self.save_data()
		if 'disable' in anime:
			self.config[guild_id]['toggle'] = 'disabled'
			return self.save_data()
		self.config[guild_id]['anime'].append(anime)
		await ctx.send(f'Added {anime}')
		self.save_data()

	@commands.Cog.listener()
	async def on_ready(self):
		for guild_id in self.config.keys():
			self.bot.loop.create_task(self.start_random_image_task(guild_id))

def setup(bot):
	bot.add_cog(RandomAnime(bot))
