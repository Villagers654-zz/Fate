from datetime import datetime
import pysftp as sftp
import subprocess
import os

print("What's the name of your user?")
user = input()
print("What's the name of your servers folder?")
dir = input()
print("Checking For Previous Backup")
p = subprocess.Popen(f"ls /home/{user}", stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
if "Backup.zip" in str(output):
	os.system(f"rm /home/{user}/Backup.zip")
print("Compressing files")
start = datetime.now()
os.system(f"zip -r /home/{user}/Backup.zip /home/{user}/{dir}")
time_elapsed = (datetime.now() - start).seconds
print(f"Compression took {time_elapsed} seconds")
print("Transferring Files")
start = datetime.now()
s = sftp.Connection(host="207.180.236.237", username="tother", password="tothy162")
s.put(f"/home/{user}/Backup.zip", "/home/tother/Backup.zip")
s.close()
time_elapsed = (datetime.now() - start).seconds
print(f"Transfer took {time_elapsed} seconds")
print("Backup Complete")
