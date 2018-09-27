from uk.sampartridge.servicerunner import PollingService, task

import asyncio
import socket
import os
import logging

class SystemdNotify(PollingService):
    default_interval=2.0

    def do_init(self, runner, name, config):
        self.enabled = config.getboolean('enabled', fallback=False)
        self.watchdog = config.getboolean('watchdog', fallback=False)

        self.addr = os.getenv('NOTIFY_SOCKET')
        if self.addr and self.addr[0] == '@':
            self.addr = '\0' + self.addr[1:]
        
        self.transport = None

    async def do_start(self):
        self.log.debug("Systemd service enabled? %s", self.enabled)
        if self.enabled:
            await self.connect()
            self.send('READY=1')
        await super().do_start()

    async def do_stop(self):
        await super().do_stop()
        if self.enabled:
            self.send('STOPPING=1')
            await self.disconnect()

    @task(can_cancel=False)
    async def do_poll(self):
        if self.watchdog:
            self.send('WATCHDOG=1')

    async def connect(self):
        try:
            if self.transport is None and self.addr is not None:
                self.disconnect_future = asyncio.Future()
                loop = asyncio.get_event_loop()
                self.log.info("Connecting to systemd socket %s", self.addr)
                #pylint: disable=E1101
                await loop.create_datagram_endpoint(lambda: self, remote_addr=self.addr, family=socket.AF_UNIX)
        except AttributeError:
            pass

    async def disconnect(self):
        if self.transport:
            self.transport.close()
            await self.disconnect_future

    def send(self, data):
        if self.transport:
            self.log.debug("Sending to systemd: %s", data)
            self.transport.sendto(data)

    def connection_made(self, transport):
        self.transpoprt = transport

    def datagram_received(self, data, addr):
        pass
    
    def connection_lost(self, exc):
        self.disconnect_future.set_result(None)
        self.transport = None
        

    