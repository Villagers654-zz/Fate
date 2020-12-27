from datetime import datetime
from botutils import colors


class Emojis:
    def __init__(self):
        self.plus = "<:plus:548465119462424595>"
        self.edited = "<:edited:550291696861315093>"
        self.members = "👥"
        self.text_channel = "<:textchannel:679179620867899412>"
        self.voice_channel = "<:voicechannel:679179727994617881>"
        self.online = "<:status_online:659976003334045727>"
        self.idle = "<:status_idle:659976006030983206>"
        self.dnd = self.do_not_disturb = "<:status_dnd:659976008627388438>"
        self.offline = self.invisible = "<:status_offline:659976011651219462>"
        self.boost = "<:boost15:673955479675994122>"
        self.booster = "<:boost12:673955482578190356>"

    @property
    def arrow(self):
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


def init(cls):
    cls.colors = colors
    cls.emotes = Emojis()
