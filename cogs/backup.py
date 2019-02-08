from utils import checks, colors
from discord.ext import commands
import subprocess
import discord
import os

class Backup:
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
			e.set_thumbnail(
				url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
			e.description = "**Progress:** `0%`\nSending message"
			msg = await ctx.send(embed=e)
			p = subprocess.Popen("ls /home/luck", stdout=subprocess.PIPE, shell=True)
			(output, err) = p.communicate()
			e.description = "**Progress:** `25%`\nChecking for previous backup"
			await msg.edit(embed=e)
			if "Backup.zip" in str(output):
				os.system("rm /home/luck/Backup.zip")
				e.description = "**Progress:** `50%`\nRemoving previous backup"
				await msg.edit(embed=e)
			e.description = "**Progress:** `75%`\nCompressing files"
			await msg.edit(embed=e)
			os.system("zip -r /home/luck/Backup.zip /home/luck/FateZero")
			e.description = "**Progress:** `100%`\nBackup complete."
			await msg.edit(embed=e)
			self.backup = False

def setup(bot):
	bot.add_cog(Backup(bot))
