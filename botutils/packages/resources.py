from datetime import datetime
from os.path import isfile
import json
from botutils import colors


def get_config():
    if not isfile("./data/userdata/config.json"):
        with open("./data/userdata/config.json", "w") as f:
            json.dump({}, f, ensure_ascii=False)
    with open("./data/userdata/config.json", "r") as f:
        return json.load(f)


def get_stats():
    if not isfile("./data/stats.json"):
        with open("./data/stats.json", "w") as f:
            json.dump({"commands": []}, f, ensure_ascii=False)
    with open("./data/stats.json", "r") as stats:
        return json.load(stats)


def generate_rainbow_rgb(amount: int) -> list:
    fixed_colors = [
        (255, 0, 0),  # Red
        (255, 127, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),  # Green
        (0, 0, 255),  # Blue
        (75, 0, 130),  # Dark Purple
        (148, 0, 211),  # Purple
    ]
    color_array = []
    for iteration, (r, g, b) in enumerate(fixed_colors):
        color_array.append((r, g, b))
        if len(fixed_colors) != iteration + 1:
            nr, ng, nb = fixed_colors[iteration + 1]
            divide_into = int(amount / len(fixed_colors)) + 2
            r_diff = (nr - r) / divide_into
            g_diff = (ng - g) / divide_into
            b_diff = (nb - b) / divide_into
            for i in range(divide_into):
                r += r_diff
                g += g_diff
                b += b_diff
                color_array.append((int(r), int(g), int(b)))
    return color_array


class Emojis:
    def __init__(self):

        # Presences
        self.online = "<:status_online:659976003334045727>"
        self.idle = "<:status_idle:659976006030983206>"
        self.dnd = self.do_not_disturb = "<:status_dnd:659976008627388438>"
        self.offline = self.invisible = "<:status_offline:659976011651219462>"

        # Server Indicators
        self.members = "👥"
        self.text_channel = "<:textchannel:679179620867899412>"
        self.voice_channel = "<:voicechannel:679179727994617881>"
        self.boost = "<:boost15:673955479675994122>"
        self.booster = "<:boost12:673955482578190356>"
        self.verified = "<:verified:673955386839269396>"
        self.partner = "<:partner:673955399694548994>"

        # Indicators
        self.on = "<:toggle_on:673955968857407541>"
        self.off = "<:toggle_off:673955971726311424>"
        self.typing = "<a:typing:673955389431349249>"
        self.loading = "<a:loading:673956001174781983>"
        self.yes = "<a:yes:789735035813101638>"
        self.soon = "<:soontm:739960152140152963>"
        self.never = "<:never:739960284965502987>"
        self.plus = "<:plus:548465119462424595>"
        self.edited = "<:edited:550291696861315093>"

        # Misc
        self.youtube = "<:YouTube:498050040384978945>"
        self.nice = "<a:nice:770080922380271657>"

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
    cls.generate_rainbow_rgb = generate_rainbow_rgb
    cls.get_config = get_config
    cls.get_stats = get_stats
    cls.emotes = Emojis()
