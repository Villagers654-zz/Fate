"""
# Discord.Py v1.0 - v1.5 ChatBridge Cog
- Link channels in other servers to a category
- Delete msgs from muted/banned users
- Ignores spam
+ Not for use of too many chats; you'll likely get rate limited,
+ and you might get beaned for api spam
"""

from os import path
import json
import aiohttp
from time import time
import os

from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord

from utils.colors import *


class ChatBridge(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.path = './data/chatbridge.json'
		self.category = None
		self.locations = {}
		self.spam_cd = {}
		self.bans = {}
		self.cache = []
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				dat = json.load(f)
				self.category = dat['category']
				self.locations = dat['locations']

	def save_data(self):
		""" Called when changes are made """
		with open(self.path, 'w+') as f:
			json.dump({'category': self.category, 'locations': self.locations}, f)

	@commands.group(name='chat-bridge', aliases=['chat-bridges', 'chatbridge', 'chatbridges'])
	@commands.cooldown(2, 4, commands.BucketType.user)
	@commands.guild_only()
	@commands.is_owner()
	@commands.bot_has_permissions(manage_webhooks=True)
	async def chat_bridge(self, ctx):
		""" View and manage config via reactions """
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=fate())
			e.set_author(name='Chat Bridges', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = ''
			for guild_id in self.locations.keys():
				guild = self.bot.get_guild(int(guild_id))
				e.description += f"• {guild.name}\n{guild.id}\n"
			await ctx.send(embed=e)

	@chat_bridge.command(name='add')
	async def _add(self, ctx, channel_id: int = None):
		""" Adds a new chat bridge """
		if not channel_id:
			channel_id = ctx.channel.id
		channel = self.bot.get_channel(channel_id)
		category = self.bot.get_channel(self.category)
		bridge = await category.create_text_channel(name=channel.guild.name)
		channel_webhook = await channel.create_webhook(name='ChatBridge')
		bridge_webhook = await bridge.create_webhook(name='ChatBridge')
		self.locations[str(channel.guild.id)] = {
			str(channel.id): {
				'linked_channel': bridge.id,
				'webhook': channel_webhook.url,
				'guild': channel.guild.id
			},
			str(bridge.id): {
				'linked_channel': channel.id,
				'webhook': bridge_webhook.url,
				'guild': bridge.guild.id
			}
		}
		await ctx.send(f"Added [{channel.guild.name}:{channel.name}] to chat bridges")
		self.save_data()

	@chat_bridge.command(name='remove', aliases=['del', 'rm'])
	async def _remove(self, ctx, guild_id=None):
		""" Removes a chatbridge """
		if not guild_id:
			author_channel_id = str(ctx.channel.id)
			for key, Dict in self.locations.items():
				if author_channel_id in Dict:
					channel_id = str(Dict[author_channel_id]['linked_channel'])
					guild_id = str(Dict[channel_id]['guild'])
		if not guild_id:
			return await ctx.send('Bridge not found')

		# remove the bridge channel
		category = self.bot.get_channel(self.category)
		dat = self.locations[guild_id]
		for chnl_id in dat.keys():
			chnl = self.bot.get_channel(int(chnl_id))
			if chnl.category:
				if chnl.category.id == category.id:
					await chnl.delete()

		del self.locations[guild_id]
		guild = self.bot.get_guild(int(guild_id))
		await ctx.send(f"Removed {guild if guild else guild_id}")
		self.save_data()

	@chat_bridge.command(name='set-category')
	async def _set_category(self, ctx, category):
		if category.isdigit():
			category = self.bot.get_channel(int(category))
		else:
			categories = [c for c in ctx.guild.channels if category.lower() == c.name]
			if not categories:
				categories = [c for c in ctx.guild.channels if category.lower() in c.name]
			if not categories:
				return await ctx.send("Category not found")
			category = categories[0]
		if not category:
			return await ctx.send("Category not found")
		self.category = category.id
		await ctx.send(f"Set the category to {category.name}")
		self.save_data()

	@commands.Cog.listener()
	async def on_message(self, msg):
		""" Send the msg to the proper location """
		if isinstance(msg.guild, discord.Guild) and self.category and not str(msg.author).endswith('#0000'):

			# anti spam
			author_id = str(msg.author.id)
			now = int(time() / 5)
			if author_id not in self.spam_cd:
				self.spam_cd[author_id] = [now, 0]
			if self.spam_cd[author_id][0] == now:
				self.spam_cd[author_id][1] += 1
			else:
				self.spam_cd[author_id] = [now, 0]
			if self.spam_cd[author_id][1] > 1:
				return

			guild_id, channel_id, webhook_url, dict_key = None, None, None, None
			author_channel_id = str(msg.channel.id)

			# get the data for the opposite location
			for key, Dict in self.locations.items():
				if author_channel_id in Dict:
					channel_id = str(Dict[author_channel_id]['linked_channel'])
					webhook_url = Dict[channel_id]['webhook']
					guild_id = Dict[channel_id]['guild']
					dict_key = key

			if guild_id and channel_id and webhook_url and dict_key:
				guild = self.bot.get_guild(guild_id)
				channel = self.bot.get_channel(int(channel_id))
				if not guild or not channel:
					print(f"removing dat\n{guild}:{channel}")
					del self.locations[dict_key]
					return

				id = str(msg.guild.id)
				if id not in self.bans:
					bans = await self.bot.get_guild(guild_id).bans()
					self.bans[id] = [time(), bans]
				last_time, bans = self.bans[id]
				if time() - last_time > 60:
					bans = await self.bot.get_guild(guild_id).bans()
					self.bans[id] = [time(), bans]
				for entry in bans:
					if entry.user.id == msg.author.id:
						return await msg.delete()
				for role in msg.author.roles:
					if 'muted' in role.name.lower():
						return

				# create new webhook if the old doesn't exits
				webhooks = await channel.webhooks()
				if not any(webhook_url == w.url for w in webhooks):
					webhook = await channel.create_webhook(name='ChatBridge')
					self.locations[dict_key][channel_id]['webhook'] = webhook.url
					webhook_url = webhook.url
					self.save_data()

				files = []; embed = None
				for attachment in msg.attachments:
					await attachment.save(attachment.filename)
					file = discord.File(attachment.filename)
					files.append(file)
				for embed in msg.embeds:
					embed = embed

				msg = await msg.channel.fetch_message(msg.id)
				if '@' in str(msg.content):
					msg.content = str(msg.content).replace('\\', '').replace('<@​', '<@')
					for user_id in msg.raw_mentions:
						username = '@' + str(self.bot.get_user(user_id))
						msg.content = msg.content.replace(f"<@{user_id}>", username)
						msg.content = msg.content.replace(f"<@!{user_id}>", username)
					msg.content = msg.content.replace('@e', '!everyone').replace('@here', '!here')
				else:
					msg = await msg.channel.fetch_message(msg.id)

				async with aiohttp.ClientSession() as session:
					webhook = Webhook.from_url(webhook_url, adapter=AsyncWebhookAdapter(session))
					await webhook.send(msg.content, username=msg.author.display_name, avatar_url=msg.author.avatar_url,
					                   files=files, embed=embed)

				for attachment in msg.attachments:
					os.remove(attachment.filename)

def setup(bot):
	bot.add_cog(ChatBridge(bot))
