"""
Module for viewing and managing emojis
"""

import requests
import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import Greedy
from PIL import Image

from utils import colors


class Emojis(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def is_blacklisted(self, emoji) -> bool:
		servers = [470961230362837002, 397415086295089155, 650950654491361280]
		blacklist = []
		for server_id in servers:
			server = self.bot.get_guild(server_id)
			for emote in server.emojis:
				blacklist.append(emote.id)
		if isinstance(emoji, discord.PartialEmoji):
			return emoji.id in blacklist
		elif isinstance(emoji, str):
			return any(str(emoji_id) in emoji for emoji_id in blacklist)

	def cleanup_text(self, text: str):
		"""cleans text to avoid errors when creating emotes"""
		if isinstance(text, list):
			text = ' '.join(text)
		if '.' in text:
			text = text[:text.find('.') + 1]
		chars = 'abcdefghijklmnopqrstuvwxyz'
		result = ''
		for char in list(text):
			if char.lower() in chars:
				result += char
		return result if result else 'new_emoji'

	async def upload_emoji(self, ctx, name, img, reason, roles=None, msg=None):
		"""Creates partial emojis with a queue to prevent spammy messages"""
		try:
			emoji = await ctx.guild.create_custom_emoji(name=name, image=img, roles=roles, reason=reason)
		except discord.errors.Forbidden as e:
			if msg:
				await msg.edit(content=f'{msg.content}\nFailed to add {name}: [`{e}`]')
			else:
				await ctx.send(f'Failed to add {name}: [`{e}`]')
		except discord.errors.HTTPException as e:
			await ctx.send(e)
			try:
				img = Image.open(img); img = img.resize((450, 450), Image.BICUBIC)
			except:
				if msg:
					return await msg.edit(content=f'{msg.content}\nFailed to resize {name}')
				else:
					return await ctx.send(f'Failed to resize {name}')
			img.save('emoji.png')
			with open('emoji.png', 'rb') as image:
				img = image.read()
			await ctx.guild.create_custom_emoji(name=name, image=img, roles=roles, reason=reason)
			await msg.edit(content=f'{msg.content}\nAdded {name} successfully')
		except AttributeError as e:
			if msg:
				await msg.edit(content=f'{msg.content}\nFailed to add {name}: [`{e}`]')
			else:
				await ctx.send(f'Failed to add {name}: [`{e}`]')
		else:
			if msg: await msg.edit(content=f'{msg.content}\nAdded {emoji} - {name}')
			else: await ctx.send(f'Added {emoji} - {name}')

	@commands.command(name="emoji", aliases=["emote"])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True)
	async def _emoji(self, ctx, *emoji: discord.PartialEmoji):
		"""Sends the emoji in image form"""
		for emoji in emoji:
			e = discord.Embed(color=colors.fate())
			e.set_author(name=emoji.name, icon_url=ctx.author.avatar_url)
			e.set_image(url=emoji.url)
			await ctx.send(embed=e)
			await asyncio.sleep(1)

	@commands.command(name='add-emoji', aliases=['add-emote'])
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	async def _add_emoji(
			self, ctx, custom: Greedy[discord.PartialEmoji],
			ids: Greedy[int], *args
	):
		""" Uploads Emojis Via Various Methods """
		msg = await ctx.send(f'Uploading emoji(s)..')

		for emoji in custom:
			if self.is_blacklisted(emoji):
				await msg.edit(content=f"{msg.content}\nERR: {emoji.name} - Invalid Emoji")
				continue
			name = emoji.name; img = requests.get(emoji.url).content
			await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author), msg=msg)

		for emoji_id in ids:
			emoji = self.bot.get_emoji(emoji_id)
			if not emoji:
				await msg.edit(content=f"{msg.content}\n{emoji_id} - Couldn't Fetch")
				continue
			img = requests.get(emoji.url).content
			await self.upload_emoji(ctx, name=str(emoji_id), img=img, reason=str(ctx.author), msg=msg)

		def check(iter):
			if iter+1 > len(args):
				return '.'
			return args[iter+1]
		mappings = {
			requests.get(arg).content: check(iter) if '.' not in check(iter) else 'new_emoji'
				for iter, arg in enumerate(args) if '.' in arg
		}
		for img, name in mappings.items():
			await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author), msg=msg)

	@commands.command(name='addemoji', aliases=['addemote'])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.guild_only()
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	async def add_emoji(self, ctx, *, args='new_emoji'):
		"""Creates partial emojis from attached files/urls"""
		args = args.split(' '); image_urls = None; roles = []
		if 'https://' in args[0]:
			image_urls = args[0]
			args.pop(0); args = ['new_emoji'] if not args else args
		if ctx.message.attachments:
			image_urls = [(file.filename, file.url) for file in ctx.message.attachments]
		if len(args) > 1: args = ' '.join(args)
		else: args = args[0]
		if not image_urls:
			return await ctx.send('You need to attach a file or provide a url')
		msg = await ctx.send('Uploading emoji(s)..')
		if not isinstance(image_urls, list):
			if self.is_blacklisted(image_urls):
				return await ctx.send('ERR: Invalid Emoji')
			name = self.cleanup_text(args); img = requests.get(image_urls).content
			await self.upload_emoji(ctx, name, img, str(ctx.author), roles, msg)
		else:
			for filename, url in image_urls:
				if self.is_blacklisted(url):
					await msg.edit(content=f"{msg.content}\nERR: {filename} - Invalid Emoji")
				name = self.cleanup_text(args if args else filename); img = requests.get(url).content
				await self.upload_emoji(ctx, name, img, str(ctx.author), roles, msg)
				await asyncio.sleep(1)

	@commands.command(name="stealemoji", aliases=["stealemote", "fromemote", "fromemoji"])
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	@commands.cooldown(1, 5, commands.BucketType.guild)
	async def stealemoji(self, ctx, *emoji: discord.PartialEmoji):
		msg = await ctx.send(f'Uploading emoji(s)..')
		for emoji in emoji:
			if self.is_blacklisted(emoji):
				await msg.edit(content=f"{msg.content}\nERR: {emoji.name} - Invalid Emoji")
				continue
			name = emoji.name; img = requests.get(emoji.url).content
			await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author), msg=msg)
			if len(msg.content) > 1900:
				msg = await ctx.send('Uploading emoji(s)..')

	@commands.command(name="delemoji", aliases=["delemote"])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.has_permissions(manage_emojis=True)
	async def _delemoji(self, ctx, *emoji: discord.Emoji):
		for emoji in emoji:
			await emoji.delete(reason=ctx.author.name)
			await ctx.send(f"Deleted emote `{emoji.name}`")

	@commands.command(name="rename-emoji")
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
