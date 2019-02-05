from discord.ext import commands
from datetime import datetime
from cogs.utils import colors
import requests
import discord
import aiohttp
import asyncio

class Utility:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def channelinfo(self, ctx, channel=None):
		if channel is None:
			ctx.channel = ctx.channel
		else:
			ctx.channel = channel
		fmt = "%m/%d/%Y"
		created = datetime.date(ctx.channel.created_at)
		e=discord.Embed(description="id: {}".format(ctx.channel.id), color=0x0000ff)
		e.set_author(name="{}:".format(ctx.channel.name), icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Main ◈", value="• Category: {}\n• Slowmode: {}".format(ctx.channel.category, ctx.channel.slowmode_delay), inline=False)
		e.add_field(name="◈ Topic ◈", value=ctx.channel.topic, inline=False)
		e.add_field(name="◈ Created ◈", value=created.strftime(fmt), inline=False)
		await ctx.send(embed=e)

	@commands.command()
	async def servericon(self, ctx):
		e=discord.Embed(color=0x80b0ff)
		e.set_image(url=ctx.guild.icon_url)
		await ctx.send(embed=e)

	@commands.command()
	async def serverinfo(self, ctx):
		fmt = "%m/%d/%Y"
		created = datetime.date(ctx.guild.created_at)
		e=discord.Embed(description="id: {0}\nOwner: {1}".format(ctx.guild.id, ctx.guild.owner.name), color=0x0000ff)
		e.set_author(name="{0}:".format(ctx.guild.name), icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Main", value="• AFK Timeout [{}]\n• Region [{}]\n• Members [{}]".format(ctx.guild.afk_timeout, ctx.guild.region, ctx.guild.member_count), inline=False)
		e.add_field(name="◈ Security", value="• Explicit Content Filter: [{0}]\n• Verification Level: [{1}]\n• 2FA Level: [{2}]".format(ctx.guild.explicit_content_filter, ctx.guild.verification_level, ctx.guild.mfa_level), inline=False)
		e.add_field(name="◈ Created", value=created.strftime(fmt), inline=False)
		await ctx.send(embed=e)

	@commands.command(name="userinfo", aliases=["stalk"])
	async def userinfo(self, ctx, *, member: discord.Member=None):
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

	@commands.command(name="addemoji", aliases=["emote", "addemote"])
	@commands.has_permissions(manage_emojis=True)
	async def _addemoji(self, ctx, *, name=None):
		try:
			if len(ctx.message.attachments) > 1:
				for attachment in ctx.message.attachments:
					name = attachment[:str(attachment.filename).lower().find(".")].replace(" ", "")[:32]
					await ctx.guild.create_custom_emoji(name=name, image=requests.get(attachment.url).content,
					                                    reason=ctx.author.name)
					await ctx.send(f"successfully added `{name}` to emotes")
			else:
				if name is None:
					for attachment in ctx.message.attachments:
						name = attachment[:str(attachment.filename).lower().find(".")].replace(" ", "")[:32]
						await ctx.guild.create_custom_emoji(name=name, image=requests.get(attachment.url).content,
						                                    reason=ctx.author.name)
						await ctx.send(f"Successfully added `{name}` to emotes")
				else:
					for attachment in ctx.message.attachments:
						name = name[:32].replace(" ", "")
						await ctx.guild.create_custom_emoji(name=name, image=requests.get(attachment.url).content,
						                                    reason=ctx.author.name)
						await ctx.send(f"Successfully added `{name}` to emotes")
		except Exception as HTTPException:
			for attachment in ctx.message.attachments:
				attachment = attachment
			e = discord.Embed(color=colors.theme())
			e.set_author(name=f"File cannot be larger than 256 kb", icon_url=attachment.proxy_url)
			e.set_thumbnail(url=ctx.author.avatar_url)
			e.description = f"Try using [TinyPNG](https://tinypng.com/) to reduce the size"
			await ctx.send(embed=e)

	@commands.command(name="delemoji", aliases=["delemote"])
	@commands.has_permissions(manage_emojis=True)
	async def _delemoji(self, ctx, *, name):
		check = 0
		for emote in ctx.guild.emojis:
			if name.lower() == emote.name.lower():
				await emote.delete(reason=ctx.author.name)
				await ctx.send(f"Deleted emote `{emote.name}`")
				check = 1
				break
		if check == 0:
			for emote in ctx.guild.emojis:
				if name.lower() in emote.name.lower():
					await emote.delete(reason=ctx.author.name)
					await ctx.send(f"Deleted emote `{emote.name}`")
					check = 1
					break
		if check == 0:
			await ctx.send("I couldnt find that emote")

	@commands.command(name='makepoll', aliases=['mp'])
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.has_permissions(manage_messages=True)
	async def makepoll(self, ctx):
		c = 0
		async for msg in ctx.channel.history(limit=3):
			if c == 1:
				await msg.add_reaction(':approve:506020668241084416')
				await msg.add_reaction(':unapprove:506020690584010772')
				await ctx.message.delete()
				break;
			c += 1

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

	@commands.command()
	async def id(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			await ctx.send(member.id)
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

def setup(bot):
	bot.add_cog(Utility(bot))
