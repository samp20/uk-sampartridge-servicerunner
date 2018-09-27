import importlib
import logging
from .notify import SystemdNotify

class Runner:
    def __init__(self, config):
        self.services = {}
        self.config = config

    def load_services(self):
        self.systemd = SystemdNotify(self, 'systemd', {})
    
        for key, value in self.config['Services'].items():
            if value == '1':
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

        await self.systemd.start(loop)

    async def stop(self):
        await self.systemd.stop()

        for service in self.services.values():
            await service.stop()