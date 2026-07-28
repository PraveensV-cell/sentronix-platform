from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ServiceInfo:
    """
    Represents a registered service in the SENTRONIX platform.
    """

    name: str
    version: str
    status: str
    description: str


class ServiceRegistry:
    """
    Central registry for all SENTRONIX services.
    """

    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}

    def register(
        self,
        service: ServiceInfo,
    ) -> None:
        """
        Register a service.
        """

        self._services[service.name] = service

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Remove a service from the registry.
        """

        self._services.pop(name, None)

    def get(
        self,
        name: str,
    ) -> Optional[ServiceInfo]:
        """
        Get a registered service by name.
        """

        return self._services.get(name)

    def get_all(
        self,
    ) -> List[ServiceInfo]:
        """
        Return all registered services.
        """

        return list(self._services.values())

    def clear(
        self,
    ) -> None:
        """
        Remove all registered services.
        """

        self._services.clear()

    def count(
        self,
    ) -> int:
        """
        Return the number of registered services.
        """

        return len(self._services)

    def register_default_services(
        self,
    ) -> None:
        """
        Register all SENTRONIX microservices.
        """

        services = [
            ServiceInfo(
                name="api-gateway",
                version="1.0.0",
                status="healthy",
                description="Central API Gateway",
            ),
            ServiceInfo(
                name="ai-service",
                version="1.0.0",
                status="healthy",
                description="AI Detection Service",
            ),
            ServiceInfo(
                name="event-service",
                version="1.0.0",
                status="healthy",
                description="Event Processing Service",
            ),
            ServiceInfo(
                name="notification-service",
                version="1.0.0",
                status="healthy",
                description="Notification Service",
            ),
            ServiceInfo(
                name="storage-service",
                version="1.0.0",
                status="healthy",
                description="Storage Service",
            ),
            ServiceInfo(
                name="analytics-service",
                version="1.0.0",
                status="healthy",
                description="Analytics Service",
            ),
        ]

        for service in services:
            self.register(service)


registry = ServiceRegistry()

registry.register_default_services()
