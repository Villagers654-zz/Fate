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

	@commands.command(name='makepoll', aliases=['mp'])
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.has_permissions(manage_messages=True)
	async def makepoll(self, ctx):
		try:
			c = 0
			async for msg in ctx.channel.history(limit=3):
				if c == 1:
					await msg.add_reaction(':approve:506020668241084416')
					await msg.add_reaction(':unapprove:506020690584010772')
					await ctx.message.delete()
					break;
				c += 1
		except Exception as e:
			await ctx.send(f'**```{e}```**')

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
	async def tinyurl(self, ctx, *, link: str):
		await ctx.message.delete()
		url = 'http://tinyurl.com/api-create.php?url=' + link
		async with aiohttp.ClientSession() as sess:
			async with sess.get(url) as resp:
				r = await resp.read()
				r = str(r).replace("b'", "").replace("'", "")
		emb = discord.Embed(color=0x80b0ff)
		emb.add_field(name="Original Link", value=link, inline=False)
		emb.add_field(name="Shortened Link", value=r, inline=False)
		emb.set_footer(text='Powered by tinyurl.com', icon_url='http://cr-api.com/static/img/branding/cr-api-logo.png')
		await ctx.send(embed=emb)

	@commands.command()
	async def invite(self, ctx):
		await ctx.send(embed=m.links)

	@commands.command()
	async def repeat(self, ctx, *, content: commands.clean_content):
		await ctx.send(content)
		await ctx.message.delete()

	@commands.command(pass_context=True, aliases=['reminder', 'alarm'])
	async def timer(self, ctx, seconds: int, *, remember: str = ""):
		if not remember:
			end_timer = ctx.send("{}, your timer for {} seconds has expired!".format(ctx.message.author.name, seconds))
			await ctx.send("{}, you have set a timer for {} seconds!".format(ctx.message.author.name, seconds))
			await asyncio.sleep(float(seconds))
			await end_timer
		else:
			end_timer = ctx.send("{}, your timer for {} seconds has expired! I was instructed to remind you about "
			                     "`{}`!".format(ctx.message.author.mention, seconds, remember))
			await ctx.send("{}, I will remind you about `{}` in {} seconds!".format(ctx.message.author.mention, remember, seconds))
			await asyncio.sleep(float(seconds))
			await end_timer

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def devstats(self, ctx):
		try:
			def bytes2human(n):
				symbols = ('GHz', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
				prefix = {}
				for i, s in enumerate(symbols):
					prefix[s] = 1 << (i + 1) * 10
				for s in reversed(symbols):
					if n >= prefix[s]:
						value = float(n) / prefix[s]
						return '%.1f%s' % (value, s)
				return "%sB" % n
			p = psutil.Process(os.getpid())
			luck = self.bot.get_user(264838866480005122)
			botram = p.memory_full_info().rss
			ramused = psutil.virtual_memory().used
			ramtotal = psutil.virtual_memory().total
			rampercent = psutil.virtual_memory().percent
			cpupercent = psutil.cpu_percent(interval=1)
			cpufreqcurrent = psutil.cpu_freq().current
			cpufreqmax = psutil.cpu_freq().max
			storageused = psutil.disk_usage('/').used
			storagetotal = psutil.disk_usage('/').total
			batterypercent = psutil.sensors_battery().percent
			ischarging = " "
			if psutil.sensors_battery().power_plugged:
				ischarging= "charging"
			e = discord.Embed()
			e.set_author(name='| Memory | ', icon_url=luck.avatar_url)
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif")
			e.description = f'__**Storage**__: [{bytes2human(storageused)}/{bytes2human(storagetotal)}]\n' \
				f'__**RAM**__: [{bytes2human(ramused)}/{bytes2human(ramtotal)}] ({rampercent}%)\n' \
				f'__**CPU**__: **Global**: {psutil.cpu_percent(interval=1)}% **Bot**: {p.cpu_percent(interval=1.0)}%\n' \
				f'__**CPU Frequency**__: [{bytes2human(cpufreqcurrent)}/{bytes2human(cpufreqmax)}]\n' \
				f'__**battery**__: {batterypercent}% {ischarging}'
			e.set_footer(text=f'{psutil.cpu_percent(interval=1, percpu=True)}')
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(e)

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
	async def poll(self, ctx, *, arg):
		try:
			e = discord.Embed()
			e=discord.Embed(description=arg, color=0x80b0ff)
			e.set_author(name="| {} |".format(ctx.author.name), icon_url=ctx.author.avatar_url)
			message = await ctx.send(embed=e)
			await message.add_reaction(':approve:506020668241084416')
			await asyncio.sleep(0.5)
			await message.add_reaction(':unapprove:506020690584010772')
			await asyncio.sleep(0.5)
			await message.add_reaction('🤷')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')

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

	@commands.command()
	async def channelinfo(self, ctx):
		try:
			fmt = "%m/%d/%Y"
			created = datetime.date(ctx.channel.created_at)
			e=discord.Embed(description="id: {}".format(ctx.channel.id), color=0x0000ff)
			e.set_author(name="{}:".format(ctx.channel.name), icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="◈ Main ◈", value="• Category: {}\n• Slowmode: {}".format(ctx.channel.category, ctx.channel.slowmode_delay), inline=False)
			e.add_field(name="◈ Topic ◈", value=ctx.channel.topic, inline=False)
			e.add_field(name="◈ Created ◈", value=created.strftime(fmt), inline=False)
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def servericon(self, ctx):
		try:
			e=discord.Embed(color=0x80b0ff)
			e.set_image(url=ctx.guild.icon_url)
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def serverinfo(self, ctx):
		try:
			fmt = "%m/%d/%Y"
			created = datetime.date(ctx.guild.created_at)
			e=discord.Embed(description="id: {0}\nOwner: {1}".format(ctx.guild.id, ctx.guild.owner.name), color=0x0000ff)
			e.set_author(name="{0}:".format(ctx.guild.name), icon_url=ctx.guild.owner.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="◈ Main", value="• AFK Timeout [{}]\n• Region [{}]\n• Members [{}]".format(ctx.guild.afk_timeout, ctx.guild.region, ctx.guild.member_count), inline=False)
			e.add_field(name="◈ Security", value="• Explicit Content Filter: [{0}]\n• Verification Level: [{1}]\n• 2FA Level: [{2}]".format(ctx.guild.explicit_content_filter, ctx.guild.verification_level, ctx.guild.mfa_level), inline=False)
			e.add_field(name="◈ Created", value=created.strftime(fmt), inline=False)
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command(name="userinfo", aliases=["stalk"])
	async def userinfo(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			fmt = "%m/%d/%Y"
			created = datetime.date(member.created_at)
			perms = ', '.join(perm for perm, value in member.guild_permissions if value)
			e=discord.Embed(description="id: {}".format(member.id), color=0x80b0ff)
			e.set_author(name="{}:".format(member.name), icon_url=member.avatar_url)
			e.set_thumbnail(url=member.avatar_url)
			e.add_field(name="◈ Main ◈", value="• Nickname [{}]\n• Activity [{}]\n• Status [{}]\n• role [{}]".format(member.nick, member.activity, member.status, member.top_role), inline=False)
			e.add_field(name="◈ Perms ◈", value="```{}```".format(perms), inline=False)
			e.add_field(name="◈ Created ◈", value=created.strftime(fmt), inline=False)
			await ctx.send(embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def avatar(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			e=discord.Embed(color=0x80b0ff)
			e.set_image(url=member.avatar_url)
			await ctx.send("◈ {}'s avatar ◈".format(member), embed=e)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	async def owner(self, ctx):
		await ctx.send(ctx.guild.owner.name)

	@commands.command()
	async def topic(self, ctx):
		await ctx.send("{}".format(ctx.channel.topic))

	@commands.command()
	async def id(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			await ctx.send(member.id)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

def setup(bot):
	bot.add_cog(Core(bot))
