from discord.ext import commands
from utils import colors
import requests
import discord
import random
import json
import os

class Reactions:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.author.id == 264838866480005122

	@commands.command(name="findgif", aliases=["gifsearch", "searchgif"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _findgif(self, ctx, *, search):
		apikey = "LIWIXISVM3A7"
		lmt = 8
		r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
		if r.status_code == 200:
			anon_id = json.loads(r.content)["anon_id"]
		else:
			anon_id = ""
		search_term = search
		r = requests.get("https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s" % (search_term, apikey, lmt, anon_id))
		if r.status_code == 200:
			try:
				dat = json.loads(r.content)
				e = discord.Embed(color=colors.random())
				e.set_image(url=dat['results'][random.randint(0, 7)]['media'][0]['gif']['url'])
				e.set_footer(text="Powered by Tenor")
				await ctx.send(embed=e)
				await ctx.message.delete()
			except:
				await ctx.send("error")
		else:
			await ctx.send("error")

	@commands.command(name='intimidate')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _intimidate(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/apple/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/apple/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def junkfood(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/junkfood/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/junkfood/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def powerup(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/powerup/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/powerup/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def observe(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/observe/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/observe/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def fatehug(self, ctx, *, content):
		path = os.getcwd() + "/data/images/reactions/hug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hug/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(f'◈ <@506735111543193601> hugs {content} ◈', file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name='disgust', aliases=['ew'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def disgust(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/disgust/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/disgust/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def snuggle(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/snuggle/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/snuggle/"))
		e = discord.Embed()
		e.set_author(name=f'{ctx.author.display_name} to {user.display_name}')
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def admire(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/admire/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/admire/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def angery(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/angery/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/angery/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name='psycho')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _psycho(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/psycho/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/psycho/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name="waste", aliases=["wasted"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def waste(self, ctx, *, content):
		path = os.getcwd() + "/data/images/reactions/waste/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/waste/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send('◈ <@{}> to {}: ◈'.format(ctx.message.author.id, content), file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def thonk(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/thonk/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/thonk/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def shrug(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/shrug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/shrug/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def yawn(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/yawn/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/yawn/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def sigh(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/sigh/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/sigh/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name="bite")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _hug(self, ctx, *, user):
		path = os.getcwd() + "/data/images/reactions/bite/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/bite/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(f"◈ {ctx.author.mention} bites {user} ◈", file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name="wine")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _wine(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/wine/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/wine/"))
		e = discord.Embed()
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name='hide')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _hide(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/hide/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hide/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def slap(self, ctx, *, content):
		path = os.getcwd() + "/data/images/reactions/slap/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/slap/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ <@{}> slaps {} ◈'.format(ctx.message.author.id, content), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def kiss(self, ctx, *, content):
		path = os.getcwd() + "/data/images/reactions/kiss/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/kiss/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ <@{}> kisses {} ◈'.format(ctx.message.author.id, content), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name='kill', aliases=['pacify'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def kill(self, ctx, *, user):
		path = os.getcwd() + "/data/images/reactions/kill/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/kill/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send('◈ <@{}> to {}: ◈'.format(ctx.message.author.id, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def hug(self, ctx, *, user):
		path = os.getcwd() + "/data/images/reactions/hug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hug/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send('◈ <@{}> hugs {} ◈'.format(ctx.message.author.id, user), file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command(name='tea', aliases=['sipstea', 'teasip', 'st', 'ts'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def tea(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/tea/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/tea/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def cry(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/cry/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/cry/"))
		e = discord.Embed()
		if len(content) > 0:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		else:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pat(self, ctx, *, arg):
		path = os.getcwd() + "/data/images/reactions/pat/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/pat/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send('◈ <@{}> pats {} ◈'.format(ctx.message.author.id, arg), file=discord.File(path, filename=os.path.basename(path)), embed=e)

# ~== Fun ==~

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def horsecock(self, ctx):
		path = os.getcwd() + "/data/images/misc/horsecock/" + random.choice(os.listdir(os.getcwd() + "/data/images/misc/horsecock/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command(name="rape")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _rape(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.set_image(url="https://cdn.discordapp.com/attachments/507914723858186261/551085804076793876/received_538311363348269.jpeg")
		await ctx.send(embed=e)
		await ctx.message.delete()

# ~== Misc == ~

	@commands.command()
	@commands.check(luck)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def homo(self, ctx):
		path = os.getcwd() + "/data/images/reactions/homo/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/homo/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

def setup(bot):
	bot.add_cog(Reactions(bot))
