from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from utils import checks, utils
from io import BytesIO
import requests
import discord
import aiohttp


class DMChannel(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.user = None
		self.channel = None
		self.webhook = None
		self.clean = False

	@commands.command(name='createdm', aliases=['createcleandm'])
	@commands.check(checks.luck)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_webhooks=True)
	async def create_dm_channel(self, ctx, user, opt=None):
		if opt:
			if ctx.message.channel_mentions:
				channel = ctx.message.channel_mentions[0]
				self.channel = channel.id
				self.webhook = await channel.create_webhook(name='dm')
			else:
				channel = self.bot.get_channel(int(user))
				self.webhook = await channel.create_webhook(name='dm')
				self.channel = channel.id
			self.user = ctx.author; self.clean = False
			return await ctx.send('👍')
		if ctx.message.mentions:
			user = ctx.message.mentions[0]
		else:
			try: user = self.bot.get_user(int(user))
			except: user = utils.get_user(ctx, user)
		if not isinstance(user, discord.User) and not isinstance(user, discord.Member):
			return await ctx.send('Improper args or user isn\'t cached')
		await user.create_dm()
		if not user.dm_channel.permissions_for(self).send_messages:
			return await ctx.send('I can\'t dm that user ;-;')
		if ctx.message.content.startswith('.createcleandm'):
			self.clean = True
		else:
			self.clean = False
		self.webhook = await ctx.channel.create_webhook(name='dm')
		await ctx.send(f'Created a dm channel with {user.name}')
		self.user = user; self.channel = ctx.channel.id

	@commands.Cog.listener()
	async def on_message(self, msg: discord.Message):
		if self.channel and self.user:
			if msg.author.id == self.user.id or msg.channel.id == self.channel:
				if '.close' in msg.content:
					await self.webhook.delete()
					self.user = None; self.channel = None; self.webhook=None
					return await msg.channel.send('Closed the dm channel')
				if not msg.webhook_id and not msg.content.startswith('created a dm channel'):
					msg.content = discord.utils.escape_mentions(msg.content)
					file = discord.File; embed = discord.Embed
					if msg.attachments:
						file = msg.attachments[0]
					if msg.embeds:
						embed = msg.embeds[0]
					if isinstance(msg.channel, discord.DMChannel):
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(self.webhook.url, adapter=AsyncWebhookAdapter(session))
							if msg.content and msg.attachments:
								return await webhook.send(msg.content, username=msg.author.name, avatar_url=msg.author.avatar_url, file=discord.File(BytesIO(requests.get(file.url).content), filename=file.filename))
							if msg.attachments:
								return await webhook.send(username=msg.author.name, avatar_url=msg.author.avatar_url, file=discord.File(BytesIO(requests.get(file.url).content), filename=file.filename))
							await webhook.send(msg.content, username=msg.author.name, avatar_url=msg.author.avatar_url)
					else:
						if msg.channel.id == self.channel:
							if not self.clean:
								msg.content = f'__**{msg.author.display_name}:**__ {msg.content}'
							if msg.attachments:
								return await self.user.send(msg.content, file=discord.File(BytesIO(requests.get(file.url).content), filename=file.filename))
							if msg.embeds:
								return await self.user.send(msg.content, embed=embed)
							await self.user.send(msg.content)

def setup(bot):
	bot.add_cog(DMChannel(bot))
