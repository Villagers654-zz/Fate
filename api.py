"""
Discord OAuth2 API
~~~~~~~~~~~~~~~~~~~

A basic representation of how to use discords OAuth2

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from aiohttp import web, ClientSession
import asyncio
from time import time
from urllib.parse import unquote

from discord.ext import commands
import discord
import jwt

from classes.exceptions import aiohttp as errors


clients = {}
API_ENDPOINT = 'https://discord.com/api/v8'
CLIENT_ID = '506735111543193601'
CLIENT_SECRET = '67_VttLomTPv55ialTsaCPEySX1l7Vm_'
REDIRECT_URI = 'http://fatebot.xyz/success'
scope = "https://discord.com/api/oauth2/authorize?client_id=506735111543193601&redirect_uri=http%3A%2F%2Ffatebot.xyz%2Fsuccess&response_type=code&scope=identify"


class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        self.app = web.Application()
        self.app.router.add_get("/user", self.user_info)
        self.app.router.add_get("/ranks", self.ranks)
        self.app.router.add_get("/success", self.authenticate)
        self.app.router.add_get("/dash", self.fake_dash)
        self.api_is_running = False
        self.secret = "1234"
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            **kwargs
        )

    async def fake_dash(self, request):
        params = request.rel_url.query
        if "token" not in params:
            return errors.invalid_data
        token = unquote(params["token"]).lstrip("b'").rstrip("'")
        try:
            data = jwt.decode(token, "1234")
        except jwt.exceptions.DecodeError:
            return errors.invalid_data
        user_id = data["user_id"]
        return web.Response(text=f"Welcome {self.get_user(user_id)}")

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
        params = request.rel_url.query
        if "code" not in params:
            return errors.invalid_data
        code = params["code"]
        if code in clients:
            return web.json_response(clients[code])

        # Get the users oauth2 access_code
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
                auth = await resp.json()

        # Get the users information
        if "access_token" not in auth:
            raise web.HTTPFound(location=scope)
        headers = {"Authorization": "Bearer " + auth["access_token"]}
        async with ClientSession() as session:
            url = "https://discord.com/api/users/@me"
            async with session.get(url, headers=headers) as resp:
                info = await resp.json()
        if not info:
            return web.Response(text="Invalid access token", status=404)

        # Encode the user info with jwt
        info["id"] = int(info["id"])
        data = {
            "user_id": info["id"],
            "expires": time() + 3600 * 24
        }
        token = jwt.encode(data, "1234")

        # Redirect to dash
        dash = f"http://fatebot.xyz/dash?token={token}"
        raise web.HTTPFound(location=dash)

    async def get_guild_info(self, user_id: int):
        guilds = []
        for guild in self.guilds:
            await asyncio.sleep(0)
            if user_id in [m.id for m in guild.members]:
                guilds.append(guild)
        resp = {}

        for guild in guilds:
            await asyncio.sleep(0)
            member = guild.get_member(int(user_id))
            if not member:
                continue
            resp[guild.id] = {
                "name": guild.name,
                "icon_url": str(guild.icon.url),
                "splash_url": str(guild.splash.url),
                "banner_url": str(guild.banner.url),
                "user_guild_permissions": list(member.guild_permissions),
                "bot_guild_permissions": list(guild.me.guild_permissions),
                "channels": {}
            }
            for channel in guild.text_channels:
                await asyncio.sleep(0)
                resp[guild.id]["channels"][channel.id] = {
                    "name": channel.name,
                    "user_permissions": list(channel.permissions_for(member)),
                    "bot_permissions": list(channel.permissions_for(guild.me))
                }

        return resp

    async def user_info(self, request):
        """Handler for getting user info via ID"""
        params = request.rel_url.query
        if "token" not in params:
            return errors.invalid_data
        token = params["token"]
        data = jwt.decode(token, "1234")
        resp = await self.get_guild_info(data["user_id"])
        return web.json_response(resp)

    async def ranks(self, request):
        pass


bot = Bot()
bot.run("")
