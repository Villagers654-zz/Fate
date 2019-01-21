from discord.ext import commands
from random import random as rd
import discord
import asyncio
import random
import base64
import os

class Fun:
	def __init__(self, bot):
		self.bot = bot

	def luck(ctx):
		return ctx.message.author.id == 264838866480005122

# ~== Test ==~

	@commands.command()
	@commands.check(luck)
	async def cogs_fun(self, ctx):
		await ctx.send('working')

# ~== Main ==~

	@commands.command()
	async def fancify(self, ctx, *, text: str):
		output = ""
		for letter in text:
			if 65 <= ord(letter) <= 90:
				output += chr(ord(letter) + 119951)
			elif 97 <= ord(letter) <= 122:
				output += chr(ord(letter) + 119919)
			elif letter == " ":
				output += " "
		await ctx.send(output)
		await ctx.message.delete()

	@commands.command(pass_context=True)
	async def encode(self, ctx, encoder: int=None, *, message: str=None):
		if encoder not in {16,32,64}:
			await ctx.send('**Usage:** `.encode {16, 32, or 64} {message}`')
		else:
			if encoder == 16:
				encode = base64.b16encode(message.encode())
			if encoder == 32:
				encode = base64.b32encode(message.encode())
			if encoder == 64:
				encode = base64.b64encode(message.encode())
			await ctx.send(encode.decode())

	@commands.command(pass_context=True)
	async def decode(self, ctx, decoder:int=None, *, message:str=None):
		if decoder not in {16,32,64}:
			await ctx.send('**Usage:** `.decode {16, 32, or 64} {message}`')
		else:
			if decoder == 16:
				decode = base64.b16decode(message.encode())
			if decoder == 32:
				decode = base64.b32decode(message.encode())
			if decoder == 64:
				decode = base64.b64decode(message.encode())
			await ctx.send(decode.decode())

	@commands.command()
	async def smash(self, ctx):
		diary = self.bot.get_channel(505618142563926027)
		e=discord.Embed(description=random.choice(["Whats up bitche, its time to get laid", "No, ew, go fuck a garbage bag or something", "No, ew, go fuck a garbage bag full of used syringes", "i'm ready when you are", "OOGA BOOGA", "*ochinchin falls out*", "Everyday can be a saturday :)"]), color=0x800080)
		e.set_author(name=random.choice(["SEX TIME!", "Horny Hour", "#beastmode"]), icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/471031451001815070/505615018276945920/IMG_20181026_033329.png")
		em=discord.Embed(description="{} {}, {}".format(random.choice(["Today I had sex with", "Just had sex with", "Just got done *doing it*  with"]), ctx.author.name, random.choice(["I kinda want seconds", "I want seconds", "worst sex i've ever had", "best sex i've ever had"])), color=0x800080)
		await ctx.send(embed=e)
		await diary.send(embed=em)

	@commands.command(name="liedetector", aliases=["ld"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def liedetector(self, ctx, *, member: discord.Member=None):
		if member is None:
			member = ctx.author
		r = random.randint(50,100)
		e=discord.Embed(color=0x0000ff)
		e.set_author(name="{}'s msg analysis".format(member.name), icon_url=member.avatar_url)
		e.description = "{}% {}".format(r, random.choice(["truth", "the truth", "a lie", "lie"]))
		await ctx.send(embed=e)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def personality(self, ctx, *, member: discord.Member=None):
		if member is None:
			member = ctx.author
		e=discord.Embed(color=random.choice([0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082]))
		e.set_author(name="{}'s Personality".format(member.name), icon_url=member.avatar_url)
		e.set_thumbnail(url=member.avatar_url)
		e.add_field(name="Type", value=f'{random.choice(["psychopath", "depressed", "cheerful", "faggotry", "bright", "dark", "god", "deceiver", "funny", "fishy", "cool", "insecure", "lonely", "optimistic", "brave", "brilliant", "dreamer", "Nurturer", "Peaceful", "Overthinker", "Idealist", "Pussy"])}', inline=False)
		e.add_field(name="Social Status", value=f'{random.choice(["Ho", "Slut", "Loser", "The nice guy", "The dick", "Dank memer"])}', inline=False)
		e.add_field(name="Hobby", value=f'{random.choice(["Art", "Drawing", "Painting", "Singing", "Writing", "Anime", "Memes", "Minecraft", "Sucking dick"])}', inline=False)
		e.add_field(name="Music Genre", value=f'{random.choice(["Nightcore", "Heavy Metal", "Alternative", "Electronic", "Classical", "Dubstep", "Jazz", "Pop", "Rap"])}', inline=False)
		await ctx.send(embed=e)
		await ctx.message.delete()

	@commands.command()
	async def quote(self, ctx):
		e=discord.Embed(description="{}".format(random.choice([
			"Keep your friends close and your cookies closer",
			"It's an emotion so don't waste time trying to put it into words",
			"You think you need to be strong in order to live? If so you're wrong, life itself gives us strength",
			"If you have love you have to live",
			"The solution to all your problems is anime",
			"Even if you regret yesterday the damage is done",
			"Not everything in this world is plain to the human eye",
			"You shouldn't define people by their maddest edges, He/she's a grey area in a world that doesn't like grey areas, but grey areas are where you find the complexity. It's where you find the humanity, the truth.",
			"To ensure that I'll never lose anything again I'll forget myself and restart",
			"A genius can understand the difference without bias",
			"All the detriment in this world stems from the lack of individuality",
			"Your words are still mine\nEven if the voice isn't",
			"No one can swim in the same riverwater twice",
			"Wherever you go, however you change, you'll still be you",
			"The shape of happiness might resemble glass. Even though you dont usually notice it, it's definitely there. You merely have to change your view slightly and that glass will sparkle when it reflects the light.",
			"Love without limit is love without meaning",
			"Situations evolve. Our desires have no bearing on that. Time blows on unaffected by our struggles",
			"Like clockwork, what a circus this is, and I'm as corrupt as any of them.",
			"Everything falls eventually, including what we say",
			"I dont wanna change the world, I just wanna change your mind.",
			"Wine helps you drink",
			"To free the victim in your heart you fight to build a better world, a world that victim can forgive",
			"Remember one thing through every dark night, there's a bright day after that. So no matter how hard it get, stick your chest out. Keep your head up, and handle it.",
			"You've got enemies? Good, that means you actually stood up for something",
			"you don't die for your friends, you live for them",
			"It's easier to say you're a monster than to just admit you're only hurt",
			"Mistakes are not shackles that halt one from stepping forward. Rather, they are that which sustain and grow ones heart",
			"Can you remember who you were before the world told you who you should be?",
			"It’s hard looking for someone so small. So don’t leave my side.",
			"Care too little, you lose them. Care too much, you get hurt.",
			"It’s not a sin to fall in love. You can’t even arrest someone over that",
			"If you are looking back all the time, you’ll never get ahead",
			"Everything doesn’t have to be decided by life and death, you know. Think about the future a little, will you?",
			"I don’t care where I get hurt, as long as my injuries are visible",
			"I’ll do what I want till the end. Cut me down if you want",
			"I won’t run, I will stand and look ahead to what I must do, I must face the fear, I won’t let it control me anymore, I will use my heart that holds my courage and my bravery to move me forward to what I must do",
			"It’s not the goodbyes that hurt, it’s the flashbacks that follow",
			"There’s no need to change the past. Because of the past we are who we are now. Every second, every action from then is linked to us here and now",
			"Everyone makes mistakes, but then you recover. Look at all of the friends you have here who adore you. It would be difficult for anything to change that. If you keep that in mind, you should be able to get back on your feet any number of times.",
			"If I haven’t had fear, then I also wouldn’t have been able to know what it’s like to have bravery in my heart.Bravery that awakens when you’re being consumed by fear",
			"There are things in this world that you cannot oppose, no matter how hard you try",
			"It’s when people realize how lonely it is being on their own, that they start to become kind",
			"Everyone exists for a reason. As small as it can be. I’m sure you have a meaning too",
			"In a confrontation the person who wants to help their friends, is stronger than the person who escapes",
			"It is the role of a parent to stand in front of their children… and protect them even if their legs were to give out at any moment",
			"There are people in this world who prefer solitude. But there is no one who can withstand it",
			"Weaklings will stay weak forever. But weakness is not evil, since human beings are weak creatures to begin with. Alone, you feel nothing but insecurity; that’s why we form guilds, that’s why we have friends. We walk together in order to live a strong life. The clumsy ones will walk into more walls than the others, and it may also take them longer to get there. If you believe in tomorrow and put yourself out there, you can naturally obtain your strength. That’s how you will be able to smile and live strong.",
			"No one can decide what someone else should do with their life",
			"Manipulating the pieces according to your strategy… That is what defines a King",
			"Comrade isn’t simply a word. Comrades are about heart. It’s the unconditional trust in your partners. Please, feel free to lean on me…. And I, too, will lean on you as well.",
			"Mistakes are not shackles that halt one from stepping forward. Rather, they are that which sustain and grow one’s heart.",
			"Unwavering Faith and Resilient Bonds will bring even miracles to your side",
			"There are walls that can’t be broken through power alone. But if there is a power that can break through those walls, it is the power of feelings.",
			"I wont stop fighting when im tired, i’ll stop fighting when you’ve shattered my heart into a thousand pieces",
			"You don't die for your friends, you live for them",
			"The moment you think of giving up, think of the reason why you held on so long",
			"Comrades are comrades because they help each other out",
			"We don’t have to know what tomorrow holds! That’s why we can live for everything we’re worth today",
			"The real sin is averting your eyes and failing to believe in anyone",
			"The anxiety, anger and hatred I couldn’t suppress. However, when I stopped to look at the sky… I realized just how small I am. There is an endless world spreading before me.",
		    "Fear isn’t evil, it only allows us to learn our own weaknesses. When we learn our weakness, people can grow stronger and kinder.",
			"Remember that everyone you meet is afraid of something, loves something, and has lost something.",
			"There’s nothing happy about having your fate decided for you! You have to grab your own happiness",
			"Forget what hurt you in the past, but never forget what it taught you",
			"You have three choices, you can give up, give in, or give it your all",
			"Don’t judge me unless you have looked through my eyes, experienced what I went through and cried as many tears as me. Until then back-off, cause you have no idea.",
			"The worst kind of pain is when you’re smiling just to stop the tears from falling",
			"If I have to hurt someone, if I have to injure a comrade, then I might as well hurt myself",
			"I haven’t relied on luck since the moment I was born. Everything has been the result of my choices. That is what leads my existence towards the future.",
			"The loneliest people are the kindest. The saddest people smile the brightest. The most damaged people are the wisest. All because they don’t wish to see anyone else suffer the way they did.",
			"Life and death are the very basis of all things. They intensify every emotion. Or, to put it in a rather different way, there is nothing quite so dull as 'life'",
			"Tears are how our heart speaks when your lips cannot describe how much we’ve been hurt",
			"It’s your words that gave me courage. It become my light that would guide me towards the right path.",
			"It’s only the end if you give up",
			"If the drive behind one’s actions is the thought of another, then it is never meaningless",
			"All I need is the power to be able to protect my comrades. So long as I can have the strength to do that, I don’t care if I’m weaker than everyone else in the world",
			"You can believe in anything, but it’s your heart that ultimately decides",
			"Hurt me with the truth, but never comfort me with a lie",
			"Even if we walk on different paths, one must always live on as you are able! You must never treat your own life as something insignificant! You must never forget the friends you lo ve for as long as you live! Let bloom the flowers of light within your hearts.",
			"Moving on doesn’t mean you forget about things. It just means you have to accept what’s happened and continue living.",
			"Those painful memories are what help us make it to tomorrow and become stronger",
			"It it always sad to part with those whom you love, but your companions will help you bear that sadness",
			"You see, for as long as we draw breath into our lungs, we shall keep hope alive inside our hearts",
			"Feelings can be controlled, but tears never lie",
			"If you realize you made a mistake with the way you’ve been living your life, you just have to take the next moment and start over",
			"If you truly desire greatness, you must first know what makes you weak. And more importantly, live with an open heart"])), color=0xFFCC00)
		e.set_author(name="| Quote", icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url=ctx.guild.icon_url)
		await ctx.send(embed=e)

	@commands.command()
	async def notice(self, ctx):
		await ctx.send(random.choice([
			"Depression Strikes Again",
		    "Would you like an espresso for your depresso",
		    "You're not you when you're hungry",
		    "Tfw you realise flies get laid more than you^",
		    "*crippling depression*",
		    "Really? That's the sperm that won?",
		    "Breakdown sponsored by Samsung",
		    "pUrE wHiTe pRiVelIdgEd mALe^"]))
		await ctx.message.delete()

	@commands.command()
	async def choose(self, ctx, *choices: str):
		await ctx.send(random.choice(choices))

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def meme(self, ctx):
		path = os.getcwd() + "/data/images/core/memes/" + random.choice(os.listdir(os.getcwd() + "/data/images/core/memes/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command(pass_context=True)
	async def mock(self, ctx, *, message):
		msgbuf = ""
		uppercount = 0
		lowercount = 0
		for c in message:
			if c.isalpha():
				if uppercount == 2:
					uppercount = 0
					upper = False
					lowercount += 1
				elif lowercount == 2:
					lowercount = 0
					upper = True
					uppercount += 1
				else:
					upper = rd() > 0.5
					uppercount = uppercount + 1 if upper else 0
					lowercount = lowercount + 1 if not upper else 0
				msgbuf += c.upper() if upper else c.lower()
			else:
				msgbuf += c
		await ctx.send(msgbuf)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def rate(self, ctx):
		c = 0
		async for msg in ctx.channel.history(limit=3):
			if c == 1:
				await msg.add_reaction(random.choice(['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']))
				await msg.add_reaction(':slash:506089603783196672')
				await msg.add_reaction('🔟')
				await ctx.message.delete()
				break;
			c += 1

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def soul(self, ctx, *, member: discord.Member=None):
		if member is None:
			member = ctx.author
		r = random.randint(0,1000)
		e=discord.Embed(color=0xFFFF00)
		e.set_author(name=f'{member.name}\'s Soul Analysis', icon_url=member.avatar_url)
		e.description = f'{r} grams of soul'
		await ctx.send(embed=e)

	@commands.command()
	async def roll(self, ctx):
		await ctx.send(random.choice(["1", "2", "3", "4", "5", "6"]))

	@commands.command(name='ask', aliases=['magicconch', '8ball'])
	async def _ask(self, ctx, *, arg):
		e=discord.Embed(color=0x80b0ff)
		e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		e.description = "**Q**: {}\n**A**: {}".format(arg, random.choice(
			["Yes", "No", "It's certain", "110% no", "It's uncertain", "Ofc", "I think not m8", "ig", "Why not ¯\_(ツ)_/¯", "Leave.",
			 "Shut up, homo.", "Sonic says it's gay to ask a discord bot questions",
			 "You only ask because im either fucking less dumb then your stupid fucking brain or your desperate for me too obliviously agree",
			 "Ye", "I should be asking the questions here.", "I'm not in the mood to answer to peasants", "Yep", "Yup", "tHe AnSwEr LiEs WiThIn",
			 "Basically yes^", "Not really", "I do not normally respond to anarchists because I am not a faggot", "Well duh", "hell yeah",
			 "hell no"]))
		await ctx.send(embed=e)
		await asyncio.sleep(0.5)
		await ctx.message.delete()

	@commands.command(name='gay', aliases=['straight', 'lesbian'])
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def gay(self, ctx, *, member: discord.Member=None):
		if member is None:
			member = ctx.author
		r = random.randint(50,100)
		e=discord.Embed(description=f'Requested by {ctx.author.name}', color=0xFC0FC0)
		e.set_author(name=f'| You are {r}% {random.choice(["gay", "straight", "lesbian"])}', icon_url=member.avatar_url)
		e.set_thumbnail(url=member.avatar_url)
		await ctx.send (embed=e)
		await ctx.message.delete()

	@commands.command()
	async def rps(self, ctx):
		try:
			def pred(m):
				return m.author == ctx.author and m.channel == ctx.channel
			choose = await ctx.send("Choose: rock, paper, or scissors")
			await asyncio.sleep(0.5)
			msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
		except asyncio.TimeoutError:
			await ctx.send(f'you faggot, you took too long', delete_after=5)
		else:
			result=discord.Embed(color=0x80b0ff)
			result.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
			r = random.choice(['rock', 'paper', 'scissors'])
			if r == 'rock':
				img = 'https://cdn.discordapp.com/attachments/501871950260469790/511284253728702465/5a0ac29f5a997e1c2cea10a1.png'
			if r == 'paper':
				img = 'https://cdn.discordapp.com/attachments/501871950260469790/511284234275782656/1541969980955.png'
			if r == 'scissors':
				img = 'https://cdn.discordapp.com/attachments/501871950260469790/511284246506110997/Scissor-PNG.png'
			result.set_thumbnail(url=img)
			result.description = f'**Fate [Zero] chose: **{r}\n**{ctx.author.name} chose:** {msg.content}'
			embed = await ctx.send(embed=result)
			await choose.delete()
			await ctx.message.delete()
			await msg.delete()

	@commands.command()
	async def rpsold(self, ctx):
		async with ctx.typing():
			try:
				rock=discord.Embed(color=0x80b0ff)
				rock.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
				rock.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511284253728702465/5a0ac29f5a997e1c2cea10a1.png")
				rock.description = "Rock"
				paper=discord.Embed(color=0x80b0ff)
				paper.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
				paper.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511284234275782656/1541969980955.png")
				paper.description = "Paper"
				scissors=discord.Embed(color=0x80b0ff)
				scissors.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
				scissors.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511284246506110997/Scissor-PNG.png")
				scissors.description = "Scissors"
				shoot=discord.Embed(color=0x80b0ff)
				shoot.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
				shoot.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511285414598803486/racing-flags.png")
				shoot.description = "Shoot"
				rps = await ctx.send(embed=rock)
				await asyncio.sleep(2)
				await rps.edit(embed=paper)
				await asyncio.sleep(2)
				await rps.edit(embed=scissors)
				await asyncio.sleep(2)
				await rps.edit(embed=shoot)
				await asyncio.sleep(4)
				c = 0
				async for msg in ctx.channel.history(limit=3):
					if c == 0:
						c += 1
						continue
					if c == 1:
						await rps.delete()
						await ctx.message.delete()
						result=discord.Embed(color=0x80b0ff)
						result.set_author(name='Rock, Paper, Scissors', icon_url=ctx.author.avatar_url)
						result.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511286149722013697/aceodo4Mi.png")
						result.description = f'I choose {random.choice(["rock", "paper", "scissors"])}\n{ctx.author.name} chose [{msg.content}]'
						await ctx.send(embed=result)
						break;
					c += 1
			except Exception as e:
				await ctx.send(f'**```ERROR: {type(e).__name__} - {e}```**')

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def sue(self, ctx, user: discord.Member):
		r = random.randint(1, 1000)
		if user.id == 264838866480005122:
			r = 0
		if ctx.author.id == 264838866480005122:
			r = random.randint(1000000, 1000000000)
		e = discord.Embed(color=0xAAF200)
		e.set_author(name=f'{ctx.author.name} has sued {user.name}', icon_url=ctx.author.avatar_url)
		e.set_thumbnail(url="https://cdn.discordapp.com/attachments/501871950260469790/511997534181392424/money-png-12.png")
		e.description = f'Amount: ${r}'
		await ctx.send(embed=e)
		await ctx.message.delete()

	@commands.command()
	async def fap(self, ctx):
		e=discord.Embed(description=">{} starts fapping {}".format(ctx.author.name, random.choice(["to trump", "to beddy", "infront of rogue", "to rogue", "to furries", "to loli's", "to shota's", "to pornhub.com videos", "to illegal porn", "to gay porn", "to lesbian porn", "to hentaihaven.com", "to poleman", "to Tomatoes lucious locks of hair", "to rape", "to Yugioh", "to tomboys"])), color=random.choice([0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082]))
		await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def vid(self, ctx):
		path = os.getcwd() + "/images/vids/" + random.choice(os.listdir(os.getcwd() + "/images/vids/"))
		e = discord.Embed()
		e.set_image(url="attachment://" + os.path.basename(path))
		await ctx.send(file=discord.File(path, filename=os.path.basename(path)), embed=e)

	@commands.command()
	async def rr(self, ctx):
		await ctx.send(random.choice(["You lived", "You died"]))

# ~== Misc ==~

def setup(bot):
	bot.add_cog(Fun(bot))
