"""
Emojis Shortcut
~~~~~~~~~~~~~~~~

A module for quick access to (discord) emojis

Functions:
    arrow : an emoji that changes depending on the holiday

:copyright: (C) 2020-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from datetime import datetime


# Presences
online = "<:status_online:659976003334045727>"
idle = "<:status_idle:659976006030983206>"
dnd = do_not_disturb = "<:status_dnd:659976008627388438>"
offline = invisible = "<:status_offline:659976011651219462>"

# Server Indicators
discord = "<:discordlogo:673955433131671552>"
members = "👥"
text_channel = "<:textchannel:679179620867899412>"
voice_channel = "<:voicechannel:679179727994617881>"
boost = "<:boost15:673955479675994122>"
booster = "<:boost12:673955482578190356>"
verified = "<:verified:673955386839269396>"
partner = "<:partner:673955399694548994>"

# Indicators
on = "<:toggle_on:673955968857407541>"
off = "<:toggle_off:673955971726311424>"
typing = "<a:typing:673955389431349249>"
loading = "<a:loading:673956001174781983>"
yes = "<a:yes:789735035813101638>"
soon = "<:soontm:739960152140152963>"
never = "<:never:739960284965502987>"
plus = "<:plus:548465119462424595>"
edited = "<:edited:550291696861315093>"
home = "🏡"
up = "⬆️"
down = "⬇️"
double_down = "⏬"
approve = "<:approve:673956036612194325>"
disapprove = "<:disapprove:673956034108194870>"

# Misc
youtube = "<:YouTube:498050040384978945>"
nice = "<a:nice:770080922380271657>"


def arrow():
    date = datetime.utcnow()
    if date.month == 1 and date.day == 26:  # Chinese New Year
        return "🐉"
    if date.month == 2 and date.day == 14:  # Valentines Day
        return "❤"
    if date.month == 6:  # Pride Month
        return "<a:arrow:679213991721173012>"
    if date.month == 7 and date.day == 4:  # July 4th
        return "🎆"
    if date.month == 10 and date.day == 31:  # Halloween
        return "🎃"
    if date.month == 11 and date.day == 26:  # Thanksgiving
        return "🦃"
    if datetime.month == 12 and date.day == 25:  # Christmas
        return "🎄"
    return "<:enter:673955417994559539>"
