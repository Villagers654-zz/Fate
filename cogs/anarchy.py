from discord import Webhook, AsyncWebhookAdapter
import aiohttp
from io import BytesIO
import requests
from discord.ext import commands
import discord

class Anarchy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = {
			529705827716825098: {
				'name': '4B4T',
				'webhook': 'https://discordapp.com/api/webhooks/602956280445009950/gYlhr2NOw97wfeVqiC0eSi8xu4Qm_h_vTe3Tx8bwfY2_kfGfU40Nl7fRrqpzRuALKinc',
				'channel': 602953723324399666
			},
			585778970734231585: {
				'name': '2B2TBE',
				'webhook': 'https://discordapp.com/api/webhooks/602956312069931038/T-6cmTfHH9W5Zd7QKeTU3xPyeX_q4XDBqEukwUjMCIS5AWu7FPyefnMp41HhK4p-zKQh',
				'channel': 602956148659847190
			},
			596177782069788672: {
				'name': '2B2TMCPE',
				'webhook': 'https://discordapp.com/api/webhooks/602956230041796705/P1MAyCYUmbZQwxEVIqXht0nB7K45YpT40eNMMufZ4nfj4ouP9uZ60IMftWUnv4DIXE04',
				'channel': 602953558438182923
			}
		}

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.channel.id in self.config:
			async with aiohttp.ClientSession() as session:
				webhook = Webhook.from_url(self.config[msg.channel.id]['webhook'], adapter=AsyncWebhookAdapter(session))
				if msg.content and msg.attachments:
					file = msg.attachments[0]
					return await webhook.send(msg.content, username=msg.author.name, vatar_url=msg.author.avatar_url,  file=discord.File(BytesIO(requests.get(file.url).content), filename=file.filename))
				if msg.attachments:
					file = msg.attachments[0]
					return await webhook.send(username=msg.author.name, avatar_url=msg.author.avatar_url, file=discord.File(BytesIO(requests.get(file.url).content), filename=file.filename))
				await webhook.send(msg.content, username=msg.author.name, avatar_url=msg.author.avatar_url)

def setup(bot):
	bot.add_cog(Anarchy(bot))
