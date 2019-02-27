from discord.ext import commands
import subprocess
import discord
import asyncio

class Owner:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command(name="changepresence", aliases=["cp"])
	@commands.check(luck)
	async def changepresence(self, ctx, *, arg):
		async with ctx.typing():
			await self.bot.change_presence(activity=discord.Game(name=arg))
			await ctx.send('done', delete_after=5)
			await asyncio.sleep(5)
			await ctx.message.delete()

	@commands.command()
	@commands.check(luck)
	async def sendfile(self, ctx, directory):
		if "fate/" in directory:
			directory = directory.replace("fate/", "/home/luck/FateZero/")
		await ctx.send(file=discord.File(directory))

	@commands.command(name='console', aliases=['c'])
	@commands.check(luck)
	async def console(self, ctx, *, command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		await ctx.send(f"```{msg[:1994]}```")

	@commands.command()
	@commands.check(luck)
	async def logout(self, ctx):
		await ctx.send('logging out')
		await self.bot.logout()

	@commands.command()
	@commands.check(luck)
	async def error(self, ctx):
		p = subprocess.Popen("cat  /root/.pm2/logs/bot-error.log", stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output).replace("\\t", "    ").replace("b'", "").replace("`", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		msg = msg[::-1]
		msg = msg[:msg.find("Ignoring"[::-1])]
		await ctx.send(f"```Ignoring{msg[::-1]}```")

	async def on_message(self, m: discord.Message):
		if m.content.lower().startswith("pls magik <@264838866480005122>"):
			def pred(m):
				return m.author.id == 270904126974590976 and m.channel == m.channel
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
			except asyncio.TimeoutError:
				async for i in m.channel.history(limit=10):
					await i.delete()
				await asyncio.sleep(10)
				async for i in m.channel.history(limit=10):
					await i.delete()
				await asyncio.sleep(10)
				async for i in m.channel.history(limit=10):
					await i.delete()
			else:
				await asyncio.sleep(0.5)
				await msg.delete()
				await m.channel.send("next time i ban you")
		commands = ["t!avatar <@264838866480005122>", ".avatar <@264838866480005122>", "./avatar <@264838866480005122>", "t.avatar <@264838866480005122>"]
		bots = [506735111543193601, 418412306981191680, 172002275412279296, 452289354296197120]
		if m.content.lower() in commands:
			def pred(m):
				return m.author.id in bots and m.channel == m.channel
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
			except asyncio.TimeoutError:
				async for i in m.channel.history(limit=10):
					await i.delete()
				await asyncio.sleep(10)
				async for i in m.channel.history(limit=10):
					await i.delete()
				await asyncio.sleep(10)
				async for i in m.channel.history(limit=10):
					await i.delete()
			else:
				await asyncio.sleep(0.5)
				await msg.delete()
				await m.channel.send("next time i ban you")

def setup(bot):
	bot.add_cog(Owner(bot))
