import asyncio



class Connection:
    def __init__(self, address):
        self.address = address
        self.loop = asyncio.get_running_loop()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def send(self):
        connection = self.loop.create_connection(asyncio.Protocol())


