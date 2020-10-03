"""
Module for viewing and managing emojis
"""

import discord
import asyncio
from typing import Union
import traceback
import aiohttp

from discord.ext import commands
from discord.ext.commands import Greedy
from PIL import Image

from utils import colors


class Emojis(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def is_blacklisted(self, ctx, emoji) -> bool:
		if ctx.author.id in self.bot.owner_ids:
			return False
		servers = [470961230362837002, 397415086295089155]
		blacklist = []
		for server_id in servers:
			server = self.bot.get_guild(server_id)
			if isinstance(server, discord.Guild):
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

	async def upload_emoji(self, ctx, name, img, reason, roles=None) -> None:
		"""Creates partial emojis with a queue to prevent spammy messages"""
		try:
			emoji = await ctx.guild.create_custom_emoji(name=name, image=img, roles=roles, reason=reason)

		# Missing required permissions to add emojis
		except discord.errors.Forbidden:
			await ctx.bot.utils.update_msg(ctx.msg, "I'm missing manage_emoji permission(s)")
			return None

		# Not a proper image
		except discord.errors.InvalidArgument:
			await ctx.bot.utils.update_msg(ctx.msg, f"{name} - Unsupported Image Type")
			return None

		# Something went wrong uploading the emoji
		except discord.errors.HTTPException as e:
			error = str(traceback.format_exc()).lower()
			# Emoji Limit Reached
			if "maximum" in error:
				await self.bot.utils.update_msg(ctx.msg, f"{name} - Emoji Limit Reached")
			# 256KB Filesize Limit
			elif "256" in error:
				await ctx.bot.utils.update_msg(ctx.msg, f'{name} - File Too Large')
			return None

		await ctx.bot.utils.update_msg(ctx.msg, f'Added {emoji} - {name}')
		return None

	@commands.command(name="emoji", aliases=["emote", "jumbo"])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True)
	async def _emoji(self, ctx, *emoji: Union[discord.Emoji, discord.PartialEmoji]):
		"""Sends the emoji in image form"""
		for emoji in emoji[:3]:
			e = discord.Embed(color=colors.fate())
			e.description = str(emoji.id)
			author_name = emoji.name
			author_url = ctx.author.avatar_url
			if isinstance(emoji, discord.Emoji):
				perms = ctx.author.guild_permissions
				bot_perms = emoji.guild.me.guild_permissions
				if perms.manage_emojis and bot_perms.manage_emojis and emoji.guild.id == ctx.guild.id:
					emoji = await emoji.guild.fetch_emoji(emoji.id)
					author_name += f" by {emoji.user}"
					e.description = f"ID: {emoji.id}"
					author_url = emoji.user.avatar_url
				e.set_footer(text=emoji.guild.name, icon_url=emoji.guild.icon_url)
			e.set_author(name=author_name, icon_url=author_url)
			e.set_image(url=emoji.url)
			await ctx.send(embed=e)
			await asyncio.sleep(1)

	@commands.command(name="emojis")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_emojis=True)
	async def emojis(self, ctx):
		e = discord.Embed(color=colors.orange())
		e.set_author(name="Emoji Count", icon_url=ctx.guild.icon_url)
		emojis = [e for e in ctx.guild.emojis if not e.animated]
		a_emojis = [e for e in ctx.guild.emojis if e.animated]
		max = ctx.guild.emoji_limit
		e.description = f"🆓 | {len(emojis)}/{max} Normal emotes" \
		                f"\n💵 | {len(a_emojis)}/{max} Animated emotes"
		restricted = [e for e in ctx.guild.emojis if e.roles]
		if restricted:
			e.description += f"\n🛑 | {len(restricted)} Restricted emotes"
			index = {}
			for emoji in restricted:
				for role in emoji.roles:
					if role not in index:
						index[role] = []
					index[role].append(emoji)
			for role, emojis in index.items():
				e.add_field(name=f"◈ @{role}", value=" ".join(list(set(emojis))), inline=False)
		await ctx.send(embed=e)

	@commands.command(name='add-emoji', aliases=['add-emote', 'addemoji', 'addemote', 'stealemoji', 'stealemote'])
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	async def _add_emoji(
			self, ctx, custom: Greedy[discord.PartialEmoji],
			ids: Greedy[int], *args
	):
		""" Uploads Emojis Via Various Methods """
		ctx.message = await ctx.channel.fetch_message(ctx.message.id)  # fix content being lowercase
		limit = ctx.guild.emoji_limit

		def at_emoji_limit() -> bool:
			return len(ctx.guild.emojis) >= limit * 2

		def total_emotes() -> int:
			return len([emoji for emoji in ctx.guild.emojis if not emoji.animated])

		def total_animated() -> int:
			return len([emoji for emoji in ctx.guild.emojis if emoji.animated])

		# Handle emoji limitations
		if at_emoji_limit():
			return await ctx.send("You're at the limit for both emojis and animated emojis")

		# initialization
		if not custom and not ids and not args and not ctx.message.attachments:
			return await ctx.send("You need to include an emoji to steal, an image/gif, or an image/gif URL")
		ids = list(ids); args = list(args)
		for arg in args:
			if arg.isdigit():
				ids.append(int(arg))
				args.remove(arg)
		ctx.msg = await ctx.send("Uploading emoji(s)..")

		# PartialEmoji objects
		for emoji in custom:
			if not at_emoji_limit():
				if emoji.animated and total_animated() == limit:
					if "Animated Limit Reached" not in ctx.msg.content:
						ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Animated Limit Reached")
					continue
				elif not emoji.animated and total_emotes() == limit:
					if "Emote Limit Reached" not in ctx.msg.content:
						ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Emote Limit Reached")
					continue
				if self.is_blacklisted(ctx, emoji):
					ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"{emoji.name} - Blacklisted Emoji")
					continue
				name = emoji.name
				img = await self.bot.download(emoji.url)
				await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author))

		# PartialEmoji IDS
		for emoji_id in ids:
			emoji = self.bot.get_emoji(emoji_id)
			if emoji:
				emoji = emoji.url
			else:
				emoji = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
			img = await self.bot.download(emoji)
			if not img:
				ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"{emoji_id} - Couldn't Fetch")
				continue

			if not at_emoji_limit():
				if not isinstance(emoji, str) and emoji.animated and total_animated() == limit:
					if "Animated Limit Reached" not in ctx.msg.content:
						ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Animated Limit Reached")
					continue
				elif not isinstance(emoji, str) and not emoji.animated and total_emotes() == limit:
					if "Emote Limit Reached" not in ctx.msg.content:
						ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Emote Limit Reached")
					continue

				# Get any optional 'name' arguments
				argsv = ctx.message.content.split()
				index = argsv.index(str(emoji_id)) + 1
				name = f"new_emoji_{emoji_id}"
				if len(argsv) > index:
					new_name = argsv[index]
					if not new_name.isdigit():
						name = new_name

				await self.upload_emoji(ctx, name=str(name), img=img, reason=str(ctx.author))

		# Image/GIF URLS
		def check(iter):
			if iter + 2 > len(args):
				return '.'
			return args[iter + 1]

		try:
			mappings = {
				await self.bot.download(arg): check(iter) if '.' not in check(iter) else 'new_emoji'
					for iter, arg in enumerate(args) if '.' in arg
			}
			for img, name in mappings.items():
				if not img:
					ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"{name} - Dead Link")
					continue
				await self.upload_emoji(ctx, name=name, img=img, reason=str(ctx.author))
		except aiohttp.InvalidURL as e:
			await self.bot.utils.updat_msg(ctx.msg, str(e))

		# Attached Images/GIFsK
		allowed_extensions = ['png', 'jpg', 'jpeg', 'gif']
		for attachment in ctx.message.attachments:
			file_is_allowed = any(not attachment.filename.endswith(ext) for ext in allowed_extensions)
			if not attachment.height or not file_is_allowed:
				ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"{attachment.filename} - Not an image or gif")
				continue
			if "gif" in attachment.filename and total_animated == limit:
				if "Animated Limit Reached" not in ctx.msg:
					ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Animated Limit Reached")
				continue
			elif "gif" not in attachment.filename and total_emotes == limit:
				if "Emote Limit Reached" not in ctx.msg.content:
					ctx.msg = await self.bot.utils.update_msg(ctx.msg, f"Emote Limit Reached")
				continue

			file = await attachment.read()  # Raw bytes file
			name = attachment.filename[:attachment.filename.find('.')]
			if args and not custom and not ids and not mappings:
				name = args[0]

			await self.upload_emoji(ctx, name=name, img=file, reason=str(ctx.author))

		if not len(ctx.msg.content.split('\n')) > 1:
			ctx.msg = await self.bot.utils.update_msg(ctx.msg, "No proper formats I can work with were provided")

	@commands.command(name="delemoji", aliases=["delemote"])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.has_permissions(manage_emojis=True)
	async def _delemoji(self, ctx, *emoji: discord.Emoji):
		for emoji in emoji:
			if emoji.guild.id != ctx.guild.id:
				await ctx.send(f"{emoji} doesn't belong to this server")
				continue
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
