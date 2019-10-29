import discord
import random

def tokens(token):
	if token is "fatezero":
		return "NTA2NzM1MTExNTQzMTkzNjAx.XUna4Q.gbbglbMazHleH39UU1hOriwd_G4"
	if token is "4b4t":
		return "NTExMTQxMzM1ODY1MjI5MzMz.Dz2fVA.Dp6_DfBwPYucYJiRz5anXACzJsg"

def links():
	embed = discord.Embed(color=0x80b0ff)
	embed.set_author(name=f'| Links | 📚', icon_url="https://images-ext-1.discordapp.net/external/kgeJxDOsmMoy2gdBr44IFpg5hpYzqxTkOUqwjYZbPtI/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/506735111543193601/689cf49cf2435163ca420996bcb723a5.webp")
	embed.set_thumbnail(url=random.choice(["https://cdn.discordapp.com/attachments/501871950260469790/513636718835007488/kisspng-computer-icons-message-icon-design-download-invite-5abf1e6f0905a2.045504771522474607037.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636728733433857/mail-open-outline.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636736492896271/mail-open-solid.png"]))
	embed.description = \
		f'[Invite](https://discordapp.com/oauth2/authorize?client_id=506735111543193601&permissions=1551232246&scope=bot) 📥\n' \
		f'[Support](https://discord.gg/wtjuznh) 📧\n' \
		f'[Discord](https://discord.gg/BQ23Z2E) <:discord:513634338487795732>'
	return embed

def emojis(emoji):
	if emoji is "plus":
		return "<:plus:548465119462424595>"
	if emoji is "edited":
		return "<:edited:550291696861315093>"

def owner(ctx):
	return ctx.author.id == 264838866480005122

def owner_id():
	return 264838866480005122

def server(item):
	if item is "id":
		return 397415086295089155
	if item is "log":
		return 577661500802465813
	if item is "error":
		return 577661500802465813

def color():
	return 0x80b0ff

def source():
	return random.choice(["Powered by CortexPE", "Powered by Luck", "Powered by Tothy", "Powered by Thready",
		    "Powered by slaves", "Powered by Beddys ego", "Powered by Samsung", "Powered by the supreme",
		                      "Powered by doritos", "Cooldown: 10 seconds"])
