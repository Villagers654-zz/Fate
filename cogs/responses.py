from discord.ext import commands
from os.path import isfile
import discord
import random
import json

class Responses:
	def __init__(self, bot):
		self.bot = bot
		self.responses = {}
		if isfile("./data/userdata/config/toggles.json"):
			with open("./data/userdata/config/toggles.json", "r") as infile:
				dat = json.load(infile)
				if "responses" in dat:
					self.responses = dat["responses"]

	def luck(ctx):
		return ctx.author.id == 264838866480005122

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def disableresponses(self, ctx):
		self.responses[str(ctx.guild.id)] = "disabled"
		await ctx.send("Disabled responses")
		with open("./data/userdata/config/toggles.json", "w") as outfile:
			json.dump({"responses": self.responses}, outfile, ensure_ascii=False)

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def enableresponses(self, ctx):
		self.responses[str(ctx.guild.id)] = "enabled"
		await ctx.send("Enabled responses")
		with open("./data/userdata/config/toggles.json", "w") as outfile:
			json.dump({"responses": self.responses}, outfile, ensure_ascii=False)

# ~== Main ==~

	async def on_message(self, m: discord.Message):
		if not m.author.bot:
			# core responses
			r = random.randint(1, 4)
			if m.content.startswith("<@506735111543193601>"):
				if not m.author.bot:
					check = 0
					m.content = m.content.replace("<@506735111543193601>  ", "")
					m.content = m.content.replace("<@506735111543193601> ", "")
					m.content = m.content.replace("<@506735111543193601>", "")
					if len(m.content) > 2:
						f = open("./data/misc/responses.txt", "r")
						for i in f.readlines():
							if m.content in i:
								f.close()
								check += 1
						if check == 0:
							f = open("./data/misc/responses.txt", "a")
							f.write("\n" + m.content)
							f.close()
					if r > 1:
						msg = random.choice(open("./data/misc/responses.txt", "r").readlines())
					else:
						msg = random.choice([
							"Once apon a time in a land far away, there lived a little boy who pinged a bot, first came rape, then came aids",
							"Don't ping me m8, it hurts you more than it hurts me",
							"Oh look, another homosexual",
							"FBI OPEN UP",
							"pUrE wHiTe pRiVelIdgEd mALe^",
							"Once apon a time in a land far away, there lived a little boy who pinged a bot, first came rape, then came aids",
							"Do you need virtual daycare or something?",
							"Fuck off hitler",
							"alright you pathetic lost child, use .help",
							"and what might **you** want",
							"No sir"])
					await m.channel.send(msg)
			m.content = m.content.lower()
			# toggleable responses
			if isinstance(m.guild, discord.Guild):
				if str(m.guild.id) not in self.responses:
					self.responses[str(m.guild.id)] = 'enabled'
					with open("./data/userdata/config/toggles.json", "w") as outfile:
						json.dump({"responses": self.responses}, outfile, ensure_ascii=False)
				if self.responses[str(m.guild.id)] == 'enabled':
					if r == 4:
						if m.content.startswith("hello"):
							await m.channel.send(random.choice(["Hello", "Hello :3", "Suh", "Suh :3", "Wazzuh"]))
						if m.content.startswith("gm"):
							await m.channel.send(
								random.choice(["Gm", "Gm :3", "Morning", "Morning :3", "Welcome to heaven"]))
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
	bot.add_cog(Responses(bot))
