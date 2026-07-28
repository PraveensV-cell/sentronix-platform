import os
import time

import cv2

from src.core.config import settings
from src.detector.model_loader import model_loader


class VideoDetectionService:
    """
    Video Detection Service.
    """

    def __init__(self):
        self.model = model_loader.get_model()

    def detect(self, video_path: str):

        cap = cv2.VideoCapture(video_path)

        fps = cap.get(cv2.CAP_PROP_FPS)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        filename = os.path.basename(video_path)

        output_path = os.path.join(
            settings.OUTPUT_DIR,
            filename,
        )

        writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        total_frames = 0

        total_detections = 0

        start = time.time()

        while True:
            success, frame = cap.read()

            if not success:
                break

            results = self.model(frame)

            annotated = results[0].plot()

            total_frames += 1

            total_detections += len(results[0].boxes)

            writer.write(annotated)

        cap.release()

        writer.release()

        elapsed = round(time.time() - start, 2)

        return {
            "output_video": output_path,
            "frames": total_frames,
            "detections": total_detections,
            "processing_time": elapsed,
        }
