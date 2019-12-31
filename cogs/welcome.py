from discord.ext import commands
from os.path import isfile
from utils import colors, utils
import discord
import asyncio
import random
import json
import os

class Welcome(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.channel = {}
		self.useimages = {}
		self.images = {}
		self.format = {}
		if isfile("./data/userdata/welcome.json"):
			with open("./data/userdata/welcome.json", "r") as f:
				dat = json.load(f)
				if "toggle" in dat:
					self.toggle = dat["toggle"]
					self.channel = dat["channel"]
					self.useimages = dat["useimages"]
					self.images = dat["images"]
					self.format = dat["format"]

	def save_data(self):
		with open("./data/userdata/welcome.json", "w") as f:
			json.dump({"toggle": self.toggle, "channel": self.channel, "useimages": self.useimages, "images": self.images,
			    "format": self.format}, f, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

	@commands.group(name="welcome", description="Welcomes users when they join")
	@commands.cooldown(1, 3, commands.BucketType.channel)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def _welcome(self, ctx):
		if not ctx.invoked_subcommand:
			guild_id = str(ctx.guild.id)
			toggle = "disabled"
			if guild_id in self.toggle:
				toggle = "enabled"
			e = discord.Embed(color=colors.tan())
			e.set_author(name="Welcome Messages", icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = "Welcomes users when they join"
			e.add_field(name="◈ Command Usage ◈", value=
				"__**Core:**__\n"
				".welcome enable\n"
				".welcome disable\n"
				".welcome config\n"
				".welcome test\n"
				"__**Utils:**__\n"
				".welcome setchannel\n"
				".welcome toggleimages\n"
				".welcome addimages\n"
				".welcome delimages\n"
				".welcome listimages\n"
				".welcome format\n", inline=False)
			images = ""
			if guild_id in self.images:
				images = f" | Custom Images: {len(self.images[guild_id])}"
			e.set_footer(text=f"Current Status: {toggle}{images}", icon_url=ctx.guild.owner.avatar_url)
			await ctx.send(embed=e)

	@_welcome.command(name="enable")
	@commands.has_permissions(manage_guild=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		messages = []
		if guild_id in self.toggle:
			return await ctx.send("This module is already enabled")
		async def cleanup():
			await ctx.message.delete()
			for msg in messages:
				await asyncio.sleep(1)
				await msg.delete()
		async def wait_for_msg():
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=30)
			except asyncio.TimeoutError:
				await cleanup()
			else:
				return msg
		msg = await ctx.send('Mention the channel I should use')
		messages.append(msg)
		completed = False
		while not completed:
			msg = await wait_for_msg()
			if not msg:
				return cleanup()
			messages.append(msg)
			if 'cancel' in msg.content.lower():
				return await cleanup()
			if len(msg.channel_mentions) < 1:
				msg = await ctx.send('That\'s not a channel mention, reply with "cancel" to stop')
				messages.append(msg)
				continue
			self.channel[guild_id] = msg.channel_mentions[0].id
			break
		msg = await ctx.send('Should I use images/gifs?')
		messages.append(msg)
		while not completed:
			msg = await wait_for_msg()
			if not msg:
				return cleanup()
			messages.append(msg)
			if 'cancel' in msg.content.lower():
				return await cleanup()
			if 'ye' in msg.content.lower():
				self.useimages[guild_id] = 'enabled'
				msg = await ctx.send('Aight, I\'ll use my own for now')
				messages.append(msg)
				break
			else:
				msg = await ctx.send('kk')
				messages.append(msg)
				break
		msg = await ctx.send('Now to set a message format:```css\nExample:\nWelcome !user to !server```')
		messages.append(msg)
		while not completed:
			msg = await wait_for_msg()
			if not msg:
				return cleanup()
			messages.append(msg)
			if 'cancel' in msg.content.lower():
				return await cleanup()
			msg = await ctx.channel.fetch_message(msg.id)
			self.format[guild_id] = msg.content
			break
		self.toggle[guild_id] = 'enabled'
		e = discord.Embed(color=colors.tan())
		e.set_author(name="Enabled Welcome Messages", icon_url=ctx.author.avatar_url)
		await ctx.send(embed=e, delete_after=10)
		await cleanup()
		self.save_data()

	@_welcome.command(name="disable")
	@commands.has_permissions(manage_guild=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.toggle:
			return await ctx.send("This module isn't enabled")
		del self.toggle[guild_id]
		await ctx.send("Disabled welcome messages")
		self.save_data()

	@_welcome.command(name="config")
	async def _config(self, ctx):
		guild_id = str(ctx.guild.id)
		toggle = "disabled"
		channel = "none"
		useimages = "disabled"
		images = 0
		format = "none"
		if guild_id in self.toggle:
			toggle = "enabled"
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id]).mention
		if guild_id in self.useimages:
			useimages = self.useimages[guild_id]
		if guild_id in self.format:
			format = self.format[guild_id]
		if guild_id in self.images:
			images = len(self.images[guild_id])
		e = discord.Embed(color=colors.tan())
		e.set_author(name="Welcome Config", icon_url=self.bot.user.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"**Toggle:** {toggle}\n" \
			f"**Channel:** {channel}\n" \
			f"**Images:** {useimages}\n" \
			f"**Custom Images:** {images}\n" \
			f"**Format:** {format}\n"
		await ctx.send(embed=e)

	@_welcome.command(name='test')
	async def _test(self, ctx):
		guild_id = str(ctx.guild.id)
		m = ctx.author
		channel = ctx.channel
		if guild_id not in self.format:
			return await ctx.send('You need to set the welcome msg format first')
		msg = self.format[guild_id]
		msg = msg.replace("$MENTION", m.mention).replace("$SERVER", m.guild.name)
		msg = msg.replace('!user', m.mention).replace('!server', m.guild.name)
		path = os.getcwd() + "/data/images/reactions/welcome/" + random.choice(
			os.listdir(os.getcwd() + "/data/images/reactions/welcome/"))
		if guild_id in self.useimages:
			e = discord.Embed(color=colors.fate())
			if guild_id in self.images:
				if self.images[guild_id]:
					e.set_image(url=random.choice(self.images[guild_id]))
					try:
						await channel.send(msg, embed=e)
					except discord.errors.Forbidden:
						del self.useimages[guild_id]
						del self.images[guild_id]
						self.save_data()
			else:
				e.set_image(url="attachment://" + os.path.basename(path))
				try:
					await channel.send(msg, file=discord.File(path, filename=os.path.basename(path)), embed=e)
				except discord.errors.Forbidden:
					del self.useimages[guild_id]
					self.save_data()
		else:
			try:
				await channel.send(msg)
			except discord.errors.Forbidden:
				del self.toggle[guild_id]
				self.save_data()

	@_welcome.command(name="setchannel")
	@commands.has_permissions(manage_guild=True)
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		guild_id = str(ctx.guild.id)
		if not channel:
			channel = ctx.channel
		self.channel[guild_id] = channel.id
		await ctx.send(f"Set the welcome message channel to {channel.mention}")
		self.save_data()

	@_welcome.command(name="toggleimages")
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(attach_files=True)
	async def _toggle_images(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.useimages:
			del self.useimages[guild_id]
			await ctx.send("Disabled Images")
			return self.save_data()
		self.useimages[guild_id] = "enabled"
		if guild_id in self.images:
			await ctx.send("Enabled Images")
		else:
			await ctx.send("Enabled Images. You have no custom "
			    "images so I'll just use my own for now")
		self.save_data()

	@_welcome.command(name="addimages")
	@commands.has_permissions(manage_guild=True)
	async def _addimages(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.images:
			self.images[guild_id] = []
		if not ctx.message.attachments:
			complete = False
			await ctx.send('Send the image(s) you\'d like to use\nReply with "done" when finished')
			while complete is False:
				msg = await utils.Bot(self.bot).wait_for_msg(ctx)  # type: discord.Message
				if msg:
					if msg.content:
						if "done" in msg.content.lower():
							return await ctx.send("Added your images 👍")
					for attachment in msg.attachments:
						self.images[guild_id].append(attachment.url)
		for attachment in ctx.message.attachments:
			self.images[guild_id].append(attachment.url)
		if len(self.images[guild_id]) > 0:
			await ctx.send("Added your image(s)")
		else:
			await ctx.send('No worries, I\'ll just keep using my own gifs for now')
			del self.images[guild_id]
		self.save_data()

	@_welcome.command(name="delimages")
	@commands.has_permissions(manage_guild=True)
	async def _delimages(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.images:
			return await ctx.send("No images >:(")
		del self.images[guild_id]
		await ctx.send("Purged images")
		self.save_data()

	@_welcome.command(name="listimages")
	@commands.has_permissions(manage_guild=True)
	async def _listimages(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.images:
			return await ctx.send("This guild has no images")
		await ctx.send(self.images[guild_id])

	@_welcome.command(name="format")
	@commands.has_permissions(manage_guild=True)
	async def _format(self, ctx, *, message=None):
		guild_id = str(ctx.guild.id)
		if message:
			self.format[guild_id] = message
		else:
			await ctx.send('What format should I use?:```css\nExample:\nWelcome !user to !server```')
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=30)
			except asyncio.TimeoutError:
				await ctx.send("Timeout error")
			else:
				msg = await self.bot.fetch_message(msg.id)
				self.format[guild_id] = msg.content
		await ctx.send("Set the welcome format 👍")
		self.save_data()

	@commands.Cog.listener()
	async def on_member_join(self, m: discord.Member):
		if isinstance(m.guild, discord.Guild):
			guild_id = str(m.guild.id)
			if guild_id in self.toggle:
				try:
					channel = self.bot.get_channel(self.channel[guild_id])
				except:
					del self.toggle[guild_id]
					return self.save_data()
				msg = self.format[guild_id]
				msg = msg.replace("$MENTION", m.mention).replace("$SERVER", m.guild.name)
				msg = msg.replace('!user', m.mention).replace('!server', m.guild.name)
				path = os.getcwd() + "/data/images/reactions/welcome/" + random.choice(
					os.listdir(os.getcwd() + "/data/images/reactions/welcome/"))
				if guild_id in self.useimages:
					e = discord.Embed(color=colors.fate())
					if guild_id in self.images:
						e.set_image(url=random.choice(self.images[guild_id]))
						try:
							await channel.send(msg, embed=e)
						except discord.errors.Forbidden:
							del self.useimages[guild_id]
							del self.images[guild_id]
							self.save_data()
						else:
							pass
					else:
						e.set_image(url="attachment://" + os.path.basename(path))
						try:
							await channel.send(msg, file=discord.File(path, filename=os.path.basename(path)), embed=e)
						except discord.errors.Forbidden:
							del self.useimages[guild_id]
							self.save_data()
						else:
							pass
				else:
					try:
						await channel.send(msg)
					except discord.errors.Forbidden:
						del self.toggle[guild_id]
						self.save_data()
					else:
						pass

def setup(bot):
	bot.add_cog(Welcome(bot))
