import requests

from integration.configs.health import HEALTH_ENDPOINT
from integration.configs.health import REQUEST_TIMEOUT
from integration.configs.services import SERVICES

print("\nSentronix Health Check\n")

for name, config in SERVICES.items():
    url = f"http://{config['host']}:{config['port']}{HEALTH_ENDPOINT}"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            print(f"[OK] {name:<15} Running")
        else:
            print(f"[WARN] {name:<15} HTTP {response.status_code}")

    except Exception:
        print(f"[FAIL] {name:<15} Offline")
