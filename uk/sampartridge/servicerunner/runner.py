import importlib
import logging
from .datagram import create_datagram_endpoint
import socket
import os

class Runner:
    def __init__(self, config):
        self.services = {}
        self.config = config
        self.enable_systemd = self.config.getboolean('DEFAULT', 'systemd', fallback=False)
        self.systemd_sock = None

    def load_services(self):
        services = self.config['Services']
        for key in services:
            if services.getboolean(key):
                self.get_service(key)

    def get_service(self, name):
        try:
            return self.services[name]
        except KeyError:
            config = self.config[name]
            module = importlib.import_module(config['module'])
            service_cls = getattr(module, config['class'])
            service = service_cls(self, name, config)
            self.services[name] = service
            return service

    async def start(self, loop):
        for service in self.services.values():
            await service.start(loop)

        if self.enable_systemd:
            await self.start_systemd()

    async def stop(self):
        await self.stop_systemd()

        for service in self.services.values():
            await service.stop()

    async def start_systemd(self):
        notify_addr = os.getenv('NOTIFY_SOCKET')
        if notify_addr is None:
            return
        if notify_addr[0] == '@':
            notify_addr = '\0' + notify_addr[1:]
        try:
            #pylint: disable=E1101
            self.systemd_sock = await create_datagram_endpoint(remote_addr=notify_addr, family=socket.AF_UNIX)
        except AttributeError:
            return
        self.systemd_sock.send(b'READY=1')

    async def stop_systemd(self):
        if self.systemd_sock:
            self.systemd_sock.send(b'STOPPING=1')
            self.systemd_sock.close()
            await self.systemd_sock.wait_closed()