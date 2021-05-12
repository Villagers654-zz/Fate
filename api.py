from aiohttp import web, ClientSession
import asyncio

from discord.ext import commands
import discord

from classes.exceptions import aiohttp as errors


clients = {}
API_ENDPOINT = 'https://discord.com/api/v8'
CLIENT_ID = '506735111543193601'
CLIENT_SECRET = '67_VttLomTPv55ialTsaCPEySX1l7Vm_'
REDIRECT_URI = 'http://fatebot.xyz/success'
scope = "https://discord.com/api/oauth2/authorize?client_id=506735111543193601&redirect_uri=http%3A%2F%2Ffatebot.xyz%2Fsuccess&response_type=code&scope=identify"

async def exchange_code(code):
  data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': REDIRECT_URI
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  async with ClientSession() as session:
      url = "https://discord.com/api/v8/oauth2/token"
      async with session.post(url, data=data, headers=headers) as resp:
          return await resp.json()


# header = {"Authorization": "Bearer " + dat["access_token"]}
# r = requests.get(f"https://discord.com/api/users/@me", headers=header)
# r.raise_for_status()
# print(r.json())



class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        self.app = web.Application()
        self.app.router.add_get("/user/{tail:[0-9]*}", self.user_info)
        self.app.router.add_get("/guild", self.guild_info)
        self.app.router.add_get("/ranks", self.ranks)
        self.app.router.add_get("/success{tail:.*}", self.get_user)
        self.api_is_running = False
        self.secret = "1234"
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            **kwargs
        )

    async def get_user(self, request):
        code = request.rel_url.query["code"]
        if code in clients:
            return web.json_response(clients[code])
        auth = await exchange_code(code)
        if "access_token" not in auth:
            raise web.HTTPFound(location=scope)
        headers = {"Authorization": "Bearer " + auth["access_token"]}
        async with ClientSession() as session:
            url = "https://discord.com/api/users/@me"
            async with session.get(url, headers=headers) as resp:
                info = await resp.json()
        if not info:
            return web.Response(text="Invalid access token", status=404)
        clients[code] = info
        return web.json_response(info)

    async def on_ready(self):
        """Initialize the API if not running"""
        print(f"Logged in as {bot.user}")
        if not self.api_is_running:
            self.api_is_running = True
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, port=80)
            await site.start()

    async def authenticate(self, request):
        """Ensure the request is legit"""
        if not request.content_length:
            return errors.invalid_data
        if request.content_length > 8000:
            return web.Response(text="Request entity too large", status=404)
        data = await request.json()
        if not data or "auth" not in data:
            return errors.invalid_data
        if data["auth"] != self.secret:
            return errors.invalid_login
        return data

    async def guild_info(self, request):
        """Handler for getting guild info via ID"""
        data = await self.authenticate(request)
        if not isinstance(data, dict):
            return data
        required = ("guild_id", "user_id")
        if any(key not in data for key in required):
            return errors.invalid_data

        resp = {"status": "success", "data": None}
        guild = self.get_guild(data["guild_id"])

        if not guild:
            resp["status"] = f"Server not found"
            return web.json_response(resp, status=404)
        user = guild.get_member(data["user_id"])
        if not user:
            resp["status"] = "User isn't in server"
            return web.json_response(resp, status=404)

        resp["data"] = {
            "name": guild.name,
            "icon_url": str(guild.icon_url),
            "splash_url": str(guild.splash_url),
            "banner_url": str(guild.banner_url),
            "user_guild_permissions": list(user.guild_permissions),
            "bot_guild_permissions": list(guild.me.guild_permissions),
            "channels": {}
        }
        for channel in guild.text_channels:
            await asyncio.sleep(0)
            resp["data"]["channels"][channel.id] = {
                "name": channel.name,
                "user_permissions": list(channel.permissions_for(user)),
                "bot_permissions": list(channel.permissions_for(guild.me))
            }

        return web.json_response(resp)

    async def user_info(self, request):
        """Handler for getting user info via ID"""
        data = await self.authenticate(request)
        if not isinstance(data, dict):
            return data

        # Extract the user_id
        paths = request.path.lstrip("/").split("/")
        _root, _user_id = paths

        return web.json_response({})

    async def ranks(self, request):
        pass


bot = Bot()
bot.run("NTExMTQxMzM1ODY1MjI5MzMz.W-gTdw.7XvdSnq6nwgdZQM5vzwhs3RABOc")
