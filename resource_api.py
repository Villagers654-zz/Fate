import nest_asyncio
nest_asyncio.apply()

from aiohttp import web
from time import time
import os

import aiofiles


cd = {}


async def check_rate_limit(request):
    ip = request.remote
    now = int(time() / 25)
    if ip not in cd:
        cd[ip] = [now, 0]
    if cd[ip][0] == now:
        cd[ip][1] += 1
    else:
        cd[ip] = [now, 0]
    if cd[ip][1] > 2:
        return True
    return False


async def get_resource(request):
    """Handler for streaming reaction GIFs"""
    ip = request.remote
    now = int(time() / 25)
    if ip not in cd:
        cd[ip] = [now, 0]
    if cd[ip][0] == now:
        cd[ip][1] += 1
    else:
        cd[ip] = [now, 0]
    if cd[ip][1] > 3:
        return web.Response(text="You are being rate-limited", status=404)

    # Ensure the file exists
    path = request.path
    if path.startswith("/reactions"):
        fp = f"./data/images/reactions/{path.lstrip('/reactions')}"
    else:
        fp = f"./assets/{path.lstrip('/assets')}"
    if not os.path.exists(fp):
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


app = web.Application()
app.router.add_get("/{tail:.*}", get_resource)
app.router.add_get('/reactions/{tail:.*/[a-zA-Z0-9]*\\....}', get_resource)


web.run_app(app, port=80)
