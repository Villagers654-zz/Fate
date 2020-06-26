import aiohttp
import os
import random
import asyncio
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord


class Reactions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.webhook = {}
		self.sent = {}

	async def queue(self, ctx, reaction, path):
		await asyncio.sleep(60 * 5)
		if path in self.sent[reaction][ctx.guild.id]:
			del self.sent[reaction][ctx.guild.id][path]
		if not self.sent[reaction][ctx.guild.id]:
			del self.sent[reaction][ctx.guild.id]

	async def send_webhook(self, ctx, reaction, args, action=None):
		# Prevent roles from being mentioned
		if args:
			if '<@&' in args or '@everyone' in args or '@here' in args:
				return await ctx.send('biTcH nO')

		user = None
		if action and ctx.message.mentions:
			if len(args.split()) == 1:
				if args.startswith('<@'):
					argsv = args.split()
					user = argsv[0]  # type: discord.Member.mention
				args = f'*{action} {args}*'
			elif args.startswith('<@'):
				args = args.split()
				user = args[0]  # type: discord.Member.mention
				args.pop(0)
				args = f'*{action} {user}*  {" ".join(args)}'

		options = os.listdir(f"./data/images/reactions/{reaction}/")

		# Check gae percentages
		if user and any("gay" in str(fn).lower() for fn in options):
			try:
				usr = await commands.UserConverter().convert(ctx, user)
			except:
				pass
			else:
				cog = self.bot.get_cog("Fun")
				if str(ctx.author.id) in cog.gay["gay"] and str(usr.id) in cog.gay["gay"]:
					if cog.gay["gay"][str(ctx.author.id)] > 50 and cog.gay["gay"][str(usr.id)] > 50:
						options = [fn for fn in options if "gay" in str(fn).lower()]

		if reaction not in self.sent:
			self.sent[reaction] = {}
		if ctx.guild.id not in self.sent[reaction]:
			self.sent[reaction][ctx.guild.id] = {}
		if len(self.sent[reaction][ctx.guild.id]) >= len(options):
			for task in self.sent[reaction][ctx.guild.id].values():
				if not task.done():
					task.cancel()
			self.sent[reaction][ctx.guild.id] = {}

		# Remove sent gifs from possible options and choose which GIF to send
		for sent_path in self.sent[reaction][ctx.guild.id].keys():
			options.remove(sent_path)
		filename = random.choice(options)
		path = os.getcwd() + f"/data/images/reactions/{reaction}/" + filename

		# Add and wait 5mins to remove the sent path
		self.sent[reaction][ctx.guild.id][filename] = self.bot.loop.create_task(self.queue(ctx, reaction, filename))

		created_webhook = False
		if ctx.channel.id not in self.webhook:
			self.webhook[ctx.channel.id] = await ctx.channel.create_webhook(name='Reaction')
			created_webhook = True

		async with aiohttp.ClientSession() as session:
			webhook = Webhook.from_url(self.webhook[ctx.channel.id].url, adapter=AsyncWebhookAdapter(session))
			await webhook.send(
				args, username=ctx.author.name, avatar_url=ctx.author.avatar_url,
				file=discord.File(path, filename=reaction + path[-(len(path) - path.find('.')):])
			)
			await ctx.message.delete()
			if created_webhook:
				await asyncio.sleep(120)
				if ctx.channel.id in self.webhook:
					if self.webhook[ctx.channel.id]:
						await self.webhook[ctx.channel.id].delete()
						del self.webhook[ctx.channel.id]


	@commands.command(name="intimidate")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def intimidate(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'apple', content)

	@commands.command(name="observe")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def observe(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'observe', content)

	@commands.command(name="disgust")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def disgust(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'disgust', content)

	@commands.command(name="snuggle")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def snuggle(self, ctx, *, content):
		await self.send_webhook(ctx, 'snuggle', content, action='snuggles')

	@commands.command(name="admire")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def admire(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'admire', content)

	@commands.command(name="waste")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def waste(self, ctx, *, args):
		await self.send_webhook(ctx, 'waste', args, action='wastes')

	@commands.command(name="shrug")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def shrug(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'shrug', content)

	@commands.command(name="yawn")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def yawn(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'yawn', content)

	@commands.command(name="sigh")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def sigh(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'sigh', content)

	@commands.command(name="bite")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def bite(self, ctx, *, args):
		await self.send_webhook(ctx, 'bite', args, action='bites')

	@commands.command(name="wine")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def wine(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'wine', content)

	@commands.command(name="hide")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def hide(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'hide', content)

	@commands.command(name="slap")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def slap(self, ctx, *, args):
		await self.send_webhook(ctx, 'slap', args, action='slaps')

	@commands.command(name="kiss")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def kiss(self, ctx, *, args):
		await self.send_webhook(ctx, 'kiss', args, action='kisses')

	@commands.command(name="kill")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def kill(self, ctx, *, args):
		await self.send_webhook(ctx, 'kill', args, action='kills')

	@commands.command(name="teasip", aliases=["tea", "st", "siptea"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def teasip(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'tea', content)

	@commands.command(name='lick')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def lick(self, ctx, *, args):
		await self.send_webhook(ctx, 'lick', args, action='licks')

	@commands.command(name='hug')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def hug(self, ctx, *, args):
		await self.send_webhook(ctx, 'hug', args, action='hugs')

	@commands.command(name="cry")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def cry(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'cry', content)

	@commands.command(name="pat")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def pat(self, ctx, *, args):
		await self.send_webhook(ctx, 'pat', args, action='pats')

	@commands.command(name="homo")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _homo(self, ctx):
		path = os.getcwd() + "/data/images/reactions/homo/" + random.choice(
			os.listdir(os.getcwd() + "/data/images/reactions/homo/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.message.delete()
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

def setup(bot):
	bot.add_cog(Reactions(bot))
