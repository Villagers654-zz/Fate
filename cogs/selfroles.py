from discord.ext import commands
from os.path import isfile
from utils import colors
import discord
import asyncio
import json

class SelfRoles(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.msgs = {}
		self.path = './data/userdata/selfroles.json'
		if isfile(self.path):
			with open(self.path, 'r') as dat:
				self.msgs = json.load(dat)

	def save_data(self):
		with open(self.path, 'w') as f:
			json.dump(self.msgs, f, ensure_ascii=False)

	@commands.command(name='selfroles', aliases=['selfrole'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True, manage_messages=True)
	async def selfroles(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.msgs:
			self.msgs[guild_id] = {}
		async def wait_for_msg():
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=30)
			except asyncio.TimeoutError:
				await ctx.send('Timeout error')
				return
			else:
				return msg
		def get_role(name):
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
		def get_custom_emojis(m):
			if len(m) == 1:
				return m
			else:
				for char in list(m):
					try: int(char)
					except: m = m.replace(char, '')
				return self.bot.get_emoji(int(m))
		e = discord.Embed(color=colors.fate())
		info = 'Send the reaction emoji and role name per role\n'
		info += 'Example: `🎁 Partnership Pings`\n'
		info += 'Reply with "done" when completed'
		e.description = info
		msg = await ctx.send(embed=e)
		await ctx.message.delete()
		selfroles = []
		role_menu = ''
		completed = False
		while not completed:
			reply = await wait_for_msg()
			if not reply:
				return await msg.delete()
			if 'done' in reply.content.lower():
				await msg.delete()
				await reply.delete()
				if not selfroles:
					return
				msg = await ctx.send('What should the role category be called?\nReply with "nothing" to skip')
				reply = await wait_for_msg()
				await msg.delete()
				if not reply:
					return
				await reply.delete()
				category = ''
				if 'nothing' not in reply.content.lower():
					category = reply.content
				menu = await ctx.send(f'__**Role Menu:**__ {category}\n{role_menu}')
				for emoji, role_id in selfroles:
					if isinstance(emoji, int):
						emoji = self.bot.get_emoji(emoji)
					await menu.add_reaction(emoji)
				self.msgs[guild_id][str(menu.id)] = selfroles
				self.save_data()
				break
			args = reply.content.split(' ')
			if len(args) != 2:
				await ctx.send('Too little or too many args')
				continue
			emoji, role = args
			emoji = get_custom_emojis(emoji)
			await reply.delete()
			if not emoji:
				await ctx.send('Emoji not found', delete_after=5)
				continue
			role = get_role(role)
			if not role:
				await ctx.send('Role not found', delete_after=5)
				continue
			emoji_id = f'{emoji}'
			if isinstance(emoji, discord.PartialEmoji):
				emoji_id = emoji.id
			selfroles.append([emoji_id, role.id])
			role_menu += f'{emoji} : {role.name}\n\n'
			e.description = f'{info}\n\n{role_menu}'
			await msg.edit(embed=e)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.msgs:
			msg_id = str(payload.message_id)
			if msg_id in self.msgs[guild_id]:
				guild = self.bot.get_guild(payload.guild_id)
				selfroles = self.msgs[guild_id][msg_id]
				emojis = []
				roles = []
				for emoji, role_id in selfroles:
					if isinstance(emoji, str):
						emoji = emoji.replace('<a', '<')
					emojis.append(emoji)
					role = guild.get_role(role_id)
					roles.append(role)
				emoji = str(payload.emoji)
				if emoji.isdigit():
					emoji = self.bot.get_emoji(emoji)
				else:
					emoji = f'{emoji}'
				index = emojis.index(emoji)
				user = guild.get_member(payload.user_id)
				await user.add_roles(roles[index])

	@commands.Cog.listener()
	async def on_message_delete(self, msg):
		guild_id = str(msg.guild.id)
		if guild_id in self.msgs:
			if str(msg.id) in self.msgs[guild_id]:
				del self.msgs[guild_id][str(msg.id)]
				self.save_data()

def setup(bot):
	bot.add_cog(SelfRoles(bot))
