from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json
import time

class Whitelist:
	def __init__(self, bot):
		self.bot = bot
		self.images = {}
		self.cd = {}
		if isfile("./data/userdata/whitelist.json"):
			with open("./data/userdata/whitelist.json") as f:
				dat = json.load(f)
				if "images" in dat:
					self.images = dat["images"]

	def save_all(self):
		with open("./data/userdata/whitelist.json") as f:
			json.dump({"images": self.images}, f, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

	@commands.group(name="whitelist")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _whitelist(self, ctx):
		if ctx.invoked_subcommand is None:
			e = discord.Embed(color=colors.white())
			e.description = \
			"**Message Whitelisting (per-channel):**\n" \
			".whitelist disable whitelisted_object\n" \
			".whitelist images ~ `only allows images`"
			await ctx.send(embed=e)

	@_whitelist.command(name="disable")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_channels=True)
	async def _disable(self, ctx, object):
		channel_id = str(ctx.channel.id)
		object = object.lower()
		if object == "images":
			del self.images[channel_id]
		await ctx.message.add_reaction("👍")
		await ctx.send("Disabled channel limiter")
		self.save_all()

	@_whitelist.command(name="images")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(manage_channels=True)
	async def _images(self, ctx):
		channel_id = str(ctx.channel.id)
		if channel_id not in self.images[channel_id]:
			self.images[channel_id] = "enabled"
			await ctx.message.add_reaction("👍")
			await ctx.send(f"Limited **{ctx.channel.name}** to only allow images")
		else:
			del self.images[channel_id]
			await ctx.message.add_reaction("👍")
			await ctx.send("Disabled channel limiter")
		self.save_all()

	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			channel_id = str(m.channel.id)
			user_id = str(m.author.id)
			if m.content.lower().startswith(".whitelist"):
				return
			await asyncio.sleep(0.5)
			# image limiter
			if channel_id in self.images:
				if len(m.attachments) < 1:
					await m.delete()
					e = discord.Embed(color=colors.white())
					e.set_author(name=m.guild.name, icon_url=m.author.avatar_url)
					e.set_thumbnail(url=m.guild.icon_url)
					e.description = f"The channel `{m.channel.name}` is set to only " \
						f"allow images. If you have manage_guild permissions and would " \
						f"like this feature disabled use `.whitelist disable images` " \
						f"in the disabled channel`"
					if user_id not in self.cd:
						self.cd[user_id] = 0
					self.cd[user_id] = time.time() + 60
					if self.cd[user_id] < time.time():
						try:
							await m.author.send(embed=e)
						except:
							pass

def setup(bot):
	bot.add_cog(Whitelist(bot))
