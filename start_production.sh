#!/usr/bin/env bash
# ==========================================================
# SENTRONIX AI PLATFORM - LINUX / CLOUD PRODUCTION LAUNCHER
# Usage:
#   chmod +x start_production.sh
#   ./start_production.sh
# ==========================================================

set -e

echo "============================================================"
echo "  SENTRONIX AI — PRODUCTION HOST LAUNCHER"
echo "============================================================"

# Check if Docker is available
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "[INFO] Docker & Docker Compose detected."
    echo "[INFO] Starting full-stack production containers..."
    docker compose -f docker-compose.prod.yml up -d --build
    echo ""
    echo "============================================================"
    echo "  SENTRONIX AI CONTAINERIZED CLUSTER RUNNING:"
    echo "  Frontend Dashboard: http://localhost (Port 80 / 5173)"
    echo "  API Gateway:        http://localhost:8000"
    echo "  Swagger UI Docs:    http://localhost:8000/docs"
    echo "  PostgreSQL:         Port 5432"
    echo "  Redis Bus:          Port 6379"
    echo "  RabbitMQ:           Port 5672 (Management: 15672)"
    echo "============================================================"
    exit 0
fi

# Fallback: Native Python execution
echo "[INFO] Docker not found. Falling back to native host runtime..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python3 scripts/verify_host.py
python3 start_sentronix.py
