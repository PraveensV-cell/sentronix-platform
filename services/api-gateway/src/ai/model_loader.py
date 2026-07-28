from ultralytics import YOLO


class ModelLoader:
    """
    Loads and caches AI models.
    """

    _models = {}

    @classmethod
    def load_yolo(
        cls,
        model_path: str = "models/yolov8n.pt",
    ):
        if model_path not in cls._models:
            cls._models[model_path] = YOLO(model_path)

        return cls._models[model_path]
