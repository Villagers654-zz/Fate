import datetime

class utc:
	def __init__(self, seconds=None):
		self.seconds = seconds

	def now(self):
		return datetime.datetime.utcnow()

	def future(self):
		return datetime.datetime.utcnow() + datetime.timedelta(seconds=self.seconds)

	def past(self):
		return datetime.datetime.utcnow() - datetime.timedelta(seconds=self.seconds)
