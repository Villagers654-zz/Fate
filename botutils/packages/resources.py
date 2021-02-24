from datetime import datetime
from os.path import isfile
import json
import asyncio
from botutils import colors


class Cache:
    def __init__(self, bot, collection):
        self.bot = bot
        self.collection = collection
        self._cache = {}
        for config in bot.mongo[collection].find({}):
            self._cache[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }
        self._unsaved = {}  # type: dict

    async def flush(self):
        collection = self.bot.aio_mongo[self.collection]
        for key, do_insert in list(self._unsaved.items()):
            await asyncio.sleep(0)
            if do_insert:
                await collection.insert_one({
                    "_id": key, **self._cache[key]
                })
            else:
                await collection.update_one(
                    filter={"_id": key},
                    update={"$set": self._cache[key]}
                )
            del self._unsaved[key]

    def keys(self):
        return self._cache.keys()

    def items(self):
        return self._cache.items()

    def __contains__(self, item):
        return item in self._cache

    def __getitem__(self, item):
        return self._cache[item]

    def __setitem__(self, key, value):
        if key in self._cache:
            self._unsaved[key] = False
        elif key not in self._unsaved:
            self._unsaved[key] = True
        self._cache[key] = value

    def remove(self, key):
        if key not in self._unsaved or (key in self._unsaved and not self._unsaved[key]):
            self.bot.loop.create_task(self._remove_from_db(key))
        if key in self._unsaved:
            del self._unsaved[key]

    def remove_sub(self, *args, **kwargs):
        self.remove_sub_key(*args, **kwargs)

    def remove_sub_key(self, key, sub_key):
        self.bot.loop.create_task(self._remove_from_db(key, sub_key))

    async def _remove_from_db(self, key, sub_key=None):
        collection = self.bot.aio_mongo[self.collection]
        if sub_key:
            await collection.update_one(
                filter={"_id": key},
                update={"$unset": {sub_key: 1}}
            )
        else:
            await collection.delete_one({"_id": key})
            del self._cache[key]


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
    # Presences
    online = "<:status_online:659976003334045727>"
    idle = "<:status_idle:659976006030983206>"
    dnd = do_not_disturb = "<:status_dnd:659976008627388438>"
    offline = invisible = "<:status_offline:659976011651219462>"

    # Server Indicators
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

    # Misc
    youtube = "<:YouTube:498050040384978945>"
    nice = "<a:nice:770080922380271657>"

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
    cls.cache = lambda col: Cache(cls.bot, col)
