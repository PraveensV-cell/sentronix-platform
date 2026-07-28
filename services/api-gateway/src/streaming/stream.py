import threading
import time

import cv2


class CameraStream:
    """
    Maintains a persistent connection to one camera.
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
    ):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url

        self.capture = None

        # Latest annotated frame
        self.frame = None

        # Latest original frame
        self.raw_frame = None

        self.running = False

        self.thread = None

    def start(self):
        """
        Start background frame reader.
        """

        if self.running:
            return

        self.running = True

        self.capture = cv2.VideoCapture(self.rtsp_url)

        self.thread = threading.Thread(
            target=self.update,
            daemon=True,
        )

        self.thread.start()

    def update(self):
        """
        Continuously read frames.
        """

        while self.running:
            if self.capture is None:
                break

            success, frame = self.capture.read()

            if success:
                # Store original frame
                self.raw_frame = frame

                # Initially stream original frame
                # DetectionWorker will replace this with
                # an annotated frame.
                self.frame = frame

            else:
                time.sleep(1)

    def get_frame(self):
        """
        Return latest frame.
        """

        return self.frame

    def get_raw_frame(self):
        """
        Return latest original frame.
        """

        return self.raw_frame

    def stop(self):
        """
        Stop stream.
        """

        self.running = False

        if self.capture:
            self.capture.release()

        self.capture = None

        self.frame = None

        self.raw_frame = None
