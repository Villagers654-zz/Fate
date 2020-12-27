from cryptography.fernet import Fernet
from getpass import getpass

# noinspection SpellCheckingInspection
class MySQL:
	def __init__(self):
		self.host = 'localhost'
		self.port = 3306
		self.user = '*'
		self.password = '*'
		self.db = '*'


class Reddit:
	def __init__(self):
		self.client_id = '*'
		self.client_secret = '*'
		self.user_agent = '*'


class Backups:
	def __init__(self):
		self.host = "*"
		self.port = 22
		self.password = "*"
		self.username = "*"


class Lavalink:
	def __init__(self):
		self.password = "*"
		self.ws_port = 2333
		self.rest_port = 2333


class Tokens:
	def __init__(self):
		self.tokens = {
			"fate": b"token goes here",
			"other_bot": b"token goes here"
		}

	def decrypt(self, token_id) -> str:
		if token_id not in self.tokens:
			raise KeyError(f"{token_id} doesn't exist in {list(self.tokens.keys())}")
		cipher = Fernet(getpass().encode())
		return cipher.decrypt(self.tokens[token_id]).decode()

