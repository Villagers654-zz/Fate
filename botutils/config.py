import json

import discord
import random


def links():
    embed = discord.Embed(color=0x80B0FF)
    embed.set_author(
        name=f"| Links | 📚",
        icon_url="https://images-ext-1.discordapp.net/external/kgeJxDOsmMoy2gdBr44IFpg5hpYzqxTkOUqwjYZbPtI/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/506735111543193601/689cf49cf2435163ca420996bcb723a5.webp",
    )
    embed.set_thumbnail(
        url=random.choice(
            [
                "https://cdn.discordapp.com/attachments/501871950260469790/513636718835007488/kisspng-computer-icons-message-icon-design-download-invite-5abf1e6f0905a2.045504771522474607037.png",
                "https://cdn.discordapp.com/attachments/501871950260469790/513636728733433857/mail-open-outline.png",
                "https://cdn.discordapp.com/attachments/501871950260469790/513636736492896271/mail-open-solid.png",
            ]
        )
    )
    embed.description = (
        f"[Invite](https://discordapp.com/oauth2/authorize?client_id=506735111543193601&permissions=1551232246&scope=bot) 📥\n"
        f"[Support](https://discord.gg/wtjuznh) 📧\n"
        f"[Discord](https://discord.gg/BQ23Z2E) <:discord:513634338487795732>\n"
        f"[Vote](https://top.gg/bot/506735111543193601) ⬆"
    )
    return embed


def owner(ctx):
    return ctx.author.id == 264838866480005122


def owner_id():
    return 264838866480005122


def server(item):
    with open("data/config.json", "r") as f:
        config = json.load(f)  # type: dict
    if item == "id":
        return config["hub_server"]
    if item == "log":
        return config["log_channel"]
    if item == "error":
        return config["log_channel"]


def emojis(emoji):
    if emoji == "plus":
        return "<:plus:548465119462424595>"
    if emoji == "edited":
        return "<:edited:550291696861315093>"
    if emoji == "invisible":
        return "<:status_offline:659976011651219462>"
    if emoji == "dnd":
        return "<:status_dnd:596576774364856321>"
    if emoji == "idle":
        return "<:status_idle:659976006030983206>"
    if emoji == "online":
        return "<:status_online:659976003334045727>"


def color():
    return 0x80B0FF


def source():
    return random.choice(
        [
            "Powered by CortexPE",
            "Powered by Luck",
            "Powered by Tothy",
            "Powered by Thready",
            "Powered by slaves",
            "Powered by Beddys ego",
            "Powered by Samsung",
            "Powered by the supreme",
            "Powered by doritos",
            "Cooldown: 10 seconds",
        ]
    )
