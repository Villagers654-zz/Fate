from utils import checks, colors
from discord.ext import commands
import datetime
import discord

class AvapxianRegime(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="update")
	@commands.check(checks.luck)
	async def updatestuff(self, ctx, item):
		item = item.lower()
		ar = self.bot.get_guild(548461409810251776)
		if item == "info":
			msg = await self.bot.get_channel(548677537140572160).get_message(549484739162275840)
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
			e.set_footer(text=f"Last Updated: {datetime.datetime.now().strftime('%m-%d-%Y %I:%M%p')}")
			await msg.edit(embed=e)
			return await ctx.message.delete()
		if item == "rules":
			msg = await self.bot.get_channel(542568067495100416).get_message(542588249646956544)
			e = discord.Embed(color=colors.red())
			e.set_thumbnail(url="https://cdn.discordapp.com/attachments/507914723858186261/542935248262922270/avapxian_regime_red.png")
			e.description = "yeet"
			fmt = "%m-%d-%Y %I:%M%p"
			e.set_footer(text=f"Last Updated: {datetime.datetime.now().strftime(fmt)}")
			await msg.edit(embed=e)
			return await ctx.message.delete()

	@commands.command(name="_update")
	@commands.check(checks.luck)
	async def _update(self, ctx):
		server = self.bot.get_guild(566461197860470804)
		msg = await self.bot.get_channel(567821718798860306).fetch_message(567823095164043267)
		e = discord.Embed(color=colors.cyan())
		e.set_author(name=f"💎 {ctx.guild.name} Partners 💎")
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = f"■ [4B4T - Gone Sexual](https://discord.gg/BQ23Z2E)\n• Description"
		e.set_footer(text=f"Last Updated: {datetime.datetime.now().strftime('%m-%d-%Y %I:%M%p')}")
		await msg.edit(embed=e)
		await ctx.message.delete()

def setup(bot):
	bot.add_cog(AvapxianRegime(bot))
