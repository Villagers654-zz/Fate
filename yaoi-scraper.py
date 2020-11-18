import sys
import requests
from praw import Reddit

main_path = sys.argv[0]
args = sys.argv[1:]  # type: list

from utils import auth
creds = auth.Reddit()
client = Reddit(
    client_id=creds.client_id,
    client_secret=creds.client_secret,
    user_agent=creds.user_agent
)

limit = 100
for arg in args:
    if arg.isdigit():
        limit = int(arg)
exts = [".png", ".jpg", ".jpeg", ".gif"]

posts = []
for submission in client.subreddit("yaoi").hot(limit=limit):
    for ext in exts:
        if ext in submission.url:
            posts.append([submission.url, ext])
            break

for i, (post_url, ext) in enumerate(posts):
    raw_data = requests.get(post_url).content
    fp = f"yaoi-{i + 1}.{ext}"
    with open(fp, "wb") as f:
        f.write(raw_data)
    print(f"Downloaded {fp}")

print(f"Downloaded {len(posts)} images of yaoi")
