from bs4 import BeautifulSoup as bs
from discord.ext import commands
from utils import config, colors
import wikipedia.exceptions
from os.path import isfile
import wikipedia
import discord
import aiohttp
import json
import time

class Core(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

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
	async def repeat(self, ctx, *, content: commands.clean_content):
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
		before = time.monotonic()
		message = await ctx.send(embed=e)
		ping = (time.monotonic() - before) * 1000
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
		e.set_author(name="Bots Latency", icon_url=img)
		e.set_thumbnail(url="https://cdn.discordapp.com/emojis/562598266881966080.png?v=1")
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

def setup(bot):
	bot.add_cog(Core(bot))
