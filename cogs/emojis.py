from discord.ext import commands
from utils import colors
import requests
import discord

class Emojis:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="addemoji", aliases=["emote", "addemote"])
	@commands.has_permissions(manage_emojis=True)
	async def _addemoji(self, ctx, *, name=None):
		try:
			chars = list("abcdefghijklmnopqrstuvwxyz")
			if len(ctx.message.attachments) > 1:
				for attachment in ctx.message.attachments:
					clean = ""
					for i in list(attachment.name):
						if i in chars:
							clean += i
					name = attachment[:str(attachment.filename).lower().find(".")].replace(" ", "")[:32]
					await ctx.guild.create_custom_emoji(name=clean, image=requests.get(attachment.url).content, reason=ctx.author.name)
					await ctx.send(f"successfully added `{name}` to emotes")
			else:
				if name is None:
					for attachment in ctx.message.attachments:
						clean = ""
						for i in list(attachment.name):
							if i in chars:
								clean += i
						name = attachment[:str(attachment.filename).lower().find(".")].replace(" ", "")[:32]
						await ctx.guild.create_custom_emoji(name=clean, image=requests.get(attachment.url).content, reason=ctx.author.name)
						await ctx.send(f"Successfully added `{name}` to emotes")
				else:
					for attachment in ctx.message.attachments:
						name = name[:32].replace(" ", "")
						await ctx.guild.create_custom_emoji(name=name, image=requests.get(attachment.url).content, reason=ctx.author.name)
						await ctx.send(f"Successfully added `{name}` to emotes")
		except Exception as HTTPException:
			if "256kb" in HTTPException:
				for attachment in ctx.message.attachments:
					attachment = attachment
				e = discord.Embed(color=colors.fate())
				e.set_author(name=f"File cannot be larger than 256 kb", icon_url=attachment.proxy_url)
				e.set_thumbnail(url=ctx.author.avatar_url)
				e.description = f"Try using [TinyPNG](https://tinypng.com/) to reduce the size"
				return await ctx.send(embed=e)
			await ctx.send(HTTPException[:2000])

	@commands.command(name="delemoji", aliases=["delemote"])
	@commands.has_permissions(manage_emojis=True)
	async def _delemoji(self, ctx, *, name):
		check = 0
		for emote in ctx.guild.emojis:
			if name.lower() == emote.name.lower():
				await emote.delete(reason=ctx.author.name)
				await ctx.send(f"Deleted emote `{emote.name}`")
				check = 1
				break
		if check == 0:
			for emote in ctx.guild.emojis:
				if name.lower() in emote.name.lower():
					await emote.delete(reason=ctx.author.name)
					await ctx.send(f"Deleted emote `{emote.name}`")
					check = 1
					break
		if check == 0:
			await ctx.send("I couldnt find that emote")

def setup(bot):
	bot.add_cog(Emojis(bot))
