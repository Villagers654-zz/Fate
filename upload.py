from datetime import datetime
import pysftp as sftp

print("What Cog?")
cog = input()
start = datetime.now()
s = sftp.Connection(host="85.235.66.51", port=7822, username="root", password="lsimhbiwfefmtalol")
s.put(f"./cogs/{cog}.py", f"/home/luck/FateZero/cogs/{cog}.py")
time_elapsed = (datetime.now() - start).seconds
print(f"Upload took {time_elapsed} seconds")
