from discord.ext import commands
from utils import checks, colors
from os.path import isfile
import discord
import json

class ServerList(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dir = './data/userdata/serverlist.json'
		self.servers = {}
		if isfile(self.dir):
			with open(self.dir, 'r') as f:
				self.servers = json.load(f)

	def save_data(self):
		with open(self.dir, 'w') as f:
			json.dump(self.servers, f, ensure_ascii=False)

	def del_invite(self, invite):
		for category in list(self.servers.keys()):
			if invite in category:
				index = category.index(invite)
				self.servers[category].pop(index)
				self.save_data()

	@commands.group(name='serverlist', aliases=['servers', 'discords'])
	@commands.cooldown(1, 5, commands.BucketType.channel)
	@commands.bot_has_permissions(embed_links=True)
	async def _serverlist(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Server List', icon_url=self.bot.user.avatar_url)
			e.set_thumbnail(url='https://cdn.discordapp.com/icons/397415086295089155/e31d9034f418c48ba766389ab9bf3d39.webp?size=1024')
			e.description = ''
			for category, invites in sorted(list(self.servers.items()), key=lambda kv: len(kv[0]), reverse=True):
				values = []
				for invite_url in invites:
					code = discord.utils.resolve_invite(invite_url)
					try:
						invite = await self.bot.fetch_invite(code)
					except:
						self.del_invite(invite_url)
						continue
					if isinstance(invite.guild, discord.PartialInviteGuild):
						self.del_invite(invite_url)
						continue
					values.append(f'• [{invite.guild.name}]({invite.url})\n')
				value = ''
				for invite in sorted(values, key=lambda kv: len(kv[0])):
					value += invite
				e.add_field(name=f'◈ {category} ◈', value=value, inline=False)
			await ctx.send(embed=e)

	@_serverlist.command(name='addserver', aliases=['add'])
	@commands.check(checks.luck)
	async def _addserver(self, ctx, invite, category):
		code = discord.utils.resolve_invite(invite)
		try: invite = await self.bot.fetch_invite(code)
		except: return await ctx.send('I can\'t use an invalid or temporary invite')
		if isinstance(invite.guild, discord.PartialInviteGuild):
			return await ctx.send('Sorry, I gotta be apart of the guild')
		if category not in self.servers:
			self.servers[category] = []
		self.servers[category].append(invite.url)
		await ctx.send(f'Added {invite.guild.name} to {category}')
		self.save_data()

	@_serverlist.command(name='delcategory', aliases=['delcat'])
	@commands.check(checks.luck)
	async def _delcategory(self, ctx, category):
		if category not in self.servers:
			return await ctx.send(f'Category \'{category}\' not found')
		del self.servers[category]
		await ctx.send(f'Deleted the category \'{category}\'')
		self.save_data()

def setup(bot):
	bot.add_cog(ServerList(bot))
