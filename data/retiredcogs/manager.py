import asyncio
import json
import traceback
import psutil
from botutils.utils import bytes2human as read


class Commands:
    def __init__(self, address):
        self.ip, self.pid = address
        self.active_commands = [self.memory_info]

    def process_commands(self, message):
        # parse the message
        args = message.split()
        if not args:
            return "A command is required"
        command = args.pop(0)

        for cmd in self.active_commands:
            if cmd.__name__ == command:
                result = error = ""
                try:
                    result = cmd(*args)
                except Exception as e:
                    error = json.dumps([str(e), str(traceback.format_exc())])
                return json.dumps({"RESULT": result, "ERROR": error})
        return "Unknown command"

    def memory_info(self, pid):
        process = psutil.Process(int(pid))
        memory_info = {
            "GLOBAL": {
                "RAM": {
                    "USED": read(psutil.virtual_memory().used),
                    "TOTAL": read(psutil.virtual_memory().total),
                    "PERCENT": f"{psutil.virtual_memory().percent}%",
                },
                "CPU": f"{psutil.cpu_percent()}$",
                "STORAGE": {
                    "USED": read(psutil.disk_usage("/").used),
                    "TOTAL": read(psutil.disk_usage("/").total),
                },
            },
            "PID": {
                "CPU": process.cpu_percent(interval=1),
                "RAM": {
                    "RSS": read(process.memory_full_info().rss),
                    "PERCENT": f"{round(process.memory_percent())}%",
                },
            },
        }
        return json.dumps(memory_info)


class Client:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    @staticmethod
    async def __handle_echo(reader, writer):
        data = await reader.read(1000)
        message = data.decode()
        addr = writer.get_extra_info("peername")
        print("Received %r from %r" % (message, addr))
        commands = Commands(addr)
        result = commands.process_commands(message)
        writer.write(result.encode())
        await writer.drain()

    def listen(self, port: 8888):
        async def start_server():
            await asyncio.start_server(
                self.__handle_echo, "127.0.0.1", port, loop=self.loop
            )

        self.loop.create_task(start_server(), name="Listener")


client = Client()
client.listen(port=1269)
client.loop.run_forever()
