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
		self.single = {}
		self.path = './data/userdata/selfroles.json'
		if isfile(self.path):
			with open(self.path, 'r') as dat:
				self.msgs = json.load(dat)

	def save_data(self):
		with open(self.path, 'w') as f:
			json.dump(self.msgs, f, ensure_ascii=False)

	@commands.group(name='selfroles', aliases=['selfrole'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(embed_links=True, manage_messages=True)
	async def selfroles(self, ctx):
		if ctx.invoked_subcommand:
			return
		guild_id = str(ctx.guild.id)
		if guild_id not in self.msgs:
			self.msgs[guild_id] = {}
		async def wait_for_msg():
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=60)
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
				try: m = self.bot.get_emoji(int(m))
				except: m = None
				return m
		e = discord.Embed(color=colors.fate())
		info = 'Send the reaction emoji and role name per role\n'
		info += 'Example: `🎁 Partnership Pings`\n'
		info += 'Reply with "done" when completed'
		e.description = info
		msg = await ctx.send(embed=e)
		await ctx.message.delete()
		selfroles = []
		role_menu = ''
		role_menu_mentions = ''
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
				msg = await ctx.send('Should i use a normal msg or embed\nReply with "msg" or "embed"')
				reply = await wait_for_msg()
				if not reply:
					return
				if 'embed' in reply.content.lower():
					m = await ctx.send('Should I use role names or role mentions?\nReply with "names" or "mentions"')
					r = await wait_for_msg()
					if not r:
						return
					if 'name' in r.content.lower():
						menu = role_menu
					else:
						menu = role_menu_mentions
					e = discord.Embed(color=colors.fate())
					e.set_author(name=f'Self-Role Menu: {category}', icon_url='https://cdn.discordapp.com/emojis/513634338487795732.png?v=1')
					e.set_thumbnail(url='https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif')
					e.description = menu
					menu = await ctx.send(embed=e)
					await m.delete()
					await r.delete()
				else:
					menu = await ctx.send(f'__**Self-Role Menu:**__ **{category}**\n{role_menu}')
				await msg.delete()
				await reply.delete()
				for emoji, role_id in selfroles:
					if isinstance(emoji, int):
						emoji = self.bot.get_emoji(emoji)
					await menu.add_reaction(emoji)
				await ctx.send('Note: you can use `.selfroles limit` to toggle whether or not users can get multiple roles from each menu', delete_after=10)
				self.msgs[guild_id][str(menu.id)] = selfroles
				self.save_data()
				break
			args = reply.content.split(' ', 1)
			if len(args) == 1:
				await ctx.send('Not enough args')
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
			role_menu_mentions += f'{emoji} : {role.mention}\n\n'
			e.description = f'{info}\n\n{role_menu}'
			await msg.edit(embed=e)

	@selfroles.command(name='limit')
	async def limit(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id in self.single:
			del self.single[guild_id]
			return await ctx.send('I\'ll now allow multiple reactions')
		self.single[guild_id] = 'True'
		await ctx.send('Limited users to 1 reaction per menu')

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
				if guild_id in self.single:
					for role in user.roles:
						if role in roles:
							await user.remove_roles(role)
				role = roles[index]
				await user.add_roles(role)

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload):
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
				await user.remove_roles(roles[index])

	@commands.Cog.listener()
	async def on_message_delete(self, msg):
		guild_id = str(msg.guild.id)
		if guild_id in self.msgs:
			if str(msg.id) in self.msgs[guild_id]:
				del self.msgs[guild_id][str(msg.id)]
				self.save_data()

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.msgs:
			del self.msgs[guild_id]
			self.save_data()
		if guild_id in self.single:
			del self.single[guild_id]
			self.save_data()

	@commands.command(name='delselfkeys')
	async def delselfkeys(self, ctx, guild_id):
		del self.msgs[guild_id]
		await ctx.send('done')
		self.save_data()

def setup(bot):
	bot.add_cog(SelfRoles(bot))
