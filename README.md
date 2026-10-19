# Sentronix Platform

Sentronix is an AI-assisted surveillance operations platform. The repository
contains a FastAPI microservice backend, PostgreSQL/Redis/RabbitMQ infrastructure,
an AI inference service, and an early Vite dashboard.

## Local development

1. Copy `.env.example` to `.env`.
2. Replace the `CHANGE_ME` values with local-only values. Do not commit `.env`.
3. Start the backend services with `docker compose up --build`.
4. Open the API gateway at `http://localhost:8000/docs`.

The dashboard is currently a separate Vite app under `ml-platform/dashboard`; it
is not yet included in the Compose stack. Start it with `npm ci` and `npm run dev`
from that directory.

## AI model weights

Model weights are not committed. The AI container keeps the existing lightweight
model as its fallback. To use a supplied YOLO11s checkpoint:

1. Create a local `models` directory in the repository root.
2. Copy the checkpoint there as `models/yolo11s.pt`.
3. Set `YOLO_MODEL=/models/yolo11s.pt` in the ignored root `.env`.
4. Set `SENTRONIX_MODELS_DIR=./models` in `.env` if using a different host path.

The Compose service mounts that directory read-only inside the AI container.
`*.pt` files are ignored by Git.

## Backend tests

```bash
python -m pip install -r services/api-gateway/requirements-dev.txt
PYTHONPATH=services/api-gateway python -m pytest services/api-gateway/tests -q
```

## Current implementation boundary

The repository is still an incremental implementation, not the complete
blueprint. The current branch has backend foundations for authentication,
cameras, detections, alerts, recordings, analytics, and AI inference. School
environments, people/face enrollment, attendance, configurable rule management,
and the operational assistant still need end-to-end implementation. AI
classifications must not be treated as identity or activity confirmation without
the corresponding model and human review.
