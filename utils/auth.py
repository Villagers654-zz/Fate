from cryptography.fernet import Fernet
from getpass import getpass

# noinspection SpellCheckingInspection
class MySQL:
	def __init__(self):
		self.host = 'localhost'
		self.port = 3306
		self.user = 'fate'
		self.password = 'EnUzAs9Q'
		self.db = 'fate'


class Reddit:
	def __init__(self):
		self.client_id = '9hu5by5j_i0FJA'
		self.client_secret = 'Oi9BTr4OZ9hVBDRXgvRonsw4Pf4'
		self.user_agent = 'ubuntu20.04:Fate:1.5.0 (by /u/FrequencyX4)'  # gotta use symantic versioning lmfao


class Backups:
	def __init__(self):
		self.host = "server.epfforce.systems"
		self.port = 2202
		self.password = "Luckofdespair1!"
		self.username = "luck" # lmao


class Lavalink:
	def __init__(self):
		self.password = "wqSLe6Aw"
		self.ws_port = 2333
		self.rest_port = 2333


class Tokens:
	def __init__(self):
		self.tokens = {
			"fate": b"gAAAAABfWsZNdiH6wDwPAQ3n2jTNL1zugFGfqDT-MlwE4UyCw0il15rw6PDvP-Vw4zZ-crCrG2mpRDjO75nExuZ1qmFT51Duh"
			        b"8kNezXA67AjM_Q2QG_nv9kuSSRg-ttf7vk2TcQlXmQUCh7L-4D-jyfT_fS_I7o7IA==",
			"beta": b"gAAAAABfWvpiSmjKEUqL-Fr2VODCkD0V6qy-H8bTlWZW_Gh7BXWNXJ4l-2P6QwPi5rl3JQFVmkVwnrtZ2W01EVUJooOQV497W"
			        b"SY9A3wF2zQUqp6k2E1CbjTzuZfADJO1kSDfmPLVBuvRPn5-Ziiy-bxbaOv7Nj-KNw=="
		}

	def decrypt(self, token_id) -> str:
		if token_id not in self.tokens:
			raise KeyError(f"{token_id} doesn't exist in {list(self.tokens.keys())}")
		cipher = Fernet(getpass().encode())
		return cipher.decrypt(self.tokens[token_id]).decode()

