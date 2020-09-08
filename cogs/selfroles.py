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

from utils import colors


class SelfRoles(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.menus = {}
		self.path = './data/userdata/selfroles.json'
		if path.isfile(self.path):
			with open(self.path, 'r') as f:
				self.menus = json.load(f)

	async def save_data(self):
		await self.bot.save_json(self.path, self.menus)

	def build_menu(self, guild_id: str, data: dict):
		""" Creates an embed from menu data """
		def role_position(kv: list) -> int:
			""" Returns a roles position for sorting """
			role = guild.get_role(int(kv[0]))
			return role.position

		guild = self.bot.get_guild(int(guild_id))
		e = discord.Embed(color=data['color'])
		name = data['name']
		e.set_author(name=f"Self-Role Menu{f': {name}' if name else ''}", icon_url=guild.owner.avatar_url)
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/514213558549217330/514345278669848597/8yx98C.gif')
		e.description = ''
		data['items'] = {
			role_id: emoji for role_id, emoji in data['items'].items()
			if int(role_id) in list(r.id for r in guild.roles)
		}
		for role_id, emoji in sorted(data['items'].items(), key=role_position, reverse=True):
			role = guild.get_role(int(role_id))
			if not role:
				continue
			role = role.mention if data['mentions'] else role.name
			e.description += f"{emoji} - {role}"
			for i in range(data['indent'] + 1):
				e.description += '\n'
		return e

	def get_emojis(self, string):
		""" Gets the custom emoji id or unicode emote """
		if not any(char.isdigit() for char in list(string)):
			return string  # unicode emoji
		string = "".join(char for char in list(string[-20:]) if char.isdigit())
		emoji = self.bot.get_emoji(int(string))
		return emoji

	async def edit_menu(self, guild_id: str, msg_id: str):
		""" Rebuilds a menu with its updated data """
		embed = self.build_menu(guild_id, self.menus[guild_id][msg_id])
		channel = self.bot.get_channel(self.menus[guild_id][msg_id]['channel'])
		try:
			msg = await channel.fetch_message(int(msg_id))
		except (AttributeError, discord.errors.NotFound):
			guild = self.bot.get_guild(int(guild_id))
			for c in guild.text_channels:
				try:
					msg = await c.fetch_message(int(msg_id))
				except (AttributeError, discord.errors.NotFound):
					continue
				await msg.edit(embed=embed)
				self.menus[guild_id][msg_id]['channel'] = c.id
				await self.save_data()
				return msg
			msg = await channel.fetch_message(int(msg_id))
		await msg.edit(embed=embed)
		return msg

	@commands.command(name='selfroles', aliases=['self-roles', 'selfrole', 'self-role'])
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def selfroles(self, ctx):
		""" Sends info & usage help on self roles """
		e = discord.Embed(color=colors.fate())
		e.set_author(name='Self-Role Menus', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.description = "Let members pick their own role via reactions. If you're " \
		                "having trouble editing a menu, use the update-menu cmd"
		e.add_field(
			name='◈ Commands',
			value=f"• **create-menu** - `sets up a new role menu`"
			      f"\n• **set-color** - `sets the embeds color`"
			      f"\n• **set-name** - `set the menu name`"
			      f"\n• **set-indent** - `sets the spacing between roles`"
			      f"\n• **add-role** - `adds a role to a menu`"
			      f"\n• **remove-role** - `removes a role from a menu`"
			      f"\n• **set-limit** - `sets users reaction limit`"
			      f"\n• **toggle-mentions** - `use role mentions`"
			      f"\n• **update-menu** - `refreshes a menu`",
			inline=False
		)
		await ctx.send(embed=e)

	@commands.command(name='update-menu')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def update_menu(self, ctx, msg_id):
		""" Rebuilds a menu """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send("This server has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("There's no menu under that msg_id")
		dat = self.menus[guild_id][msg_id]  # type: dict
		if not dat['channel']:
			try:
				await ctx.channel.fetch_message(msg_id)
			except:
				return await ctx.send("Use this cmd in the channel the menus in, as it has no channel_id saved")
			self.menus[guild_id][msg_id]['channel'] = ctx.channel.id
			dat['channel'] = ctx.channel.id
			await self.save_data()
		for role_id, emoji in list(dat['items'].items()):
			role = ctx.guild.get_role(int(role_id))
			if not role:
				emoji = self.menus[guild_id][msg_id]['items'][role_id]
				del self.menus[guild_id][msg_id]['items'][role_id]
				msg = await self.edit_menu(guild_id, msg_id)
				if isinstance(emoji, int):
					emoji = self.bot.get_emoji(emoji)
				for reaction in msg.reactions:
					if str(reaction.emoji) == str(emoji):
						async for user in reaction.users():
							await msg.remove_reaction(reaction, user)
		channel = self.bot.get_channel(dat['channel'])
		msg = await channel.fetch_message(int(msg_id))
		embed = self.build_menu(guild_id, dat)
		await msg.edit(embed=embed)
		await ctx.send('Updated the menu 👍')

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
				msg = await self.bot.wait_for('message', check=pred, timeout=120)
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
			"name": None,  # type: str
			"color": None,  # type: int
			"channel": None,  # type: int
			"items": {},
			"indent": 1,
			"limit": None,
			"mentions": None  # type: bool
		}
		instructions = await ctx.send('What should the menu be called\nReply with "cancel" to exit, '
		                              'or "skip" to use none')
		msg = await wait_for_msg()
		if not msg:
			return
		menu['name'] = msg.content
		await asyncio.sleep(0.5)
		await msg.delete()

		if 'quick' not in ctx.message.content:

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
					hex = int(f'0x{msg.content}', 0)
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
				for content in msg.content.split('\n'):
					args = content.split(' ', 1)
					if len(args) == 1:
						await msg.delete()
						await ctx.send('Not enough args', delete_after=5)
						continue
					emote, role = args
					emoji = self.get_emojis(emote)
					if not emoji:
						print(emote)
						await ctx.send(f'Emoji not found for {emote}', delete_after=5)
						continue
					role = await self.bot.utils.get_role(ctx, role)
					if not role:
						await ctx.send('Role not found', delete_after=5)
						continue
					emoji_id = f'{emoji}'
					if isinstance(emoji, discord.PartialEmoji):
						emoji_id = emoji.id
					menu['items'][str(role.id)] = emoji_id
					await ctx.send(f"Added {role.name}", delete_after=5)
			await asyncio.sleep(0.5)
			await msg.delete()
		else:
			menu['color'] = colors.fate()
			menu['mentions'] = True

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
			try:
				await msg.add_reaction(emoji)
			except discord.errors.HTTPException:
				await ctx.send(f"I couldn't access the emoji {emoji}\nYou'll need to add the reaction yourself")
		if guild_id not in self.menus:
			self.menus[guild_id] = {}
		self.menus[guild_id][str(msg.id)] = menu
		await instructions.delete()
		await ctx.send('Created your self-role menu 👍')
		await self.save_data()

	@commands.command(name='set-color')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_color(self, ctx, msg_id=None, hex=None):
		""" Sets the embed color for an existing menu """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}set-color msg_id hex"
		if not msg_id:
			return await ctx.send(usage)
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		if not hex:
			return await ctx.send(usage)
		try:
			hex = int(f"0x{hex.replace('#', '')}", 0)
		except:
			return await ctx.send(f"Invalid hex\nExample: #9eafe3")
		self.menus[guild_id][msg_id]['color'] = hex
		await self.edit_menu(guild_id, msg_id)
		await ctx.send("Set the color 👍")
		await self.save_data()

	@commands.command(name='set-name')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_name(self, ctx, msg_id=None, new_name=None):
		""" Sets an existing menus name """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}set-name msg_id new_name"
		if not msg_id:
			return await ctx.send(usage)
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		self.menus[guild_id][msg_id]['name'] = new_name
		await self.edit_menu(guild_id, msg_id)
		await ctx.send("Set the name 👍")
		await self.save_data()

	@commands.command(name='set-indent')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_indent(self, ctx, msg_id=None, indent: int = None):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}set-indent msg_id 0-2"
		if not msg_id:
			return await ctx.send(usage)
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		if not indent:
			return await ctx.send(usage)
		if indent > 2:
			return await ctx.send("The max indent is 2")
		self.menus[guild_id][msg_id]['indent'] = indent
		await self.edit_menu(guild_id, msg_id)
		await ctx.send(f"Set the menus indent to {indent}")
		await self.save_data()

	@commands.command(name='add-role')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def add_role(self, ctx, msg_id, emoji=None, *, role=None):
		""" Adds a role to an existing menu """
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}add-role msg_id emoji rolename"
		if not emoji or not role:
			return await ctx.send(usage)
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		emoji = self.get_emojis(emoji)
		if not emoji:
			return await ctx.send('Emoji not found')
		role = await self.bot.utils.get_role(ctx, role)
		if not role:
			return await ctx.send('Role not found')
		emoji_id = f'{emoji}'
		if isinstance(emoji, discord.PartialEmoji):
			emoji_id = emoji.id
		self.menus[guild_id][msg_id]['items'][str(role.id)] = emoji_id
		try:
			msg = await self.edit_menu(guild_id, msg_id)
		except AttributeError:
			del self.menus[guild_id][msg_id]['items'][str(role.id)]
			return await ctx.send(f"I couldn't find that menu in this server. Please try using `{p}update-menu {msg_id}` "
			                      f"inside the same channel the menu is in as it's likely an old selfrole menu")
		if isinstance(emoji, int):
			emoji = self.bot.get_emoji(emoji)
		try:
			await msg.add_reaction(emoji)
		except discord.errors.HTTPException:
			return await ctx.send("I can't find that emoji")
		await ctx.send(f"Added {role.name}")
		await self.save_data()

	@commands.command(name='remove-role')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def remove_role(self, ctx, msg_id, *, role):
		""" Removes a role from an existing menu """
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		role = await self.bot.utils.get_role(ctx, role)
		if not role:
			return await ctx.send("Role not found, if its a deleted role, try adding a reaction to it on the menu")
		if str(role.id) not in self.menus[guild_id][msg_id]['items']:
			return await ctx.send("That role isn't in the menu")
		emoji = self.menus[guild_id][msg_id]['items'][str(role.id)]
		del self.menus[guild_id][msg_id]['items'][str(role.id)]
		msg = await self.edit_menu(guild_id, msg_id)
		if isinstance(emoji, int):
			emoji = self.bot.get_emoji(emoji)
		for reaction in msg.reactions:
			if str(reaction.emoji) == str(emoji):
				async for user in reaction.users():
					await msg.remove_reaction(reaction, user)
		await ctx.send(f"Removed {role.name}")
		await self.save_data()

	@commands.command(name='set-limit')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def set_limit(self, ctx, msg_id=None, limit: int = None):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}set-limit msg_id limit"
		if not msg_id:
			return await ctx.send(usage)
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		if not limit:
			return await ctx.send(usage)
		self.menus[guild_id][msg_id]['limit'] = limit
		await self.edit_menu(guild_id, msg_id)
		await ctx.send(f"Set the limit to {limit}")
		await self.save_data()

	@commands.command(name='toggle-mentions')
	@commands.cooldown(2, 5, commands.BucketType.user)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.has_permissions(manage_roles=True)
	async def toggle_mentions(self, ctx, msg_id=None):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.menus:
			return await ctx.send(f"This guild has no self-role menus")
		p = self.bot.utils.get_prefix(ctx)
		usage = f"{p}toggle-mentions msg_id"
		if not msg_id:
			return await ctx.send(usage)
		if msg_id not in self.menus[guild_id]:
			return await ctx.send("That menu doesn't exist")
		if self.menus[guild_id][msg_id]['mentions']:
			self.menus[guild_id][msg_id]['mentions'] = False
		else:
			self.menus[guild_id][msg_id]['mentions'] = True
		await self.edit_menu(guild_id, msg_id)
		toggle = self.menus[guild_id][msg_id]['mentions']
		await ctx.send(f"{'enabled' if toggle else 'disabled'} mentions")
		await self.save_data()

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.menus:
			msg_id = str(payload.message_id)
			if msg_id in self.menus[guild_id]:

				guild = self.bot.get_guild(payload.guild_id)
				channel = self.bot.get_channel(payload.channel_id)
				msg = await channel.fetch_message(msg_id)
				target = guild.get_member(payload.user_id)
				if target.bot:
					return

				for role_id, emoji in self.menus[guild_id][msg_id]['items'].items():

					if isinstance(emoji, int):
						emoji = self.bot.get_emoji(emoji)
					if str(emoji) == str(payload.emoji):
						role = guild.get_role(int(role_id))
						if not role:
							try:
								await target.send(
									f"Sorry, but the role with the emoji {emoji} that you reacted to in "
									f"{guild} doesn't seem to exist anymore. I've just removed it from the menu"
								)
							except discord.errors.Forbidden:
								pass
							del self.menus[guild_id][msg_id]['items'][role_id]
							return await self.edit_menu(guild_id, msg_id)
						await target.add_roles(role)

						if self.menus[guild_id][msg_id]['limit']:
							limit = self.menus[guild_id][msg_id]['limit']
							index = 0
							for reaction in msg.reactions:
								async for user in reaction.users():
									if user.id == target.id:
										if index >= limit:
											await msg.remove_reaction(reaction, user)
										index += 1

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		guild_id = str(payload.guild_id)
		if guild_id in self.menus:
			msg_id = str(payload.message_id)
			if msg_id in self.menus[guild_id]:
				guild = self.bot.get_guild(payload.guild_id)
				target = guild.get_member(payload.user_id)
				for role_id, emoji in self.menus[guild_id][msg_id]['items'].items():
					if isinstance(emoji, int):
						emoji = self.bot.get_emoji(emoji)
					if str(emoji) == str(payload.emoji):
						role = guild.get_role(int(role_id))
						if not target:
							return
						if role in target.roles:
							await target.remove_roles(role)

	@commands.Cog.listener()
	async def on_message_delete(self, msg):
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			if guild_id in self.menus:
				if str(msg.id) in self.menus[guild_id]:
					del self.menus[guild_id][str(msg.id)]
					await self.save_data()

def setup(bot):
	bot.add_cog(SelfRoles(bot))
