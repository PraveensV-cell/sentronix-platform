from src.core.service_registry import registry


def get_service_information():

    return {
        "name": "SENTRONIX API Gateway",
        "version": "1.0.0",
        "environment": "development",
        "status": "healthy",
        "registered_services": registry.count(),
    }
