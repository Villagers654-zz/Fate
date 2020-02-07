"""
# Discord.Py v1.0 - v1.5 ChatBridge Cog
- Link channels in other servers to a category
- Delete msgs from muted/banned users
- Ignores spam
+ Not for use of too many chats; you'll likely get rate limited,
  and you might get beaned for api spam
"""

import aiohttp
from time import time
import os

from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord


class ChatBridge(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.locations = {}
		self.spam_cd = {}
		self.bans = {}
		self.cache = []
		self.locations = {
			649076405103230986: {  # queens #general-sfw
				"webhook": "https://discordapp.com/api/webhooks/649076406340419610/zoxwNW_aQNTmZAJ7amKJe0sIxlRHD23UmCkJWNRVPK350JxBn6ZJ3_Kl-bbjKij_jpmN",
				"linked_webhook": "https://discordapp.com/api/webhooks/649076405799485448/vq20vnsfzA9z3ECiVm6jORjAJNeQmaVWVXhUm8ph--CIOREM0k4onSzqn1wE_cR0Snhn",
				"linked_channel": 649069768745287708
			},
			664620517168513042: {  # crafting table  #general
				"webhook": "https://discordapp.com/api/webhooks/667185061128306728/Jr24f_yvKwt42NzVdAYD_DyP7rPqOMzpJPQIWxaWiwDilT87uMAMnR_8JB3S-1TaYQkt",
				"linked_webhook": "https://discordapp.com/api/webhooks/664620517797527562/hfvE3CBcGyMN-52wZ3Pqrw7ZRDwNcqCrRwzBvnyseuCCoTl1tMAtMmZUSReWEeNnJ4At",
				"linked_channel": 614889263196143742
			},
			675140804725178399: {  # 2b2tmcpe #general
				"webhook": "https://discordapp.com/api/webhooks/675140914179735572/HQ5iOE_gQLLLHrcEnAG-8_MHzcpAlLMKDZKylDjouyCZ60Cd95_22618Hwwi5e3qks1b",
				"linked_webhook": "https://discordapp.com/api/webhooks/659475342133690379/qP_M5MKoNbeHwRn2QStfsGazFi5mc_W92qMmck7tnQhXT2mdDfIzETI5dIqpUumRcy8t",
				"linked_channel": 638536531916881930
			},
			675140846919745569: {  # 2b2tmcpe #general-chinese
				"webhook": "https://discordapp.com/api/webhooks/675141978819657767/H2EyoyVi_BTvXir5ma3FEZdbU9YrddWKM35WcDLYtPmUBbL8WIM_yehW6MI2vukfbHDj",
				"linked_webhook": "https://discordapp.com/api/webhooks/675142741482668064/WgTleAzDrIgEyK_OO0206pBK2vsVP_QYtWfNH1WXSx4OEiEyZz5fk7aQzURQgDO2zhs1",
				"linked_channel": 638572031591317514
			}
		}

	@commands.Cog.listener()
	async def on_message(self, msg):
		""" Send the msg to the proper location """
		if isinstance(msg.guild, discord.Guild) and not str(msg.author).endswith('#0000'):

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

			webhook_url = None
			if msg.channel.id in self.locations:
				webhook_url = self.locations[msg.channel.id]['linked_webhook']
			elif any(msg.channel.id == dat['linked_channel'] for dat in self.locations.values()):
				for channel_id, dat in self.locations.items():
					if msg.channel.id == dat['linked_channel']:
						webhook_url = self.locations[channel_id]['webhook']
			else:
				return

			files = []; embed = None
			for attachment in msg.attachments:
				path = os.path.join('static', attachment.filename)
				await attachment.save(path)
				file = discord.File(path)
				files.append(file)
			for embed in msg.embeds:
				embed = embed

			msg = await msg.channel.fetch_message(msg.id)
			if '@' in msg.content:
				msg.content = str(msg.content).replace('\\', '').replace('<@​', '<@')
				for user_id in msg.raw_mentions:
					username = '@' + str(self.bot.get_user(user_id))
					msg.content = msg.content.replace(f"<@{user_id}>", username)
					msg.content = msg.content.replace(f"<@!{user_id}>", username)
				msg.content = msg.content.replace('@e', '!everyone').replace('@here', '!here')

			async with aiohttp.ClientSession() as session:
				webhook = Webhook.from_url(webhook_url, adapter=AsyncWebhookAdapter(session))
				try:
					await webhook.send(msg.content, username=msg.author.display_name,
					                   avatar_url=msg.author.avatar_url, files=files, embed=embed)
				except discord.errors.HTTPException:
					await webhook.send(msg.content, username=msg.author.display_name,
					                   avatar_url=msg.author.avatar_url, embed=embed)

			for attachment in msg.attachments:
				os.remove(os.path.join('static', attachment.filename))

def setup(bot):
	bot.add_cog(ChatBridge(bot))
