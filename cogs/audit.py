from discord.ext import commands
from utils import colors
import discord

class Audit:
	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="audit")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _audit(self, ctx):
		if not ctx.invoked_subcommand:
			e = discord.Embed(color=colors.cyan())
			e.set_author(name="Audit Log Data", icon_url=ctx.author.avatar_url)
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.description = ""
			e.add_field(name="◈ Commands ◈", value=
			".audit last {amount (default 1)}\n"
			".audit search action {action} {amount}\n"
			".audit search target {@user} {amount}\n"
			".audit search user {@user} {amount}\n", inline=False)
			e.add_field(name="◈ Actions ◈", value="Examples: kick, ban, message_delete\nFor a full list "
			"[click here](https://discordpy.readthedocs.io/en/rewrite/api.html#discord.AuditLogAction)", inline=False)
			await ctx.send(embed=e)

	@_audit.group(name="search")
	@commands.has_permissions(view_audit_log=True)
	async def _search(self, ctx):
		pass

	@_search.command(name="action")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _action(self, ctx, action, amount=1):
		e = discord.Embed(color=colors.cyan())
		e.description = f"Last {amount} {action}'s"
		action = eval("discord.AuditLogAction." + action)
		async for entry in ctx.guild.audit_logs(limit=amount, action=action):
			e.description += "\n✦ **{0.user.name}:** {0.action} to {0.target.name}".format(entry).replace("AuditLogAction.", "")
		await ctx.send(embed=e)

	@_search.command(name="user")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _user(self, ctx, user: discord.Member, amount=1):
		e = discord.Embed(color=colors.cyan())
		e.set_author(name=f"{user}'s last {amount} action(s)", icon_url=user.avatar_url)
		e.description = ""
		audit_position = 0
		async for entry in ctx.guild.audit_logs(limit=amount, user=user):
			e.description += "\n✦ **{0.target}:** {0.action}".format(entry).replace("AuditLogAction.", "")
			audit_position += 1
		e.set_footer(text=f"Total Found: {audit_position}")
		await ctx.send(embed=e)

	@_search.command(name="target")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def _target(self, ctx, user: discord.Member, amount=1):
		e = discord.Embed(color=colors.cyan())
		e.set_author(name=f"Last {amount} action(s) against {user}", icon_url=user.avatar_url)
		e.description = ""
		audit_position = 0
		async for entry in ctx.guild.audit_logs():
			if entry.target is user:
				e.description += "\n✦ **{0.user}:** {0.action}".format(entry).replace("AuditLogAction.", "")
				audit_position += 1
				if audit_position is amount:
					break
		e.set_footer(text=f"Total Found: {audit_position}")
		await ctx.send(embed=e)

	@_audit.command(name="last")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.has_permissions(view_audit_log=True)
	async def _last(self, ctx, amount=1):
		e = discord.Embed(color=colors.cyan())
		e.description = f"Last {amount} action(s)"
		async for entry in ctx.guild.audit_logs(limit=amount):
			try:
				e.description += "\n✦ {0.user.name} | {0.action} to {0.target.name}".format(entry).replace("AuditLogAction.", "")
			except:
				e.description += "\n✦ {0.user} | {0.action} to {0.target}".format(entry).replace("AuditLogAction.", "")
		await ctx.send(embed=e)

def setup(bot):
	bot.add_cog(Audit(bot))
