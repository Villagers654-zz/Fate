from discord.ext import commands
from os.path import isfile
import json

class Mute:
	def __init__(self, bot):
		self.bot = bot
		self.xp = {}
		self.xp_path = './data/xp.json'
		if isfile(self.xp_path):
			with open(self.xp_path, 'r') as f:
				dat = json.load(f)
				if 'stuff' in dat:
					self.xp = dat['stuff']
		self.bio = {}
		self.path = './data/profiles.json'
		if isfile(self.path):
			with open(self.path, 'r') as f:
				dat = json.load(f)
				if 'bio' in dat:
					self.bio = dat['bio']

	def save_xp(self):
		with open(self.xp_path, 'w') as f:
			json.dump(self.xp, f, ensure_ascii=False)

	def save_profiles(self):
		with open(self.path, 'w') as f:
			json.dump({'bio': self.bio}, f, ensure_ascii=False)

def setup(bot):
	bot.add_cog(Mute(bot))
