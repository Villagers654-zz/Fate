from utils import bytes2human as p
from discord.ext import commands
from datetime import datetime
import discord
import asyncio
import psutil
import json
import os

config = {'channel_id': 510410941809033216, 'message': None}

class Stats(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def get_xp_data(self):
		with open("./data/userdata/xp.json", "r") as f:
			return json.load(f)

	def monthly_global_data(self):
		return self.get_xp_data()["monthly_global"]

	def monthly_guilds_data(self):
		return self.get_xp_data()["monthly_guilded"]

	async def stats_task(self):
		while True:
			try:
				channel = self.bot.get_channel(config['channel_id'])
				if not isinstance(channel, discord.TextChannel):
					print('4B4T Stats: channel not found'); break
				guild = channel.guild
				guild_id = str(guild.id)
				e = discord.Embed(title="", color=0x4A0E50)
				e.description = "💎 Official 4B4T Server 💎"
				xp = {}
				for user_id in list(self.monthly_guilds_data()[guild_id]):
					xp[user_id] = len(self.monthly_guilds_data()[guild_id][user_id])
				leaderboard = ""
				rank = 1
				for user_id, xp in (sorted(xp.items(), key=lambda kv: kv[1], reverse=True))[:15]:
					name = "INVALID-USER"
					user = guild.get_member(int(user_id))
					if isinstance(user, discord.Member):
						name = user.display_name
					leaderboard += f'**#{rank}.** `{name}`: {xp}\n'
					rank += 1
				f = psutil.Process(os.getpid())
				try: cpufreqcurrent = p.bytes2human(psutil.cpu_freq().current)
				except: cpufreqcurrent = "unavailable"
				try: cpufreqmax = p.bytes2human(psutil.cpu_freq().max)
				except: cpufreqmax = "unavailable"
				e.set_thumbnail(url=channel.guild.icon_url)
				e.set_author(name=f'~~~====🥂🍸🍷Stats🍷🍸🥂====~~~')
				e.add_field(name="◈ Discord ◈", value=f'__**Owner**__: {channel.guild.owner}\n__**Members**__: {channel.guild.member_count}', inline=False)
				e.add_field(name="Leaderboard", value=leaderboard, inline=False)
				e.add_field(name="◈ Memory ◈", value=
					f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
					f"__**RAM**__: **Global**: {p.bytes2human(psutil.virtual_memory().used)} **Bot**: {p.bytes2human(f.memory_full_info().rss)}\n"
					f"__**CPU**__: **Global**: {psutil.cpu_percent()}% **Bot**: {f.cpu_percent()}%\n"
					f"__**CPU Per Core**__: {[round(i) for i in psutil.cpu_percent(percpu=True)]}\n"
					f"__**CPU Frequency**__: [{cpufreqcurrent}/{cpufreqmax}]")
				fmt = "%m-%d-%Y %I:%M%p"
				time = datetime.now()
				time = time.strftime(fmt)
				e.set_footer(text=f'Last Updated: {time}')
				if not config['message']:
					async for msg in channel.history(limit=5):
						if msg.author.id == self.bot.user.id:
							config['message'] = msg; break
						await msg.delete()
					config['message'] = await channel.send(embed=discord.Embed())
				msg = config['message']
				await msg.edit(embed=e)
			except AttributeError:
				print(AttributeError)
			await asyncio.sleep(1500)

	@commands.Cog.listener()
	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.stats_task())

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.channel.id == config['channel_id']:
			if msg.author.id != self.bot.user.id:
				await asyncio.sleep(60)
				await msg.delete()

def setup(bot):
	bot.add_cog(Stats(bot))
