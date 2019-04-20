from discord.ext import commands
from utils import colors, utils
from os.path import isfile
from time import time
import discord
import asyncio
import json

class VcLog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/userdata/VcLog.json'
		self.channel = {}
		self.clean_channel = {}
		self.join_cd = {}
		self.leave_cd = {}
		self.move_cd = {}
		if isfile(self.path):
			with open(self.path, 'r') as f:
				dat = json.load(f)
				if 'channel' in dat:
					self.channel = dat['channel']
				if 'clean_channel' in dat:
					self.clean_channel = dat['clean_channel']

	def save_json(self):
		with open(self.path, 'w') as f:
			json.dump({'channel': self.channel, 'clean_channel': self.clean_channel}, f, ensure_ascii=False)

	async def ensure_permissions(self, guild_id, channel_id=None):
		if channel_id:
			channel = self.bot.get_channel(channel_id)
			if channel:
				bot = channel.guild.get_member(self.bot.user.id)
				if channel.permissions_for(bot).send_messages:
					return True
			return False
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			if not channel:
				del self.channel[guild_id]
				self.save_json()
				return False
		if guild_id in self.clean_channel:
			channel = self.bot.get_channel(self.clean_channel[guild_id])
			if not channel:
				del self.clean_channel[guild_id]
				self.save_json()
				return False
			bot = channel.guild.get_member(self.bot.user.id)
			if not channel.permissions_for(bot).send_messages:
				del self.clean_channel[guild_id]
				self.save_json()
				return False
			if not channel.permissions_for(bot).manage_messages:
				del self.clean_channel[guild_id]
				self.save_json()
				return False
		return True

	@commands.group(name='vclog')
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def _vclog(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Vc Logger', icon_url=ctx.author.avatar_url)
			if ctx.guild.icon_url:
				e.set_thumbnail(url=ctx.guild.icon_url)
			else:
				e.set_thumbnail(url=self.bot.user.avatar_url)
			e.description = 'Logs when users join/leave VC to a dedicated channel'
			e.add_field(name='◈ Usage ◈', value='.vclog enable\n.vclog disable', inline=False)
			if str(ctx.guild.id) in self.channel:
				status = 'Current Status: enabled'
			else:
				status = 'Current Status: disabled'
			e.set_footer(text=status)
			await ctx.send(embed=e)

	@_vclog.command(name='enable')
	@commands.has_permissions(manage_channels=True)
	async def _enable(self, ctx):
		guild_id = str(ctx.guild.id)
		await ctx.send('Mention the channel I should use')
		msg = await utils.Bot(self.bot).wait_for_msg(ctx)
		if not msg.channel_mentions:
			return await ctx.send('That isn\'t a channel mention')
		channel_id = msg.channel_mentions[0].id
		channel_access = await self.ensure_permissions(guild_id, channel_id)
		if not channel_access:
			return await ctx.send('Sry, I don\'t have access to that channel')
		await ctx.send('Would you like me to delete all non vc-log messages?')
		msg = await utils.Bot(self.bot).wait_for_msg(ctx)
		reply = msg.content.lower()
		if 'yes' in reply or 'sure' in reply or 'ok' in reply or 'yep' in reply:
			self.clean_channel[guild_id] = channel_id
			channel_access = await self.ensure_permissions(guild_id)
			if not channel_access:
				return await ctx.send('Sry, I\'m missing manage message(s) permissions in there')
		else:
			self.channel[guild_id] = channel_id
		await ctx.send('Enabled VcLog')
		self.save_json()

	@_vclog.command(name='disable')
	@commands.has_permissions(manage_channels=True)
	async def _disable(self, ctx):
		guild_id = str(ctx.guild.id)
		if guild_id not in self.channel:
			return await ctx.send('VcLog isn\'nt enabled')
		del self.channel[guild_id]
		await ctx.send('Disabled VcLog')
		self.save_json()

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		guild_id = str(member.guild.id)
		if guild_id in self.channel or guild_id in self.clean_channel:
			if guild_id in self.channel:
				channel = self.bot.get_channel(self.channel[guild_id])
			else:
				channel = self.bot.get_channel(self.clean_channel[guild_id])
			bot_has_permissions = await self.ensure_permissions(guild_id)
			if bot_has_permissions:
				user_id = str(member.id)
				if not before.channel:
					if guild_id not in self.join_cd:
						self.join_cd[guild_id] = {}
					if user_id not in self.join_cd[guild_id]:
						self.join_cd[guild_id][user_id] = 0
					if self.join_cd[guild_id][user_id] < time():
						await channel.send(f'<:plus:548465119462424595> **{member.display_name} joined {after.channel.name}**')
						self.join_cd[guild_id][user_id] = time() + 10
						return
				if not after.channel:
					if guild_id not in self.leave_cd:
						self.leave_cd[guild_id] = {}
					if user_id not in self.leave_cd[guild_id]:
						self.leave_cd[guild_id][user_id] = 0
					if self.leave_cd[guild_id][user_id] < time():
						await channel.send(f'❌ **{member.display_name} left {before.channel.name}**')
						self.leave_cd[guild_id][user_id] = time() + 10
						return
				if before.channel.id != after.channel.id:
					now = int(time() / 10)
					if guild_id not in self.move_cd:
						self.move_cd[guild_id] = {}
					if user_id not in self.move_cd[guild_id]:
						self.move_cd[guild_id][user_id] = [now, 0]
					if self.move_cd[guild_id][user_id][0] == now:
						self.move_cd[guild_id][user_id][1] += 1
					else:
						self.move_cd[guild_id][user_id] = [now, 0]
					if self.move_cd[guild_id][user_id][1] > 2:
						return
					return await channel.send(f'🚸 **{member.display_name} moved to {after.channel.name}**')
				if before.mute is False and after.mute is True:
					return await channel.send(f'🔈 **{member.display_name} was muted**')
				if before.mute is True and after.mute is False:
					return await channel.send(f'🔊 **{member.display_name} was unmuted**')
				if before.deaf is False and after.deaf is True:
					return await channel.send(f'🎧 **{member.display_name} was deafened**')
				if before.deaf is True and after.deaf is False:
					await channel.send(f'🎤 **{member.display_name} was undeafened**')

	@commands.Cog.listener()
	async def on_message(self, msg: discord.Message):
		if isinstance(msg.guild, discord.Guild):
			guild_id = str(msg.guild.id)
			if guild_id in self.clean_channel:
				if msg.channel.id == self.clean_channel[guild_id]:
					if msg.author.id == self.bot.user.id:
						chars = ['<:plus:548465119462424595>', '❌', '🔈', '🔊', '🚸', '🎧', '🎤']
						for x in chars:
							if msg.content.startswith(x):
								return
					bot_has_permissions = await self.ensure_permissions(guild_id)
					if bot_has_permissions:
						await asyncio.sleep(20)
						try:
							await msg.delete()
						except:
							pass

def setup(bot):
	bot.add_cog(VcLog(bot))
