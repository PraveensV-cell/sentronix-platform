from dataclasses import dataclass
from typing import Dict


@dataclass
class ServiceInfo:
    name: str
    version: str
    status: str
    description: str


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}

    def register(self, service: ServiceInfo):
        self._services[service.name] = service

    def get(self, name: str):
        return self._services.get(name)

    def get_all(self):
        return list(self._services.values())


registry = ServiceRegistry()
