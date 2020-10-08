import json
import random
from os.path import isfile

import discord
from discord.ext import commands


class Responses(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.responses = {}
		if isfile("./data/userdata/config/toggles.json"):
			with open("./data/userdata/config/toggles.json", "r") as infile:
				dat = json.load(infile)
				if "responses" in dat:
					self.responses = dat["responses"]

	def cache(self):
		with open("./data/userdata/chatbot.json", "r") as f:
			return json.load(f)["cache"]["global"]

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def disableresponses(self, ctx):
		self.responses[str(ctx.guild.id)] = "disabled"
		await ctx.send("Disabled responses")
		await self.bot.save_json("./data/userdata/config/toggles.json", {"responses": self.responses})

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def enableresponses(self, ctx):
		self.responses[str(ctx.guild.id)] = "enabled"
		await ctx.send("Enabled responses")
		await self.bot.save_json("./data/userdata/config/toggles.json", {"responses": self.responses})

# ~== Main ==~

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if not m.author.bot and m.channel.permissions_for(m.guild.me).send_messages:
				m.content = m.content.lower()
				# toggleable responses
				if str(m.guild.id) not in self.responses:
					self.responses[str(m.guild.id)] = 'disabled'
					await self.bot.save_json("./data/userdata/config/toggles.json", {"responses": self.responses})
				if self.responses[str(m.guild.id)] == 'enabled':
					# if list(filter(lambda x: m.content.startswith(x), ["<@506735111543193601>", "<@!506735111543193601>"])):
					# 	m.content = m.content.replace("!", "").replace("<@506735111543193601> ", "")
					# 	found = False
					# 	keys = m.content.split(" ")
					# 	key = random.choice(keys)
					# 	if "the" in keys:
					# 		key = keys[keys.index("the") + 1]
					# 	if "if" in keys:
					# 		key = keys[keys.index("if") + 2]
					# 	matches = []
					# 	for msg in self.cache():
					# 		if key in msg:
					# 			matches.append(msg)
					# 			found = True
					# 	if found:
					# 		name = m.author.display_name
					# 		choice = random.choice(matches)
					# 		choice = choice.replace(str(self.bot.user.mention), str(m.author.mention))
					# 		if choice.lower() == m.content.lower():
					# 			return
					# 		choice = choice.replace('Fate', name).replace('fate', name)
					# 		try:
					# 			async with m.channel.typing():
					# 				await asyncio.sleep(1)
					# 			await m.channel.send(choice)
					# 		except:
					# 			pass
					if random.randint(1, 4) == 4:
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
								"Ripperoni",
								"Sucks to suck"]))
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
