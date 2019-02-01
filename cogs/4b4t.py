from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import random
import json

class Minecraft:
	def __init__(self, bot):
		self.bot = bot
		self.motds = []
		self.old_motds = []
		if isfile("./data/4b4t/motds.json"):
			with open("./data/4b4t/motds.json", "r") as infile:
				dat = json.load(infile)
				if "motds" in dat and "old_motds" in dat:
					self.motds = dat["motds"]
					self.old_motds = dat["old_motds"]

	def save(self):
		with open("./data/4b4t/motds.json", "w") as outfile:
			json.dump({"motds": self.motds, "old_motds": self.old_motds}, outfile, ensure_ascii=False)

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

	@commands.command()
	async def motdcount(self, ctx):
		await ctx.send(len(self.motds))

	@commands.command()
	async def ltest(self, ctx):
		for i in self.old_motds:
			await ctx.send(i)

	@commands.command()
	@commands.check(luck)
	async def cleanup(self, ctx):
		async for msg in ctx.channel.history():
			if msg.author.id == 529287770233896961:
				pass
			else:
				await msg.delete()

	@commands.command(aliases=["pc"])
	async def playercount(self, ctx):
		await ctx.send(self.bot.get_guild(470961230362837002).get_member(529287770233896961).game)

	@commands.command()
	async def fixmotds(self, ctx):
		motds = ["When the Stars Fall", "Fuck the battle cat", "Woah. . .", "MrBoom10 is Online!", "Heil Sharp 5!", "Sponsored by Samsung", "FBI OPEN UP", "Gapple up", "iLiKe NuT", "All heil nut", "The 7 SR Fags", "ToTheR iS goD", "Fly on Fly off", "Ripperoni pepperoni", "Mayfly!", "Legit Anarchy!", "TotherIsTostitos", "Legit has been muted", "#Free Legit", "Now better than 2p2e!", "6 million juice", "Maps are the best", "7th team lgbt", "elon's musk", "Virtual Daycare", "Time Ticks On", "HeckaGuide was here", "fite me", "fortnut sucks", "7tm Surpreme", "ZR", "Half Life 3", "HI MOM", "no u", "HeckuvaGuide", "NANI?!?", "HA BEAT YA TO IT", "a war in motd", "Hawhatalooser", "obliviscancer", "YEET to DELETE", "You have aids", "ifyoucantbeatitYEETit", "Let’s grab our paint sets", "Communism", "T O T H E R", "FishyBear", "baccacito", "Why so serious?", "disabled due to a exploit", "mikey big gay", "juice wrld", "Huggably rapably fresh", "♡Juice wrld♡", "0/10 meme", "xJuice Wrld", "PURGE THE INFIDELS", "Niggatry", "This shit is not secure", "The Security is Shit", "They need the sack", "Tomato juice!", "Thready = bae", "Send Luck Loli Hentai", "Pole-Man", "Disbanded", "Privileged", "Threadys Republic", "Homiesexual", "Digital Daycare", "IM BACK!!!", "u got food?", "Thready = god 3xpl01ter", "poleman is bae", "The Fuckening", "ANIMOO", "MrBoom10 had the closest base to 0,0", "isthismotdgood", "where's the food", "bettter Believe it's not butter", "Lmao", "Illuminati confirmed", "Cool Story Bro", "It's a dirty liar", "Fate is a hoe", "4B4T", "Fate=Garden tool", "<Gay", "Fate is a slut", "Abuse", "Kool Kidz Klub", "Ewwww", "FREE CANDY", "SeNd NuDeS", "SeNd CoRdS", "It's a block game", "it's a small world", "Beat the Meat", "Hey that's mine", "VFD", "D A B", "ChairyChairChair", "I will beat luck", "MotdKing", "I'll be here all day", "Wait I'm busy", "Sorry Luck", "Over 9000!", "You would not believe your eyes", "Despaciti", "Despacito", "All hail plankton", "Pubg", "Plus Ultra!", "The Cake is a lie", "Half Life 3 confirmed", "OG", "Hi Mom!", "WektWabbitPlayz", "Mad cuz Bad", "Mincecraft", "Memes", "Sky Banana", "Reee?", "The community isn't the same", "Mother of the devil", "Do your homework", "The base dropped harder than my grades", "All the other kids", "According to all known laws of aviation", "Fate want sucky sucky?", "It's not a phase mom", "Aliens.", "CookieToast", "Fortnite is gay", "Madness?", "This is madness", "This is Sparta!", "This is Anarchy!", "2+2 is... 10", "Quest for Cake", "the big lesbian is coming", "Powered by Beddys ego", "Art", "A MAJESTIC FUCKING EAGLE", "WhyAmIStillGettingHate", "Fateisemo", "FateisBait", "Brickr Ban Book", "Emo", "Burn it with fire", "2 Steves 1 block", "red pancakes", "2 letters E Z", "PG-13", "Beat Your Meat 2", "EVERYONE IS HERE", "Sponsored by Walmart", "5b5t", "7B7T", "I didn't do it", "Bye have a great tiem", "OwO", "Jake from State farm", "Capitalism", "Sorry Fam", "Trust No One", "It only takes one player", "4b4t java fags found us", "I'm back", "depresso expresso", "Heck=motd king", "Poleman is back Mikey", "ISAWEDTHISBOSTINHALF", "Triiiiiipaloski", "#gaslegit", "This is Patrick", "FD", "Kill Yourself Wait Please Don't", "Faggotry", "Waffles", "Blue Waffles", "red pancakes", "moooore", "With a Portuguese Breakfast", "The Motd King has arrived", "Bow down faggots", "NO U", "Oh Snap", "Shits going down", "Gone Sexual", "we are burning this town", "Gone Wrong", "testttt", "Family Friendly Christian Server", "mikey is a furry", "nohomo", "Reeeeee...", "TundyBear", "ThreadyBear", "Fate is Your Dad", "Look Mom I'm on TV!", "Karen took the kids", "Upgrade Complete", "Watered Down", "A Giant Flying Space Banana", "Mom why'd you take me from dad", "Soviet Union Approved!", "Subscribe to PewDiePie", "tother is a furry", "Sponsored by Fate", "Fate is lowkey dom", "TotherIsGod", "Age of Bots", "Dawn of The Bots", "thunder likes bdsm", "tother likes bdsm", "Luck secretly likes bdsm", "Luck is secretly submissive", "Luck highkey is a furry", "Tomato has the best hentai archive", "Yeet or be Yeeted", "Yote", "GotherMeteor", "WhenTheSelfBottingIsntEnough", "AngerySad", "test", "TeSt", "what are the odds this will even show up?", "Totho El Gotho", "Straight To Hell", "Fates Hangout", "1 tb of lolicon", "1 rn of lolicon", "Tother == Furry:", "1 testtt", "Faggot shit", "Traps aren’t gya", "traps aren’t gay", "chigger chagger nigger dagger", "Fate x Rythm", "It was Thunder's idea!", "Mikey did it!", "Tothy is Tacky", "Tothy highkey a furry", "LegitAnarchy.tk", "land of the weebs, turn back", "its not to late to save yourself", "turn back!", "watch out for fate 👀", "dont piss off luck", "TotherShouldBeOwner"]
		for i in motds:
			self.motds.append(i)
		self.old_motds.append("yeet")
		with open("./data/4b4t/motds.json", "w") as outfile:
			json.dump({"motds": self.motds, "old_motds": self.old_motds}, outfile, ensure_ascii=False)
		await ctx.send("done")

	@commands.command(name='submitmotd', aliases=['motd'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def submitmotd(self, ctx, *, motd=None):
		if motd is None:
			return await ctx.send('motd is a required argument that is missing')
		if len(motd) > 35:
			return await ctx.send('too big ;-;')
		if len(motd) < 3:
			return await ctx.send('too small ;-;')
		for i in self.motds:
			if str(i).lower() in motd.lower():
				return await ctx.send('That MOTD already exists')
		self.motds.append(motd)
		e = discord.Embed(description=f"`{motd}`", color=0x0000ff)
		e.set_author(name="{} | Submitted your MOTD:".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.author.avatar_url)
		await ctx.send(embed=e, delete_after=10)
		await ctx.message.delete()
		if len(self.motds) > 100:
			self.old_motds.append(self.motds[0])
			del self.motds[0]
		self.save()

	@commands.command(name="shufflemotd", aliases=["motdshuffle"])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def shufflemotd(self, ctx):
		guild = self.bot.get_guild(470961230362837002)
		motd = f"{random.choice(self.motds)}"
		await guild.edit(name=f"4B4T - {motd}")
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name="{} shuffled the MOTD".format(ctx.author.name), icon_url=ctx.author.avatar_url)
		e.description = f"New: {motd}"
		await ctx.send(embed=e, delete_after=10)
		await ctx.message.delete()
		if len(self.motds) > 100:
			self.old_motds.append(self.motds[0])
			del self.motds[0]
			self.save()

	async def motdshuffle(self):
		while True:
			with open("/home/legit/4b4t/data/server.properties", 'r') as f:
				get_all = f.readlines()
			with open("/home/legit/4b4t/data/server.properties", 'w') as f:
				for i, line in enumerate(get_all, 1):
					if i == 12:
						f.writelines(f"motd=4B4T - {random.choice(self.motds)}\n")
					else:
						f.writelines(line)
			await asyncio.sleep(1800)

	async def on_ready(self):
		await asyncio.sleep(0.5)
		self.bot.loop.create_task(self.motdshuffle())
		# clean motd

	async def on_member_join(self, member: discord.Member):
		if member.guild.id == 470961230362837002:
			guild = self.bot.get_guild(470961230362837002)
			motd = f"{random.choice(self.motds)}"
			await guild.edit(name=f"4B4T - {motd}")

def setup(bot):
	bot.add_cog(Minecraft(bot))
