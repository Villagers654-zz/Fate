from discord.ext import commands
from time import time
import discord
import aiosqlite

class Test(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.db_path = './data/test.db'

	@commands.command(name="setup_notes")
	async def setup(self, ctx):
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(f"CREATE TABLE notes (user int, note message_text, created_at float)", {'id': ctx.author.id})
			await db.close()

	@commands.command(name="test_note")
	async def note(self, ctx, *, arg=None):
		async with aiosqlite.connect(self.db_path) as db:
			cursor = await db.execute("SELECT * FROM notes WHERE user = :user_id", {'user_id': ctx.author.id})
			rows = await cursor.fetchall()
			print(rows)
			if arg:
				await db.execute("INSERT INTO notes VALUES (:user_id, :note, :created_at)", {'user_id': ctx.author.id, 'note': arg, 'created_at': time()})
				total_notes = 0
				for tuple in rows:
					total_notes += 1
				if total_notes > 5:
					pos = 0
					for note, timestamp in (sorted(rows, key=lambda kv: kv[1], reverse=True)):
						pos += 1
						if pos > 6:
							await db.execute("DELETE from notes WHERE created_at = :created_at", {'id': ctx.author.id, 'created_at': timestamp})
				await ctx.send("noted")
			else:
				exists = False
				for x, y, z in rows:
					if x == ctx.author.id:
						exists = True
						break
				if not exists:
					await ctx.send("no data")
					return await db.close()
				e = discord.Embed()
				e.description = ""
				pos = 0
				for note, timestamp in rows:
					pos += 1
					e.description += f"#{pos}. `{note}`"
				await ctx.send(embed=e)
			await db.close()

def setup(bot):
	bot.add_cog(Test(bot))
