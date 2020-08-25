from discord.ext import commands
from utils import colors
import discord
import asyncio
import json

class Config(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def save_config(self, config):
		with open('./data/userdata/config.json', 'w') as f:
			json.dump(config, f, ensure_ascii=False)

	def prefix(self, id):
		with open("./data/userdata/prefixes.json", "r") as f:
			dat = json.load(f)
			if id in dat:
				return dat[id]
			return "."

	def restore_roles(self, id):
		with open("./data/userdata/restore_roles.json", "r") as f:
			if id in json.load(f)['guilds']:
				return "active"
			return "inactive"

	def chatfilter(self, id):
		with open("./data/userdata/chatfilter.json", "r") as f:
			if int(id) in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def anti_spam(self, id):
		with open("./data/userdata/anti_spam.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def anti_raid(self, id):
		with open("./data/userdata/anti_raid.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def selfroles(self, id):
		with open("./data/userdata/selfroles.json", "r") as f:
			if id in json.load(f):
				return "active"
			return "inactive"

	def autorole(self, id):
		with open("./data/userdata/autorole.json", "r") as f:
			if id in json.load(f)["roles"]:
				return "active"
			return "inactive"

	def welcome(self, id):
		with open("./data/userdata/welcome.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def farewell(self, id):
		with open("./data/userdata/farewell.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def chatbot(self, id):
		with open("./data/userdata/chatbot.json", "r") as f:
			if id in json.load(f)["toggle"]:
				return "active"
			return "inactive"

	def logger(self, id):
		with open("./data/userdata/logger.json", "r") as f:
			if id in json.load(f)["channel"]:
				return "active"
			return "inactive"

	def lock(self, id):
		with open("./data/userdata/lock.json", "r") as f:
			if id in json.load(f)["lock"]:
				return "active"
			return "inactive"

	@commands.group(name="config", aliases=["conf"])
	@commands.guild_only()
	@commands.cooldown(1, 3, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def _config(self, ctx):
		if not ctx.invoked_subcommand:
			guild_id = str(ctx.guild.id)
			e = discord.Embed(color=colors.fate())
			e.set_author(name="| 💎 Server Config 💎", icon_url=ctx.guild.owner.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = f"**Prefix:** [`{self.prefix(guild_id)}`]\n"
			module_config =  f"**Restore Roles:** [`{self.restore_roles(guild_id)}`]\n" \
				f"**Chat Filter:** [`{self.chatfilter(guild_id)}`]\n" \
				f"**Anti Spam:** [`{self.anti_spam(guild_id)}`]\n" \
				f"**Anti Raid:** [`{self.anti_raid(guild_id)}`]\n" \
				f"**Self Roles:** [`{self.selfroles(guild_id)}`]\n" \
				f"**Auto Role:** [`{self.autorole(guild_id)}`]\n" \
				f"**Welcome:** [`{self.welcome(guild_id)}`]\n" \
				f"**Farewell:** [`{self.farewell(guild_id)}`]\n" \
				f"**Chatbot:** [`{self.chatbot(guild_id)}`]\n" \
				f"**Logger:** [`{self.logger(guild_id)}`]\n" \
				f"**Lock:** [`{self.lock(guild_id)}`]"
			e.add_field(name="◈ Modules ◈", value=module_config, inline=False)
			subcommands = f'{self.prefix(guild_id)}config warns'
			e.add_field(name='◈ Editable Configs ◈', value=subcommands, inline=False)
			await ctx.send(embed=e)

	@_config.command(name='warns')
	@commands.has_permissions(manage_guild=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def _warns(self, ctx):
		guild_id = str(ctx.guild.id)
		emojis = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣']
		config = self.bot.utils.get_config()  # type: dict
		if 'warns' not in config:
			config['warns'] = {}
		if 'expire' not in config['warns']:
			config['warns']['expire'] = []
		if 'punishments' not in config['warns']:
			config['warns']['punishments'] = {}
		self.save_config(config)
		if guild_id not in config:
			config['warns'][guild_id] = {}
		async def wait_for_reaction():
			def check(reaction, user):
				return user == ctx.author
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except asyncio.TimeoutError:
				await ctx.send('Timeout Error')
			else:
				return str(reaction.emoji)
		def emoji(index):
			return emojis[index - 1]
		def default():
			e = discord.Embed(color=colors.fate())
			e.set_author(name='Warn Config', icon_url=ctx.author.avatar_url)
			e.description = \
				f'{emoji(1)} : View Config\n' \
				f'{emoji(2)} : Edit Config\n' \
				f'{emoji(3)} : Cancel\n'
			return e
		complete = False
		msg = await ctx.send(embed=default())
		while not complete:
			await msg.edit(embed=default())
			await msg.clear_reactions()
			await msg.add_reaction(emoji(1))
			await msg.add_reaction(emoji(2))
			await msg.add_reaction(emoji(3))
			reaction = await wait_for_reaction()
			if reaction == emoji(1):
				await msg.clear_reactions()
				config = self.bot.utils.get_config()  # type: dict
				if guild_id not in config['warns']:
					config['warns'][guild_id] = {}
				dat = config['warns']
				expiring = False
				if guild_id in dat['expire']:
					expiring = True
				punishments = 'None'
				if guild_id in dat['punishments']:
					punishments = ''
					index = 1
					for punishment in dat['punishments'][guild_id]:
						punishments += f'**#{index}. `{punishment}`**\n'
				e = discord.Embed(color=colors.fate())
				e.set_author(name='Warn Config', icon_url=ctx.author.avatar_url)
				e.description = f'**Warns Expire: {expiring}\nCustom Punishments:**\n{punishments}'
				await msg.edit(embed=e)
				await msg.add_reaction('⏹')
				await msg.add_reaction('🔄')
				reaction = await wait_for_reaction()
				if reaction == '⏹':
					break
				if reaction == '🔄':
					continue
			if reaction == emoji(2):
				await msg.clear_reactions()
				e = discord.Embed(color=colors.fate())
				e.description = 'Should warns expire after a month?'
				await msg.edit(embed=e)
				await msg.add_reaction('✔')
				await msg.add_reaction('❌')
				reaction = await wait_for_reaction()
				config = self.bot.utils.get_config()  # type: dict
				if reaction == '✔':
					if guild_id not in config['warns']['expire']:
						config['warns']['expire'].append(guild_id)
						self.save_config(config)
				else:
					if guild_id in config['warns']['expire']:
						index = config['warns']['expire'].index(guild_id)
						config['warns']['expire'].pop(index)
				await msg.clear_reactions()
				e = discord.Embed(color=colors.fate())
				e.description = 'Set custom punishments?'
				await msg.edit(embed=e)
				await msg.add_reaction('✔')
				await msg.add_reaction('❌')
				reaction = await wait_for_reaction()
				if reaction == '❌':
					config = self.bot.utils.get_config()  # type: dict
					if guild_id in config['warns']['punishments']:
						del config['warns']['punishments'][guild_id]
						self.save_config(config)
				else:
					await msg.clear_reactions()
					punishments = []
					def dump():
						config = self.bot.utils.get_config()  # type: dict
						if guild_id not in config['warns']:
							config['warns'][guild_id] = {}
						if punishments:
							config['warns']['punishments'][guild_id] = punishments
						else:
							config['warns']['punishments'][guild_id] = ['None']
						self.save_config(config)
					def pos(index):
						positions = ['1st', '2nd', '3rd', '4th', '4th', '6th', '7th', '8th']
						return positions[index - 1]
					index = 1
					finished = False
					while not finished:
						if len(punishments) > 7:
							dump()
							break
						e = discord.Embed(color=colors.fate())
						e.description = f'**Punishments: {punishments}**\n\n' \
							f'Set the {pos(index)} punishment:\n' \
							f'1⃣: None\n2⃣ : Mute\n3⃣ : Kick\n' \
							f'4⃣ : Softban\n5⃣ : Ban\n'
						index += 1
						await msg.edit(embed=e)
						for emoji in emojis:
							await msg.add_reaction(emoji)
						await msg.add_reaction('✔')
						reaction = await wait_for_reaction()
						if reaction == '✔':
							dump()
							break
						options = ['None', 'Mute', 'Kick', 'Softban', 'Ban']
						try:
							reaction_index = emojis.index(reaction)
						except:
							await ctx.send("Invalid reaction >:(")
							continue
						punishments.append(options[reaction_index])
			else:
				if reaction == emoji(3):
					break
			break
		await ctx.message.delete()
		await msg.delete()


def setup(bot):
	bot.add_cog(Config(bot))
