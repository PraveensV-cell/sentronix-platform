from __future__ import annotations

import torch

from ultralytics import YOLO

from src.core.config import settings
from src.core.logger import logger


class ModelLoader:
    """
    Manages YOLO model loading and configuration.
    """

    def __init__(self):
        self.models: dict[str, YOLO] = {}
        self.active_model: str | None = None
        self.device = self.detect_device()

    def detect_device(
        self,
    ) -> str:
        """
        Detect available compute device.
        """

        if torch.cuda.is_available():
            logger.info(
                "CUDA GPU detected. Using GPU.",
            )

            return "cuda"

        logger.info(
            "GPU not available. Using CPU.",
        )

        return "cpu"

    def load_model(
        self,
        model_name: str | None = None,
    ) -> YOLO:
        """
        Load YOLO model with cache.
        """

        if model_name is None:
            model_name = settings.YOLO_MODEL

        if model_name in self.models:
            logger.info(
                f"Using cached model: {model_name}",
            )

            self.active_model = model_name

            return self.models[model_name]

        try:
            logger.info(
                f"Loading YOLO model: {model_name}",
            )

            model = YOLO(
                model_name,
            )

            model.to(
                self.device,
            )

            self.models[model_name] = model

            self.active_model = model_name

            logger.success(
                f"Model loaded successfully: {model_name}",
            )

            return model

        except Exception as error:
            logger.error(
                f"Model loading failed: {error}",
            )

            raise

    def get_model(
        self,
        model_name: str | None = None,
    ) -> YOLO:
        """
        Get loaded model.
        """

        if model_name is None:
            model_name = settings.YOLO_MODEL

        if model_name not in self.models:
            return self.load_model(
                model_name,
            )

        return self.models[model_name]

    def reload_model(
        self,
        model_name: str | None = None,
    ) -> YOLO:
        """
        Reload YOLO model.
        """

        if model_name is None:
            model_name = settings.YOLO_MODEL

        self.models.pop(
            model_name,
            None,
        )

        return self.load_model(
            model_name,
        )

    def unload_models(
        self,
    ):
        """
        Release loaded models.
        """

        self.models.clear()

        self.active_model = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(
            "YOLO models unloaded.",
        )

    def model_info(
        self,
    ) -> dict:
        """
        Return model information.
        """

        return {
            "active_model": self.active_model,
            "device": self.device,
            "loaded_models": list(
                self.models.keys(),
            ),
        }


model_loader = ModelLoader()
