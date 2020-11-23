import discord
from utils import colors, config


class HelpMenus:
    def __init__(self, bot):
        self.bot = bot

    def default(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Help🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            f"[Support Server]({self.bot.config['support_server']}) | "
            f"[Bot Invite]({self.bot.invite_url})"
        )
        usage = (
            "• using a cmd with no args will usually send its help menu\n"
            "• try using `.module enable` instead of `.enable module`"
        )
        e.add_field(name="◈ Basic Bot Usage", value=usage, inline=False)
        categories = (
            "• **Core** - `main bot commands`\n"
            "• **Mod** - `moderation commands`\n"
            "• **Utility** - `helpful commands`\n"
            "• **Fun** - `fun games/commands`\n"
            "• **Music** - `play moosic in vc`"
        )
        e.add_field(name="◈ Categories", value=categories, inline=False)
        e.set_footer(
            text="Use the reactions to navigate", icon_url=self.bot.user.avatar_url
        )
        return e

    def core(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Core🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            "• **config** - `sends toggles for core modules`\n"
            "• **prefix** - `lets you change the bots prefix`\n"
            "• **links** - `sends invite/support links`\n"
            "• **ping** - `checks the bots latency`\n"
            "• **say** - `says stuff through the bot`\n"
            "• **profile** - `rank card based on xp`\n"
            "• **set** - `configure profiles and xp`\n"
            "• **xp-config** - `overview of current xp config`\n"
            "• **enable** - `enable a command`\n"
            "• **disable** - `disable a command`"
            "• **restrict** - `block ppl/channels from using cmds`\n"
            "• **unrestrict** - `undoes the following^`\n"
            "• **restricted** - `lists restricted channels/users`\n"
            "• **info** `depending on your args it provides information for users/roles/channels & invites`\n"
            "• **sinfo** - `sends server info`\n"
            "• **partners** - `fates partnered bots/servers`\n"
            "• **servers** - `featured server list`\n"
            "• **statistics** - `how many use each module?`"
            "• **leaderboard** - `servers lvl/xp ranking`\n"
            "• **gleaderboard** - `global lvl/xp ranking`\n"
            "• **ggleaderboard** - `global server ranking`\n"
            "• **mleaderboard** - `monthly server ranking`\n"
            "• **gmleaderboard** - `global monthly ranking`\n"
            "• **vcleaderboard** - `voice call leaderboard`\n"
            "• **gvcleaderboard** - `global vc leaderboard`\n"
        )
        return e

    def mod(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Mod🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            "• **addmod** - `add a user or role as mod`\n"
            "• **delmod** - `remove a user or role as mod`\n"
            "• **modlogs** - `shows active mutes/temp-bans`\n"
            "• **unmute** - `unmutes users so they can talk`\n"
            "• **warn** - `warns users and punishes`\n"
            "• **delwarn** - `removes warns with the provided reason`\n"
            "• **clearwarns** - `resets a users warns`\n"
            "• **config warns** - `set punishments for warn`\n"
            "• **mute** - `mutes users so they can't talk`\n"
            "• **kick** - `kicks a user from the server`\n"
            "• **softban** - `bans and unbans a user deleting 7 days of their msg history`\n"
            "• **tempban** - `bans a user for x amount of time`\n"
            "• **ban** `bans a user from the server`\n"
            "• **role** - `adds/removes roles from a user`\n"
            "• **restore-roles** - `gives roles back on rejoin`\n"
            "• **selfroles** - `gives roles via reaction menus`\n"
            "• **autorole** - `gives users roles on-join`\n"
            "• **verification** - `verify users on_join`\n"
            "• **limit** - `limit channels to only allow messages with things like images`\n"
            "• **anti-spam** - `mutes users when they spam`\n"
            "• **audit** - `tools for searching through the audit log`\n"
            "• **lock** - `kicks users on-join`\n"
            "• **lockb** - `bans users on-join`\n"
            "• **unlock** - `disables any active locks`\n"
            "• **pin** - `pings the msg above`\n"
            "• **purge** - `mass delete messages`\n"
            "• **del-cat** - `deletes a category and its channels`\n"
            "• **nick** - `sets a users nickname`\n"
            "• **massnick** - `sets every users nickname`\n"
            "• **massrole** - `gives everyone a specific role`"
        )
        return e

    def utility(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Utility🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            "• **giveaway** - `easily setup a giveaway`\n"
            "• **members** - `sends the servers member count`\n"
            "• **icon** - `sends the servers icon`\n"
            "• **sinfo** - `sends server info`\n"
            "• **poll** - `makes a reaction poll via embed`\n"
            "• **welcome** - `welcomes users on-join`\n"
            "• **farewell** - `gives users a farewell on-leave`\n"
            "• **logger** - `logs actions to a channel`\n"
            "• **color** - `tests a hex or changes a roles color`\n"
            "• **emoji** - `sends an emojis full image`\n"
            "• **emojis** - `shows the available emoji slots`\n"
            "• **addemoji** - `adds emojis from links or files`\n"
            "• **stealemoji** - `steals an emoji from another server`\n"
            "• **delemoji** - `deletes an emoji`\n"
            "• **owner** - `sends the servers owner mention`\n"
            "• **avatar** - `sends your profile picture`\n"
            "• **topic** - `sends the channel topic`\n"
            "• **note** - `saves a note`\n"
            "• **quicknote** - `notes something without the gif`\n"
            "• **notes** - `sends your last 5 notes`\n"
            "• **wiki** - `sends information on words/phrases`\n"
            "• **ud** - `sends a definition from urban dictionary`\n"
            "• **findmsg** - `searches msg history for a word/phase`\n"
            "• **afk** - `tells users you're afk when mentioned`\n"
            "• **id** - `sends your id & the channels id`\n"
            "• **perms** - `checks what users/roles has a perm`\n"
            "• **create-webhook** - `creates webhooks for mobile`\n"
            "• **vc-log** - `logs vc events to a channel`\n"
            "• **move** - `moves chats to another channel`\n"
            "• **last-entry** - `info on the last ban`\n"
            "• **webhooks** - `list every channels webhooks`\n"
            "• **timer** - `get a reminder on something`\n"
            "• **timers** - `view your running timers`"
        )
        return e

    def fun(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Fun🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            "• **meme** - `sends a random meme`\n"
            "• **ld** - `detects if a users lying`\n"
            "• **fancify** - `makes text fancy`\n"
            "• **factions** - `work/claim/raid/grow`\n"
            "• **encode** - `encodes a msg in base64`\n"
            "• **decode** - `decodes a msg in base64`\n"
            "• **notice** - `acknowledges depression`\n"
            "• **snipe** - `sends the last deleted msg`\n"
            "• **mock** - `mOcKs tExT fOr yOu`\n"
            "• **rate** - `rates the above msg`\n"
            "• **roll** - `sends a number beteen 1 & 6`\n"
            "• **sue** - `sues the mentioned user`\n"
            "• **ask** - `ask meh stuff ¯\_(ツ)_/¯`\n"
            "• **rps** - `play rock paper scissors`\n"
            "• **cookie** - `giv and eat cookies 🤤`\n"
            "• **shoot** - `shoots a user`\n"
            "• **inject** - `injects a user with 'someth'`\n"
            "• **slice** - `slices anything up`\n"
            "• **stab** - `stabs a user`\n"
            "• **boop** - `very kinky shit`\n"
            "• **rr** - `play Russian roulette`"
        )
        return e

    def music(self):
        e = discord.Embed(color=colors.fate())
        owner = self.bot.get_user(config.owner_id())
        e.set_author(name="~==🥂🍸🍷Music🍷🍸🥂==~", icon_url=owner.avatar_url)
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.description = (
            "• **play** - `searches or plays from url`\n"
            "• **playnow** - `plays immediately ignoring queue`\n"
            "• **playat** - `skips to a position in queue`\n"
            "• **find** - `finds a vid from youtube`\n"
            "• **stop** - `stops playing music`\n"
            "• **skip** - `skips a song`\n"
            "• **previous** - `plays the previous song`\n"
            "• **repeat** - `plays a song on a loop while enabled`\n"
            "• **shuffle** - `shuffles the queue`\n"
            "• **pause** - `pauses the current song`\n"
            "• **resume** - `unpauses the current song`\n"
            "• **volume** - `set the playing volume`\n"
            "• **queue** - `shows upcoming songs`\n"
            "• **remove** - `remove a song from queue`\n"
            "• **dc** - `disconnects from vc`\n"
            "• **np** - `info on the current song`"
        )
        return e
