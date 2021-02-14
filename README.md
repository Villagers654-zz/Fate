# Fate
![black](https://img.shields.io/badge/code%20style-black-black) ![black](https://img.shields.io/badge/version-1.0.0-green)

A multipurpose discord bot

<a href="https://top.gg/bot/506735111543193601">
    <img src="https://top.gg/api/widget/506735111543193601.svg" alt="Fate" />
</a>

## Getting Started
### Compatibility
Python 3.8 or higher due to required asyncio features
### Installing
> Clone the Project
```
git clone https://github.com/FrequencyX4/Fate.git
```
> Prerequisites
```py
pip install -r requirements.txt
```
> Music
- Download  the LavaLink server from https://github.com/Devoxin/Lavalink.py
- Configure the Lavalink server with the default config   
If not be sure to adjust the connection settings in [`cogs/music.py`](https://github.com/FrequencyX4/Fate/blob/master/cogs/music.py)
### Initial Setup
-  You can configure things like the debug channel, command prefix, and personalization in [`data/config.json`](https://github.com/FrequencyX4/Fate/blob/master/data/config.json)
###  Configuring - this is more compicated but is required for making the bot work!
- create `./data/xp.json`
- edit `./data/config.json` to your hearts content
- create `./utils/auth.py` from `./utils/auth_template.py`
- edit `./data/userdata/config.json`
### Running
```py
python fate.py
```
## License
This project is licensed for private, confidential, and only authorized use - see [`LICENSE`](https://github.com/FrequencyX4/Fate/blob/master/LICENSE) file for details
## Acknowledgments
- [CortexPE - Python Teacher](https://github.com/CortexPE)
- [Lavalink - For Music Support](https://github.com/Devoxin/Lavalink.py)
- [2B2T Stats & Information](https://2b2t.dev/)
- [vzhou842 - ](https://github.com/vzhou842) [Profanity Filter](https://github.com/vzhou842/profanity-check)
