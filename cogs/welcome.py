from discord.ext import commands
from os.path import isfile
import discord
import random
import json
import os

class Events:
	def __init__(self, bot):
		self.bot = bot
		self.identifier = {}
		self.channel = {}
		self.usepings = {}
		self.useimages = {}
		if isfile("./data/config/welcome.json"):
			with open("./data/config/welcome.json", "r") as infile:
				dat = json.load(infile)
				if "identifier" in dat and "channel" in dat and "usepings" in dat and "useimages" in dat:
					self.identifier = dat["identifier"]
					self.channel = dat["channel"]
					self.usepings = dat["usepings"]
					self.useimages = dat["useimages"]

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Core ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_welcome(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	@commands.group(name='welcome')
	@commands.has_permissions(manage_guild=True)
	async def _welcome(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send('**Welcome Message Instructions:**\n'
			               '.welcome enable ~ `enables welcome messages`\n'
			               '.welcome disable ~ `disables welcome messages`\n'
			               '.welcome setchannel ~ `sets the channel`\n'
			               '.welcome usepings ~ `true or false`\n'
			               '.welcome useimages ~ `true or false`')

	@_welcome.command(name='toggle')
	async def _toggle(self, ctx):
		"""Not in use, but still works"""
		report = ""
		if str(ctx.guild.id) not in self.identifier:
			self.identifier[str(ctx.guild.id)] = 'True'
			report += 'Enabled welcome messages'
		else:
			if self.identifier[str(ctx.guild.id)] == 'True':
				self.identifier[str(ctx.guild.id)] = 'False'
				report += 'Disabled welcome messages'
			else:
				if self.identifier[str(ctx.guild.id)] == 'False':
					self.identifier[str(ctx.guild.id)] = 'True'
					report += 'Enabled welcome messages'
		if str(ctx.guild.id) not in self.channel:
			self.channel[str(ctx.guild.id)] = ctx.channel.id
			report += f'\nWelcome channel not set, therefore it has been automatically set to {ctx.channel.name}'
		if str(ctx.guild.id) not in self.useimages:
			self.useimages[str(ctx.guild.id)] = 'False'
			report += '\nUseimages not set, therefore it has been automatically set to false'
		if str(ctx.guild.id) not in self.usepings:
			self.usepings[str(ctx.guild.id)] = 'False'
			report += '\nUsepings not set, therefore it has been automatically set to false'
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)
		await ctx.send(report)

	@_welcome.command(name='enable')
	async def _enable(self, ctx):
		report = ""
		if str(ctx.guild.id) not in self.identifier:
			self.identifier[str(ctx.guild.id)] = 'True'
			report += 'Enabled welcome messages'
		else:
			self.identifier[str(ctx.guild.id)] = 'True'
			report += 'Enabled welcome messages'
		if str(ctx.guild.id) not in self.channel:
			self.channel[str(ctx.guild.id)] = ctx.channel.id
			report += f'\nWelcome channel not set, therefore it has been automatically set to {ctx.channel.name}'
		if str(ctx.guild.id) not in self.useimages:
			self.useimages[str(ctx.guild.id)] = 'False'
			report += '\nUseimages not set, therefore it has been automatically set to `false`'
		if str(ctx.guild.id) not in self.usepings:
			self.usepings[str(ctx.guild.id)] = 'False'
			report += '\nUsepings not set, therefore it has been automatically set to `false`'
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)
		await ctx.send(report)

	@_welcome.command(name='disable')
	async def _disable(self, ctx):
		report = ""
		if str(ctx.guild.id) not in self.identifier:
			self.identifier[str(ctx.guild.id)] = 'False'
			report += 'Disabled welcome messages'
		else:
			self.identifier[str(ctx.guild.id)] = 'False'
			report += 'Disabled welcome messages'
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)
		await ctx.send(report)

	@_welcome.command(name='setchannel')
	async def _setchannel(self, ctx, channel: discord.TextChannel=None):
		if channel is None:
			channel = ctx.channel
		self.channel[str(ctx.guild.id)] = channel.id
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)
		await ctx.send(f'Set the welcome channel to `{channel.name}`')

	@_welcome.command(name='usepings')
	async def _usepings(self, ctx, toggle=None):
		if toggle is None:
			if str(ctx.guild.id) not in self.useimages:
				self.usepings[str(ctx.guild.id)] = 'True'
				await ctx.send('Enabled `usepings`')
			else:
				if self.usepings[str(ctx.guild.id)] == 'False':
					self.usepings[str(ctx.guild.id)] = 'True'
					await ctx.send('Enabled `usepings`')
				else:
					self.usepings[str(ctx.guild.id)] = 'False'
					await ctx.send('Disabled `usepings`')
		else:
			toggle = toggle.lower()
			if toggle == 'true':
				self.usepings[str(ctx.guild.id)] = 'True'
				await ctx.send('Enabled `usepings`')
			else:
				if toggle == 'false':
					self.usepings[str(ctx.guild.id)] = 'False'
					await ctx.send('Disabled `usepings`')
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)

	@_welcome.command(name='useimages')
	async def _useimages(self, ctx, toggle=None):
		if toggle is None:
			if str(ctx.guild.id) not in self.useimages:
				self.useimages[str(ctx.guild.id)] = 'True'
				await ctx.send('Enabled `useimages`')
			else:
				if self.useimages[str(ctx.guild.id)] == 'False':
					self.useimages[str(ctx.guild.id)] = 'True'
					await ctx.send('Enabled `useimages`')
				else:
					self.useimages[str(ctx.guild.id)] = 'False'
					await ctx.send('Disabled `useimages`')
		else:
			toggle = toggle.lower()
			if toggle == 'true':
				self.useimages[str(ctx.guild.id)] = 'True'
				await ctx.send('Enabled `useimages`')
			else:
				if toggle == 'false':
					self.useimages[str(ctx.guild.id)] = 'False'
					await ctx.send('Disabled `useimages`')
		with open("./data/config/welcome.json", "w") as outfile:
			json.dump({"identifier": self.identifier, "channel": self.channel, "usepings": self.usepings,
			           "useimages": self.useimages}, outfile, ensure_ascii=False)

	async def on_member_join(self, member: discord.Member):
		if str(member.guild.id) in self.identifier:
			if self.identifier[str(member.guild.id)] == 'True':
				message = None
				channel = self.bot.get_channel(self.channel[str(member.guild.id)])
				path = os.getcwd() + "/data/images/reactions/welcome/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/welcome/"))
				e = discord.Embed(color=0x80b0ff)
				if self.usepings[str(member.guild.id)] == 'True':
					message = f'welcome {member.mention} to **{member.guild.name}**'
				else:
					e.set_author(name=f'welcome {member.name} to {member.guild.name}')
				if self.useimages[str(member.guild.id)] == 'True':
					e.set_image(url="attachment://" + os.path.basename(path))
					if message == None:
						await channel.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)
					else:
						await channel.send(message, file=discord.File(path, filename=os.path.basename(path)), embed=e)
				else:
					if message == None:
						await channel.send(embed=e)
					else:
						await channel.send(message)

def setup(bot):
	bot.add_cog(Events(bot))
