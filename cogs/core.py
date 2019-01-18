from bs4 import BeautifulSoup as bs
from data.misc import menus as m
from discord.ext import commands
from datetime import datetime
import wikipedia.exceptions
import wikipedia
import discord
import aiohttp
import asyncio
import psutil
import time
import os

class Core:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	def tothy(ctx):
		return ctx.message.author.id == 355026215137968129

	def fourbeefourtee(ctx):
		return ctx.author.id in [264838866480005122, 264838866480005122]

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_core(self, ctx):
		await ctx.send('working')

# ~== Main Commands ==~

	@commands.command()
	async def topguilds(self, ctx):
		e = discord.Embed(color=0x80b0ff)
		e.title = "Top Guildies"
		e.description = ""
		rank = 1
		for guild in sorted([[g.name, g.member_count] for g in self.bot.guilds], key=lambda k: k[1], reverse=True)[:8]:
			e.description += "**{}.** {}: `{}`\n".format(rank, guild[0], guild[1])
			rank += 1
		await ctx.send(embed=e)

	@commands.command()
	async def invite(self, ctx):
		await ctx.send(embed=m.links)

	@commands.command()
	async def repeat(self, ctx, *, content: commands.clean_content):
		await ctx.send(content)
		await ctx.message.delete()

	@commands.command(pass_context=True)
	async def ping(self, ctx):
		before = time.monotonic()
		message = await ctx.send("Measuring ping:")
		ping = (time.monotonic() - before) * 1000
		await message.edit(content=f"My ping: `{int(ping)}ms`")

	@commands.command(pass_context=True)
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

# ~== Info ==~















def setup(bot):
	bot.add_cog(Core(bot))
