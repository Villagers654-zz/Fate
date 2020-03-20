from os.path import isfile
import json
import asyncio
import requests
from discord.ext import commands
import discord
from PIL import Image
from utils import colors


class EmojiChannel(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.channel = {}
		self.file_path = './data/emoji_channel.json'
		if isfile(self.file_path):
			with open(self.file_path, 'r') as f:
				self.channel = json.load(f)


	def save_data(self):
		with open(self.file_path, 'w') as f:
			json.dump(self.channel, f, ensure_ascii=False)


	@commands.group(name='emoji-channel')
	@commands.bot_has_permissions(embed_links=True)
	async def emoji_channel(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Usage', icon_url=ctx.author.avatar_url)
			e.description = '.emoji-channel enable\n.emoji-channel disable'
			await ctx.send(embed=e)

	@emoji_channel.command(name='enable')
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	async def _enable(self, ctx):
		self.channel[str(ctx.guild.id)] = ctx.channel.id
		await ctx.send(f'Enabled emoji-channel in {ctx.channel.mention}')
		self.save_data()

	@emoji_channel.command(name='disable')
	@commands.has_permissions(manage_emojis=True)
	@commands.bot_has_permissions(manage_emojis=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.channel:
			return await ctx.send('Emoji-Channel is\'nt enabled')
		del self.channel[guild_id]
		await ctx.send(f'Disabled emoji-channel')
		self.save_data()


	@commands.Cog.listener()
	async def on_message(self, msg):
		guild_id = str(msg.guild.id)
		if guild_id in self.channel and msg.attachments:
			if msg.channel.id == self.channel[guild_id]:
				try:
					await msg.add_reaction('👍')
					await asyncio.sleep(0.5)
					await msg.add_reaction('👎')
				except discord.errors.Forbidden:
					m = 'Disabled emoji-channel, missing perms to manage msgs'
					await msg.guild.owner.send(m)
					del self.channel[guild_id]
					self.save_data()


	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		guild = self.bot.get_guild(payload.guild_id)
		channel = self.bot.get_channel(payload.channel_id)
		msg = await channel.fetch_message(payload.message_id)
		user = guild.get_member(payload.user_id)
		if str(guild.id) in self.channel:
			if user.guild_permissions.manage_emojis and not user.id == self.bot.user.id:
				print(payload.emoji)
				if str(payload.emoji) == '👍':
					img = requests.get(msg.attachments[0].url).content
					name = list(msg.content if msg.content else 'new_emoji')
					chars = 'abcdefghijklmnopqrstuvwxyz_'  # wont cause error
					name = ''.join([c for c in name if str(c).lower() in chars])
					if not name:
						name = 'new_emoji'
					try:
						await guild.create_custom_emoji(name=name, image=img)
					except discord.errors.HTTPException as e:
						img = Image.open(img); img = img.resize((450, 450), Image.BICUBIC)
						img.save('emoji.png')
						with open('emoji.png', 'rb') as image:
							img = image.read()
						try:
							await guild.create_custom_emoji(name=name, image=img)
						except Exception as e:
							return await channel.send(e)
					except AttributeError as e:
						return await channel.send(e)
					await msg.delete()
				else:
					await msg.delete()


def setup(bot):
	bot.add_cog(EmojiChannel(bot))
