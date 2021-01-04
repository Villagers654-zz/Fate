import json
import pymongo
from discord.ext import commands





class Conversion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create the connection
        connection = pymongo.MongoClient("127.0.0.1", port=27017)
        db = connection["fate"]

        # Reset the table if exists
        if "AntiSpam" in db.list_collection_names():
            db.drop_collection("AntiSpam")
        collection = db["AntiSpam"]

        # Convert old data
        cog = bot.cogs["AntiSpam"]
        for guild_id, data in cog.toggle.items():
            config = {"_id": int(guild_id)}

            config["rate_limit"] = {
                "toggle": True if data["Rate-Limit"] else False,
                "timespan": 5,
                "threshold": 4
            }
            collection.insert_one(config)

        data = {}
        for config in collection.find({}):
            data[config["_id"]] = {
                key: value for key, value in config.items() if key != "_id"
            }

        with open("results.txt", "w+") as f:
            json.dump(data, f, indent=2)


def setup(bot):
    bot.add_cog(Conversion(bot))
