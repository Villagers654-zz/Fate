import discord
import random

core = discord.Embed(title="~~~====🥂🍸🍷Core🍷🍸🥂====~~~", color=0x80b0ff)
core.add_field(name="◈ Main ◈", value="`disableresponses` `enableresponses` `ggleaderboard` `gleaderboard` `leaderboard` `repeat` `stalk` `links` `ping` `info`", inline=False)
core.add_field(name="◈ Responses ◈", value="`hello` `ree` `gm` `gn`", inline=False)
core.add_field(name="◈ Music ◈", value="`join` `summon` `play` `stop` `skip` `pause` `resume` `volume` `queue` `remove` `shuffle` `dc` `np`", inline=False)
core.add_field(name="◈ Ads ◈", value="`discords` `servers` `realms`", inline=False)

utility = discord.Embed(title="~~~====🥂🍸🍷Utility🍷🍸🥂====~~~", color=0x80b0ff)
utility.add_field(name="◈ Main ◈", value="`channelinfo` `servericon` `serverinfo` `userinfo` `addemoji` `fromemoji` `delemoji` `makepoll` `welcome` `farewell` `logger` `owner` `avatar` `topic` `timer` `limit` `lock` `lockb` `lockm` `note` `quicknote` `notes` `wiki` `ud` `id`", inline=False)

react = discord.Embed(title="~~~====🥂🍸🍷Reactions🍷🍸🥂====~~~", color=0x80b0ff)
react.add_field(name="• FAQ", value="• Some commands may require you to add\ncontent after. For example: `.hug @person`", inline=False)
react.add_field(name="• Commands", value="`intimidate` `powerup` `observe` `disgust` `admire` `angery` `cuddle` `teasip` `psycho` `thonk` `shrug` `yawn` `hide` `wine` `sigh` `kiss` `kill` `slap` `hug` `pat` `cry`", inline=False)

mod = discord.Embed(title="~~~====🥂🍸🍷Mod🍷🍸🥂====~~~", color=0x80b0ff)
mod.add_field(name="• Commands", value="`mute` `unmute` `vcmute` `vcunmute` `warn` `clearwarns` `addrole` `removerole` `selfroles` `delete` `purge` `nick` `massnick` `kick` `mute` `ban` `pin`", inline=False)

fun = discord.Embed(title="~~~====🥂🍸🍷Fun🍷🍸🥂====~~~", color=0x80b0ff)
fun.add_field(name="• Core", value="`personality` `liedetector` `fancify` `coffee` `encode` `decode` `choose` `notice` `quote` `mock` `meme` `rate` `roll` `soul` `gay` `sue` `fap` `ask` `rps` `rr`", inline=False)
fun.add_field(name="• Actions", value="`crucify` `cookie` `shoot` `inject` `slice` `boop` `stab` `kill`", inline=False)
fun.add_field(name="• Responses", value="`@Fate` `Kys`", inline=False)

art = discord.Embed(title="~~~====🥂🍸🍷TextArt🍷🍸🥂====~~~", color=0x80b0ff)
art.add_field(name="• Commands", value="• chill ~ `wavey (~˘▾˘)~`\n• fuckit ~ `fuck itヽ(ﾟｰﾟ)ﾉ`\n• cross ~ `yield (╬ Ò ‸ Ó)`\n• angry ~ `(ノಠ益ಠ)ノ彡┻━┻`\n• yes ~ `thumbs up 👍`", inline=True)

m = discord.Embed(title="~~~====🥂🍸🍷Misc🍷🍸🥂====~~~", color=0x80b0ff)
m.add_field(name="• Math", value="`add` `subtract` `multiply` `divide`", inline=False)

e = discord.Embed(title="~~~====🥂🍸🍷Embeds🍷🍸🥂====~~~", color=0x80b0ff)
e.add_field(name="FAQ", value="• Field = {name} {value}\n• Color = {hex}", inline=False)
e.add_field(name="• Usage", value="• embeda ~ `simple content embed {content}`\n• embedb ~ `{title} {name} {value}`\n• embedc ~ `{title} {url} {name} {value}`\n• embedu `{title} {url} {color} + 2 fields`\n• embedx ~ `{title} {url} {color} {name}\n{value} {name} {value} {name} {value}`", inline=True)

links = discord.Embed(color=0x80b0ff)
links.set_author(name=f'| Links | 📚', icon_url="https://images-ext-1.discordapp.net/external/kgeJxDOsmMoy2gdBr44IFpg5hpYzqxTkOUqwjYZbPtI/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/506735111543193601/689cf49cf2435163ca420996bcb723a5.webp")
links.set_thumbnail(url=random.choice(["https://cdn.discordapp.com/attachments/501871950260469790/513636718835007488/kisspng-computer-icons-message-icon-design-download-invite-5abf1e6f0905a2.045504771522474607037.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636728733433857/mail-open-outline.png", "https://cdn.discordapp.com/attachments/501871950260469790/513636736492896271/mail-open-solid.png"]))
links.description = f'[Invite](https://discordapp.com/oauth2/authorize?client_id=506735111543193601&permissions=1559620710&scope=bot) 📥\n[Support](https://discord.gg/HkeCzSw) 📧\n[Discord](https://discord.gg/BQ23Z2E) <:discord:513634338487795732>'

