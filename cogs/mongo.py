from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands


class Conversion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # # Create the connection
        # connection = pymongo.MongoClient("127.0.0.1", port=27017)
        # db = connection["fate"]
        #
        # # Reset the table if exists
        # if "AntiSpam" in db.list_collection_names():
        #     db.drop_collection("AntiSpam")
        # collection = db["AntiSpam"]
        #
        # # Convert old data
        # cog = bot.cogs["AntiSpam"]
        # for guild_id, data in cog.toggle.items():
        #     config = {"_id": int(guild_id)}
        #
        #     config["rate_limit"] = {
        #         "toggle": True if data["Rate-Limit"] else False,
        #         "timespan": 5,
        #         "threshold": 4
        #     }
        #     collection.insert_one(config)
        #
        # data = {}
        # for config in collection.find({}):
        #     data[config["_id"]] = {
        #         key: value for key, value in config.items() if key != "_id"
        #     }
        #
        # with open("results.txt", "w+") as f:
        #     json.dump(data, f, indent=2)

    def get_database(self):
        conf = self.bot.config["mongodb"]

        client = AsyncIOMotorClient(conf["url"], **conf["connection_args"])
        db = client.get_database(conf["db"])

        return db

    async def find(self, collection: str, filter: dict, projection: dict = None, fetchall=False):
        db = self.get_database()
        collection = db[collection]

        # What to return
        if filter is None:
            filter = {}

        # What not to return
        if projection is None:
            projection = {}

        if fetchall:
            cursor = collection.find(filter=filter, projection=projection)
            results = []
            async for item in cursor:
                results.append(item)
        else:
            results = await collection.find_one(filter=filter, projection=projection)

        return results

    async def insert(self, collection, data):
        db = self.get_database()
        collection = db[collection]

        await collection.insert_one(
            data
        )

    async def update(self, collection, filter: dict, data: dict, upsert = True):
        db = self.get_database()
        collection = db[collection]

        # What to return
        if filter is None:
            filter = {}

        await collection.update_one(
            filter, {"$set": data}, upsert=upsert
        )

    @commands.command()
    @commands.is_owner()
    async def test_add(self, ctx):
        await self.insert("test", {"_id": 9, "random_thing": "yes"})
        x = await self.find("test", {})
        await ctx.send(x)


def setup(bot):
    bot.add_cog(Conversion(bot))
