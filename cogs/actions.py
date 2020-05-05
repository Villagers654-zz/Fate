from discord.ext import commands
import discord
import random

class Actions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.protected = [
			264838866480005122,  # luck
			355026215137968129  # tother
		]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(description="Shoots a user")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def shoot(self, ctx, user: discord.Member):
		if user.id in self.protected:
			if ctx.author.id in self.protected:
				return await ctx.send('nO')
			return await ctx.send('*shoots you instead*')
		results = [
			"$user got shot in the head and died instantly",
			"$user got shot in the heart and died quickly and painfully",
			"$user got shot in the arm and is rolling around in agonizing pain",
			"$user got shot in the leg and is now hopping around on one leg",
			"$user got shot in the dick",
			"$user pulled his own gun out and shot you first, seems my stage 4 brain cancer is faster than you",
			"$author shot $user skillfully; piercing $user's heart"
		]
		result = random.choice(results).replace('$user', user.display_name).replace('$author', ctx.author.display_name)
		await ctx.send(f"🔫 | pew pew, {result}")

	@commands.command(description="Injects a user with something random")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def inject(self, ctx, user: discord.Member):
		if user.id in self.protected:
			if ctx.author.id in self.protected:
				return await ctx.send('nO')
			return await ctx.send('*injects you instead*')
		injections = [
			"AIDS", "HIV positive blood", "an STD", "the cure", "FLex Seal", "Kool-Aid powder",
			"soda", "the flu", "Coronavirus", "Covid-19"
		]
		choices = [
			"$user has been injected with $injection", "$user was injected with $injection and died",
			"injected $injection into $user's dick", "$user was injected with $injection and got autism",
			"$author tripped and injected himself with $injection"
		]
		choice = random.choice(choices).replace('$user', user.display_name).replace('$author', ctx.author.display_name)
		await ctx.send(f"💉 | {choice.replace('$injection', random.choice(injections))}")

	@commands.command(description="Slices anything into bits")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def slice(self, ctx, user: discord.Member):
		if user.id in self.protected:
			if ctx.author.id in self.protected:
				return await ctx.send('nO')
			return await ctx.send('*slices you instead*')
		await ctx.send("⚔ | {} {}".format(user.display_name, random.choice(["just got sliced up into sushi", "just got sliced up into string cheese"])))

	@commands.command(description="Boops a user")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def boop(self, ctx, user: discord.Member):
		await ctx.send("<@{}> {} boops {}".format(ctx.author.id, random.choice(["sneakily", "sexually", "forcefully", "gently", "softly"]), user.name))
		await ctx.message.delete()

	@commands.command(description="Gives a user anything of your choosing")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def give(self, ctx, *, item):
		await ctx.send("<@{}> gives {}".format(ctx.author.id, item))
		await ctx.message.delete()

	@commands.command(description="Stabs a user")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def stab(self, ctx, user: discord.Member):
		if user.id in self.protected:
			if ctx.author.id in self.protected:
				return await ctx.send('nO')
			return await ctx.send('*stabs you instead*')
		await ctx.send("⚔ | {} {}, {}".format(user.display_name, random.choice(["has been stabbed in the head", "has been stabbed in the shoulder", "has been stabbed in the chest", "has beeb stabbed in the arm", "has been stabbed in the gut", "has been stabbed in the dick", "has been stabbed in the leg", "has been stabbed in the foot"]), random.choice(["you really shouldn't let a bot carry a blade :p", "you should let me stab people more often", "you should let me stab **it** more often", "this is fun", "poor thing didn't stand a chance", "whatever that **thing** is, it definitely deserved it", "poor thing dropped like a fly"])))

	@commands.command(description="You simply die")
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def die(self, ctx, *, member: discord.Member=None):
		try:
			if member is None:
				member = ctx.author
			await ctx.send(f'{member.name} dies')
			await ctx.message.delete()
		except Exception as e:
			await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**', delete_after=10)

	@commands.command(name='kms', aliases=['suicide'], description="Textart")
	@commands.cooldown(1, 5, commands.BucketType.channel)
	async def kms(self, ctx):
		if ctx.author.id in self.protected:
			return await ctx.send('nO')
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
