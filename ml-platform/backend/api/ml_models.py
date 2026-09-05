ML_MODELS = [
    {
        "id": "object_detection",
        "name": "Object Detection",
        "status": "ready",
        "version": "1.0.0",
    },
    {
        "id": "object_tracking",
        "name": "Object Tracking",
        "status": "standby",
        "version": "1.0.0",
    },
    {
        "id": "ocr",
        "name": "OCR",
        "status": "standby",
        "version": "1.0.0",
    },
    {
        "id": "face_recognition",
        "name": "Face Recognition",
        "status": "standby",
        "version": "1.0.0",
    },
]


def get_model(
    model_id: str,
):
    for model in ML_MODELS:
        if model["id"] == model_id:
            return model

    return None


def get_ready_models():
    return [model for model in ML_MODELS if model["status"] == "ready"]


def get_model_count():
    return len(ML_MODELS)


def get_ready_model_count():
    return len(get_ready_models())
