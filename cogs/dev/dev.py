from typing import *
from time import monotonic
from os import path
from os.path import isfile
from io import BytesIO
from datetime import datetime, timedelta
import subprocess
import requests
import discord
import asyncio
import os
import traceback
import random
import aiohttp
import json
from time import time
import io
from random import randint
import sys
from pympler import asizeof

from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
from ast import literal_eval
from PIL import Image, ImageFont, ImageDraw, ImageSequence
import youtube_dl
import inspect
from contextlib import redirect_stdout

from utils import colors, config, checks
from cogs.core.utils import Utils as utils


class EmptyException(Exception):
	pass


def get_size(obj, seen=None):
	"""Recursively finds size of objects"""
	size = sys.getsizeof(obj)
	if seen is None:
		seen = set()
	obj_id = id(obj)
	if obj_id in seen:
		return 0
	# Important mark as seen *before* entering recursion to gracefully handle
	# self-referential objects
	seen.add(obj_id)
	if isinstance(obj, dict):
		size += sum([get_size(v, seen) for v in obj.values()])
		size += sum([get_size(k, seen) for k in obj.keys()])
	elif hasattr(obj, '__dict__'):
		size += get_size(obj.__dict__, seen)
	elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
		size += sum([get_size(i, seen) for i in obj])
	return size


class WaitForMessage:
	def __init__(self, bot, user, channel=None, timeout=60):
		self.bot = bot
		self.user = user
		self.channel = channel
		self.timeout = timeout

	async def __aenter__(self):
		def predicate(msg):
			if self.channel and msg.channel.id != self.channel.id:
				return False
			return msg.author.id == self.user.id

		try:
			message = await self.bot.wait_for("message", check=predicate, timeout=self.timeout)
		except asyncio.TimeoutError:
			raise self.bot.ignore()
		return message

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		print("__exit__")

class ListManager(list):
	def __init__(self, bot, keep_for: int = 10):
		self.bot = bot
		self.keep_for = keep_for
		super().__init__()

	async def remove_after(self, value):
		await asyncio.sleep(self.keep_for)
		if value in super().__iter__():
			super().remove(value)

	def append(self, *args, **kwargs):
		super().append(*args, **kwargs)
		self.bot.loop.create_task(
			self.remove_after(args[0])
		)


class Dev(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last = {}
		self.silence = None
		self.lst = ListManager(bot, keep_for=10)



	@commands.command(name="set-avatar", aliases=["set_avatar"])
	@commands.is_owner()
	async def set_avatar(self, ctx):
		if not ctx.message.attachments:
			return await ctx.send("You need to attach a file")
		raw_file = await ctx.message.attachments[0].read()
		await self.bot.user.edit(avatar=raw_file)
		await ctx.send("Updated my avatar")

	@commands.Cog.listener("on_message")
	async def prevent_bmo_spam(self, msg):
		if msg.author.id == 0 and msg.embeds and msg.guild:
			if msg.channel.permissions_for(msg.guild.me).manage_messages:
				segment = "I know this is annoying"
				if segment in str(msg.embeds[0].to_dict()):
					await msg.delete()

	@commands.command(name="yeet-stuff")
	@commands.is_owner()
	async def _yeet_exploiters(self, ctx):
		await ctx.send("Yeeting stuff")
		total = 0
		async with self.bot.pool.acquire() as conn:
			async with conn.cursor() as cur:
				queries = []
				await cur.execute(f"select user_id, xp from global_msg;")
				results = await cur.fetchall()
				index = {}
				for user_id, xp in results:
					if user_id in index:
						if xp <= index[user_id]:
							queries.append(
								f"delete from global_msg "
								f"where user_id = {user_id} "
								f"and xp = {xp} limit 1;"
							)
							total += 1
						else:
							queries.append(f"delete from global_msg where user_id = {user_id} and xp = {index[user_id]};")
					else:
						index[user_id] = xp
				await ctx.send(f"Removing {len(queries)} duplicates")
				last = time()
				for i, query in enumerate(queries):
					await cur.execute(query)
					if time() - last > 25:
						await ctx.send(f"{len(queries) - (i + 1)} left")
						last = time()
				await conn.commit()
		await ctx.send(f"Removed {total} global duplicates")

		await ctx.send("Onto guilded..")
		total = 0
		async with self.bot.pool.acquire() as conn:
			async with conn.cursor() as cur:
				last = time()
				await cur.execute(f"select guild_id, user_id, xp from msg;")
				results = await cur.fetchall()
				index = {}
				removed = []
				for guild_id, user_id, xp in sorted(results, key=lambda kv: kv[0]):
					if guild_id not in index:
						index[guild_id] = {}
					if user_id in index[guild_id]:
						if xp <= index[guild_id][user_id]:
							if [guild_id, user_id] in removed:
								continue
							await cur.execute(
								f"delete from msg "
								f"where guild_id = {guild_id} "
								f"and user_id = {user_id};"
							)
							await cur.execute(
								f"insert into msg "
								f"values ({guild_id}, {user_id}, {xp});"
							)
							removed.append([guild_id, user_id])
							total += 1
							if time() - last > 30:
								await ctx.send(f"currently at {total}/{len(results)}")
								last = time()
						else:
							queries.append(f"delete from msg where guild_id = {guild_id} and user_id = {user_id} and xp = {index[guild_id][user_id]};")
					else:
						index[guild_id][user_id] = xp
				await conn.commit()
		await ctx.send(f"Removed {total} guilded duplicates")

	@commands.command(name="update-console")
	async def update_console(self, ctx):
		r = "\033[0;37;0m"
		green = "\033[1;32;40m"

		print(chr(27) + "[2J")  # Clear the terminal
		columns, lines = os.get_terminal_size()
		lines = ["" for _ in range(lines - 1)]
		lines[0] = f"{green}◈ {self.bot.user} ◈{r}"
		# lines[0] = lines[0] + f"{green}Online{r}".rjust(columns - len(lines[0]) + 36, " ")
		lines[1] = f"• {self.bot.user.id}"
		lines[2] = f"• Servers: {len(self.bot.guilds)}"
		lines[3] = f"• Users: {len(self.bot.users)}"

		last = len(lines) - 1
		lines[last] = f"{green}Up And Running{r}"
		lines[last] = lines[last].center(columns - len(lines[last]) + 18, " ")
		print("\n".join(lines))
		await ctx.send("Updated console")


	@commands.command(name="cut-frames")
	async def cut_frames(self, ctx):
		if not ctx.message.attachments:
			return await ctx.send("You need to attach a file")
		attachment = ctx.message.attachments[0]
		file = BytesIO(await attachment.read())
		img = Image.open(file)
		frames = []
		index = 0
		dur = img.info["duration"]
		for frame in ImageSequence.Iterator(img):
			if index % 2 == 0:
				frame = frame.resize((85, 85), Image.BICUBIC).convert("RGB")
				frames.append(frame)
			index += 1
		frames[0].save(
			"./static/cut.gif",
			save_all=True,
			append_images=frames[1:],
			loop=0,
			duration=dur*2,
			optimize=False
		)
		await ctx.send(file=discord.File("./static/cut.gif"))

	@commands.command()
	async def appendlst(self, ctx, value):
		self.lst.append(value)
		await ctx.send("done")

	@commands.command()
	async def lst(self, ctx):
		await ctx.send(self.lst)

	@commands.command(name="uptime")
	async def uptime(self, ctx):
		async with self.bot.open("./data/uptime.json", "r") as f:
			uptime_data = json.loads(await f.read())
		uptime_data = [
			datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
			for date_string in uptime_data
		]

		timespan = (uptime_data[len(uptime_data) - 1] - uptime_data[0]).seconds
		downtime = 0
		for iteration, date in enumerate(uptime_data):
			if iteration != len(uptime_data) - 1:
				diff = (uptime_data[iteration + 1] - date).seconds
				if diff > 60:
					downtime += diff
					continue

		if downtime == 0:
			downtime = 1
		percentage = 100 - ((round(downtime) / round(timespan)) * 100)
		await ctx.send(100 - percentage)

	@commands.command(name="cog-usage")
	@commands.is_owner()
	async def module_usage(self, ctx):
		def collect_memory_usage():
			def get_size(object):
				full_size = 0
				for var in vars(object):
					var = eval(f"object.{var}")
					if isinstance(var, dict):
						full_size += asizeof.asizeof(var, detail=1)
				return full_size

			e = discord.Embed(color=colors.fate())
			e.set_author(name=f"Top Memory Usage")
			e.description = ""
			cogs = [
					(cog, get_size(self.bot.get_cog(cog))) for cog in self.bot.cogs
				]
			for i, (cog, usage) in enumerate(sorted(cogs, reverse=True, key=lambda kv: kv[1])[:9]):
				e.description += f"#{i + 1}. `{cog}` - {self.bot.utils.bytes2human(usage)}\n"
			e.add_field(
				name="◈ Message Cache",
				value=f"`{len(self.bot.cached_messages)} messages` - " + str(self.bot.utils.bytes2human(
					asizeof.asizeof(self.bot.cached_messages, detail=1)
				)),
				inline=False
			)
			return e

		msg = await ctx.send("Fetching all the shit ig ._.")
		result = await self.bot.loop.run_in_executor(None, collect_memory_usage)
		await msg.edit(content=None, embed=result)

	async def verify_user(self, context=None, channel=None, user=None, timeout=45, delete_after=False):
		if not user and not context:
			raise TypeError("verify_user() requires either 'context' or 'user', and neither was given")
		if not channel and not context:
			raise TypeError("verify_user() requires either 'context' or 'channel', and neither was given")
		if not user:
			user = context.author
		if not channel:
			channel = context.channel

		fp = os.path.basename(f"./static/captcha-{time()}.gif")
		abcs = "abcdefghijklmnopqrstuvwxyz"
		chars = " ".join([random.choice(list(abcs)).upper() for _i in range(6)])

		def create_card():
			colors = ["orange", "green", "white", "cyan", "red"]
			font = ImageFont.truetype("./utils/fonts/Modern_Sans_Light.otf", 75)
			size = font.getsize(chars)
			card = Image.new("RGBA", size=(size[0] + 20, 80), color=(255, 255, 255, 0))
			draw = ImageDraw.Draw(card)
			draw.text((10, 10), chars, fill="blue", font=font)

			lowest_range = 5
			max_range = size[0] + 15
			redirections = 5
			divide = (max_range - lowest_range) / redirections

			sets = []
			for i in range(9):
				positions = [[10, randint(10, 65)]]
				for iteration in range(redirections + 1):
					positions.append([divide * (iteration + 1), randint(10, 65)])
				sets.append(positions)

			new_sets = []
			for iteration, full_positions in enumerate(sets):
				# new_sets.append(full_positions)  # Extends too far to the right
				if iteration != len(sets) - 1:
					next_positions = sets[iteration + 1]
#
					# Add frames in-between
					for iter in range(10):
						new_set = []
						for i, (x, y) in enumerate(full_positions):
							if i != len(full_positions) - 1:
								nx, ny = next_positions[i]
								takeaway = (y - ny) / 10
								progress = (takeaway * (iter + 1))
								new_set.append([x, y - progress])
						new_sets.append(new_set)

			frames = []
			nums = [int(x * (255 / len(new_sets))) for x in range(len(new_sets))]
			colors = [(255, int(x), int(x)) for x in nums]
			color_array = self.bot.utils.generate_rainbow_rgb(len(new_sets))
			for iteration, positions in enumerate(new_sets):
				card = Image.new("P", size=(size[0] + 20, 80), color=(47, 49, 54))
				draw = ImageDraw.Draw(card)
				draw.text((10, 10), chars, fill=color_array[iteration], font=font)
				for i, (x, y) in enumerate(positions):
					if i != len(positions) - 1:
						nx, ny = positions[i + 1]
						draw.line((x, y, nx, ny), fill=colors[iteration], width=4)
				frames.append(card)

			main = frames[0]
			frames.pop(0)
			main.save(fp, 'GIF', save_all=True,  append_images=[*frames, *reversed(frames)], duration=2, loop=0, optimize=False)

		await self.bot.loop.run_in_executor(None, create_card)

		e = discord.Embed(color=colors.fate())
		e.set_author(name=str(user), icon_url=user.avatar_url)
		e.set_image(url="attachment://" + fp)
		e.set_footer(text=f"You have {self.bot.utils.get_time(timeout)}")
		message = await channel.send(f"{user.mention} please verify you're human", embed=e, file=discord.File(fp))
		os.remove(fp)

		def pred(m):
			return m.author.id == user.id and str(m.content).lower() == chars.lower().replace(" ", "")

		try:
			await self.bot.wait_for("message", check=pred, timeout=timeout)
		except asyncio.TimeoutError:
			if delete_after:
				await message.delete()
			else:
				e.set_footer(text="Captcha Failed")
				await message.edit(embed=e)
			return False
		else:
			if delete_after:
				await message.delete()
			else:
				e.set_footer(text="Captcha Passed")
				await message.edit(content=None, embed=e)
			return True

	@commands.command(name="test-verify")
	async def read(self, ctx):
		await self.verify_user(ctx, ctx.channel, ctx.author)

	def console(ctx):
		return ctx.author.id == config.owner_id()

	def slut(ctx: commands.Context):
		return ctx.author.id in [config.owner_id(), 292840109072580618, 355026215137968129, 459235187469975572, 611108193275478018, 544911653058248734, 243233669148442624, 261569654646898688, 365943419769585674, 297045071457681409]

	def cleanup_code(self, content):
		"""Automatically removes code blocks from the code."""
		# remove ```py\n```
		if content.startswith("```") and content.endswith("```"):
			return "\n".join(content.split("\n")[1:-1])

		# remove `foo`
		return content.strip("` \n")

	def get_syntax_error(self, e):
		if e.text is None:
			return f"```py\n{e.__class__.__name__}: {e}\n```"
		return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'


	@commands.command(name="modlog")
	@commands.is_owner()
	async def modlog(self, ctx, *, reason):
		cog = self.bot.cogs["CaseManager"]
		case = await cog.add_case(ctx.guild.id, ctx.author.id, "mute", reason, ctx.author.id)
		await ctx.send(f"Added case #{case}")


	@commands.command(name="new-run")
	async def run(self, ctx, *, args):
		variables = {
			"ctx": ctx,
			"bot": self.bot,
			"message": ctx.message,
			"guild": ctx.guild,
			"channel": ctx.channel,
			"author": ctx.author,
			"_": None,
		}

		cleaned = self.cleanup_code(args)
		executor = exec
		if cleaned.count("\n") == 0:
			# single statement, potentially 'eval'
			try:
				code = compile(cleaned, "<repl session>", "eval")
			except SyntaxError:
				pass
			else:
				executor = eval

		if executor is exec:
			try:
				code = compile(cleaned, "<repl session>", "exec")
			except SyntaxError as e:
				await ctx.send(self.get_syntax_error(e))

		variables["message"] = ctx.message

		fmt = None
		stdout = io.StringIO()

		try:
			with redirect_stdout(stdout):
				result = executor(code, variables)
				if inspect.isawaitable(result):
					result = await result
		except Exception as e:
			value = stdout.getvalue()
			fmt = f"```py\n{value}{traceback.format_exc()}\n```"
		else:
			value = stdout.getvalue()
			if result is not None:
				fmt = f"```py\n{value}{result}\n```"
				variables["_"] = result
			elif value:
				fmt = f"```py\n{value}\n```"

		try:
			if fmt is not None:
				if len(fmt) > 2000:
					await ctx.send("Content too big to be printed.")
				else:
					await ctx.send(fmt)
		except discord.Forbidden:
			pass
		except discord.HTTPException as e:
			await ctx.send(f"Unexpected error: `{e}`")

	@commands.command(name="choice")
	async def choose_what(self, ctx, *options):
		choice = await self.bot.get_choice(ctx, *options, user=ctx.author)
		await ctx.send(f"You chose {choice}")

	@commands.command(name="captcha")
	async def captcha(self, ctx):
		passed = await self.verify_user(ctx, user=ctx.author)
		if passed:
			await ctx.send("Successfully completed verification")
		else:
			await ctx.send("You failure..")

	@commands.command("thinking-bee")
	@commands.is_owner()
	async def thinking_bee(self, ctx, user: Optional[discord.User]):
		if not user:
			user = ctx.channel
		with open("bee_movie.txt", "r") as f:
			script = f.readlines()
		chunk = ""
		index = 0
		for line in script:
			if len(chunk) + len(line) >= 1000:
				await user.send(chunk)
				chunk = ""
				index += 1
				if index % 100 == 0:
					await ctx.send(f"I'm at {index} messages sent")
				continue
			chunk += line
		await user.send(chunk)
		await ctx.send("Buzz buzz, I'm finished")

	@commands.command(name="debug", aliases=['debug-mode', "debug_mode"])
	@commands.cooldown(*utils.default_cooldown())
	@commands.is_owner()
	async def debug_mode(self, ctx):
		self.bot.config["debug_mode"] = False if self.bot.config["debug_mode"] else True
		await ctx.send(f"{'Enabled' if self.bot.config['debug_mode'] else 'Disabled'} debug mode")

	@commands.command(name='download', aliases=['dl'])
	@commands.check(lambda ctx: ctx.author.id in [264838866480005122, 355026215137968129])
	async def download(self, ctx, url):
		with youtube_dl.YoutubeDL() as ydl:
			info = ydl.extract_info(url, download=False)
		fp = f"./static/{info.get('title', None).replace(' ', '_')}.mp3"
		ydl_opts = {
			'format': 'bestaudio/best',
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'preferredcodec': 'mp3',
				'preferredquality': '192',
			}],
			'outtmpl': fp,
		}
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
		await ctx.send(file=discord.File(fp))
		os.remove(fp)

	@commands.command(name='role-converter')
	async def role_converter(self, ctx, *, role):
		role = await self.bot.utils.get_role(ctx, role)
		await ctx.send(str(role))

	@commands.command('add-log')
	async def add_log(self, ctx, *, msg):
		with open('discord.log', 'r') as f:
			log = f.read()
		log += msg
		with open('discord.log', 'w') as f:
			f.write(log)
		await ctx.send('Done')

	@commands.command(name='test')
	async def test(self, ctx):
		e = discord.Embed(color=colors.fate())
		e.set_author(name="Fate Bot", icon_url=self.bot.get_user(self.bot.config["bot_owner_id"]).avatar_url)
		e.set_thumbnail(url=self.bot.user.avatar_url)
		e.description = "A multipurpose bot with fun, moderation, and utility features just to help out as needed" \
		                "\nMy commands prefix is `.` or my @mention"
		e.add_field(
			name="◈ Some Moderation Features",
			value="• anti spam - `useful for things like fast rates`"
				  "\n• anti raid - `prevent mass kick and ban raids`"
				  "\n• chatfilter - `filter out certain words and phrases`"
				  "\n• restrict - `prevent use of cmds in specific channels`",
			inline=False
		)
		e.add_field(
			name="◈ Some Utility Features",
			value="• logger - `log actions on the server`"
			      "\n• selfroles - `self assigning roles`"
			      "\n• vclog - `log voice actions`"
				  "\n• giveaways - `give away rewards`",
			inline=False
		)
		e.add_field(
			name="◈ Some Fun Features",
			value="• ranking - `customizable xp system`"
			      "\n• factions - `factions minigame, on discord`",
			inline=False
		)
		e.add_field(
			name="◈ Some Misc Features",
			value=">>> Join/leave messages, a music player powered by Lavalink, and reaction commands "
			      "alongside a reaction based help menu for ease of use",
			inline=False
		)
		e.add_field(
			name="◈ Some Linkies",
			value=f"[Invite Me]({self.bot.invite_url}) | [Get Some Support]({self.bot.config['support_server']})"
		)
		await ctx.send(embed=e)

		# x = 'breh
		# y = 'uwu'
		# no_width_char = u"\u200B"
		# result = x + y.rjust(32 - len(x), char)
		# result = result.replace(' ', ' '+no_width_char)
		# e = discord.Embed(description=result)
		# await ctx.send(result, embed=e)

		# user_id = ctx.author.id
		# yeet = await self.bot.select('*', 'global_msg', user_id=user_id)
		# await ctx.send(yeet)

		# index = {
		# 	cat: {
		# 		cmd.name: cmd.description for cmd in self.bot.commands if type(cmd.cog).__name__ == cat
		# 	} for cat in set(type(cmd.cog).__name__ for cmd in self.bot.commands)
		# }
		# await ctx.send(f"```json\n{str(json.dumps(index, indent=2))[:1950]}```")

		# p = subprocess.Popen(f'python3 memory_info.py {os.getpid()}', stdout=subprocess.PIPE, shell=True)
		# await asyncio.sleep(1)
		# (output, err) = p.communicate()
		# output = str(output if len(str(output)) > 0 else err).replace("\\t", "    ").replace("b'", "").split("\\n")
		# await ctx.send(output)
#
		# reader, writer = await asyncio.open_connection('127.0.0.1', 1269, loop=self.bot.loop)
		# writer.write(f'memory_info {os.getpid()}'.encode())
		# data = await reader.read(1000)
		# reply = data.decode()
		# await ctx.send(reply)

	@commands.command(name='convert-xp')
	@commands.is_owner()
	async def convert_xp(self, ctx):
		before = monotonic()
		data = {}
		for directory in os.listdir(path.join('xp', 'guilds')):
			if directory.isdigit():
				data[directory] = {}
				for filename in os.listdir(path.join('xp', 'guilds', directory)):
					if '.json' in filename:
						try:
							with open(path.join('xp', 'guilds', directory, filename), 'r') as f:
								data[directory][filename.replace('.json', '')] = json.load(f)
						except json.JSONDecodeError:
							with open(path.join('xp', 'guilds', directory, 'backup', filename), 'r') as f:
								data[directory][filename.replace('.json', '')] = json.load(f)

		async with self.bot.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute("DROP TABLE IF EXISTS msg;")
				await cur.execute("DROP TABLE IF EXISTS monthly_msg;")
				await cur.execute("DROP TABLE IF EXISTS vc_xp;")
				await cur.execute("DROP TABLE IF EXISTS global_msg;")
				await cur.execute("DROP TABLE IF EXISTS global_vc;")
				await cur.execute("DROP TABLE IF EXISTS global_monthly;")

				await cur.execute("CREATE TABLE msg (guild_id bigint, user_id bigint, xp int);")
				await cur.execute("CREATE TABLE vc_xp (guild_id bigint, user_id bigint, xp int);")
				await cur.execute("CREATE TABLE monthly_msg (guild_id bigint, user_id bigint, msg_time float, xp int);")

				for guild_id, dat in data.items():
					for user_id, xp in dat['msg'].items():
						await cur.execute(f"INSERT INTO msg VALUES ({int(guild_id)}, {int(user_id)}, {xp});")

					for user_id, xp in dat['vc'].items():
						await cur.execute(f"INSERT INTO vc_xp VALUES ({int(guild_id)}, {int(user_id)}, {int(xp)});")

					for user_id, msgs in dat['monthly_msg'].items():
						for msg_time, xp in msgs.items():
							await cur.execute(f"INSERT INTO monthly_msg VALUES ({int(guild_id)}, {int(user_id)}, {msg_time}, {xp});")

				await cur.execute("CREATE TABLE global_msg (user_id bigint, xp int);")
				with open('./xp/global/msg.json', 'r') as f:
					dat = json.load(f)
				for user_id, xp in dat.items():
					await cur.execute(f"INSERT INTO global_msg VALUES ({int(user_id)}, {xp});")
				await ctx.send('Converted global msg xp')

				await cur.execute("CREATE TABLE global_vc (user_id bigint, xp int);")
				with open('./xp/global/vc.json', 'r') as f:
					dat = json.load(f)
				for user_id, xp in dat.items():
					await cur.execute(f"INSERT INTO global_vc VALUES({int(user_id)}, {xp});")
				await ctx.send('Converted global vc xp')

				with open('./xp/global/monthly_msg.json', 'r') as f:
					dat = json.load(f)
				await cur.execute(f"CREATE TABLE global_monthly (user_id bigint, msg_time int, xp int);")
				for user_id, msgs in dat.items():
					for msg_time, xp in msgs.items():
						await cur.execute(f"INSERT INTO global_monthly VALUES ({int(user_id)}, {msg_time}, {xp});")

				await conn.commit()
		await ctx.send(f"Converted global xp\noperation took {round((monotonic() - before) * 1000)}ms")

	@commands.command(name='check', enabled=False)
	@commands.is_owner()
	async def check(self, ctx, url):
		""" Check the pixels in an img """
		def guess_seq_len(seq):
			guess = 1
			max_len = len(seq) / 2
			for x in range(2, int(max_len)):
				if seq[0:x] == seq[x:2 * x]:
					guess = x

			return guess

		gif_dir = path.join('static', 'gif')
		if not path.exists(gif_dir):
			os.mkdir(gif_dir)
		for file in os.listdir(gif_dir):
			os.remove(path.join(gif_dir, file))

		before = monotonic()
		im = Image.open(BytesIO(requests.get(url).content))
		try:
			index = 0
			while True:
				im.seek(index)
				im.save(path.join(gif_dir, str(index) + '.png'))
				index += 1
		except EOFError:
			pass

		data = []
		last = []
		for file in os.listdir(gif_dir):
			im = Image.open(path.join(gif_dir, file)).convert("RGBA")
			im_data = im.getdata()
			for r, g, b, c in im_data:
				data.append(r+g+b)
			r = g = b = c = 0
			for pixel in im_data:
				r += pixel[0]
				g += pixel[1]
				b += pixel[2]
				c += 1
			r = r / c
			g = g / c
			b = b / c
			last.append(r+g+b)
		seq = guess_seq_len(last)

		bright = [c for c in data if c > 64]
		dark = [c for c in data if c < 64]
		ping = (monotonic() - before) * 1000

		await ctx.send(f'Collection took {round(ping)}ms')
		await ctx.send(f'1: {len(bright)}\n2: {len(dark)}\n3: {len(data)}')
		await ctx.send(f'4: {seq}')

	@commands.command(name='dev-add-emoji')
	@commands.is_owner()
	async def dev_add_emojis(self, ctx):
		await ctx.send('Starting..')
		async for msg in ctx.channel.history(limit=200):
			for attachment in msg.attachments:
				image = requests.get(attachment.url).content  # type: bytes
				try:
					await ctx.guild.create_custom_emoji(name='uno', image=image)
				except Exception as e:
					if '256' not in str(e):
						return await ctx.send(e)
					await ctx.send(f'Too large: {attachment.filename}')
		await ctx.send('done')

	@commands.command(name='rgb')
	async def rgb(self, ctx, r: int, g: int, b: int):
		color = (int(r), int(g), int(b))
		im = Image.new('RGBA', (10, 10), color)
		im.save('static/test.png')
		await ctx.send(file=discord.File('static/test.png'))

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if payload.message_id == 661574587313684491:
			if payload.emoji.id == 661774359769251850:
				guild = self.bot.get_guild(payload.guild_id)
				member = guild.get_member(payload.user_id)
				await member.add_roles(guild.get_role(661413818538393630))

	@commands.command(name='e-elon')
	async def sjagcmhier(self, ctx):
		e = discord.Embed()
		e.set_author(name='e', icon_url='https://cdn.discordapp.com/avatars/544911653058248734/a_b0cfadfcb842a8d328c59b353444ec8f.gif?size=1024')
		await ctx.send(embed=e)

	@commands.command(name='react')
	@commands.is_owner()
	async def react(self, ctx, msg_id: int, channel: Optional[discord.TextChannel], emoji):
		if not channel:
			channel = ctx.channel
		msg = await channel.fetch_message(msg_id)
		await msg.add_reaction(emoji)

	@commands.command(name='role-ids')
	async def role_ids(self, ctx):
		roles = '\n'.join([f'{role.name} - {role.id}' for role in ctx.guild.roles])
		await ctx.send(f'```{roles}```')

	@commands.command(name='steal-from')
	@commands.is_owner()
	async def steal_emojis_from_guild(self, ctx, guild_id: int):
		guild = self.bot.get_guild(guild_id)
		required = None

		#emojis = [emoji for emoji in ctx.guild.emojis if not emoji.animated]
		#animated_emojis = [emoji for emoji in ctx.guild.emojis if emoji.animated]
#
		#other_emojis = [emoji for emoji in guild.emojis if not emoji.animated]
		#other_animated_emojis = [emoji for emoji in guild.emojis if emoji.animated]
#
		#if len(other_emojis) > ctx.guild.emoji_limit - len(emojis):
		#	required = 0 - (ctx.guild.emoji_limit - len(emojis) - len(other_emojis))
		#	await ctx.send(f"You need {required} more normal slots")
		#if len(other_animated_emojis) > ctx.guild.emoji_limit - len(animated_emojis):
		#	required = 0 - (ctx.guild.emoji_limit - len(animated_emojis) - len(other_animated_emojis))
		#	await ctx.send(f"{'You need' if not required else 'and'} {required} animated slots")
		#if required:
		#	return

		await ctx.send('◈ Transferring Emojis..')
		for emoji in list(guild.emojis):
			try:
				await ctx.guild.create_custom_emoji(name=emoji.name, image=requests.get(emoji.url).content, reason="Loading emotes from other server")
				await ctx.send(f"{emoji} - Added {emoji.name}")
			except Exception as e:
				await ctx.send(f"{emoji} - Error:\n`{e}`")
		await ctx.send('Done')

	@commands.command(name='load-gay')
	@commands.has_permissions(manage_roles=True)
	async def load_gay(self, ctx):
		color_set = {
			'Blood Red': [0xff0000, '🍎'],
			'Orange': [0xff5b00, '🍊'],
			'Bright Yellow': [0xffff00, '🍋'],
			'Dark Yellow': [0xffd800, '💛'],
			'Light Green': [0x00ff00, '🍐'],
			'Dark Green': [0x009200, '🍏'],
			'Light Blue': [0x00ffff, '❄'],
			'Navy Blue': [0x0089ff, '🗺'],
			'Dark Blue': [0x0000ff, '🦋'],
			'Dark Purple': [0x9400d3, '🍇'],
			'Light Purple': [0xb04eff, '💜'],
			'Hot Pink': [0xf47fff, '💗'],
			'Pink': [0xff9dd1, '🌸'],
			'Black': [0x030303, '🕸'],
		}
		msg = await ctx.send("Creating gae..")
		for name, dat in color_set.items():
			hex, emoji = dat
			role = await ctx.guild.create_role(name=name, color=discord.Color(hex))
			await msg.edit(content=f"{msg.content}\nCreated {role.mention}")


	@commands.command(name='get-mentions')
	async def get_mentions(self, ctx):
		await ctx.message.attachments[0].save('members.txt')
		with open('members.txt', 'r') as f:
			lines = f.readlines()
			msg = ''
			for line in lines:
				user_id, tag, mention = line.split(', ')
				if int(user_id) not in [m.id for m in ctx.guild.members]:
					if len(msg) + len(f'{mention}') > 2000:
						await ctx.send(msg)
						msg = ''
					msg += f'{mention}'
			await ctx.send(msg)


	@commands.command(name='wsay')
	async def webhook_say(self, ctx, *, args):
		webhook = await ctx.channel.create_webhook(name='test')
		async with aiohttp.ClientSession() as session:
			webhook = Webhook.from_url(webhook.url, adapter=AsyncWebhookAdapter(session))
			await webhook.send(
				args, username=ctx.author.name, avatar_url=ctx.author.avatar_url,
				allowed_mentions=self.bot.allowed_mentions
			)
			await webhook.delete()
		await ctx.message.delete()

	@commands.command(name='members-in')
	async def members_in(self, ctx, guild_id: int):
		if guild_id == 594055355609382922:  # dq6
			return await ctx.send('biTch nO')
		guild = self.bot.get_guild(guild_id)
		e = discord.Embed(color=colors.fate())
		e.set_author(name=f'Members in {guild}', icon_url=guild.icon_url)
		e.description = ''
		for member in guild.members:
			if member.id in [m.id for m in ctx.guild.members]:
				e.description += f'{member.mention}\n'
		await ctx.send(embed=e)

	@commands.command(name='mass-milk')
	@commands.check(slut)
	async def mass_milk(self, ctx, amount=25):
		if amount > 50:
			return await ctx.send('the fuck? you retard')
		async for msg in ctx.channel.history(limit=amount):
			if msg.id != ctx.message.id:
				await msg.add_reaction(self.bot.get_emoji(608070340924407823))
		await ctx.message.delete()

	@commands.command(name='create-color-roles')
	@commands.is_owner()
	async def create_color_roles(self, ctx):
		color_set = {
			'Blood Red': 0xff0000,
			'Orange': 0xff5b00,
			'Bright Yellow': 0xffff00,
			'Dark Yellow': 0xffd800,
			'Light Green': 0x00ff00,
			'Dark Green': 0x009200,
			'Light Blue': 0x00ffff,
			'Navy Blue': 0x0089ff,
			'Dark Blue': 0x0000ff,
			'Dark Purple': 0x9400d3,
			'Lavender': 0xb04eff,
			'Hot Pink': 0xf47fff,
			'Pink': 0xff9dd1,
			'Black': 0x030303,
		}
		for name, color in color_set.items():
			await ctx.guild.create_role(name=name, colour=discord.Color(color))
		await ctx.message.delete()

	@commands.command(name='luckynick')
	@commands.is_owner()
	async def luckynick(self, ctx, user, nick):
		if user.isdigit():
			user = ctx.guild.get_member(int(user))
			return await user.edit(nick=nick)
		user = ctx.message.mentions[0]
		await user.edit(nick=nick)

#	@commands.command(name='query')
#	async def query(self, ctx, address, port='19132'):
#		status = mc.ServerStatus(f'{address}:{port}')
#		response = "Players online: {0} \\ {1}\nMOTD: {2}\nVersion: {3}"
#		formatted_response = response.format(status.online_players, status.max_players, status.motd, status.version)
#		await ctx.send(formatted_response)

	@commands.command(name='makegay')
	@commands.is_owner()
	async def makegay(self, ctx):
		roles = [role for role in ctx.guild.roles if '=' not in role.name and not role.managed]
		roles.sort(reverse=True)
		index = zip(roles, colors.ColorSets().rainbow())
		old_colors = []
		for role, color in index:
			old_colors.append([role, role.color])
			await role.edit(color=discord.Color(color))
		await ctx.send('Done')
		await asyncio.sleep(20)
		for role, color in old_colors:
			await role.edit(color=discord.Color(int(str(color).replace('#', '0x'))))
		await ctx.send('Reverted roles')

	@commands.command(name='addimg')
	async def _addimg(self, ctx):
		msg = await ctx.channel.fetch_message(616037404263972865)
		embed = msg.embeds[0]
		embed.set_image(url='https://cdn.discordapp.com/attachments/536071529595666442/597597200570122250/20190609_024713.jpg')
		await msg.edit(embed=embed)
		await ctx.message.delete()

	@commands.command(name='get-average')
	async def get_average(self, ctx, user: discord.Member):
		im = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert('RGBA')
		pixels = list(im.getdata())
		r = g = b = c = 0
		for pixel in pixels:
			brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
			if pixel[3] > 64 and brightness > 100:
				r += pixel[0]
				g += pixel[1]
				b += pixel[2]
				c += 1
		r = r / c; g = g / c; b = b / c
		av = (round(r), round(g), round(b))
		card = Image.new('RGBA', (100, 100), color=av)
		card.save('color.png')
		await ctx.send('#%02x%02x%02x' % av,file=discord.File('color.png'))
		os.remove('color.png')

	@commands.command(name='grindlink')
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.guild_only()
	@commands.bot_has_permissions(create_instant_invite=True, manage_channels=True)
	@commands.is_owner()
	async def grind_link(self, ctx, option='selective'):
		await asyncio.sleep(0.5)
		await ctx.message.delete()
		found = False; index = 0
		while not found:
			if index == 100:
				return await ctx.send('Couldn\'t gen a good invite')
			await asyncio.sleep(1)
			invite = await ctx.channel.create_invite(reason='finding perfect invite', temporary=True)
			code = discord.utils.resolve_invite(invite.url)
			new = str(invite.code).lower()
			if "2b2t" in new or "polis" in new or "luck" in new:
				return await ctx.send(f'Made a good invite: {invite.url}')
			if 'upper' in option.lower():
				if invite.code != invite.code.upper():
					await invite.delete(reason='Bad Invite')
					await ctx.channel.send(f'Failure: {code}', delete_after=3)
					index += 1; continue
				return await ctx.send(f'Made a good invite: {invite.url}')
			if 'lower' in option.lower():
				if invite.code != invite.code.lower():
					await invite.delete(reason='Bad Invite')
					await ctx.channel.send(f'Failure: {code}', delete_after=3)
					index += 1; continue
				return await ctx.send(f'Made a good invite: {invite.url}')
			e = discord.Embed(color=colors.fate())
			e.description = invite.url
			msg = await ctx.send(embed=e)
			await msg.add_reaction('✔')
			await msg.add_reaction('❌')
			await msg.add_reaction('🛑')
			def check(reaction, user):
				return user == ctx.author and str(reaction.emoji) in ['✔', '❌', '🛑']
			try: reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except asyncio.TimeoutError: return await ctx.send('Timeout Error')
			reaction = str(reaction.emoji)
			if not reaction:
				return
			if reaction == '🛑':
				await ctx.send('oop', delete_after=3)
				await invite.delete()
				return await msg.delete()
			if reaction == '✔':
				await ctx.send(invite.url)
				return await msg.delete()
			else:
				await invite.delete()
				await msg.delete()
			index += 1

	@commands.command(name='getinvites')
	@commands.is_owner()
	async def get_invites(self, ctx, guild_id: int):
		guild = self.bot.get_guild(guild_id)
		invites = await guild.invites()
		await ctx.send(invites)

	@staticmethod
	def silence_check(ctx: commands.Context):
		return ctx.author.id in [
			config.owner_id(), 243233669148442624
		]

	@commands.command(name='silence')
	@commands.check(silence_check)
	async def silence(self, ctx):
		if self.silence == ctx.channel:
			self.silence = None
			return
		self.silence = ctx.channel
		await ctx.message.add_reaction('👍')

	@commands.command(name='type')
	@commands.is_owner()
	async def type(self, ctx, object, target_class):
		if isinstance(eval(object), eval(target_class)):
			await ctx.send('True')
		else:
			await ctx.send('False')

	# @commands.command(name='guildban', enabled=False)
	# @commands.is_owner()
	# async def guildban(self, ctx, guild_id: int, user_id: int, reason='Faggotry'):
	# 	guild = self.bot.get_guild(guild_id)
	# 	member = guild.get_member(user_id)
	# 	await guild.ban(member, reason=reason)
	# 	await ctx.send(f'Banned {member.name} from {guild.name}')

	# @commands.command(name="luckypurge")
	# @commands.cooldown(1, 5, commands.BucketType.channel)
	# @commands.is_owner()
	# async def _purge(self, ctx, amount: int):
	# 	await ctx.message.channel.purge(before=ctx.message, limit=amount)
	# 	await ctx.message.delete()
	# 	await ctx.send("{}, successfully purged {} messages".format(ctx.author.name, amount), delete_after=5)

	# @commands.command(name='readchannel')
	# @commands.is_owner()
	# async def readchannel(self, ctx, channel_id: int, amount: int):
	# 	channel = self.bot.get_channel(channel_id)
	# 	messages = ""
	# 	async for msg in channel.history(limit=amount):
	# 		messages = f"**{msg.author.name}:** {msg.content}\n{messages}"[:5800]
	# 	if channel.guild.icon_url:
	# 		image_url = channel.guild.icon_url
	# 	else:
	# 		image_url = self.bot.user.avatar_url
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_author(name=channel.guild.name, icon_url=image_url)
	# 	for group in [messages[i:i + 1000] for i in range(0, len(messages), 1000)]:
	# 		e.add_field(name=f"{channel.name}'s history", value=group, inline=False)
	# 	if len(messages) == 5800:
	# 		e.set_footer(text="Character Limit Reached")
	# 	await ctx.send(embed=e)

	@commands.command(name='resize')
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def resize(self, ctx, url=None):
		def resize(url):
			img = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
			img = img.resize((512, 512), Image.BICUBIC)
			img.save('resized.png')
		if url:
			resize(url)
		else:
			resize(ctx.message.attachments[0].url)
		await ctx.send(file=discord.File('resized.png'))
		os.remove('resized.png')

	# @commands.command(name="xinfo")
	# async def _info(self, ctx, user: discord.Member = None):
	# 	if user is None:
	# 		user = ctx.author
	# 	card = Image.open(BytesIO(requests.get(user.avatar_url).content)).convert("RGBA")
	# 	card = card.resize((1024, 1024), Image.BICUBIC)
	# 	draw = ImageDraw.Draw(card)
	# 	font = ImageFont.truetype("Modern_Sans_Light.otf", 75)  # Make sure you insert a valid font from your folder.
	# 	fontbig = ImageFont.truetype("Fitamint Script.ttf", 200)  # Make sure you insert a valid font from your folder.
	# 	#    (x,y)::↓ ↓ ↓ (text)::↓ ↓     (r,g,b)::↓ ↓ ↓
	# 	draw.text((10, 40), "Information:", (255, 255, 255), font=fontbig)
	# 	draw.text((10, 300), "Username: {}".format(user.name), (255, 255, 255), font=font)
	# 	draw.text((10, 400), "ID: {}".format(user.id), (255, 255, 255), font=font)
	# 	draw.text((10, 500), "Status: {}".format(user.status), (255, 255, 255), font=font)
	# 	draw.text((10, 600), "Created: {}".format(datetime.date(user.created_at).strftime("%m/%d/%Y")), (255, 255, 255), font=font)
	# 	draw.text((10, 700), "Nickname: {}".format(user.display_name), (255, 255, 255), font=font)
	# 	draw.text((10, 800), "Top Role: {}".format(user.top_role), (255, 255, 255), font=font)
	# 	draw.text((10, 900), "Joined: {}".format(datetime.date(user.joined_at).strftime("%m/%d/%Y")), (255, 255, 255), font=font)
	# 	card.save('yeet.png')  # Change infoimg2.png if needed.
	# 	await ctx.send(file=discord.File("yeet.png"))
	# 	os.remove('yeet.png')

	@commands.command(name='scrape-files')
	@commands.is_owner()
	async def scrape_images(self, ctx, *args):
		""" save image urls from channel history to a txt """
		kwargs = {key:literal_eval(value) for key, value in [a.split('=') for a in args]}
		amount = 1000 if 'amount' not in kwargs else kwargs['amount']
		lmt = kwargs['limit'] if 'limit' in kwargs else None
		embeds = kwargs['embeds'] if 'embeds' in kwargs else True
		ignored = []  # member id's to ignore
		targets = []  # only images from specific users
		if 'ignored' in kwargs:
			members = [utils.get_user(ctx, user) for user in kwargs['ignored']]
			ignored = [m.id for m in members if isinstance(m, discord.Member)]
		if 'targets' in kwargs:
			members = [utils.get_user(ctx, user) for user in kwargs['targets']]
			targets = [m.id for m in members if isinstance(m, discord.Member)]
		if 'filename' not in kwargs:
			return await ctx.send('You need to specify a filename')
		timeframe = None; after = None
		types = ['days', 'hours', 'minutes', 'seconds']
		if any(t in kwargs for t in types):
			timeframe = timedelta()
		if 'days' in kwargs:
			timeframe = timeframe + timedelta(days=kwargs['days'])
		if 'hours' in kwargs:
			timeframe = timeframe + timedelta(hours=kwargs['hours'])
		if 'minutes' in kwargs:
			timeframe = timeframe + timedelta(minutes=kwargs['minutes'])
		if 'seconds' in kwargs:
			timeframe = timeframe + timedelta(seconds=kwargs['seconds'])
		if timeframe:
			after = datetime.utcnow() - timeframe
		attachments = []  # type: [discord.Attachment,]
		index = 0  # amount of images added
		async for msg in ctx.channel.history(limit=lmt, after=after):
			if index == amount:
				break
			if msg.author.id not in ignored and msg.attachments:
				if (msg.embeds and embeds) or not msg.embeds:
					if targets and msg.author.id in targets or not targets:
						for attachment in msg.attachments:
							attachments.append(attachment.url)
							index += 1
		if 'extensions' in kwargs:
			attachments = [a for a in attachments if any(ext in a for ext in kwargs['extensions'])]
		path = os.path.join('./data/images/urls', kwargs['filename'])
		lines = []
		if isfile(path):
			with open(path, 'r') as f:
				lines = f.readlines()
		lines = [line for line in list({*lines, *attachments}) if len(line) > 5]
		with open(path, 'w') as f:
			f.write('\n'.join(lines) if len(lines) > 1 else lines[0])
		if 'return' in kwargs:
			if kwargs['return']:
				await ctx.send(file=discord.File(path))
			else:
				await ctx.send('👍')
		else:
			await ctx.send('👍')
		if 'delete_after' in kwargs:
			if kwargs['delete_after']:
				os.remove(path)

	@commands.command(name="scrapeimages")
	@commands.is_owner()
	async def _scrapeimages(self, ctx, filename, limit = 1000):
		if not isfile(f"./data/images/urls/{filename}"):
			with open(f"./data/images/urls/{filename}", "w") as f:
				image_urls = ""
				async for msg in ctx.channel.history(limit=limit):
					if msg.attachments:
						for attachment in msg.attachments:
							if not image_urls:
								image_urls += attachment.url
							else:
								image_urls += f"\n{attachment.url}"
				f.write(image_urls)
		else:
			f = open(f"./data/images/urls/{filename}", "r")
			urls = f.readlines()
			f.close()
			async for msg in ctx.channel.history(limit=limit):
				if msg.attachments:
					for attachment in msg.attachments:
						urls.append(f"{attachment.url}")
			clean_content = ""
			for url in urls:
				if url not in clean_content:
					clean_content += f"\n{url}"
			f = open(f"./data/images/urls/{filename}", "w")
			f.write(clean_content.replace("\n\n", "\n"))
			f.close()
		await ctx.send("Done")

	@commands.command()
	@commands.is_owner()
	async def sendfile(self, ctx, directory):
		if "fate/" in directory:
			directory = directory.replace("fate/", "/home/luck/FateZero/")
		await ctx.send(file=discord.File(directory))

	@commands.command(name='console', aliases=['c'])
	@commands.is_owner()
	async def console(self, ctx, *, command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = str(output if len(str(output)) > 0 else err).replace("\\t", "    ").replace("b'", "").split("\\n")
		msg = ""
		for i in output[:len(output) - 1]:
			msg += f"{i}\n"
		await ctx.send(f"```{msg[:1994]}```")

	@commands.command(name='logout')
	@commands.is_owner()
	async def logout(self, ctx):
		if ctx.author.id == 243233669148442624:
			return await ctx.send("Haha.. you thought you could log me out. I'm Invincible")
		await ctx.send('logging out')
		await self.bot.logout()

	@commands.command(name="error")
	@commands.is_owner()
	async def error(self, ctx):
		await ctx.send(f"```{self.bot.last_traceback}```")

	@commands.command(name='channel-send', aliases=['chs'])
	@commands.check(checks.luck)
	async def channel_send(self, ctx, channel: discord.TextChannel, *, content):
		try: await channel.send(content)
		except: return await ctx.send('I\'m missing permission', delete_after=3)
		finally: await ctx.message.delete()


	@commands.command(name='run')
	@commands.is_owner()
	async def run(self, ctx, *, args):
		try:
			if args == 'reload':
				self.bot.reload_extension('cogs.console')
				return await ctx.send('👍')
			if args.startswith('import') or args.startswith('from'):
				with open('./cogs/console.py', 'r') as f:
					imports, *code = f.read().split('# ~')
					imports += f'{args}\n'
					file = '# ~'.join([imports, *code])
					with open('./cogs/console.py', 'w') as wf:
						wf.write(file)
				self.bot.reload_extension('cogs.console')
				return await ctx.channel.send('👍')
			if 'await' in args:
				args = args.replace('await ', '')
				return await eval(args)
			if 'send' in args:
				args = args.replace('send ', '')
				return await ctx.send(eval(args))
			eval(args)
			await ctx.send('👍')
		except:
			error = str(traceback.format_exc()).replace('\\', '')
			await ctx.send(f'```css\n{discord.utils.escape_markdown(error)}```')

	@commands.command()
	async def ltr(self, ctx):
		await ctx.send(u"\u200E")

	@commands.command(name='print')
	@commands.is_owner()
	@commands.has_permissions(embed_links=True)
	async def print(self, ctx, *, arg):
		async with ctx.typing():
			print(f'{ctx.author.name}: {arg}')
			e=discord.Embed(color=colors.fate())
			e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			e.description = f'Printed `{arg}` to the console'
			await ctx.send(embed=e, delete_after=5)
			try: await ctx.message.delete()
			except: pass

	@commands.command(name="r")
	@commands.is_owner()
	async def repeat(self, ctx, *, arg):
		await ctx.send(arg)
		try: await ctx.message.delete()
		except: pass

	@commands.command(name='leave-server', aliases=['leave_guild'])
	@commands.is_owner()
	async def leave_guild(self, ctx, guild_id: int = None):
		if not guild_id:
			guild_id = ctx.guild.id
		guild = self.bot.get_guild(guild_id)
		await ctx.send(f'leaving {guild}')
		await guild.leave()
		try: await ctx.send(f'left {guild.name}')
		except: pass

	@commands.command()
	@commands.is_owner()
	async def twist(self, ctx, arg):
		async with ctx.typing():
			await ctx.message.delete()
			await ctx.send("Initiating dick twist ceremony")
			await asyncio.sleep(1)
			await ctx.send("*twists {}'s dick off*".format(arg))
			await asyncio.sleep(0.5)
			await ctx.send("*places {}'s dick inside of ceremonial chalice & grinds it up*".format(arg))
			await asyncio.sleep(0.5)
			await ctx.send("gives {} coffee in which his dick was the coffee grinds".format(arg))

	@commands.command()
	@commands.is_owner()
	async def edit(self, ctx, *, arg):
		async for msg in ctx.channel.history(limit=5):
			if msg.author.id == self.bot.user.id:
				await msg.edit(content=arg)
				return await ctx.message.delete()

	# @commands.command(name='luckydelete', aliases=['md'])
	# @commands.is_owner()
	# async def luckydelete(self, ctx):
	# 	async for msg in ctx.channel.history(limit=2):
	# 		if msg.id != ctx.message.id:
	# 			try: await msg.delete()
	# 			except: await ctx.send('Error', delete_after=2)
	# 			await ctx.message.delete()

	# @commands.command(name='luckykick')
	# @commands.is_owner()
	# @commands.cooldown(1, 25, commands.BucketType.user)
	# async def luckykick(self, ctx, user:discord.Member, *, reason:str=None):
	# 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# 		return await ctx.send('I can\'t kick that user ;-;')
	# 	await user.kick(reason=reason)
	# 	path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
	# 	e = discord.Embed(color=0x80b0ff)
	# 	e.set_image(url="attachment://" + os.path.basename(path))
	# 	file = discord.File(path, filename=os.path.basename(path))
	# 	await ctx.send(f'◈ {ctx.message.author.display_name} kicked {user} ◈', file=file, embed=e)
	# 	await ctx.message.delete()
	# 	try:await user.send(f"You have been kicked from **{ctx.guild.name}** by **{ctx.author.name}** for `{reason}`")
	# 	except: pass

	# @commands.command()
	# @commands.is_owner()
	# @commands.cooldown(1, 25, commands.BucketType.user)
	# async def luckyban(self, ctx, user:discord.Member, *, reason='unspecified reasons'):
	# 	if user.top_role.position >= ctx.guild.me.top_role.position:
	# 		return await ctx.send('I can\'t ban that user ;-;')
	# 	await ctx.guild.ban(user, reason=reason, delete_message_days=0)
	# 	path = os.getcwd() + "/data/images/reactions/beaned/" + random.choice(os.listdir(os.getcwd() + "/data/images/reactions/beaned/"))
	# 	e = discord.Embed(color=colors.fate())
	# 	e.set_image(url='attachment://' + os.path.basename(path))
	# 	file = discord.File(path, filename=os.path.basename(path))
	# 	await ctx.send(f'◈ {ctx.author.display_name} banned {user} ◈', file=file, embed=e)
	# 	try: await user.send(f'You\'ve been banned in **{ctx.guild.name}** by **{ctx.author.name}** for {reason}')
	# 	except: pass

	@commands.command()
	async def luckyspam(self, ctx, times: int, *, content='Format: .spam numberofmessages "content"'):
		if ctx.author.id not in self.bot.owner_ids:
			if ctx.author.id != 243233669148442624:
				return
		for i in range(times):
			await ctx.send(content)
			await asyncio.sleep(1)

	@commands.command()
	@commands.check(checks.luck)
	async def antitother(self, ctx, times: int):
		choices = [
			"Fagitos", "https://discord.gg/BQ23Z2E", "Reeeeeeeeeeeeeeeeeeeeeee",
			"pUrE wHiTe pRiVelIdgEd mALe", "there's a wasp sucking out all my stick juices",
			"Really? That's the sperm that won?", "May the fly be with you", "You're not you when you're hungry",
			"I recognize that flower, see you soon :)", "FBI OPEN UP", "Sponsored by Samsung", "iLiKe NuT",
			"Florin joins, Yall dislocate yo joints...", "old school tricks rise again", "i can't see, my thumbs are in the way",
			"All Heil nut", "SARGON NEED MORE DOPAMINE", ".prune 1000", "Nani",
			"I’m more blind then Hitler when he had that chlorine gas up in his eye",
			"real art^", "2b2t.org is a copy of the middle east", "warned for advertising", "jOiN sR",
			"6 million juice", "The 7th SR Fag", "7th team lgbt", "DAiLy reMinDer sEx RoboTs coSt lesS thAn ReAl gRilLs",
			"elon's musk", "Fuck the battle cat", "9/11", 'is it bad language or bad code', 'clonk gay',
			'i have social diabetes', 'https://cdn.discordapp.com/attachments/457322344818409482/531321000361721856/image0-1.jpg',
			'Tother: Sharon', "we're giving them what they want, if they wanna identify as a peice of coal we can burn them freely",
			f"You've been muted for spam in {ctx.guild.name} for 2 minutes and 30 seconds"
		]
		for i in range(times):
			await ctx.send(random.choice(choices))

	@commands.Cog.listener()
	async def on_message(self, m: discord.Message):
		if isinstance(m.guild, discord.Guild):
			if m.channel == self.silence:
				return await m.delete()
			if m.content.lower().startswith("pls magik <@264838866480005122>"):
				def pred(m):
					return m.author.id == 270904126974590976 and m.channel == m.channel
				try:
					msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
				except asyncio.TimeoutError:
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
				else:
					await asyncio.sleep(0.5)
					await msg.delete()
					await m.channel.send("next time i ban you")
			commands = ["t!avatar <@264838866480005122>", ".avatar <@264838866480005122>",
			            "./avatar <@264838866480005122>", "t.avatar <@264838866480005122>"]
			bots = [506735111543193601, 418412306981191680, 172002275412279296, 452289354296197120]
			if m.content.lower() in commands:
				def pred(m):
					return m.author.id in bots and m.channel == m.channel

				try:
					msg = await self.bot.wait_for('message', check=pred, timeout=10.0)
				except asyncio.TimeoutError:
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
					await asyncio.sleep(10)
					async for i in m.channel.history(limit=10):
						await i.delete()
				else:
					await asyncio.sleep(0.5)
					await msg.delete()
					await m.channel.send("next time i ban you")


def setup(bot):
	bot.add_cog(Dev(bot))
