from discord.ext import commands
import discord
import random

class Actions:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(description="Shoots a user")
	async def shoot(self, ctx, user: discord.Member):
		await ctx.send("🔫 | pew pew, {} {}, {}".format(user.display_name, random.choice(["has been shot in the head and died instantly", "has been shot in the heart and died quickly and painfully", "has been shot in the arm and is rolling around in agonizing pain", "has been shot in the leg and is now hopping around on one leg like an autist", "has been shot in the dick"]), random.choice(["you really shouldn't let a bot carry a gun :p", "you should let me shoot people more often", "you should let me shoot faggots more often", "this is fun", "poor faggot didn't stand a chance", "he/she definitely deserved it", "poor autist dropped like a fly"])))

	@commands.command(description="Injects a user with something random")
	async def inject(self, ctx, user: discord.Member):
		await ctx.send("💉 | {} {}".format(user, random.choice(["has been injected with AIDS", "has been injected with HIV positive blood", "has been injected with an STD", "has been injected with the cure", "has been injected with Flex Seal", "has been injected with Kool-Aid powder"])))

	@commands.command(description="Slices anything into bits")
	async def slice(self, ctx, user: discord.Member):
		await ctx.send("⚔ | {} {}".format(user.display_name, random.choice(["just got sliced up into sushi", "just got sliced up into string cheese"])))

	@commands.command(description="Boops a user")
	async def boop(self, ctx, user: discord.Member):
		await ctx.send("<@{}> {} boops {}".format(ctx.author.id, random.choice(["sneakily", "sexually", "forcefully", "gently", "softly"]), user.display_name))
		await ctx.message.delete()

	@commands.command(description="Gives a user anything of your choosing")
	async def give(self, ctx, *, item):
		await ctx.send("<@{}> gives {}".format(ctx.author.id, item))
		await ctx.message.delete()

	@commands.command(description="Stabs a user")
	async def stab(self, ctx, user: discord.Member):
		await ctx.send("⚔ | {} {}, {}".format(user.display_name, random.choice(["has been stabbed in the head", "has been stabbed in the shoulder", "has been stabbed in the chest", "has beeb stabbed in the arm", "has been stabbed in the gut", "has been stabbed in the dick", "has been stabbed in the leg", "has been stabbed in the foot"]), random.choice(["you really shouldn't let a bot carry a blade :p", "you should let me stab people more often", "you should let me stab faggots more often", "this is fun", "poor faggot didn't stand a chance", "whatever that **thing** is, it definitely deserved it", "poor autist dropped like a fly"])))

	@commands.command(description="You simply die")
	async def die(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			await ctx.send(f'{member.name} dies')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=10)

	@commands.command(name='kms', aliases=['suicide'], description="Textart")
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
	bot.add_cog(Actions(bot))
