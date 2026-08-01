from __future__ import annotations

import os
import time

import cv2

from src.core.config import settings
from src.core.logger import logger
from src.detector.inference import (
    inference_engine,
)
from src.detector.tracker import (
    tracker,
)
from src.services.tracking_service import (
    tracking_service,
)


class VideoDetectionService:
    """
    Handles video object detection and tracking.
    """

    def detect(
        self,
        video_path: str,
    ) -> dict:
        """
        Process uploaded video.
        """

        cap = cv2.VideoCapture(
            video_path,
        )

        if not cap.isOpened():
            return {
                "success": False,
                "message": "Unable to open video.",
            }

        fps = cap.get(
            cv2.CAP_PROP_FPS,
        )

        if fps <= 0:
            fps = 30

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH,
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT,
            )
        )

        filename = os.path.basename(
            video_path,
        )

        os.makedirs(
            settings.OUTPUT_DIR,
            exist_ok=True,
        )

        output_path = os.path.join(
            settings.OUTPUT_DIR,
            f"processed_{filename}",
        )

        writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(  # type: ignore
                *"mp4v",
            ),
            fps,
            (width, height),
        )

        if not writer.isOpened():
            cap.release()

            return {
                "success": False,
                "message": "Unable to create output video.",
            }

        total_frames = 0
        total_detections = 0

        start_time = time.time()

        try:
            while True:
                success, frame = cap.read()

                if not success:
                    break

                detections = inference_engine.run(
                    frame,
                    settings.CONFIDENCE_THRESHOLD,
                )

                tracked = tracker.update(
                    detections,
                )

                tracking_service.update(
                    tracked,
                )

                annotated = frame.copy()

                for detection in tracked:
                    bbox = detection.get(
                        "bbox",
                    )

                    if not bbox:
                        continue

                    x1, y1, x2, y2 = map(
                        int,
                        bbox,
                    )

                    cv2.rectangle(
                        annotated,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    label = (
                        f"{detection.get('label', 'object')} "
                        f"{detection.get('confidence', 0)}"
                    )

                    cv2.putText(
                        annotated,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

                writer.write(
                    annotated,
                )

                total_frames += 1

                total_detections += len(
                    tracked,
                )

        except Exception as error:
            logger.error(
                f"Video detection failed: {error}",
            )

        finally:
            cap.release()

            writer.release()

        elapsed = round(
            time.time() - start_time,
            2,
        )

        return {
            "success": True,
            "output_video": output_path,
            "frames_processed": total_frames,
            "detections": total_detections,
            "processing_time": elapsed,
        }


video_detection_service = VideoDetectionService()
