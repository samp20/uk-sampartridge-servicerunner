import asyncio

class DatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, maxqueuesize, loop):
        self._queue = asyncio.Queue(maxqueuesize)
        self._closed = True
        self._closed_future = loop.create_future()

    def connection_made(self, transport):
        self._transport = transport
        self._closed = False

    def datagram_received(self, data, addr):
        try:
            self._queue.put_nowait((data, addr))
        except asyncio.QueueFull:
            pass

    def error_received(self, exc):
        pass

    def connection_lost(self, exc):
        self._closed = True
        try:
            self._queue.put_nowait((None, None))
        except asyncio.QueueFull:
            pass
        self._closed_future.set_result(True)

    def send(self, data, addr=None):
        self._transport.sendto(data, addr)

    async def read(self):
        if self._closed:
            return None
        data, addr = await self._queue.get()
        if data is None:
            return None
        return data, addr

    def close(self):
        self._transport.close()

    async def wait_closed(self):
        await self._closed_future
    

async def create_datagram_endpoint(maxqueuesize=0, **kwargs):
    loop = asyncio.get_running_loop()
    _, protocol = await loop.create_datagram_endpoint(lambda: DatagramProtocol(maxqueuesize, loop), **kwargs)
    return protocol