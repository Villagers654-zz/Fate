from discord.ext import commands
import discord
import random

class mainclass:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_actions(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	@commands.command()
	async def crucify(self, ctx, arg):
		e=discord.Embed(description="has crucified {}".format(arg), color=0x000001)
		e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/505160690932121613/crucify-147995__340.png")
		await ctx.send(embed=e)
		await ctx.message.delete()

	@commands.command()
	async def cookie(self, ctx, *, arg):
		await ctx.send("🍪 | <@{}> gives {} a cookie".format(ctx.author.id, arg))
		await ctx.message.delete()

	@commands.command()
	async def shoot(self, ctx, *, arg):
		await ctx.send("🔫 | pew pew, {} {}, {}".format(arg, random.choice(["has been shot in the head and died instantly", "has been shot in the heart and died quickly and painfully", "has been shot in the arm and is rolling around in agonizing pain", "has been shot in the leg and is now hopping around on one leg like an autist", "has been shot in the dick"]), random.choice(["you really shouldn't let a bot carry a gun :p", "you should let me shoot people more often", "you should let me shoot faggots more often", "this is fun", "poor faggot didn't stand a chance", "he/she definitely deserved it", "poor autist dropped like a fly"])))

	@commands.command()
	async def inject(self, ctx, *, arg):
		await ctx.send("💉 | {} {}".format(arg, random.choice(["has been injected with AIDS", "has been injected with HIV positive blood", "has been injected with an STD", "has been injected with the cure", "has been injected with Flex Seal", "has been injected with Kool-Aid powder"])))

	@commands.command()
	async def slice(self, ctx, *, arg):
		await ctx.send("⚔ | {} {}".format(arg, random.choice(["just got sliced up into sushi", "just got sliced up into string cheese"])))

	@commands.command()
	async def boop(self, ctx, *, arg):
		await ctx.send("<@{}> {} boops {}".format(ctx.author.id, random.choice(["sneakily", "sexually", "forcefully", "gently", "softly"]), arg))
		await ctx.message.delete()

	@commands.command()
	async def give(self, ctx, *, arg):
		await ctx.send("<@{}> gives {}".format(ctx.author.id, arg))
		await ctx.message.delete()

	@commands.command()
	async def stab(self, ctx, arg):
		await ctx.send("⚔ | {} {}, {}".format(arg, random.choice(["has been stabbed in the head", "has been stabbed in the shoulder", "has been stabbed in the chest", "has beeb stabbed in the arm", "has been stabbed in the gut", "has been stabbed in the dick", "has been stabbed in the leg", "has been stabbed in the foot"]), random.choice(["you really shouldn't let a bot carry a blade :p", "you should let me stab people more often", "you should let me stab faggots more often", "this is fun", "poor faggot didn't stand a chance", "whatever that **thing** is, it definitely deserved it", "poor autist dropped like a fly"])))

	@commands.command()
	async def die(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			await ctx.send(f'{member.name} dies')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=10)

	@commands.command(name='kms', aliases=['suicide'])
	async def kms(self, ctx):
		await ctx.send("""━━━━━┒
┓┏┓┏┓┃Oof
┛┗┛┗┛┃＼O／
┓┏┓┏┓┃ /
┛┗┛┗┛┃ノ)
┓┏┓┏┓┃ 
┛┗┛┗┛┃ 
┓┏┓┏┓┃ 
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┛┗┛┗┛┃ 
┓┏┓┏┓┃ 
┛┗┛┗┛┃ 
┓┏┓┏┓┃ 
┛┗┛┗┛┃ 
┓┏┓┏┓┃
┃┃┃┃┃┃
┻┻┻┻┻┻""")

def setup(bot):
    bot.add_cog(mainclass(bot))
