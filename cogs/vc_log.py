from discord.ext import commands
from utils import colors, utils
from os.path import isfile
import discord
import json

class VcLog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.path = './data/userdata/VcLog.json'
		self.channel = {}
		if isfile(self.path):
			with open(self.path, 'r') as f:
				self.channel = json.load(f)

	def save_json(self):
		with open(self.path, 'w') as f:
			json.dump(self.channel, f, ensure_ascii=False)

	async def ensure_permissions(self, guild_id):
		channel = self.bot.get_channel(self.channel[guild_id])
		if not channel:
			del self.channel[guild_id]
			self.save_json()
			return False
		bot = channel.guild.get_member(self.bot.user.id)
		if not channel.permissions_for(bot).send_messages:
			del self.channel[guild_id]
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
		mentions = msg.channel_mentions
		if not mentions:
			return await ctx.send('That isn\'t a channel mention')
		self.channel[guild_id] = msg.channel_mentions[0].id
		channel_access = await self.ensure_permissions(guild_id)
		if not channel_access:
			await ctx.send('Sry, I don\'t have access to that channel')
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
		if guild_id in self.channel:
			channel = self.bot.get_channel(self.channel[guild_id])
			bot_has_required_perms = await self.ensure_permissions(guild_id)
			if bot_has_required_perms:
				if not before.channel:
					await channel.send(f'<:plus:548465119462424595> **{member.display_name} joined {after.channel.name}**')
				if not after.channel:
					await channel.send(f'❌ **{member.display_name} left {before.channel.name}**')

def setup(bot):
	bot.add_cog(VcLog(bot))
