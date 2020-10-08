from os.path import isfile
import json
from discord.ext import commands
import discord
from utils import colors


class Checklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.path = "./data/userdata/checklist.json"
        if isfile(self.path):
            with open(self.path, "r") as f:
                self.data = json.load(f)

    def save_data(self):
        with open(self.path, "w+") as f:
            json.dump(self.data, f)

    @commands.command(name="checklist")
    async def checklist(self, ctx, *args):
        user_id = str(ctx.author.id)
        args = list(args)
        if user_id not in self.data:
            self.data[user_id] = {}
        usage = (
            ".checklist create name\n•Creates a checklist\n"
            ".checklist checklist_name\n• Views a checklist\n"
            ".checklist del checklist_name\n• Deletes a checklist\n"
            ".checklist checklist_name args\n• Adds a task to a checklist"
        )
        if not args:  # show cmd usage + checklists
            e = discord.Embed(color=colors.orange())
            e.description = usage
            if self.data[user_id]:
                checklists = ""
                for checklist in self.data[user_id].keys():
                    checklists += f"{checklist}\n"
                e.add_field(name="Checklists", value=checklists)
            await ctx.send(embed=e)
        elif len(args) == 1:  # show a checklist
            try:
                checklist = self.data[user_id][args[0]]
            except discord.DiscordException:
                return await ctx.send("Unknown checklist")
            emojis = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]

            def get_checklist(checklist):
                e = discord.Embed(color=colors.orange())
                e.set_author(
                    name=f"Checklist: {args[0]}", icon_url=ctx.author.avatar_url
                )
                e.set_thumbnail(url=self.bot.user.avatar_url)
                e.description = ""
                for iteration in range(len(checklist)):
                    task, completed = checklist[iteration]
                    if not completed:
                        e.description += f"\n**#{iteration + 1}**. {task}"
                    else:
                        e.description += f"\n**#{iteration + 1}**. ~~{task}~~"
                return e

            msg = await ctx.send(embed=get_checklist(checklist))
            for iteration in range(len(checklist)):
                await msg.add_reaction(emojis[iteration])
            # start the while loop
        elif len(args) == 2:  # create/delete a checklist
            if args[0] == "create":
                self.data[user_id][args[1]] = []
                e = discord.Embed()
                e.description = f'Created your checklist "{args[1]}"'
                await ctx.send(embed=e)
                self.save_data()
            elif args[0] == "del":
                try:
                    del self.data[user_id][args[0]]
                except IndexError:
                    return await ctx.send("Unknown checklist")
                await ctx.send("👍")
                self.save_data()
            else:
                await ctx.send("Unknown argument passed")
        elif len(args) >= 2:  # adding a task to a checklist
            checklist = args[0]
            args.pop(0)
            if checklist not in self.data[user_id].keys():
                return await ctx.send("Unknown checklist")
            self.data[user_id][checklist].append([" ".join(args), False])
            e = discord.Embed(color=colors.orange())
            e.description = f'Added {" ".join(args)} to {checklist}'
            await ctx.send(embed=e)
            self.save_data()
        else:  # show cmd usage
            e = discord.Embed(color=colors.orange())
            e.set_author(name="Checklist Usage", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.description = usage
            await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Checklist(bot))
