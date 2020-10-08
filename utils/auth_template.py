# Rename this file to outh.py in order for it to be functional

# noinspection SpellCheckingInspection
class MySQL:
    def __init__(self):
        self.host = "localhost"
        self.port = 3306  # int
        self.user = "root"
        self.password = "Eppy"
        self.db = ""


class Reddit:
    def __init__(self):
        self.client_id = ""
        self.client_secret = ("",)
        self.user_agent = ""


def reddit():
    return {"client_id": "", "client_secret": "", "user_agent": ""}


def tokens(token):
    if token == "fatezero":
        return "nO"
    if token == "4b4t":
        return "really? nO"
