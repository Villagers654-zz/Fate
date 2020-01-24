# Link multiple channels together via link command

from os import path
import json
import aiohttp
import asyncio
from time import time

from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord

from utils import colors, utils, config


def toggle_webhook_check():
	""" restrict use of webhooks to bot owner """
	async def predicate(ctx):
		return ctx.author.id == config.owner_id()

	return commands.check(predicate)


class GlobalChat(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/userdata/global_chat.json'
		self.config = {}
		self.msgs = []
		self.user_cd = {}
		self.guild_cd = {}
		self.global_cd = {}
		self.silence = False
		self.slowmode = False
		self.blocked = []
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.config = json.load(f)  # type: dict
		for guild_id, conf in list(self.config.items()):
			if conf['last'] < time() - 36288000:
				del self.config[guild_id]
				self.save_data()

	def save_data(self):
		with open(self.path, 'w+') as f:
			json.dump(self.config, f)

	async def remove_webhook(self, guild_id, channel):
		""" deletes the global chat webhook so they don't pile up """
		try:
			webhooks = await channel.webhooks()
			for webhook in webhooks:
				if webhook.url == self.config[guild_id]['webhook']:
					await webhook.delete()
		except discord.errors.Forbidden:
			pass

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
				value=f"{p}global-chat link\n> add your channel\n"
				      f"{p}global-chat unlink\n> remove your channel"
			)
			await ctx.send(embed=e)

	@global_chat.command(name='link')
	@commands.has_permissions(administrator=True)
	async def _link(self, ctx, channel: discord.TextChannel = None):
		""" add a channel to global chat """
		if not channel:
			channel = ctx.channel
		guild_id = str(ctx.guild.id)
		if guild_id in self.config:
			if self.config[guild_id]['webhook']:
				await self.remove_webhook(guild_id, channel)
		self.config[guild_id] = {
			"channel": channel.id,
			"webhook": None,
			"last": time()
		}
		await ctx.send(f"Linked {channel.mention}")
		self.save_data()

	@global_chat.command(name='unlink')
	@commands.has_permissions(administrator=True)
	async def _unlink(self, ctx, channel: discord.TextChannel = None):
		""" removes a channel from global chat """
		if not channel:
			channel = ctx.channel
		guild_id = str(ctx.guild.id)
		if guild_id not in self.config:
			return await ctx.send("Oi.. this channel's not linked")
		if self.config[guild_id]['webhook']:
			if self.config[guild_id]['webhook']:
				await self.remove_webhook(guild_id, channel)
		del self.config[guild_id]
		await ctx.send(f"Unlinked {channel.mention}")
		self.save_data()

	@global_chat.command(name='toggle-webhooks')
	@toggle_webhook_check()
	async def _toggle_webhooks(self, ctx, channel: discord.TextChannel = None):
		""" enables or disables the use of webhooks """
		if not channel:
			channel = ctx.channel
		guild_id = str(ctx.guild.id)
		if self.config[guild_id]['webhook']:
			await self.remove_webhook(guild_id, channel)
			self.config[guild_id]['webhook'] = None
			await ctx.send('Disabled webhooks')
		else:
			webhook = await channel.create_webhook(name='Global Chat')
			self.config[guild_id]['webhook'] = webhook.url
			await ctx.send('Enabled webhooks')
		self.save_data()

	@commands.Cog.listener()
	async def on_message(self, msg):
		if isinstance(msg.guild, discord.Guild) and (msg.content or msg.attachments) and (
				not str(msg.author).endswith('#0000')) and not msg.content.startswith('.') and (
				not msg.content.startswith('Linked')) and not msg.author.bot and (
				not msg.author.id == self.bot.user.id):

			guild_id = str(msg.guild.id)
			user_id = str(msg.author.id)
			if guild_id in self.config:
				if msg.channel.id != self.config[guild_id]['channel']:
					return

				async def queue(m):
					""" temporarily put the msg in a list """
					self.msgs.append(m)
					await asyncio.sleep(5)
					self.msgs.remove(m)

				async def block():
					""" block a user from live chat for 15mins """
					self.blocked.append(user_id)
					await asyncio.sleep(60 * 15)
					self.blocked.remove(user_id)

				# rate limits
				ignore = False
				if user_id in self.blocked or guild_id in self.blocked or self.silence:
					return

				if len(self.msgs) >= 5:
					self.silence = True
					for channel_id in [dat['channel'] for dat in self.config.values()]:
						channel = self.bot.get_channel(channel_id)
						await channel.send('Initiating slowmode due to hitting the rate limit')
					self.slowmode = True
					self.silence = False

				guild = [m for m in self.msgs if str(m.guild.id) == guild_id]
				if self.slowmode and len(guild) >= 2:
					ignore = True
				if len(guild) >= 3:
					ignore = True

				user = [m for m in self.msgs if str(m.author.id) == user_id]
				if len(user) >= 2:
					ignore = True
				if len(user) >= 3:
					if user_id not in self.blocked:
						await msg.channel.send(f"{msg.author.mention} you've been temp blocked from global chat")
						await block()
					ignore = True

				self.bot.loop.create_task(queue(msg))
				if ignore:
					return await msg.delete()
				msg = await msg.channel.fetch_message(msg.id)
				self.config[guild_id]['last'] = time()
				self.save_data()

				# distribute the msg everywhere
				async with aiohttp.ClientSession() as session:
					for guild_id, conf in self.config.items():
						if guild_id == str(msg.guild.id):
							continue
						try:
							if conf['webhook']:
								if '@' in msg.content:
									msg.content = str(msg.content).replace('@', '!')
								webhook = Webhook.from_url(conf['webhook'], adapter=AsyncWebhookAdapter(session))
								await webhook.send(
									msg.content, username=msg.author.display_name, avatar_url=msg.author.avatar_url
								)
							else:
								channel = self.bot.get_channel(conf['channel'])
								e = discord.Embed(color=msg.author.color)
								e.set_author(name=str(msg.author), icon_url=msg.author.avatar_url)
								e.description = msg.content
								if msg.attachments:
									e.set_image(url=msg.attachments[0].url)
								await channel.send(embed=e)
						except discord.errors.InvalidArgument:  # invalid webhook url
							del self.config[guild_id]
						except discord.errors.Forbidden:  # missing permissions to send
							del self.config[guild_id]


def setup(bot):
	bot.add_cog(GlobalChat(bot))
