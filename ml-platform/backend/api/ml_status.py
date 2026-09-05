from api.ml_models import (
    ML_MODELS,
    get_model,
    get_model_count,
    get_ready_model_count,
    get_ready_models,
)
from fastapi import APIRouter

router = APIRouter(
    prefix="/ml",
    tags=["ML Models"],
)


@router.get("/status")
def get_ml_status():
    return {
        "status": "running",
        "total_models": get_model_count(),
        "ready_models": get_ready_model_count(),
        "models": ML_MODELS,
    }


@router.get("/models")
def get_models():
    return {
        "count": get_model_count(),
        "models": ML_MODELS,
    }


@router.get("/ready")
def get_ready_ml_models():
    models = get_ready_models()

    return {
        "count": len(models),
        "models": models,
    }


@router.get("/models/{model_id}")
def get_ml_model(
    model_id: str,
):
    model = get_model(model_id)

    if model is None:
        return {
            "success": False,
            "message": "Model not found",
            "model_id": model_id,
        }

    return {
        "success": True,
        "model": model,
    }
