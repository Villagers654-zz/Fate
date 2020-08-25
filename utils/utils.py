from datetime import datetime, timedelta
import asyncio
import time
import json
import subprocess
import os
import re
import aiofiles
import discord


class AsyncFileManager:
	def __init__(self, file: str, mode: str = "r", lock: asyncio.Lock = None):
		self.file = file
		self.temp_file = file
		if "w" in mode:
			self.temp_file += ".tmp"
		self.mode = mode
		self.fp_manager = None
		self.lock = lock

	async def __aenter__(self):
		if self.lock:
			await self.lock.acquire()
		self.fp_manager = await aiofiles.open(file=self.temp_file, mode=self.mode)
		return self.fp_manager

	async def __aexit__(self, _exc_type, _exc_value, _exc_traceback):
		await self.fp_manager.close()
		if self.file != self.temp_file:
			os.rename(self.temp_file, self.file)
		if self.lock:
			self.lock.release()


class Result:
	def __init__(self, result, errored=False, traceback=None):
		self.result = result
		self.errored = errored
		self.traceback = traceback


class Filter:
	def __init__(self):
		self._blacklist = []
		self.index = {
			"a": ['@', '4'], "b": [], "c": [], "d": [], "e": ['3'],
			"f": [], "g": [], "h": [], "i": ['!', '1'], "j": [],
			"k": [], "l": [], "m": [], "n": [], "o": ["0", "\\(\\)", "\\[\\]"],
			"p": [], "q": [], "r": [], "s": ['$'], "t": [],
			"u": [], "v": [], "w": [], "x": [], "y": [],
			"z": [], "0": [], "1": [], "2": [], "3": [],
			"4": [], "5": [], "6": [], "7": [], "8": [],
			"9": []
		}

	@property
	def blacklist(self):
		return self._blacklist

	@blacklist.setter
	def blacklist(self, value: list):
		self._blacklist = [item.lower() for item in value]

	def __call__(self, message: str):
		for phrase in self.blacklist:
			if len(phrase) > 3:
				message=message.replace(' ', '')
			chunks = str(message).replace(' ', '').lower().split()
			if phrase in chunks:
				return True, phrase
			if not len(list(filter(lambda char: char in message, list(phrase)))) > 1:
				continue
			pattern = ""
			for char in phrase:
				if char in self.index and self.index[char]:
					main_char = char if char in self.index.keys() else f"\\{char}"
					singles = [c for c in self.index[char] if len(c) == 1]
					multi = [c for c in self.index[char] if len(c) > 1]
					pattern += f"([{main_char}{''.join(f'{c}' for c in singles)}]"
					if singles and multi:
						pattern += "|"
					if multi:
						pattern += "|".join(f"({c})" for c in multi)
					pattern += ")"
				else:
					pattern += char
				pattern += "+"
			print(pattern)
			if re.search(pattern, message):
				return True, pattern  # Flagged

			#if len(message) > 3 and len(phrase) > 3:
				#if phrase == "inane":
					#print("going into special for inane")
				#sections = []
				#tmp_pattern = str(pattern)
				#matches = re.findall(r"\[.*]", tmp_pattern)
				#if matches:
					#for match in matches:
						#sections.append(match)
						#tmp_pattern.replace(match, "")
				#for char in tmp_pattern:
					#sections.append(char)

				#for section in sections:
					#chars = list(pattern)
					#index = pattern.index(section)
					#left_index = index - 1 if index else index
					#right_index = index + 1 if index < len(chars) - 1 else len(chars) - 1
					#if '.' != chars[left_index] and '.' != chars[right_index] and chars[index] != '.':
						#replaced = str(pattern).replace(section, f"{chars[index]}*")
						#if re.search(replaced, message):
							#return True, replaced

					# for s in [s for s in sections if s != section and s != "."]:
					# 	if re.search(str(replaced).replace(s, ".*"), message):
					# 		print("Double replaced pattern: " + str(replaced).replace(s, ".*"))
					# 		print(f"{phrase} was flagged in {message} with 2 chars removed")
					# 		return True

		return False, None

class MemoryInfo:
	@staticmethod
	async def __coro_fetch(interval=0):
		p = subprocess.Popen(f'python3 memory_info.py {os.getpid()} {interval}', stdout=subprocess.PIPE, shell=True)
		await asyncio.sleep(1)
		(output, err) = p.communicate()
		output = output.decode()
		return json.loads(output)

	@staticmethod
	def __fetch(interval=1):
		p = subprocess.Popen(f'python3 memory_info.py {os.getpid()} {interval}', stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		output = output.decode()
		return json.loads(output)

	@staticmethod
	async def full(interval=1):
		return await MemoryInfo.__coro_fetch(interval)

	@staticmethod
	async def cpu(interval=1):
		mem = await MemoryInfo.__coro_fetch(interval)
		return mem['PID']['CPU']

	@staticmethod
	def ram(interval=0):
		return MemoryInfo.__fetch(interval)['PID']['RAM']['RSS']

	@staticmethod
	async def cpu_info(interval=1):
		mem = await MemoryInfo.__coro_fetch(interval)
		return {'global': mem['GLOBAL']['CPU'], 'bot': mem['PID']['CPU']}

	@staticmethod
	def global_cpu(interval=1):
		return MemoryInfo.__fetch(interval)['GLOBAL']['CPU']

	@staticmethod
	def global_ram(interval=0):
		return MemoryInfo.__fetch()['GLOBAL']['RAM']['USED']


class Bot:
	def __init__(self, bot):
		self.bot = bot
		self.dir = './data/stats.json'

	async def wait_for_msg(self, ctx):
		def pred(m):
			return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
		try:
			msg = await self.bot.wait_for('message', check=pred, timeout=60)
		except asyncio.TimeoutError:
			await ctx.send("Timeout error")
			return False
		else:
			return msg


class User:
	def __init__(self, user: discord.User):
		self.user = user

	async def init(self):
		dm_channel = self.user.dm_channel
		if not dm_channel:
			await self.user.create_dm()

	def can_dm(self):
		return self.user.dm_channel.permissions_for(self).send_messages


class Datetime:
	def __init__(self, seconds):
		self.seconds = seconds

	def future(self):
		return datetime.utcnow() + timedelta(seconds=self.seconds)

	def past(self):
		return datetime.utcnow() - timedelta(seconds=self.seconds)


class Time:
	def __init__(self, seconds):
		self.seconds = seconds

	def future(self):
		return time.time() + self.seconds

	def past(self):
		return time.time() - self.seconds
