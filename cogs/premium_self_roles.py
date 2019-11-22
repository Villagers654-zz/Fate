"""
Self Roles / Reaction Roles
+ Create menus
+ Edit existing menus
- Use role mentions
- Set the embed color
- Set the indentation
- Add/Remove roles
- Set users reaction limit
+ Re-Sort the roles
"""

import asyncio
from os import path
import json

from discord.ext import commands
import discord

from utils import colors, utils


class Premium_Self_Roles(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.menus = {}
		self.path = './data/userdata/premium_selfroles'
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.menus = json.load(f)

	def save_data(self):
		with open(self.path, 'w+') as f:
			json.dump(self.menus, f)

	def build_menu(self, guild_id: str, data: dict):
		""" Creates an embed from menu data """
		def role_position(kv: list) -> int:
			""" Returns a roles position for sorting """
			role = guild.get_role(int(kv[0]))
			return role.position

		guild = self.bot.get_guild(int(guild_id))
		e = discord.Embed(color=data['color'])
		name = data['name']
		e.set_author(name=f"Self-Role Menu {f'- {name}' if name else ''}", icon_url=guild.owner.avatar_url)
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif')
		e.description = ''
		for role_id, emoji in sorted(data['items'].items(), key=role_position, reverse=True):
			role = guild.get_role(int(role_id))
			role = role.mention if data['mentions'] else role.name
			e.description += f"{emoji} - {role}"
			for i in range(data['indent'] + 1):
				e.description += '\n'
		return e

	def get_custom_emojis(self, m):
		if len(m) == 1:
			return m
		else:
			for char in list(m):
				try: int(char)
				except: m = m.replace(char, '')
			try: m = self.bot.get_emoji(int(m))
			except: m = None
			return m

	@commands.command(name='premium-selfroles')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def premium_selfroles(self, ctx):
		""" Sends info & usage help on self roles """
		e = discord.Embed(color=colors.fate())
		e.set_author(name='Self-Role Menus', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.description = 'Let members pick their own role via reactions'
		e.add_field(
			name='◈ Commands',
			value=f"• **create-menu** - `sets up a new role menu`"
			      f"\n• **set-color** - `sets the embeds color`"
			      f"\n• **set-name** - `set the menu name`"
			      f"\n• **set-indent** - `sets the spacing between roles`"
			      f"\n• **add-role** - `adds a role to a menu`"
			      f"\n• **remove-role** - `removes a role from a menu`"
			      f"\n• **set-limit** - `sets users reaction limit`"
			      f"\n• **sort-menu** - `re-sorts the roles`",
			inline=False
		)
		await ctx.send(embed=e)

	@commands.command(name='sort-menu')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def sort_menu(self, ctx, msg_id):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send("This server has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("There's no menu under that msg_id")
		dat = self.menus[guild_id][msg_id]  # type: dict
		channel = self.bot.get_channel(dat['channel'])
		msg = await channel.fetch_message(int(msg_id))
		embed = self.build_menu(guild_id, dat)
		await msg.edit(embed=embed)
		await ctx.send('Sorted the menu 👍')

	@commands.command(name='create-menu')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def create_menu(self, ctx):
		async def wait_for_msg():
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await instructions.delete()
				return None
			else:
				if 'cancel' in msg.content:
					await instructions.delete()
					await msg.delete()
					return None
				return msg

		menu = {
			"name": None,
			"color": None,
			"channel": None,
			"items": {},
			"indent": 1,
			"limit": None,
			"mentions": None
		}
		instructions = await ctx.send('What should the menu be called\nReply with "cancel" to exit, '
		                              'or "skip" to use default color')
		msg = await wait_for_msg()
		if not msg:
			return
		menu['name'] = msg.content
		await asyncio.sleep(0.5)
		await msg.delete()

		await instructions.edit(content='What hex color should the menu be\nReply with "cancel" to exit, '
		                                'or "skip" to use default color')
		while not menu['color']:
			msg = await wait_for_msg()
			if not msg:
				return
			if 'skip' in msg.content:
				menu['color'] = colors.fate()
				break
			try:
				hex = int(f'0x{msg.content}')
				menu['color'] = hex
			except:
				await msg.delete()
				await ctx.send('Invalid hex', delete_after=5)
		await asyncio.sleep(0.5)
		await msg.delete()

		await instructions.edit(content='How many reactions should users be allowed to add\nReply with '
		                                '"cancel" to exit, or "skip" to allow infinite')
		while not menu['limit']:
			msg = await wait_for_msg()
			if not msg:
				return
			if 'skip' in msg.content:
				menu['limit'] = None
				break
			try:
				limit = int(msg.content)
				menu['limit'] = limit
			except:
				await msg.delete()
				await ctx.send('Invalid reply', delete_after=5)
		await asyncio.sleep(0.5)
		await msg.delete()

		await instructions.edit(content='Should I use role mentions instead of role names\nReply with "yes" or "no"')
		while True:
			msg = await wait_for_msg()
			if not msg:
				return
			msg.content = msg.content.lower()
			if 'yes' not in msg.content and 'no' not in msg.content:
				await msg.delete()
				await ctx.send('Invalid reply', delete_after=5)
				continue
			if 'yes' in msg.content:
				menu['mentions'] = True
			else:
				menu['mentions'] = False
			break
		await asyncio.sleep(1)
		await msg.delete()

		await instructions.edit(content='Send the emoji and role-name for each role\n'
		                                'Reply with "done" when complete or add them later.\n'
		                                'Reply with "cancel" to exit')
		while True:
			msg = await wait_for_msg()
			if not msg:
				return
			if 'done' in msg.content:
				break
			args = msg.content.split(' ', 1)
			if len(args) == 1:
				await msg.delete()
				await ctx.send('Not enough args', delete_after=5)
				continue
			emoji, role = args
			emoji = self.get_custom_emojis(emoji)
			if not emoji:
				await msg.delete()
				await ctx.send('Emoji not found', delete_after=5)
				continue
			role = await utils.get_role(ctx, role)
			if not role:
				await msg.delete()
				await ctx.send('Role not found', delete_after=5)
				continue
			emoji_id = f'{emoji}'
			if isinstance(emoji, discord.PartialEmoji):
				emoji_id = emoji.id
			menu['items'][str(role.id)] = emoji_id
			await msg.delete()
			await ctx.send(f"Added {role.name}", delete_after=5)

		await instructions.edit(content='Mention the channel I should use\nReply with "cancel" to exit')
		while True:
			msg = await wait_for_msg()
			if not msg:
				return
			if not msg.channel_mentions:
				await msg.delete()
				await ctx.send("You didn't mention a channel", delete_after=5)
				continue
			menu['channel'] = msg.channel_mentions[0].id
			break
		await asyncio.sleep(0.5)
		await msg.delete()

		guild_id = str(ctx.guild.id)
		embed = self.build_menu(guild_id, data=menu)
		channel = self.bot.get_channel(menu['channel'])
		msg = await channel.send(embed=embed)
		for emoji in menu['items'].values():
			if isinstance(emoji, int):
				emoji = self.bot.get_emoji(emoji)
			await msg.add_reaction(emoji)
		if guild_id not in self.menus:
			self.menus[guild_id] = {}
		self.menus[guild_id][str(msg.id)] = menu
		await instructions.delete()
		await ctx.send('Created your self-role menu 👍')
		self.save_data()

	@commands.command(name='set-color')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_color(self, ctx, msg_id, hex):
		pass

	@commands.command(name='set-category')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_category(self, ctx, msg_id, category_name):
		pass

	@commands.command(name='set-indent')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_indent(self, ctx, msg_id, indent: int):
		pass

	@commands.command(name='add-role')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def add_role(self, ctx, msg_id, emoji=None, *, role=None):
		p = utils.get_prefix(ctx)
		usage = f"{p}add-role msg_id emoji rolename"
		if not emoji or not role:
			await ctx.send(usage)
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		emoji = self.get_custom_emojis(emoji)
		if not emoji:
			return await ctx.send('Emoji not found', delete_after=5)
		role = await utils.get_role(ctx, role)
		if not role:
			return await ctx.send('Role not found', delete_after=5)
		emoji_id = f'{emoji}'
		if isinstance(emoji, discord.PartialEmoji):
			emoji_id = emoji.id
		self.menus[guild_id][msg_id]['items'][str(role.id)] = emoji_id
		embed = self.build_menu(guild_id, self.menus[guild_id][msg_id])
		channel = self.bot.get_channel(self.menus[guild_id][msg_id]['channel'])
		msg = await channel.fetch_message(int(msg_id))
		await msg.edit(embed=embed)
		if isinstance(emoji, int):
			emoji = self.bot.get_emoji(emoji)
		await msg.add_reaction(emoji)
		await ctx.send(f"Added {role.name}")
		self.save_data()

	@commands.command(name='remove-role')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def remove_role(self, ctx, msg_id, *, role):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		role = await utils.get_role(ctx, role)
		if not role:
			return await ctx.send("Role not found")
		if str(role.id) not in self.menus[guild_id][msg_id]['items']:
			return await ctx.send("That role isn't in the menu")
		emoji = self.menus[guild_id][msg_id]['items'][str(role.id)]
		del self.menus[guild_id][msg_id]['items'][str(role.id)]
		embed = self.build_menu(guild_id, self.menus[guild_id][msg_id])
		channel = self.bot.get_channel(self.menus[guild_id][msg_id]['channel'])
		msg = await channel.fetch_message(int(msg_id))
		await msg.edit(embed=embed)
		if isinstance(emoji, int):
			emoji = self.bot.get_emoji(emoji)
		for reaction in msg.reactions:
			if str(reaction.emoji) == str(emoji):
				async for user in reaction.users():
					await msg.remove_reaction(reaction, user)
		await ctx.send(f"Removed {role.name}")
		self.save_data()

	@commands.command(name='set-limit')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_limit(self, ctx, msg_id):
		pass

def setup(bot):
	bot.add_cog(Premium_Self_Roles(bot))
