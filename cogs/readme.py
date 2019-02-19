from discord.ext import commands
import discord

class customclass:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_readme(self, ctx):
		await ctx.send('working')

# ~== Fun ==~

	@commands.command()
	async def updatereadme(self, ctx):
		try:
			channel = self.bot.get_channel(470963498914938880)
			msg = await channel.get_message(521271462754254849)
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
			e.add_field(name="~==🌹🥂🍸🍷Global Rules🍷🍸🥂🌹==~", value="""■ Leaving to avoid mute results in a higher grade punishment of our choice
■ No doxxing (limited to this discord)
■ No pinging roles (this goes for mods too)
■ No gifs / videos / emotes with flashing lights that may trigger epilepsy
■ Be respectful with handling the music bots, (no earrape, no skipping to annoy people, and no skipping inconsideratly)
■ No pestering staff repetitively
■ No useless / annoying pings
■ No spamming""", inline=False)
			e.add_field(name="-~===🌹🥂🍸🍷Misc🍷🍸🥂🌹===~-", value="Minecraft Version: 1.9", inline=False)
			e.set_thumbnail(url=channel.guild.icon_url)
			self.bot.unload_extension('cogs.readme')
			self.bot.load_extension('cogs.readme')
			await msg.edit(embed=e)
			await ctx.message.add_reaction('👍')
		except Exception as e:
			await ctx.send(f'update failed```{e}```')


# ~== Pings ==~

def setup(bot):
	bot.add_cog(customclass(bot))
