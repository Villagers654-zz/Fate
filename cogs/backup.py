from utils import checks, colors, ssh, config
from discord.ext import commands
import subprocess
import discord
import asyncio
import os

class Backup(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.backup = False

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
			p = subprocess.Popen("ls", stdout=subprocess.PIPE, shell=True)
			(output, err) = p.communicate()
			await msg.edit(embed=e)
			if "Backup.zip" in str(output):
				e.description = "**Progress:** `25%`\nRemoving previous backup"
				await msg.edit(embed=e)
				os.system("rm Backup.zip")
			e.description = "**Progress:** `50%`\nCompressing files"
			await msg.edit(embed=e)
			os.system("zip -r Backup.zip /home/luck/FateZero")
			e.description = "**Progress:** `75%`\nTransferring Backup"
			await msg.edit(embed=e)
			ssh.upload("luck", "Backup.zip", "/home/luck/Backup.zip")
			e.description = "**Progress:** `100%`\nBackup complete."
			await msg.edit(embed=e)
			self.backup = False

	async def backup_task(self):
		while True:
			await asyncio.sleep(129600)
			p = subprocess.Popen("ls", stdout=subprocess.PIPE, shell=True)
			(output, err) = p.communicate()
			if "Backup.zip" in str(output):
				os.system("rm Backup.zip")
			os.system("zip -r Backup.zip /home/luck/FateZero")
			ssh.upload("luck", "Backup.zip", "/home/luck/Backup.zip")
			await self.bot.get_channel(config.server("log")).send("Ran scheduled backup successfully")

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.backup_task())

def setup(bot):
	bot.add_cog(Backup(bot))
