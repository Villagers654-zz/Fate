import asyncio
import random
from discord.ext import commands
import discord
from utils import checks, colors


class Sliders:

	def max(self):
		e = discord.Embed(color=colors.red())
		e.set_author(name='2B2TMCPE - Minecraft Anarchy', icon_url='https://cdn.discordapp.com/avatars/293420269832503306/a574a59c804e0797da44751e76cf324e.webp?size=1024')
		e.set_thumbnail(url='https://cdn.discordapp.com/icons/630178744908382219/0a254e8cb841ba9a9d3193b5b03da4f8.webp?size=1024')
		e.set_image(url='https://cdn.discordapp.com/icons/630178744908382219/0a254e8cb841ba9a9d3193b5b03da4f8.webp?size=1024')
		e.description = 'This is a minecraft bedrock edition server that is based on 2b2t.org, ' \
		    'and it is complete anarchy. On this server you can do whatever you want: kill players, ' \
		    'spam, trap spawn, hack, fly, poison players, loot, mine. But be aware that other players ' \
		    'will also do the same, and you will die, a lot. Good luck! For more challenges, ' \
		    '(Disclaimer, we have nothing to do with the actual 2b2t.org server). The servers owned by ' \
		    'lordliam8 and Maxxie115 that runs on the server software NukkitX. 2b2tmcpe.org is currently ' \
		    'over 1 year old and has a large and active player base comprised of many Taiwanese and English players.\n' \
		    '**IP:** __2b2tmcpe.org__ **port:** __19132__\n**Discord:** [click here](https://discord.gg/dg7j5JF/)'
		image_urls = [
			'https://cdn.discordapp.com/attachments/630180017921327115/634189147178795019/Screenshot_20190305-215348_BlockLauncher-1.jpg',
			'https://cdn.discordapp.com/attachments/630178745403179040/634189168456630272/IMG_2266.PNG',
			'https://cdn.discordapp.com/attachments/630178745403179040/634189168926392350/IMG_2276.PNG',
			'https://cdn.discordapp.com/attachments/630178745403179040/634189473717944340/IMG_2267.PNG',
			'https://cdn.discordapp.com/attachments/630178745403179040/634195810501787649/image0.jpg'
		]
		e.set_image(url=random.choice(image_urls))
		return e

	def rotten_union(self):
		e = discord.Embed(color=colors.purple())
		e.set_author(name='Rotten Union', icon_url='https://cdn.discordapp.com/avatars/395228090013450241/f1f9803fa97805133dd18fc32e798ea1.webp?size=1024')
		e.set_thumbnail(url='https://cdn.discordapp.com/attachments/642452511940280341/642460088312791060/662c684f2a983df4f85f.gif')
		e.description = "Hello, and welcome to the up and coming TF2 community servers:\n" \
						"Rotten Servers.\nCurrently we don't own any servers, but of course the more the merrier.\n" \
		                "-giveaways\n-plenty of roles, and possibly more if you tell us to add some\n" \
						"-mee6 ranking for that satisfying achievement feeling\n" \
						"-healthy and friendly community\n" \
						"-space to help you grow into your dreams\n" \
						"-constantly online admins for your safety\n" \
						"-always ready to hear your suggestions and to adapt to your liking\n" \
						"e hope you, by joining, will help us grow to a massive and well known community, happiness is not something we lack.\n" \
		                "Discord: [click here to join](https://discord.gg/PSc259G)"
		e.set_image(url='https://cdn.discordapp.com/attachments/642452511940280341/642458545316691989/images.png')
		return e



	#def luke(self):
	#	e = discord.Embed(color=colors.green())
	#	e.set_author(name='2B2TPE - Minecraft Anarchy', icon_url='https://cdn.discordapp.com/avatars/451107694934360094/b9b03963ff0eb72a1160412f2e2bfea4.webp?size=1024')
	#	e.set_thumbnail(url='https://cdn.discordapp.com/icons/523678393565315077/1224c92145828542ac266dcf8804f70d.webp?size=1024')
	#	e.description = '2B2TPE.ORG is an anarchy server based on 2b2t.org. At the moment it has the largest map when ranked with the other servers, ' \
	#	    '(over 200gb), and one of the longest running maps of all bedrock anarchy servers, second only to 2p2e\n\n__For IOS, Android, and Windows 10:__\n**IP:** `2b2tPE.org` **Port:** `19132`\n' \
	#	    '__For IOS, Android, Windows10, and Java:__\n**IP:** `2b2tPE.org` **Port:** `19153`\n' \
	#	    '**Discord:** [click here](https://discord.gg/Ha5wxwd)'
	#	return e

	#def mars(self):
	#	e = discord.Embed(color=colors.orange())
	#	e.set_author(name='Mars', icon_url='https://cdn.discordapp.com/avatars/544911653058248734/a_12ff164baa36ae2171358e968d148f4f.gif?size=1024')
	#	e.set_thumbnail(url='https://cdn.discordapp.com/icons/610638435711189002/a_4841a26e78005fcf7b36974d0ab7d3eb.gif?size=1024')
	#	e.description = 'Come land on Mars, where you can hang out with other Mars enthusiasts and talk games, pets, bots, or anything else, and even start your own fan club!'
	#	return e

class Polis(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.slideshow_interval = 120
		self.protected = {
			"channels": [
				502236124308307968
			],
			"roles": [
				612384935159922699
			]
		}
		self.emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
		self.emoji = random.choice(self.emojis)
		if self.bot.is_ready():
			bot.loop.create_task(self.update_rules())

	async def showcase_slider(self):
		""" embeded partnership slideshow """
		channel = self.bot.get_channel(610767401386115091)
		msg = await channel.fetch_message(634162917935284226)
		while True:
			servers = [eval(f'Sliders().{func}()') for func in dir(Sliders()) if not func.startswith('__')]
			for embed in servers:
				await msg.edit(embed=embed)
				await asyncio.sleep(self.slideshow_interval)
			await asyncio.sleep(1)

	async def update_rules(self):
		channel = self.bot.get_channel(470963498914938880)
		msg = await channel.fetch_message(521271462754254849)
		e = discord.Embed(color=0x40E0D0)  # cyan
		e.set_thumbnail(url=channel.guild.icon_url)
		emoji = random.choice(self.emojis)
		self.emoji = emoji
		verified = [
			m for m in channel.guild.members if 612384935159922699 in [r.id for r in m.roles]
		]
		e.set_author(
			name=f'{len(verified)} of {channel.guild.member_count} Members Verified',
			icon_url=self.bot.get_emoji(585566210067005500).url
		)
		e.description = f"React with {emoji} to get access to the server. If you fail you'll be kicked, " \
		                f"and the emoji changes every time after you react."
		with open('./data/misc/rules.txt', 'r') as f:
			content = f.read()
		content = content.replace(':status_online:', str(self.bot.get_emoji(659976003334045727)))
		content = content.replace(':status_idle:', str(self.bot.get_emoji(659976006030983206)))
		content = content.replace(':status_dnd:', str(self.bot.get_emoji(659976008627388438)))
		content = content.replace(':status_offline:', str(self.bot.get_emoji(659976011651219462)))
		return await msg.edit(content=content, embed=e)

	@commands.command(name='start-slider')
	@commands.check(checks.luck)
	async def start_slider(self, ctx):
		self.bot.loop.create_task(self.showcase_slider())
		await ctx.send('👍', delete_after=3)
		await asyncio.sleep(3)
		await ctx.message.delete()

	@commands.command(name='update-readme')
	async def update_readme(self, ctx):
		await self.update_rules()
		await ctx.message.add_reaction('👍')

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.showcase_slider())
		self.bot.loop.create_task(self.update_rules())

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if payload.message_id == 521271462754254849:
			channel = self.bot.get_channel(payload.channel_id)
			msg = await channel.fetch_message(payload.message_id)
			member = channel.guild.get_member(payload.user_id)
			role = channel.guild.get_role(612384935159922699)
			if str(payload.emoji) not in self.emojis:
				await msg.remove_reaction(payload.emoji, member)
				return await self.update_rules()
			if str(payload.emoji) != self.emoji:
				await msg.remove_reaction(payload.emoji, member)
				if role not in member.roles:
					await self.update_rules()
					try:
						return await member.kick(reason='Failed Human Verification')
					except:
						pass
				return
			if role not in member.roles:
				await member.add_roles(role)
			await msg.remove_reaction(payload.emoji, member)
			await self.update_rules()

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		if role.id in self.protected['roles']:
			async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
				await entry.user.ban()

def setup(bot):
	bot.add_cog(Polis(bot))
