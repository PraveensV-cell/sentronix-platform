from ultralytics import YOLO

from src.core.config import settings
from src.core.logger import logger


class ModelLoader:
    """
    Loads and manages the YOLO model.
    """

    def __init__(self):
        self.model = None

    def load_model(self):
        """
        Load the YOLO model if it is not already loaded.
        """

        if self.model is None:
            logger.info(f"Loading YOLO model: {settings.YOLO_MODEL}")

            self.model = YOLO(settings.YOLO_MODEL)

            logger.success("YOLO model loaded successfully.")

        return self.model

    def get_model(self):
        """
        Return the loaded model.
        """

        if self.model is None:
            return self.load_model()

        return self.model


model_loader = ModelLoader()
