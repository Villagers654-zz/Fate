from utils.utils import bytes2human
from discord.ext import commands
from datetime import datetime
import aiohttp
import asyncio
import random
from io import BytesIO
import requests
import json
import os
import time
import platform

import discord
from PIL import Image
from colormap import rgb2hex
import psutil

from utils import colors, utils, bytes2human as p, config

class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.find = {}
		self.afk = {}

	def avg_color(self, url):
		"""Gets an image and returns the average color"""
		if not url:
			return colors.fate()
		im = Image.open(BytesIO(requests.get(url).content)).convert('RGBA')
		pixels = list(im.getdata())
		r = g = b = c = 0
		for pixel in pixels:
			brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
			if pixel[3] > 64 and brightness > 80:
				r += pixel[0]
				g += pixel[1]
				b += pixel[2]
				c += 1
		r = r / c; g = g / c; b = b / c
		return eval('0x' + rgb2hex(round(r), round(g), round(b)).replace('#', ''))

	async def wait_for_dismissal(self, ctx, msg):
		def pred(m):
			return m.channel.id == ctx.channel.id and m.content.lower().startswith('k')
		try:
			reply = await self.bot.wait_for('message', check=pred, timeout=25)
		except asyncio.TimeoutError:
			pass
		else:
			await asyncio.sleep(0.21)
			await ctx.message.delete()
			await asyncio.sleep(0.21)
			await msg.delete()
			await asyncio.sleep(0.21)
			await reply.delete()

	@commands.command(name='info', cog='utility')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def info(self, ctx, target=None):
		"""Returns information for invites, users, roles & channels"""
		if not target:  # bot stats/info
			m, s = divmod(time.time() - self.bot.START_TIME, 60)
			h, m = divmod(m, 60)
			guilds = len(list(self.bot.guilds))
			users = len(list(self.bot.users))
			path = os.getcwd() + "/data/images/banners/" + random.choice(
				os.listdir(os.getcwd() + "/data/images/banners/"))
			bot_pid = psutil.Process(os.getpid())
			e = discord.Embed(color=colors.fate())
			e.set_author(name="Fate [Zerø]: Core Info", icon_url=self.bot.get_user(config.owner_id()).avatar_url)
			stats = self.bot.get_stats  # type: dict
			commands = 0;
			lines = 0
			for command_date in stats['commands']:
				date = datetime.strptime(command_date, '%Y-%m-%d %H:%M:%S.%f')
				if (datetime.now() - date).days < 7:
					commands += 1
				else:
					index = stats['commands'].index(command_date)
					stats['commands'].pop(index)
					with open('./data/stats.json', 'w') as f:
						json.dump(stats, f, ensure_ascii=False)
			with open('fate.py', 'r') as f:
				lines += len(f.readlines())
			for file in os.listdir('cogs'):
				if file.endswith('.py'):
					with open(f'./cogs/{file}', 'r') as f:
						lines += len(f.readlines())
			e.description = f'Weekly Commands Used: {commands}\n' \
				f'Total lines of code: {lines}'
			e.set_thumbnail(url=self.bot.user.avatar_url)
			e.set_image(url="attachment://" + os.path.basename(path))
			e.add_field(name="◈ Summary ◈",  value="Fate is a ~~multipurpose~~ hybrid bot created for ~~sexual assault~~ fun", inline=False)
			e.add_field(name="◈ Statistics ◈", value=f'Commands: [{len(self.bot.commands)}]\nModules: [{len(self.bot.extensions)}]\nServers: [{guilds}]\nUsers: [{users}]')
			e.add_field(name="◈ Credits ◈", value="• Tothy ~ `rival`\n• Cortex ~ `teacher`\n• Discord.py ~ `existing`")
			e.add_field(name="◈ Memory ◈", value=
				f"__**Storage**__: [{p.bytes2human(psutil.disk_usage('/').used)}/{p.bytes2human(psutil.disk_usage('/').total)}]\n"
				f"__**RAM**__: [{p.bytes2human(psutil.virtual_memory().used)}/{p.bytes2human(psutil.virtual_memory().total)}] ({psutil.virtual_memory().percent}%)\n"
				f"__**Bot RAM**__: {p.bytes2human(bot_pid.memory_full_info().rss)} ({round(bot_pid.memory_percent())}%)\n"
				f"__**CPU**__: **Global**: {psutil.cpu_percent()}% **Bot**: {bot_pid.cpu_percent()}%\n")
			e.add_field(name="◈ Uptime ◈", value="Uptime: {} Hours {} Minutes {} seconds".format(int(h), int(m), int(s)))
			e.set_footer(text=f"Powered by Python {platform.python_version()} and Discord.py {discord.__version__}", icon_url="https://cdn.discordapp.com/attachments/501871950260469790/567779834533773315/RPrw70n.png")
			msg = await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
			return await self.wait_for_dismissal(ctx, msg)
		if 'discord.gg' in target:
			code = discord.utils.resolve_invite(target)
			try:
				invite = await self.bot.fetch_invite(code)
			except discord.errors.Forbidden:
				return await ctx.send('Failed to resolve invite url')
			guild = invite.guild
			e = discord.Embed(color=colors.red() if invite.revoked else colors.fate())
			e.set_thumbnail(url=guild.splash_url if guild.splash_url else guild.icon_url)
			e.set_author(name=f'{invite.guild.name}:', icon_url=guild.icon_url)
			created = datetime.date(guild.created_at)
			e.description = f'◈ SID: [`{guild.id}`]\n' \
			    f'◈ Inviter: [`{invite.inviter if invite.inviter else "unknown#0000"}`]\n' \
				f'◈ Member Count: [`{invite.approximate_member_count}`]\n' \
				f'◈ Online Members: [`{invite.approximate_presence_count}`]\n' \
				f'◈ Channel: [`#{invite.channel.name}`]\n' \
				f'◈ CID: [`{invite.channel.id}`]\n' \
				f'◈ Verification Level: [`{guild.verification_level}`]\n' \
				f'◈ Created: [`{created.strftime("%m/%d/%Y")}`]'
			if guild.banner_url:
				e.set_image(url=guild.banner_url)
			uses = invite.uses if isinstance(invite.uses, int) else '-'
			lmt = invite.max_uses if invite.max_uses else '-'
			e.set_footer(text=f'Uses: [{uses}/{lmt}]')
			return await ctx.send(embed=e)
		if ctx.message.mentions:  # user mentions
			user = ctx.message.mentions[0]
			icon_url = user.avatar_url if user.avatar_url else self.bot.user.avatar_url
			try: e = discord.Embed(color=self.avg_color(user.avatar_url))
			except ZeroDivisionError: e = discord.Embed(color=user.top_role.color)
			e.set_author(name=user.display_name, icon_url=icon_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = f'__**ID:**__ {user.id}\n{f"Active On Mobile" if user.is_on_mobile() else ""}'
			main = f'{f"**• Nickname** [`{user.nick}`]" if user.nick else ""}\n' \
				f'**• Activity** [`{user.activity.name if user.activity else None}`]\n' \
				f'**• Status** [`{user.status}`]\n' \
				f'**• Role** [{user.top_role.mention}]'
			e.add_field(name='◈ Main ◈', value=main, inline=False)
			roles = ['']; index = 0
			for role in sorted(user.roles, reverse=True):
				if len(roles[index]) + len(role.mention) + 2 > 1000:
					roles.append('')
					index += 1
				roles[index] += f'{role.mention} '
			for role_list in roles:
				index = roles.index(role_list)
				e.add_field(name=f'◈ Roles ◈ ({len(user.roles)})' if index is 0 else '~', value=role_list, inline=False)
			permissions = user.guild_permissions
			notable = ['view_audit_log', 'manage_roles', 'manage_channels', 'manage_emojis',
				'kick_members', 'ban_members', 'manage_messages', 'mention_everyone']
			perms = ', '.join(perm for perm, value in permissions if value and perm in notable)
			perms = 'administrator' if permissions.administrator else perms
			if perms: e.add_field(name='◈ Perms ◈', value=perms, inline=False)
			e.add_field(name='◈ Created ◈', value=datetime.date(user.created_at).strftime("%m/%d/%Y"), inline=False)
			return await ctx.send(embed=e)
		if ctx.message.channel_mentions:
			channel = ctx.message.channel_mentions[0]
			e = discord.Embed(description=f'ID: {channel.id}', color=0x0000ff)
			e.set_author(name=f'{channel.name}:', icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.add_field(name="◈ Main ◈", value=f'• Category: {channel.category}\n• Slowmode: {channel.slowmode_delay}', inline=True)
			if channel.topic:
				e.add_field(name="◈ Topic ◈", value=channel.topic, inline=True)
			e.add_field(name="◈ Created ◈", value=datetime.date(channel.created_at).strftime("%m/%d/%Y"), inline=True)
			return await ctx.send(embed=e)
		role = await utils.get_role(ctx, target)
		if not isinstance(role, discord.Role):
			return
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
		e.add_field(name="◈ Perms ◈", value=f"```{perms if perms else 'None'}```", inline=False)
		e.add_field(name="◈ Created ◈", value=datetime.date(role.created_at).strftime('%m/%d/%Y'), inline=False)
		await ctx.send(embed=e)

	@commands.command(name='serverinfo', aliases=['sinfo'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def serverinfo(self, ctx):
		try: e = discord.Embed(color=self.avg_color(ctx.guild.icon_url))
		except ZeroDivisionError: e = discord.Embed(color=colors.fate())
		e.description = f'id: {ctx.guild.id}\nOwner: {ctx.guild.owner}'
		e.set_author(name=f'{ctx.guild.name}:', icon_url=ctx.guild.owner.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		main = f'• AFK Timeout [`{ctx.guild.afk_timeout}`]\n' \
			f'• Region [`{ctx.guild.region}`]\n' \
			f'• Members [`{ctx.guild.member_count}`]'
		e.add_field(name='◈ Main ◈', value=main, inline=False)
		security = f'• Explicit Content Filter: [`{ctx.guild.explicit_content_filter}`]\n' \
			f'• Verification Level: [`{ctx.guild.verification_level}`]\n' \
			f'• 2FA Level: [`{ctx.guild.mfa_level}`]'
		e.add_field(name='◈ Security ◈', value=security, inline=False)
		if ctx.guild.premium_tier:
			perks = f'• Boost Level [`{ctx.guild.premium_tier}`]\n' \
				f'• Total Boosts [`{len(ctx.guild.premium_subscribers)}`]\n' \
				f'• Max Emoji\'s [`{ctx.guild.emoji_limit}`]\n' \
				f'• Max Bitrate [`{bytes2human(ctx.guild.bitrate_limit).replace(".0", "")}`]\n' \
				f'• Max Filesize [`{bytes2human(ctx.guild.filesize_limit).replace(".0", "")}`]'
			e.add_field(name='◈ Perks ◈', value=perks, inline=False)
		created = datetime.date(ctx.guild.created_at)
		e.add_field(name='◈ Created ◈', value=created.strftime('%m/%d/%Y'), inline=False)
		await ctx.send(embed=e)

	@commands.command(name='servericon', aliases=['icon'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def servericon(self, ctx):
		e=discord.Embed(color=0x80b0ff)
		e.set_image(url=ctx.guild.icon_url)
		await ctx.send(embed=e)

	@commands.command(name='makepoll', aliases=['mp'])
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.has_permissions(add_reactions=True)
	@commands.bot_has_permissions(add_reactions=True)
	async def makepoll(self, ctx):
		async for msg in ctx.channel.history(limit=2):
			if msg.id != ctx.message.id:
				await msg.add_reaction(':approve:506020668241084416')
				await msg.add_reaction(':unapprove:506020690584010772')
				return await ctx.message.delete()

	@commands.command(name='members', aliases=['membercount'])
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def members(self, ctx):
		humans = 0; bots = 0; online = 0
		for member in ctx.guild.members:
			if member.bot:
				bots += 1
			else:
				humans += 1
			status_list = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
			if member.status in status_list:
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
			user = ctx.author.mention
		user = utils.get_user(ctx, user)
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

	@commands.command(name='topic')
	@commands.cooldown(1, 10, commands.BucketType.channel)
	@commands.guild_only()
	async def topic(self, ctx):
		if not ctx.channel.topic:
			return await ctx.send('This channel has no topic')
		await ctx.send(ctx.channel.topic)

	@commands.command(name='color', aliases=['setcolor', 'changecolor'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	async def color(self, ctx, *args):
		if len(args) == 0:
			color = colors.random()
			e = discord.Embed(color=color)
			e.set_author(name=f"#{color}", icon_url=ctx.author.avatar_url)
			return await ctx.send(embed=e)
		if len(args) == 1:
			hex = args[0]
			hex = hex.replace('#', '')
			e = discord.Embed(color=eval(f"0x{hex}"))
			return await ctx.send(embed=e)
		if not ctx.author.guild_permissions.manage_roles:
			return await ctx.send('You need manage roles permissions to use this')
		role = await utils.get_role(ctx, args[0])
		hex = discord.Color(eval('0x' + args[1].replace('#', '')))
		if role.position >= ctx.author.top_role.position:
			return await ctx.send('That roles above your paygrade, take a seat')
		previous_color = role.color
		await role.edit(color=hex)
		await ctx.send(f'Changed {role.name}\'s color from {previous_color} to {hex}')

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

	@commands.command(name='findmsg')
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

	@commands.command(name='poll')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True, add_reactions=True)
	async def poll(self, ctx, *, arg):
		e = discord.Embed(description=arg, color=0x80b0ff)
		e.set_author(name="| {} |".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		message = await ctx.send(embed=e)
		await message.add_reaction(':approve:506020668241084416')
		await asyncio.sleep(0.5)
		await message.add_reaction(':unapprove:506020690584010772')
		await asyncio.sleep(0.5)
		await message.add_reaction('🤷')
		await ctx.message.delete()

	@commands.command(name='id')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def id(self, ctx, *, user=None):
		if user:
			user = utils.get_user(ctx, user)
			if not user:
				return await ctx.send('User not found')
			return await ctx.send(user.id)
		for user in ctx.message.mentions:
			return await ctx.send(user.id)
		for channel in ctx.message.channel_mentions:
			return await ctx.send(channel.id)
		e = discord.Embed(color=colors.fate())
		e.description = f'{ctx.author.mention}: {ctx.author.id}\n' \
			f'{ctx.channel.mention}: {ctx.channel.id}'
		await ctx.send(embed=e)

	@commands.command(name='estimate-inactives')
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(kick_members=True)
	async def estimate_inactives(self, ctx, days: int):
		inactive_count = await ctx.guild.estimate_pruned_members(days=days)
		e = discord.Embed(color=colors.fate())
		e.description = f'Inactive Users: {inactive_count}'
		await ctx.send(embed=e)

	@commands.command(name='afk')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def afk(self, ctx, *, reason='afk'):
		if ctx.message.mentions or ctx.message.role_mentions:
			return await ctx.send('nO')
		e = discord.Embed(color=colors.fate())
		e.set_author(name='You are now afk', icon_url=ctx.author.avatar_url)
		await ctx.send(embed=e, delete_after=5)
		self.afk[str(ctx.author.id)] = reason
		await asyncio.sleep(5)
		await ctx.message.delete()

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.bot: return
		user_id = str(msg.author.id)
		if user_id in self.afk:
			del self.afk[user_id]
			await msg.channel.send('removed your afk', delete_after=3)
		else:
			for user in msg.mentions:
				user_id = str(user.id)
				if user_id in self.afk:
					replies = ['shh', 'shush', 'shush child', 'stfu cunt', 'nO']
					choice = random.choice(replies)
					await msg.channel.send(f'{choice} he\'s {self.afk[user_id]}')

def setup(bot):
	bot.add_cog(Utility(bot))
