import asyncio
import random
import traceback
import discord


class Tasks:
	def __init__(self, bot):
		self.bot = bot
		self.enabled_tasks = [self.status_task, self.debug_log]
		self.running = []

	def running_tasks(self):
		return [
			task for task in asyncio.all_tasks(self.bot.loop) if not task.done() and not task.cancelled()
		]

	def running_task_names(self):
		return sorted([task.get_name() for task in self.running_tasks()])

	def ensure_all(self):
		"""Start any core tasks that aren't running"""
		for coro in self.enabled_tasks:
			if coro.__name__ not in [task.get_name() for task in self.running_tasks()]:
				new_task = self.bot.loop.create_task(coro())
				new_task.set_name(coro.__name__)
				print(f'Started task {new_task.get_name()}')

	def start(self, coro, *args, **kwargs):
		"""Start a task without fear of duplicates"""
		if 'task_id' in kwargs:
			task_id = kwargs['task_id']  # type: str
			del kwargs['task_id']
		else:
			task_id = coro.__name__

		if task_id in self.running_task_names():
			return None

		new_task = self.bot.loop.create_task(coro(*args, **kwargs))
		new_task.set_name(task_id)
		print(f'Started task {task_id}')
		return new_task

	def cancel(self, task_name):
		"""Cancel a running task - doesn't work"""
		for task in asyncio.all_tasks(self.bot.loop):
			if task.get_name() == task_name:
				task.cancel()
				print(f'Cancelled {task.get_name()} - {task.cancelled()}')

	async def status_task(self):
		while True:
			motds = [
				'FBI OPEN UP', 'YEET to DELETE', 'Pole-Man', '♡Juice wrld♡', 'Mad cuz Bad', 'Quest for Cake',
				'Gone Sexual',
				'@EPFFORCE#1337 wuz here'
			]
			stages = ['Serendipity', 'Euphoria', 'Singularity', 'Epiphany']
			for i in range(len(stages)):
				try:
					await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'Seeking For The Clock'))
					await asyncio.sleep(45)
					await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'{stages[i]} | use .help'))
					await asyncio.sleep(15)
					await self.bot.change_presence(status=discord.Status.idle, activity=discord.Game(name=f'SVR: {len(self.bot.guilds)} USR: {len(self.bot.users)}'))
					await asyncio.sleep(15)
					await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=f'{stages[i]} | {random.choice(motds)}'))
				except (discord.errors.Forbidden, discord.errors.HTTPException):
					print(f'Error changing my status:\n{traceback.format_exc()}')
				await asyncio.sleep(15)

	async def debug_log(self):
		channel = self.bot.get_channel(675878044824764456)
		log = []
		reads = 0
		while True:
			reads += 1
			with open('discord.log', 'r') as f:
				lines = f.readlines()
			new_lines = len(lines) - len(log)
			if new_lines > 0:
				added_lines = lines[-new_lines:]
				msg = ''.join(added_lines)
				char = u"\u0000"
				for group in [msg[i:i + 1990] for i in range(0, len(msg), 1990)]:
					group = group.replace(char, "")
					if group:
						await channel.send(f'```{group}```')
				log = [*log, *added_lines]
			if reads == 1000:
				with open('discord.log', 'w') as f:
					f.write('')
				log = []
				reads = 0
			await asyncio.sleep(1)
