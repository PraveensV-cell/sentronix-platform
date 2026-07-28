import time

import torch

from src.ai.detector import AIEngine


class AIMonitor:
    """
    Monitors AI Engine health.
    """

    def __init__(self):
        self.engine = AIEngine()

    def get_status(self) -> str:
        """
        Check whether AI model is loaded.
        """

        try:
            if self.engine.model is not None:
                return "ONLINE"

        except Exception:
            pass

        return "OFFLINE"

    def get_device(self) -> str:
        """
        Return current inference device.
        """

        if torch.cuda.is_available():
            return "GPU"

        return "CPU"

    def get_gpu_available(self) -> bool:
        """
        Return CUDA availability.
        """

        return torch.cuda.is_available()

    def get_model_name(self) -> str:
        """
        Return loaded model name.
        """

        try:
            return str(self.engine.model.model_name)

        except Exception:
            return "Unknown"

    def get_inference_latency(self) -> float:
        """
        Measure inference latency.
        """

        try:
            start = time.perf_counter()

            # Dummy inference
            self.engine.model.predict(
                source="https://ultralytics.com/images/bus.jpg",
                verbose=False,
            )

            end = time.perf_counter()

            return round(
                (end - start) * 1000,
                2,
            )

        except Exception:
            return -1.0

    def collect(self) -> dict:
        """
        Collect AI health metrics.
        """

        return {
            "status": self.get_status(),
            "device": self.get_device(),
            "gpu_available": self.get_gpu_available(),
            "model": self.get_model_name(),
            "latency_ms": self.get_inference_latency(),
        }
