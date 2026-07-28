SERVICES = {
    "gateway": {
        "host": "localhost",
        "port": 8000,
    },
    "ai": {
        "host": "localhost",
        "port": 8001,
    },
    "camera": {
        "host": "localhost",
        "port": 8002,
    },
    "device": {
        "host": "localhost",
        "port": 8003,
    },
    "event": {
        "host": "localhost",
        "port": 8004,
    },
    "notification": {
        "host": "localhost",
        "port": 8005,
    },
    "storage": {
        "host": "localhost",
        "port": 8006,
    },
    "analytics": {
        "host": "localhost",
        "port": 8007,
    },
}


def get_service_url(service: str) -> str:
    """
    Return the base URL for a service.
    """

    config = SERVICES.get(service)

    if config is None:
        raise ValueError(f"Unknown service: {service}")

    return f"http://{config['host']}:{config['port']}"
