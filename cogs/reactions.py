from discord.ext import commands
from utils import colors, checks
import requests
import discord
import asyncio
import random
import json
import os

class Reactions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="tenor")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _tenor(self, ctx, *, search):
		apikey = "LIWIXISVM3A7"
		lmt = 50
		r = requests.get("https://api.tenor.com/v1/anonid?key=%s" % apikey)
		if r.status_code == 200:
			anon_id = json.loads(r.content)["anon_id"]
		else:
			anon_id = ""
		r = requests.get("https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s&anon_id=%s" % (search, apikey, lmt, anon_id))
		if r.status_code == 200:
			try:
				dat = json.loads(r.content)
				e = discord.Embed(color=colors.random())
				e.set_image(url=dat['results'][random.randint(0, len(dat['results']) - 1)]['media'][0]['gif']['url'])
				e.set_footer(text="Powered by Tenor")
				await ctx.send(embed=e)
				await ctx.message.delete()
			except Exception as e:
				await ctx.send(e)
		else:
			await ctx.send("error")

	@commands.command(name="intimidate")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _intimidate(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/apple/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/apple/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()
		self.update_data_usage(path)

	@commands.command(name="junkfood")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _junkfood(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/junkfood/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/junkfood/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="powerup")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _powerup(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/powerup/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/powerup/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="observe")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _observe(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/observe/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/observe/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="fatehug")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _fatehug(self, ctx, *, user):
		path = os.getcwd() + "/data/images/reactions/hug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hug/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(f'◈ {self.bot.user.mention} hugs {user} ◈', file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="disgust")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _disgust(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/disgust/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/disgust/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="snuggle")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _snuggle(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/snuggle/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/snuggle/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f'{ctx.author.display_name} to {user.display_name}')
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="admire")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _admire(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/admire/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/admire/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="angery")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _angery(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/angery/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/angery/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="psycho")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _psycho(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/psycho/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/psycho/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="waste")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _waste(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/waste/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/waste/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} to {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="thonk")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _thonk(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/thonk/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/thonk/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="shrug")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _shrug(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/shrug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/shrug/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="yawn")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _yawn(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/yawn/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/yawn/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="sigh")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _sigh(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/sigh/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/sigh/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="bite")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _bite(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/bite/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/bite/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} bites {user.display_name}: ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="wine")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _wine(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/wine/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/wine/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="hide")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _hide(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/hide/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hide/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="slap")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _slap(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/slap/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/slap/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} slaps {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="kiss")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _kiss(self, ctx, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/kiss/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/kiss/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} kisses {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="kill")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _kill(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/kill/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/kill/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} to {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="hug")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _hug(self, ctx, *, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/hug/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/hug/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} hugs {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="teasip", aliases=["tea", "st"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _teasip(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/tea/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/tea/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="cry")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _cry(self, ctx, *, content=""):
		path = os.getcwd() + "/data/images/reactions/cry/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/cry/"))
		e = discord.Embed(color=colors.fate())
		if content:
			e.set_author(name=f"{content}", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="pat")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def _pat(self, ctx, user: discord.Member):
		path = os.getcwd() + "/data/images/reactions/pat/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/pat/"))
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f"◈ {ctx.author.display_name} pats {user.display_name} ◈", icon_url=ctx.author.avatar_url)
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name="horsecock")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True)
	async def _horsecock(self, ctx):
		path = os.getcwd() + "/data/images/misc/horsecock/" + random.choice(os.listdir(os.getcwd() + "/data/images/misc/horsecock/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command(name="rape")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True)
	async def _rape(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.set_image(url="https://cdn.discordapp.com/attachments/507914723858186261/551085804076793876/received_538311363348269.jpeg")
		await ctx.send(embed=e)
		await ctx.message.delete()

	@commands.command(name="homo")
	@commands.check(checks.luck)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _homo(self, ctx):
		path = os.getcwd() + "/data/images/reactions/homo/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/homo/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

def setup(bot):
	bot.add_cog(Reactions(bot))
