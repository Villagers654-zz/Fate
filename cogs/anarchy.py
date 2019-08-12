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
				'webhook': 'https://discordapp.com/api/webhooks/602956280445009950/gYlhr2NOw97wfeVqiC0eSi8xu4Qm_h_vTe3Tx8bwfY2_kfGfU40Nl7fRrqpzRuALKinc'
			},
			585778970734231585: {
				'name': '2B2TBE',
				'webhook': 'https://discordapp.com/api/webhooks/602956312069931038/T-6cmTfHH9W5Zd7QKeTU3xPyeX_q4XDBqEukwUjMCIS5AWu7FPyefnMp41HhK4p-zKQh'
			},
			608667515429584928: {
				'name': '2B2TMCPE',
				'webhook': 'https://discordapp.com/api/webhooks/602956230041796705/P1MAyCYUmbZQwxEVIqXht0nB7K45YpT40eNMMufZ4nfj4ouP9uZ60IMftWUnv4DIXE04'
			},
			523687931483783168: {
				'name': '2B2TPE',
				'webhook': 'https://discordapp.com/api/webhooks/605669469486055424/TczBigg9Oj0ydHQw6Ta4QGkFIlxjfHft63dcxAHCeE5ZX6W8LSvhu6ECpdMlFoTrFnaa'
			},
			543896208175923200: {
				'name': 'ConstantiamPE',
				'webhook': 'https://discordapp.com/api/webhooks/605829483177574402/uG6wy7XNrzZJyD343Unf8eQ5UVeQfX1fbBBgIRC5OGSxeEiSP28dwysphqVGixSOmg0n'
			},
			594374002672271400: {
				'name': 'ConstantiamPE+',
				'webhook': 'https://discordapp.com/api/webhooks/605829984707411978/iNM4sSqxNMfAA0ruR1Bz2VzQSFmeMnG14dg1MxDCUR0SsbRK_BFnhRFfc8MYb5dA1EpS'
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
