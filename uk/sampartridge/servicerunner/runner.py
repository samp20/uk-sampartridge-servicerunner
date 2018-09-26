import importlib
import logging

class Runner:
    def __init__(self, config):
        self.services = {}
        self.config = config

    def load_services(self):
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
        for name, service in self.services.items():
            await service.start(loop)

    async def stop(self):
        for name, service in self.services.items():
            await service.stop()