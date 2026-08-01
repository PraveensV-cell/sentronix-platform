from __future__ import annotations

import cv2
import requests

from src.core.config import settings


class AIClient:
    """
    AI Service communication.
    """

    def detect(
        self,
        frame,
    ):
        """
        Send frame to AI Service.
        """

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
        )

        if not success:
            return {
                "success": False,
                "detections": [],
            }

        files = {
            "file": (
                "frame.jpg",
                buffer.tobytes(),
                "image/jpeg",
            )
        }

        try:
            response = requests.post(
                f"{settings.AI_SERVICE_URL}/detect",
                files=files,
                timeout=settings.AI_DETECTION_TIMEOUT,
            )

            return response.json()

        except Exception:
            return {
                "success": False,
                "detections": [],
            }


ai_client = AIClient()
