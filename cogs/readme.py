from discord.ext import commands
from datetime import datetime
from utils import checks, colors
import discord

class Readme(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.group(name='update')
	@commands.check(checks.luck)
	async def _update(self, ctx):
		if not ctx.invoked_subcommand:
			await ctx.send('Improper subcommand passed')

	@_update.command(name='2b2t')
	async def _oof(self, ctx):
		channel = self.bot.get_channel(579828107863916565)
		msg = await channel.fetch_message(579873497023643658)
		e = discord.Embed(color=0x40E0D0)
		e.set_author(name="💎 Official 2B2TBE Discord Server 💎")
		e.description = "■ Server: play.2b2t.be : 19132\n■ Full Vanilla Features\n■ Supreme Anti-Cheat\n■ Full Anarchy"
		e.add_field(name="-~===🌹🥂🍸🍷Links🍷🍸🥂🌹===~-", value="■ [Invite](http://discord.gg/azjzfvn) | [Vote](https://google.com) | [Donate](https://google.com)", inline=False)
		e.add_field(name='-~===🌹🥂🍸🍷Founders🍷🍸🥂🌹===~-', value='Master Luke, Maxxie115, FishyBear, Ginjeet, Legit, Luck')
		e.add_field(name="-~===🌹🥂🍸🍷Rules🍷🍸🥂🌹===~-", value='■ Channel topics contain most rules\n'
			'■ First offense results in mute (warning some cases)\n'
			'■ Second offense results in a kick\n'
			'■ Third offense results in ban\n'
			'■ Depending on the severity of ones actions lower grade crimes don\'t have to be punished in strict order and can receive repeated mutes with extended time.\n' \
			'■ Amount of time between each offense is taken into notice\n'
			'■ Warnings are just warnings, whether or not you receive a warning or mute is entirely up to the mod unless told otherwise by a higher position\n'
			'■ Some bot commands can be ignored if they contribute to the chat in a certain manner, for instance, reaction commands are allowed depending on the channel, or if you\'re that special little someone that pushes the rules, no spammy bot commands\n'
			'■ Things outside of the rules can be deemed punishment worthy', inline=False)
		e.add_field(name="~==🌹🥂🍸🍷Global Rules🍷🍸🥂🌹==~", value='■ This server abides by discords TOS, therefore breaking the TOS counts as an offense\n'
		    '■ Leaving to avoid mute results in a higher grade punishment of our choice\n'
			'■ No doxxing (limited to this discord)\n'
			'■ No pinging roles (this goes for mods too)\n'
			'■ No gifs / videos / emotes with flashing lights that may trigger epilepsy\n'
			'■ Be respectful with handling the music bots, (no earrape, no skipping to annoy people, and no skipping inconsideratly)\n'
			'■ No pestering staff repetitively\n'
			'■ No useless / annoying pings\n'
			'■ No spamming', inline=False)
		e.add_field(name="-~===🌹🥂🍸🍷Misc🍷🍸🥂🌹===~-", value="Minecraft Version: unknown", inline=False)
		e.set_thumbnail(url=channel.guild.icon_url)
		await msg.edit(embed=e)
		await ctx.message.delete()

	@_update.command(name='4b4t')
	async def _readme(self, ctx):
		try:
			channel = self.bot.get_channel(470963498914938880)
			msg = await channel.fetch_message(521271462754254849)
			e = discord.Embed(color=0x40E0D0)
			e.set_author(name="💎 Official 4B4T Discord Server 💎")
			e.description = "■ Server: 4b4t.net : 19132\n■ Full Vanilla Features\n■ Full Anarchy"
			e.add_field(name="-~===🌹🥂🍸🍷Links🍷🍸🥂🌹===~-", value="■ Invite: discord.gg/BQ23Z2E\n■ Vote: legitanarchy.ml", inline=False)
			e.add_field(name="-~===🌹🥂🍸🍷Rules🍷🍸🥂🌹===~-", value="""■ Channel topics contain most rules
■ First offense results in mute (warning some cases)
■ Second offense results in a kick
■ Third offense results in ban
■ Depending on the severity of ones actions lower grade crimes don't have to be punished in strict order and can receive repeated mutes with extended time. 
■ Amount of time between each offense is taken into notice
■ Warnings are just warnings, whether or not you receive a warning or mute is entirely up to the mod unless told otherwise by a higher position
■ Some bot commands can be ignored if they contribute to the chat in a certain manner, for instance, reaction commands are allowed depending on the channel, or if you're that special little someone that pushes the rules, no spammy bot commands
■ Things outside of the rules can be deemed punishment worthy""", inline=False)
			e.add_field(name="~==🌹🥂🍸🍷Global Rules🍷🍸🥂🌹==~", value="""■ This server abides by discords TOS, therefore breaking the TOS counts as an offense\n■ Leaving to avoid mute results in a higher grade punishment of our choice
■ No doxxing (limited to this discord)
■ No pinging roles (this goes for mods too)
■ No gifs / videos / emotes with flashing lights that may trigger epilepsy
■ Be respectful with handling the music bots, (no earrape, no skipping to annoy people, and no skipping inconsideratly)
■ No pestering staff repetitively
■ No useless / annoying pings
■ No spamming""", inline=False)
			e.add_field(name="-~===🌹🥂🍸🍷Misc🍷🍸🥂🌹===~-", value="Minecraft Version: 1.12", inline=False)
			e.set_thumbnail(url=channel.guild.icon_url)
			self.bot.unload_extension('cogs.readme')
			self.bot.load_extension('cogs.readme')
			await msg.edit(embed=e)
			await ctx.message.add_reaction('👍')
		except Exception as e:
			await ctx.send(f'update failed```{e}```')

	@_update.command(name='esr')
	async def _esr(self, ctx):
		ar = self.bot.get_guild(548461409810251776)
		msg = await self.bot.get_channel(548677537140572160).fetch_message(549484739162275840)
		e = discord.Embed(color=colors.cyan())
		e.set_author(name="💎 Exousía Supreme Regimee 💎")
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"■ **[2P2E:](https://discord.gg/XGw58UZ)** play.2p2e.net : 19132\n" \
			f"■ **[4b4t:](https://discord.gg/BQ23Z2E)** 4b4t.net : 19132\n" \
			f"-~==🌹🥂🍸🍷Readme🍷🍸🥂🌹==~-\n" \
			f"■ Welcome To Esr\n" \
			f"■ ree reeee reeeeeeeeee\n" \
			f"-~===🌹🥂🍸🍷Roles🍷🍸🥂🌹===~-\n" \
			f"■ {ar.get_role(548679250430132237).mention} - <a:tother:542643529726296074>\n" \
			f"• Team Leaders\n" \
			f"■ {ar.get_role(548679738915422249).mention} - <a:happy_banana:542646975267340298>\n" \
			f"• **Discord** Admin\n" \
			f"■ {ar.get_role(548680104574976001).mention} - <a:lolidance:542643279984984069>\n" \
			f"• Elite Member\n" \
			f"■ {ar.get_role(548679428767481871).mention} - \n" \
			f"• Official Member\n" \
			f"■ {ar.get_role(549467413016739843).mention} - \n" \
			f"• Ally of ESR\n" \
			f"-~===🌹🥂🍸🍷Rules🍷🍸🥂🌹===~-\n" \
			f"■ No being fucking retarded\n" \
			f"-~===🌹🥂🍸🍷Misc🍷🍸🥂🌹===~-\n"
		e.set_image(url="https://cdn.discordapp.com/attachments/501871950260469790/559193926318424084/RankCriteria.png")
		e.set_footer(text=f"Last Updated: {datetime.now().strftime('%m-%d-%Y %I:%M%p')}")
		await msg.edit(embed=e)
		return await ctx.message.delete()

def setup(bot):
	bot.add_cog(Readme(bot))
