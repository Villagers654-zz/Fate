#!/bin/dash
echo "Installing python3"
apt install python3
echo "Installing pip3"
apt install python3-pip
echo "Installing git"
apt install git
echo "Installing discord.py rewrite"
pip3 install git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
echo "Installing Modules"
pip3 install aiohttp
pip3 install psutil
pip3 install youtube_dl
pip3 install ffmpeg
pip3 install requests
pip3 install termcolor
pip3 install bs4
pip3 install wikipedia
echo "Setup Complete"
