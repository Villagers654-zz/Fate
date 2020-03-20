from utils import checks, colors, ssh, config
from discord.ext import commands
from zipfile import ZipFile
from time import monotonic
import subprocess
import discord
import asyncio
import os

class Backup(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.backup = False

	def get_all_file_paths(self, directory):
		file_paths = []
		for root, directories, files in os.walk(directory):
			for filename in files:
				filepath = os.path.join(root, filename)
				file_paths.append(filepath)
		return file_paths

	@commands.command(name="backup")
	@commands.check(checks.luck)
	async def _backup(self, ctx):
		if self.backup is True:
			return await ctx.send("Backup was already in progress")
		async with ctx.typing():
			self.backup = True
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Backing up files..", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
			e.description = "**Progress:** `0%`\nChecking for previous backup"
			msg = await ctx.send(embed=e)
			if os.path.isfile('Backup.zip'):
				e.description = "**Progress:** `25%`\nRemoving previous backup"
				await msg.edit(embed=e)
				os.remove('Backup.zip')
			e.description = '**Indexing files:** `50%`'
			await msg.edit(embed=e)
			file_paths = self.get_all_file_paths(os.getcwd())
			e.description = "**Progress:** `75%`\nCompressing files"
			await msg.edit(embed=e)
			before = monotonic()
			with ZipFile('Backup.zip', 'w') as zip:
				for file in file_paths:
					zip.write(file)
			ping = str(round((monotonic() - before) * 1000)) + 'ms'
			e.description = f'**Backup Complete:** `{ping}`'
			await msg.edit(embed=e)
			self.backup = False

	async def backup_task(self):
		while True:
			await asyncio.sleep(129600)
			before = monotonic()
			if os.path.isfile('Backup.zip'):
				os.remove('Backup.zip')
			file_paths = self.get_all_file_paths(os.getcwd())
			with ZipFile('Backup.zip', 'w') as zip:
				for file in file_paths:
					zip.write(file)
			ping = round((monotonic() - before) * 1000)
			await self.bot.get_channel(config.server("log")).send(f'Ran Scheduled Backup: {ping}ms')

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.backup_task())

def setup(bot):
	bot.add_cog(Backup(bot))
