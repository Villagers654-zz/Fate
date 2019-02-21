from discord.ext import commands
from py_mcpe_stats import Query

class query:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="query")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _query(self, ctx, host, port: int=19132):
		q = Query(host, port)
		server_data = q.query()
		await ctx.send(server_data.MOTD)

def setup(bot):
	bot.add_cog(query(bot))
