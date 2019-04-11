from bs4 import BeautifulSoup as bs
from discord.ext import commands
from utils import config, colors
from time import time, monotonic
import wikipedia.exceptions
from os.path import isfile
from io import BytesIO
import wikipedia
import requests
import discord
import aiohttp
import json

class Core(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.last = {}

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def topguilds(self, ctx):
		e = discord.Embed(color=0x80b0ff)
		e.title = "Top Guilds"
		e.description = ""
		rank = 1
		for guild in sorted([[g.name, g.member_count] for g in self.bot.guilds], key=lambda k: k[1], reverse=True)[:8]:
			e.description += "**{}.** {}: `{}`\n".format(rank, guild[0], guild[1])
			rank += 1
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def invite(self, ctx):
		await ctx.send(embed=config.links())

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def say(self, ctx, *, content: commands.clean_content):
		await ctx.send(content)
		await ctx.message.delete()

	@commands.command(name="prefix")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_guild=True)
	async def _prefix(self, ctx, *, prefix):
		if not isinstance(ctx.guild, discord.Guild):
			return await ctx.send("This command can't be used in dm")
		guild_id = str(ctx.guild.id)
		if not isfile("./data/userdata/prefixes.json"):
			with open("./data/userdata/prefixes.json", "w") as f:
				failed_save_data = {}
				json.dump(failed_save_data, f)
				print("reverted")
		with open("./data/userdata/prefixes.json", "r") as f:
			prefixes = json.load(f)
		with open("./data/userdata/prefixes.json", "w") as f:
			prefixes[guild_id] = prefix
			json.dump(prefixes, f, indent=4)
		await ctx.send(f"Changed the servers prefix to `{prefix}`")

	@commands.command(pass_context=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def ping(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.set_author(name="Measuring ping:")
		before = monotonic()
		message = await ctx.send(embed=e)
		ping = (monotonic() - before) * 1000
		if ping < 175:
			img = "https://cdn.discordapp.com/emojis/562592256939393035.png?v=1"
		else:
			if ping < 250:
				img = "https://cdn.discordapp.com/emojis/562592178204049408.png?v=1"
			else:
				if ping < 400:
					img = "https://cdn.discordapp.com/emojis/562592177692213248.png?v=1"
				else:
					if ping < 550:
						img = "https://cdn.discordapp.com/emojis/562592176463151105.png?v=1"
					else:
						if ping < 700:
							img = "https://cdn.discordapp.com/emojis/562592175880405003.png?v=1"
						else:
							img = "https://cdn.discordapp.com/emojis/562592175192539146.png?v=1"
		api = str(self.bot.latency * 1000)
		api = api[:api.find(".")]
		e.set_author(name=f"Bots Latency", icon_url=self.bot.user.avatar_url)
		e.set_thumbnail(url=img)
		e.description = f"**Message Trip:** `{int(ping)}ms`\n**Websocket Heartbeat:** `{api}ms`"
		await message.edit(embed=e)

	@commands.command(pass_context=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def wiki(self,ctx,*,query:str):
		try:
			q = wikipedia.page(query)
			e = discord.Embed(color=0x80b0ff)
			e.set_author(name=f"Search Phrase: {query}", icon_url=ctx.author.avatar_url)
			e.description = "Result: {}```{}```For more information, visit [here]({})".format(q.title,wikipedia.summary(query, sentences=5),q.url)
			await ctx.send(embed=e)
		except wikipedia.exceptions.PageError:
			await ctx.send("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command(pass_context=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def ud(self,ctx,*,query:str):
		channel_id = str(ctx.channel.id)
		if channel_id not in self.last:
			self.last[channel_id] = (None, None)
		if query == self.last[channel_id][0]:
			if self.last[channel_id][1] > time() - 60:
				return await ctx.message.add_reaction("❌")
		self.last[channel_id] = (query, time())
		url = "http://www.urbandictionary.com/define.php?term={}".format(query.replace(" ","%20"))
		async with aiohttp.ClientSession() as sess:
			async with sess.get(url) as resp:
				r = await resp.read()
		resp = bs(r,'html.parser')
		try:
			if len(resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")) >= 1000:
				meaning = resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")[:1000] + "..."
			else:
				meaning = resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")
			e = discord.Embed(color=0x80b0ff)
			e.set_author(name=f'{query} 🔍', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/450528552199258123/524139193723781120/urban-dictionary-logo.png")
			e.description = "**Meaning:**\n{}\n\n**Example:**\n{}\n".format(meaning,resp.find('div', {'class':'example'}).text.strip('\n'))
			e.set_footer(text="~{}".format(resp.find('div', {'class': 'contributor'}).text.strip('\n')))
			await ctx.send(embed=e)
		except AttributeError:
			await ctx.send("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.Cog.listener()
	async def on_message(self, msg: discord.Message):
		if isinstance(msg.channel, discord.DMChannel):
			channel = self.bot.get_channel(552828495244558381)
			if msg.attachments:
				for attachment in msg.attachments:
					if msg.author.id == self.bot.user.id:
						return await channel.send(f"__**Fate --> {msg.channel.recipient}:**__ {msg.content}",
						    file=discord.File(BytesIO(requests.get(attachment.url).content), filename=attachment.filename))
					return await channel.send(f"__**{msg.author.name}:**__ {msg.content}",
						file=discord.File(BytesIO(requests.get(attachment.url).content), filename=attachment.filename))
			if msg.embeds:
				if msg.author.id == self.bot.user.id:
					return await channel.send(f"__**Fate --> {msg.channel.recipient}:**__ {msg.content}", embed=msg.embeds[0])
				return await channel.send(f"__**{msg.channel.recipient}:**__ {msg.content}", embed=msg.embeds[0])
			if msg.author.id == self.bot.user.id:
				return await channel.send(f"__**Fate --> {msg.channel.recipient}:**__ {msg.content}")
			await channel.send(f"__**{msg.author}:**__ {msg.content}")

def setup(bot):
	bot.add_cog(Core(bot))
