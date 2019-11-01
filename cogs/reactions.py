import aiohttp
import os
import random
import asyncio
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import discord
from utils import colors, checks


class Reactions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.webhook = {}


	async def send_webhook(self, ctx, reaction, args):
		path = os.getcwd() + f"/data/images/reactions/{reaction}/" + random.choice(
			os.listdir(os.getcwd() + f"/data/images/reactions/{reaction}/"))
		e = discord.Embed(color=colors.fate())
		e.set_image(url="attachment://" + os.path.basename(path))
		created_webhook = False
		if ctx.channel.id not in self.webhook:
			self.webhook[ctx.channel.id] = await ctx.channel.create_webhook(name='Reaction')
			created_webhook = True
		async with aiohttp.ClientSession() as session:
			webhook = Webhook.from_url(self.webhook[ctx.channel.id].url, adapter=AsyncWebhookAdapter(session))
			await webhook.send(args, username=ctx.author.name, avatar_url=ctx.author.avatar_url,
			                   file=discord.File(path, filename=os.path.basename(path)), embed=e)
			await ctx.message.delete()
			if created_webhook:
				await asyncio.sleep(120)
				await self.webhook[ctx.channel.id].delete()
				del self.webhook[ctx.channel.id]


	@commands.command(name="intimidate")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def intimidate(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'apple', content)

	@commands.command(name="powerup")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def powerup(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'powerup', content)

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
		if content.startswith('<@') and 'snuggle' not in content:
			content = f'*snuggles {content}*'
		await self.send_webhook(ctx, 'snuggle', content)

	@commands.command(name="admire")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def admire(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'admire', content)

	@commands.command(name="waste")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def waste(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'waste', user.mention)

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
	async def bite(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'bite', user.name)

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
	async def slap(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'slap', user.mention)

	@commands.command(name="kiss")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def kiss(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'kiss', user.mention)

	@commands.command(name="kill")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def kill(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'kill', user.mention)

	@commands.command(name="teasip", aliases=["tea", "st"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def teasip(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'tea', content)

	@commands.command(name='hug')
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(attach_files=True, manage_messages=True, manage_webhooks=True)
	async def hug(self, ctx, *, args):
		if args.startswith('<@') and 'hugs' not in args:
			args = f'*hugs {args}*'
		await self.send_webhook(ctx, 'hug', args)

	@commands.command(name="cry")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def cry(self, ctx, *, content=None):
		await self.send_webhook(ctx, 'cry', content)

	@commands.command(name="pat")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True, attach_files=True, manage_messages=True)
	async def pat(self, ctx, user: discord.Member):
		await self.send_webhook(ctx, 'pat', user.mention)

	@commands.command(name="homo")
	@commands.check(checks.luck)
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
