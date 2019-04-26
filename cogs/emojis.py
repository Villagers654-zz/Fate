from discord.ext import commands
from utils import colors
import requests
import discord
import asyncio

class Emojis(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="emoji", aliases=["emote"], description="Sends the emoji's image file")
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _emoji(self, ctx, *emoji: discord.PartialEmoji):
		for emoji in emoji:
			await asyncio.sleep(1)
			e = discord.Embed(color=colors.fate())
			e.set_author(name=emoji.name, icon_url=ctx.author.avatar_url)
			e.set_image(url=emoji.url)
			await ctx.send(embed=e)

	@commands.command(name="addemoji", aliases=["addemote"])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.has_permissions(manage_emojis=True)
	async def _addemoji(self, ctx, *, name=None):
		try:
			chars = list("abcdefghijklmnopqrstuvwxyz")
			if len(ctx.message.attachments) > 1:
				for attachment in ctx.message.attachments:
					clean = ""
					name = str(attachment.filename)
					name = name[:name.find(".")]
					for i in list(name):
						if i.lower() in chars:
							clean += i
					await ctx.guild.create_custom_emoji(name=clean, image=requests.get(attachment.url).content, reason=ctx.author.name)
					await ctx.send(f"Added `{clean}` to emotes")
			else:
				if name is None:
					for attachment in ctx.message.attachments:
						clean = ""
						name = str(attachment.filename)
						name = name[:name.find(".")]
						for i in list(name):
							if i.lower() in chars:
								clean += i
						await ctx.guild.create_custom_emoji(name=clean, image=requests.get(attachment.url).content, reason=ctx.author.name)
						await ctx.send(f"Added `{clean}` to emotes")
				else:
					for attachment in ctx.message.attachments:
						name = name[:32].replace(" ", "")
						await ctx.guild.create_custom_emoji(name=name, image=requests.get(attachment.url).content, reason=ctx.author.name)
						await ctx.send(f"Added `{name}` to emotes")
		except Exception as HTTPException:
			if "256 kb" in str(HTTPException):
				for attachment in ctx.message.attachments:
					e = discord.Embed(color=colors.fate())
					e.set_author(name=f"File cannot be larger than 256 kb", icon_url=attachment.proxy_url)
					e.set_thumbnail(url=ctx.author.avatar_url)
					e.description = f"Try using [TinyPNG](https://tinypng.com/) to reduce the size"
					return await ctx.send(embed=e)
			await ctx.send(str(HTTPException)[:2000])

	@commands.command(name="stealemoji", aliases=["stealemote", "fromemote", "fromemoji"])
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	@commands.cooldown(1, 5, commands.BucketType.guild)
	async def stealemoji(self, ctx, *emoji: discord.PartialEmoji):
		for emoji in emoji:
			uploaded = False
			index = 0
			while uploaded is False:
				index += 1
				if index > 4:
					await ctx.send(f'Skipping `{emoji.name}`')
					break
				try:
					await ctx.guild.create_custom_emoji(name=emoji.name, image=requests.get(emoji.url).content, reason=ctx.author.name)
					await ctx.send(f"Added `{emoji.name}` to emotes")
					uploaded = True
				except Exception as e:
					await ctx.send(f"Error adding `{emoji.name}`, i'll retry: {e}")
				await asyncio.sleep(index)

	@commands.command(name="delemoji", aliases=["delemote"])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.has_permissions(manage_emojis=True)
	async def _delemoji(self, ctx, *emoji: discord.Emoji):
		for emoji in emoji:
			await emoji.delete(reason=ctx.author.name)
			await ctx.send(f"Deleted emote `{emoji.name}`")

	@commands.command(name="rename_emoji")
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.has_permissions(manage_emojis=True)
	async def _rename_emoji(self, ctx, emoji: discord.Emoji, name):
		clean_name = ""
		old_name = emoji.name
		for i in list(name):
			if i in list("abcdefghijklmnopqrstuvwxyz"):
				clean_name += i
		await emoji.edit(name=name, reason=ctx.author.name)
		await ctx.send(f"Renamed emote `{old_name}` to `{clean_name}`")

def setup(bot):
	bot.add_cog(Emojis(bot))
