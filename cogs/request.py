import asyncio
from discord.ext import commands
import discord

class Request(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last = {}

	@commands.command(name='request')
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def request(self, ctx, *, request):
		channel = self.bot.get_channel(608027431432880148)
		e = discord.Embed(color=ctx.author.color)
		e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.description = request
		e.set_footer(text=ctx.author.id)
		msg = await channel.send(embed=e)
		await msg.add_reaction('✔')
		await msg.add_reaction('❌')
		await ctx.send('Sent your request', delete_after=5)
		await asyncio.sleep(5)
		await ctx.message.delete()

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, data):
		if not self.bot.get_user(data.user_id).bot:
			channel = self.bot.get_channel(608027431432880148)
			if data.channel_id == channel.id:
				msg = await channel.fetch_message(data.message_id)
				request = msg.embeds[0].description
				user_id = msg.embeds[0].footer.text
				user = self.bot.get_user(int(user_id))
				if str(data.emoji) == "✔":
					try: await user.send(f'Your request for `{request}` was accepted')
					except: pass
				else:
					try: await user.send(f'Your request for `{request}` was denied')
					except: pass
				await msg.delete()

def setup(bot):
	bot.add_cog(Request(bot))
