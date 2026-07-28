# Sentronix Integration

This directory contains the integration layer for the Sentronix platform.

## Components

- Gateway configuration
- Service configuration
- Health monitoring
- Docker Compose
- Startup scripts
- Shutdown scripts

## Services

| Service | Port |
|----------|------|
| API Gateway | 8000 |
| AI Service | 8001 |
| Camera Service | 8002 |
| Device Service | 8003 |
| Event Service | 8004 |
| Notification Service | 8005 |
| Storage Service | 8006 |
| Analytics Service | 8007 |

## Startup

```powershell
docker compose up -d
```

## Shutdown

```powershell
docker compose down
```

## Health Check

Run:

```powershell
python scripts/health_check.py
```

Expected Output:

```text
[OK] gateway
[OK] ai
[OK] camera
[OK] device
[OK] event
[OK] notification
[OK] storage
[OK] analytics
```
