"""
Module Dedicated to a Private Server
- Management / House Keeping
- Reddit Posts on a loop
"""

import asyncio

from discord.ext import commands
import discord
from praw import Reddit

from utils import colors, outh


class MHA(commands.Cog):
	def __init__(self, bot):
		self.bot = bot


	async def reddit_task(self):
		""" Sends a reddit post every x seconds """

		channel_id = 643250114974056477
		interval = 60 * 5  # 5 minutes
		subreddit = 'BokuNoHeroAcademia'
		credentials = outh.reddit()  # type: dict
		reddit = Reddit(
			client_id=credentials['client_id'],
			client_secret=credentials['client_secret'],
			user_agent=credentials['user_agent']
		)

		while True:
			for submission in reddit.subreddit(subreddit).hot(limit=1000):
				extensions = ['.png', '.jpg', '.jpeg', '.webp', 'gif']
				if any(ext in submission.url for ext in extensions):
					e = discord.Embed(color=colors.red())
					e.set_author(name=submission.title, icon_url=submission.author.icon_img)
					e.set_image(url=submission.url)
					e.set_footer(text=f'{submission.author.name} | 👍 {submission.score} | 💬 {submission.num_comments}')
					await self.bot.get_channel(channel_id).send(embed=e)
					await asyncio.sleep(interval)


	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.reddit_task())


def setup(bot):
	bot.add_cog(MHA(bot))
