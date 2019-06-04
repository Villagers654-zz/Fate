from discord.ext import commands
from datetime import datetime
from utils import colors
import discord
import aiohttp
import asyncio
import random

class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.find = {}
		self.afk = {}

	def get_user(self, ctx, user):
		if user.startswith("<@"):
			for char in list(user):
				if char not in list('1234567890'):
					user = user.replace(str(char), '')
			return ctx.guild.get_member(int(user))
		else:
			user = user.lower()
			for member in ctx.guild.members:
				if user == member.name.lower():
					return member
			for member in ctx.guild.members:
				if user == member.display_name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.name.lower():
					return member
			for member in ctx.guild.members:
				if user in member.display_name.lower():
					return member
		return

	def get_role(self, ctx, name):
		if name.startswith("<@"):
			for char in list(name):
				if char not in list('1234567890'):
					name = name.replace(str(char), '')
			return ctx.guild.get_member(int(name))
		else:
			for role in ctx.guild.roles:
				if name == role.name.lower():
					return role
			for role in ctx.guild.roles:
				if name in role.name.lower():
					return role
			return

	@commands.command(name='servericon', aliases=['icon'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def servericon(self, ctx):
		e=discord.Embed(color=0x80b0ff)
		e.set_image(url=ctx.guild.icon_url)
		await ctx.send(embed=e)

	@commands.command(name='channelinfo', aliases=['cinfo'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def channelinfo(self, ctx, channel: discord.TextChannel=None):
		if not channel:
			channel = ctx.channel
		e = discord.Embed(description=f'ID: {channel.id}', color=0x0000ff)
		e.set_author(name=f'{channel.name}:', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.add_field(name="◈ Main ◈", value=f'• Category: {channel.category}\n• Slowmode: {channel.slowmode_delay}', inline=True)
		if channel.topic:
			e.add_field(name="◈ Topic ◈", value=channel.topic, inline=True)
		e.add_field(name="◈ Created ◈", value=datetime.date(channel.created_at).strftime("%m/%d/%Y"), inline=True)
		await ctx.send(embed=e)

	@commands.command(name='serverinfo', aliases=['sinfo'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
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

	@commands.command(name='userinfo', aliases=['uinfo'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def userinfo(self, ctx, *, user=None):
		if not user:
			user = ctx.author.name
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send('User not found')
		color = user.color if user.color else colors.fate()
		icon_url = user.avatar_url if user.avatar_url else self.bot.user.avatar_url
		e = discord.Embed(color=color)
		e.set_author(name=user.display_name, icon_url=icon_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f'__**ID:**__ {user.id}\n{f"Active On Mobile" if user.is_on_mobile() else ""}'
		main = f'{f"**• Nickname** [`{user.nick}]" if user.nick else ""}\n' \
			f'**• Activity** [`{user.activity.name if user.activity else None}`]\n' \
			f'**• Status** [`{user.status}`]\n' \
			f'**• Role** [{user.top_role.mention}]'
		e.add_field(name='◈ Main ◈', value=main, inline=False)
		permissions = user.guild_permissions
		notable = ['view_audit_log', 'manage_roles', 'manage_channels', 'manage_emojis',
		           'kick_members', 'ban_members', 'manage_messages', 'mention_everyone']
		perms = ', '.join(perm for perm, value in permissions if value and perm in notable)
		perms = 'administrator' if permissions.administrator else perms
		if perms:
			e.add_field(name='◈ Perms ◈', value=perms, inline=False)
		e.add_field(name='◈ Created ◈', value=datetime.date(user.created_at).strftime("%m/%d/%Y"), inline=False)
		await ctx.send(embed=e)

	@commands.command(name='roleinfo', aliases=['rinfo'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(manage_roles=True)
	@commands.bot_has_permissions(embed_links=True)
	async def roleinfo(self, ctx, *, role):
		role = self.get_role(ctx, role)
		if not role:
			return await ctx.send('Role not found')
		icon_url = ctx.guild.owner.avatar_url if ctx.guild.owner.avatar_url else self.bot.user.avatar_url
		e = discord.Embed(color=role.color)
		e.set_author(name=f"{role.name}:", icon_url=icon_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f'__**ID:**__ {role.id}'
		e.add_field(name="◈ Main ◈", value=f"**Members:** [{len(role.members)}]\n"
			f"**Color:** [{role.color}]\n"
			f"**Mentionable:** [{role.mentionable}]\n"
			f"**Integrated:** [{role.managed}]\n"
			f"**Position:** [{role.position}]\n", inline=False)
		notable = ['view_audit_log', 'manage_roles', 'manage_channels', 'manage_emojis',
		           'kick_members', 'ban_members', 'manage_messages', 'mention_everyone']
		perms = ', '.join(perm for perm, value in role.permissions if value and perm in notable)
		perms = 'administrator' if role.permissions.administrator else perms
		e.add_field(name="◈ Perms ◈", value=f"```{perms}```", inline=False)
		e.add_field(name="◈ Created ◈", value=datetime.date(role.created_at).strftime('%m/%d/%Y'), inline=False)
		await ctx.send(embed=e)

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

	@commands.command(name='members', aliases=['membercount'])
	@commands.bot_has_permissions(embed_links=True)
	async def members(self, ctx):
		humans = 0
		bots = 0
		online = 0
		for member in ctx.guild.members:
			if member.bot:
				bots += 1
			else:
				humans += 1
			status_array = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
			if member.status in status_array:
				online += 1
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"Member Count", icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f'**Total:** [`{ctx.guild.member_count}`]\n' \
			f'**Online:** [`{online}`]\n' \
			f'**Humans:** [`{humans}`]\n' \
			f'**Bots:** [`{bots}`]'
		await ctx.send(embed=e)

	@commands.command(name='tinyurl')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
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

	@commands.command(name='avatar', aliases=['av'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def avatar(self, ctx, *, user=None):
		if not user:
			user = ctx.author.name
		user = self.get_user(ctx, user)
		if not isinstance(user, discord.Member):
			return await ctx.send('User not found')
		if not user.avatar_url:
			return await ctx.send(f'{user.display_name} doesn\'t have an avatar')
		e=discord.Embed(color=0x80b0ff)
		e.set_image(url=user.avatar_url)
		await ctx.send(f'◈ {user.display_name}\'s avatar ◈', embed=e)

	@commands.command(name='owner')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def owner(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.description = f'**Server Owner:** {ctx.guild.owner.mention}'
		await ctx.send(embed=e)

	@commands.command()
	async def topic(self, ctx):
		await ctx.send("{}".format(ctx.channel.topic))

	@commands.command(name='color')
	async def color(self, ctx, hex=None):
		if hex:
			hex = hex.replace('#', '')
			e = discord.Embed(color=eval(f"0x{hex}"))
			await ctx.send(embed=e)
		else:
			color = colors.random()
			e = discord.Embed(color=color)
			e.set_author(name=f"#{color}", icon_url=ctx.author.avatar_url)
			await ctx.send(embed=e)

	@commands.command(name="timer", pass_context=True, aliases=['reminder', 'alarm'])
	async def _timer(self, ctx, time, *, remember: commands.clean_content = ""):
		if "d" in time:
			t = int(time.replace("d", "")) * 60 * 60 * 24
		if "h" in time:
			t = int(time.replace("h", "")) * 60 * 60
		if "m" in time:
			t = int(time.replace("m", "")) * 60
		r = time.replace("m", " minutes").replace("1 minutes", "1 minute")
		r = r.replace("h", " hours").replace("1 hours", "1 hour")
		r = r.replace("d", " days").replace("1 days", "1 day")
		if not remember:
			await ctx.send(f"{ctx.author.name}, you have set a timer for {r}")
			await asyncio.sleep(float(t))
			await ctx.send(f"{ctx.author.name}, your timer for {r} has expired!")
		else:
			await ctx.send(f"{ctx.message.author.mention}, I will remind you about `{remember}` in {r}")
			await asyncio.sleep(float(t))
			await ctx.send(f"{ctx.message.author.mention}, your timer for {r} has expired! I was instructed to remind you about `{remember}`!")

	@commands.command(name="findmsg")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	async def _findmsg(self, ctx, *, content=None):
		if content is None:
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Error ⚠", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = \
				"Content is a required argument\n" \
			    "Usage: `.find {content}`\n" \
				"Limit: 16,000"
			e.set_footer(text="Searches for a message")
			return await ctx.send(embed=e)
		async with ctx.typing():
			channel_id = str(ctx.channel.id)
			if channel_id in self.find:
				return await ctx.send("I'm already searching")
			self.find[channel_id] = True
			async for msg in ctx.channel.history(limit=25000):
				if ctx.message.id != msg.id:
					if content.lower() in msg.content.lower():
						e = discord.Embed(color=colors.fate())
						e.set_author(name="Message Found 🔍", icon_url=ctx.author.avatar_url)
						e.set_thumbnail(url=ctx.guild.icon_url)
						e.description = f"**Author:** `{msg.author}`\n" \
							f"[Jump to MSG]({msg.jump_url})"
						if msg.content != "":
							e.add_field(name="Full Content:", value=msg.content)
						if len(msg.attachments) > 0:
							for attachment in msg.attachments:
								e.set_image(url=attachment.url)
						await ctx.send(embed=e)
						del self.find[channel_id]
						return await ctx.message.delete()
		await ctx.send("Nothing found")
		del self.find[channel_id]

	@commands.command()
	async def poll(self, ctx, *, arg):
		e=discord.Embed(description=arg, color=0x80b0ff)
		e.set_author(name="| {} |".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		message = await ctx.send(embed=e)
		await message.add_reaction(':approve:506020668241084416')
		await asyncio.sleep(0.5)
		await message.add_reaction(':unapprove:506020690584010772')
		await asyncio.sleep(0.5)
		await message.add_reaction('🤷')
		await ctx.message.delete()

	@commands.command()
	async def id(self, ctx, *, member: discord.Member=None):
		if member is None:
			member = ctx.author
		await ctx.send(member.id)

	@commands.command(name="channels")
	async def _channels(self, ctx):
		channels = ""
		for channel in ctx.guild.channels:
			channels += channel.name + "\n"
		await ctx.send(channels)

	@commands.command(name='afk')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def afk(self, ctx, *, reason='unspecified'):
		e = discord.Embed(color=colors.fate())
		e.set_author(name='You are now afk', icon_url=ctx.author.avatar_url)
		await ctx.send(embed=e, delete_after=5)
		self.afk[str(ctx.author.id)] = reason
		await asyncio.sleep(5)
		await ctx.message.delete()

	@commands.Cog.listener()
	async def on_message(self, msg):
		user_id = str(msg.author.id)
		if user_id in self.afk:
			del self.afk[user_id]
			await msg.channel.send('removed your afk', delete_after=3)
		else:
			for user in msg.mentions:
				user_id = str(user.id)
				if user_id in self.afk:
					choice = random.choice(['shh', 'shush', 'stfu cunt', 'nO'])
					await msg.channel.send(f'{choice} he\'s {self.afk[user_id]}', delete_after=10)

def setup(bot):
	bot.add_cog(Utility(bot))
