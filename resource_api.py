import nest_asyncio
nest_asyncio.apply()

from aiohttp import web
from time import time
import os
import ssl

import aiofiles


class ResourcesAPI:
    def __init__(self):
        self.cd = {}

        self.app = web.Application()
        self.app.router.add_get("/{tail:.*}", self.get_resource)
        self.app.router.add_get('/reactions/{tail:.*/[a-zA-Z0-9]*\\....}', self.get_resource)

    def run(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.load_cert_chain("cert")
        web.run_app(self.app, ssl_context=ssl_context)

    def is_on_cooldown(self, ip) -> bool:
        now = int(time() / 25)
        if ip not in self.cd:
            self.cd[ip] = [now, 0]
        if self.cd[ip][0] == now:
            self.cd[ip][1] += 1
        else:
            self.cd[ip] = [now, 0]
        if self.cd[ip][1] > 3:
            return True
        return False

    async def get_resource(self, request):
        """Handler for streaming reaction GIFs"""
        if self.is_on_cooldown(request.remote):
            return web.Response(text="You are being rate-limited", status=404)

        # Ensure the file exists
        path = request.path
        if path.startswith("/reactions"):
            fp = f"./data/images/reactions/{path.lstrip('/reactions')}"
        else:
            fp = f"./assets/{path.lstrip('/assets')}"
        if os.path.isdir(fp) or not os.path.exists(fp):
            return web.HTTPNotFound()
        print(f"Received a request for {request.path}")

        # Stream the gif
        async with aiofiles.open(fp, "rb") as f:
            file = await f.read()
        resp = web.StreamResponse()
        ext = fp[-(len(fp) - fp.rfind(".")):].lstrip(".")
        resp.headers["Content-Type"] = f"Image/{ext.upper()}"
        resp.headers["Content-Disposition"] = f"filename='file.{ext}';"
        await resp.prepare(request)
        await resp.write(file)
        await resp.write_eof()


app = ResourcesAPI()
app.run()
