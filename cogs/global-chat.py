"""
Link multiple channels together via link command
"""

from os import path
import json
import aiohttp
import asyncio

from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord

from utils import colors, utils


class GlobalChat(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/userdata/global_chat.json'
		self.channels = {}
		self.webhooks = False
		self.cd = {}
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				dat = json.load(f)  # type: dict
				self.channels = dat['channels']
				self.webhooks = dat['webhooks']

	def save_data(self):
		with open(self.path, 'w+') as f:
			json.dump({'channels': self.channels, 'webhooks': self.webhooks}, f)

	@commands.group(name='global-chat', aliases=['gc'])
	@commands.cooldown(*utils.default_cooldown())
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True, manage_webhooks=True)
	async def global_chat(self, ctx):
		""" Link multiple channels together """
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Global Chat', icon_url=self.bot.user.avatar_url)
			e.description = 'Link a channel and send and/or receive messages in other linked channels'
			p = utils.get_prefix(ctx)  # type: str
			e.add_field(
				name='◈ Usage',
				value=f"{p}global-chat link\n> add your channel"
				      f"\n{p}global-chat unlink\n> remove your channel"
			)
			await ctx.send(embed=e)

	@global_chat.command(name='link')
	@commands.has_permissions(administrator=True)
	async def _link(self, ctx, channel: discord.TextChannel = None):
		""" add a channel to global chat """
		if not channel:
			channel = ctx.channel
		channel_id = str(channel.id)
		if channel_id in self.channels:
			return await ctx.send('Oi.. you already linked this channel')
		webhook = await channel.create_webhook(name='Global Chat')
		self.channels[channel_id] = webhook.url
		await ctx.send(f"Linked {channel.mention}")
		self.save_data()

	@global_chat.command(name='unlink')
	@commands.has_permissions(administrator=True)
	async def _unlink(self, ctx, channel: discord.TextChannel = None):
		""" removes a channel from global chat """
		if not channel:
			channel = ctx.channel
		channel_id = str(channel.id)
		if channel_id not in self.channels:
			return await ctx.send("Oi.. this channel's not linked")
		del self.channels[channel_id]
		await ctx.send(f"Unlinked {channel.mention}")
		self.save_data()

	@global_chat.command(name='toggle-webhooks')
	@commands.is_owner()
	async def _toggle_webhooks(self, ctx):
		""" enables or disables the use of webhooks """
		if self.webhooks == True:
			self.webhooks = False
			await ctx.send('Disabled webhooks')
		else:
			self.webhooks = True
			await ctx.send('Enabled webhooks')
		self.save_data()

	@commands.Cog.listener()
	async def on_message(self, msg):
		if isinstance(msg.guild, discord.Guild) and (msg.content or msg.attachments):
			channel_id = str(msg.channel.id)
			if channel_id in self.channels and not str(msg.author).endswith('#0000') and not msg.content.startswith('Linked'):
				user_id = msg.author.id
				if user_id not in self.cd:
					self.cd[user_id] = []
				if len(self.cd[user_id]) < 2:
					self.cd[user_id].append(msg.id)
					msg = await msg.channel.fetch_message(msg.id)
					channels = [
						(id, url) for id, url in self.channels.items() if id != channel_id
					]
					if self.webhooks:
						async with aiohttp.ClientSession() as session:
							for channel_id, webhook_url in channels:
								try:
									webhook = Webhook.from_url(webhook_url, adapter=AsyncWebhookAdapter(session))
									await webhook.send(
										msg.content, username=msg.author.display_name, avatar_url=msg.author.avatar_url
									)
								except:
									del self.channels[channel_id]
					else:
						for channel_id, webhook_url in channels:
							channel = self.bot.get_channel(int(channel_id))
							e = discord.Embed(color=msg.author.color)
							e.set_author(name=str(msg.author), icon_url=msg.author.avatar_url)
							e.description = msg.content
							if msg.attachments:
								e.set_image(url=msg.attachments[0].url)
							await channel.send(embed=e)
					await asyncio.sleep(5)
					self.cd[user_id].remove(msg.id)

def setup(bot):
	bot.add_cog(GlobalChat(bot))
