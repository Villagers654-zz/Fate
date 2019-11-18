"""
Discord.Py Cog for Kithro :]
- undo's unnecessary markdown
"""

import aiohttp

from discord.ext import commands
import discord
from discord import Webhook, AsyncWebhookAdapter


class Kithro(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, msg):
		kithro_id = 453276270399062019
		if isinstance(msg.guild, discord.Guild) and msg.author.id == kithro_id:
			if msg.guild.me.guild_permissions.manage_webhooks and (
					msg.content.startswith("`")) and msg.content.endswith("`"):
				webhook = await msg.channel.create_webhook(name=msg.author.display_name)
				clean_content = msg.content.replace("`", "")
				async with aiohttp.ClientSession() as session:
					webhook = Webhook.from_url(webhook.url, adapter=AsyncWebhookAdapter(session))
					await webhook.send(clean_content, avatar_url=msg.author.avatar_url)
					await msg.delete()

def setup(bot):
	bot.add_cog(Kithro(bot))
