from discord.ext import commands
from os.path import isfile
import traceback
import discord
import random
import json

class Toggles:
	def __init__(self, bot):
		self.bot = bot
		self.responses = {}
		if isfile("./data/config/toggles.json"):
			with open("./data/config/toggles.json", "r") as infile:
				dat = json.load(infile)
				if "responses" in dat:
					self.responses = dat["responses"]

	def luck(ctx):
		return ctx.author.id == 264838866480005122

	@commands.command()
	@commands.check(luck)
	async def cogs_responses(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	async def on_message(self, m: discord.Message):
		m.content = m.content.lower()
		r = random.randint(1, 8)
		if m.content.startswith("<@506735111543193601>"):
			await m.channel.send(random.choice([
				"Once apon a time in a land far away, there lived a little boy who pinged a bot, first came rape, then came aids",
				"Don't ping me m8, it hurts you more than it hurts me",
				"Oh look, another homosexual",
				"FBI OPEN UP",
				"pUrE wHiTe pRiVelIdgEd mALe^",
				"Once apon a time in a land far away, there lived a little boy who pinged a bot, first came rape, then came aids",
				"Do you need virtual daycare or something?",
				"Shut your skin tone chicken bone google chrome no home flip phone disowned ice cream cone garden gnome extra chromosome metronome dimmadome genome full blown monochrome student loan indiana jones overgrown flintstone x and y hormone friend zoned sylvester stallone sierra leone autozone professionally seen silver patrone head ass tf up.",
				"Fuck off hitler",
				"alright you pathetic lost child, use .help",
				"and what might **you** want",
				"No sir"]))
		if m.content.startswith("sponsered by totherbot"):
			await m.channel.send(random.choice([
				"Sponsored by faggatron",
				"Can someone ban that rotarded tother bot",
				"*powered by tothers ego*"]))
		if m.content.startswith("ew, fates here?"):
			await m.channel.send(random.choice([
				"ew, faggatron used my name",
				"also can someone ban that rotarded tother bot",
				"*powered by tothers ego*"]))
		if "please, stop harrasing my bot" in m.content:
			await m.channel.send('then please stop noticing me every time im pinged reeee')
		if isinstance(m.guild, discord.Guild):
			if str(m.guild.id) not in self.responses:
				self.responses[str(m.guild.id)] = 'enabled'
				with open("./data/config/toggles.json", "w") as outfile:
					json.dump({"responses": self.responses}, outfile, ensure_ascii=False)
			if self.responses[str(m.guild.id)] == 'enabled':
				if r >= 7:
					if m.content.startswith("hello"):
						await m.channel.send(random.choice(["Hello", "Hello :3", "Suh", "Suh :3", "Wazzuh", "Despacito :]"]))
					if m.content.startswith("gm"):
						await m.channel.send(random.choice(["Gm", "Gm :3", "Morning", "Morning :3", "Welcome to heaven"]))
					if m.content.startswith("gn"):
						await m.channel.send(random.choice(["Gn", "Gn :3", "Night", "Nighty"]))
					if m.content.startswith("ree"):
						await m.channel.send(random.choice([
							"*depression strikes again*", "*pole-man strikes again*",
							"Would you like an espresso for your depresso",
							"You're not you when you're hungry",
							"*crippling depression*",
							"Breakdown sponsored by Samsung",
							"No espresso for you",
							"Sucks to be you m8",
							"Ripperoni"]))
					if m.content.startswith("kys"):
						await m.channel.send(random.choice([
							"*nazi vegan feminism rally starts*",
							"Sorry hitler, Germany's not here", "NoT iN mY cHriSTiAn sErVeR..\nDo it in threadys",
							"tfw you see faggots that should kill themselves telling other people to kill themselves",
							"Shut your skin tone chicken bone google chrome no home flip phone disowned ice cream cone garden gnome extra chromosome metronome dimmadome genome full blown monochrome student loan indiana jones overgrown flintstone x and y hormone friend zoned sylvester stallone sierra leone autozone professionally seen silver patrone head ass tf up.",
							"Well aren't you just a fun filled little lollipop tripple dipped in psycho",
							"Woah, calm down satan"]))

def setup(bot):
	bot.add_cog(Toggles(bot))
