from os.path import isfile
import json
from datetime import datetime, timedelta
import asyncio
import requests
from discord.ext import commands
import discord
from utils import colors, utils


class IconShuffle(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dat = {}
		self.dir = './data/userdata/icon_shuffle.json'
		if isfile(self.dir):
			with open(self.dir, 'r') as f:
				self.dat = json.load(f)

	def save_data(self):
		with open(self.dir, 'w+') as f:
			json.dump(self.dat, f)

	def init(self, guild_id):
		""" Initial Setup - Prevents Key-Errors """
		if guild_id not in self.dat:
			self.dat[guild_id] = {
				'toggle': False,
				'shuffling': False,
				'interval': utils.get_seconds(hours=2),
				'start': None,
				'icons': []
			}

	async def shuffle_server_icon(self, guild_id):
		""" Shuffles a guilds icon every x seconds """
		while True:
			if not self.dat[guild_id]['toggle']:
				return
			self.dat[guild_id]['shuffling'] = True
			guild = self.bot.get_guild(int(guild_id))
			if not guild:  # bot left or was removed
				del self.dat[guild_id]
				self.dat[guild_id]['shuffling'] = False
				return self.save_data()
			print(f'Starting {__name__} for {guild.name}')
			interval = self.dat[guild_id]['interval']  # type: int
			icons = self.dat[guild_id]['icons']  # type: list
			start = self.dat[guild_id]['start']
			if not start: start = datetime.now()
			else: start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
			expiration = (datetime.now() - (start + timedelta(days=7))).days
			if expiration >= 0:  # 7 days expired and needs renewal
				print(f'Terminating icon shuffle for {guild.name}')
				del self.dat[guild_id]
				return self.save_data()
			for x in range(len(icons)):
				if not self.dat[guild_id]['toggle']:
					print(f'Terminating icon shuffle for {guild.name}')
					self.dat[guild_id]['shuffling'] = False
					return
				icon = requests.get(icons[x]).content
				await guild.edit(icon=icon)
				await asyncio.sleep(interval)
			await asyncio.sleep(5)

	@commands.group(name='iconshuffle')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _icon_shuffle(self, ctx):
		""" Returns a help menu if no arguments were passed """
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Server Icon Shuffle', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = 'Changes the server icon every x seconds, requires weekly renewal to prevent api abuse'
			usage = '• .iconshuffle toggle\nEnables/disables the module\n' \
			    '• .iconshuffle setintevval timer\nTimer: 1d for 1 day, 1h for one hour\n' \
			    '• .iconshuffle add {file|url}\nAdds an img to the list of icons to shuffle through. ' \
			    'Warning: the previous icons must finish their cycle before the list updates'
			e.add_field(name='◈ Usage ◈', value=usage)
			await ctx.send(embed=e)

	@_icon_shuffle.command(name='toggle')
	@commands.has_permissions(manage_guild=True)
	async def _toggle(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.dat:
			self.init(guild_id)
			self.dat[guild_id]['toggle'] = True
			self.bot.loop.create_task(self.shuffle_server_icon(guild_id))
		else:
			if self.dat[guild_id]['toggle']:
				self.dat[guild_id]['toggle'] = False
			else:
				self.dat[guild_id]['toggle'] = True
				if not self.dat[guild_id]['shuffling']:
					self.bot.loop.create_task(self.shuffle_server_icon(guild_id))
		if self.dat[guild_id]['toggle']:
			await ctx.send('Enabled Icon Shuffle')
		else:
			await ctx.send('Disabled Icon Shuffle')
		self.save_data()

	@_icon_shuffle.command(name='setinterval')
	@commands.has_permissions(manage_guild=True)
	async def _set_interval(self, ctx, time):
		guild_id = str(ctx.guild.id)
		self.init(guild_id); interval = None
		if time.isdigit() and 'Luck' in ctx.author.name:
			self.dat[guild_id]['interval'] = int(time)
			await ctx.send(f'Set the interval for {time} seconds')
			return self.save_data()
		if "d" in time:
			interval = int(time.replace("d", "")) * 60 * 60 * 24
		if "h" in time:
			interval = int(time.replace("h", "")) * 60 * 60
		if not isinstance(interval, int):
			return await ctx.send('Invalid timer')
		time = time.replace("h", " hours").replace("1 hours", "1 hour")
		time = time.replace("d", " days").replace("1 days", "1 day")
		self.dat[guild_id]['interval'] = interval
		await ctx.send(f'Set the interval for {time}')
		self.save_data()

	@_icon_shuffle.command(name='setimgs')
	@commands.has_permissions(manage_guild=True)
	async def _set_imgs(self, ctx, *links):
		if not links and not ctx.message.attachments:
			return await ctx.send('Attach a file or provide a link when using this cmd')
		guild_id = str(ctx.guild.id); self.init(guild_id)
		attachments = links if len(links) > 0 else [f.url for f in ctx.message.attachments]
		self.dat[guild_id]['icons'] = attachments
		await ctx.send(f'Added {len(attachments)} icons')
		self.save_data()

	@commands.Cog.listener()
	async def on_ready(self):
		for guild_id in self.dat:
			self.dat[guild_id]['shuffling'] = False
			if self.dat[guild_id]['toggle']:
				self.bot.loop.create_task(self.shuffle_server_icon(guild_id))

def setup(bot):
	bot.add_cog(IconShuffle(bot))
