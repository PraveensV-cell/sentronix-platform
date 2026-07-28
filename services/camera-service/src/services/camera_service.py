from __future__ import annotations

from typing import Dict

import cv2

from src.schemas.camera import CameraCreate
from src.schemas.camera import CameraResponse
from src.schemas.camera import CameraStatus


class CameraService:
    """
    Manages registered cameras.
    """

    def __init__(self):
        self.cameras: Dict[str, CameraCreate] = {}

    def register_camera(
        self,
        camera: CameraCreate,
    ) -> CameraResponse:
        """
        Register a new camera.
        """

        self.cameras[camera.camera_name] = camera

        return CameraResponse(
            camera_name=camera.camera_name,
            camera_url=camera.camera_url,
            location=camera.location,
            connected=self.test_connection(
                camera.camera_url,
            ),
        )

    def get_all_cameras(
        self,
    ) -> list[CameraResponse]:
        """
        Return all registered cameras.
        """

        cameras: list[CameraResponse] = []

        for camera in self.cameras.values():
            cameras.append(
                CameraResponse(
                    camera_name=camera.camera_name,
                    camera_url=camera.camera_url,
                    location=camera.location,
                    connected=self.test_connection(
                        camera.camera_url,
                    ),
                )
            )

        return cameras

    def get_camera(
        self,
        camera_name: str,
    ) -> CameraResponse | None:
        """
        Return one camera.
        """

        camera = self.cameras.get(camera_name)

        if camera is None:
            return None

        return CameraResponse(
            camera_name=camera.camera_name,
            camera_url=camera.camera_url,
            location=camera.location,
            connected=self.test_connection(
                camera.camera_url,
            ),
        )

    def remove_camera(
        self,
        camera_name: str,
    ) -> bool:
        """
        Remove camera.
        """

        if camera_name not in self.cameras:
            return False

        del self.cameras[camera_name]

        return True

    def test_connection(
        self,
        url: str,
    ) -> bool:
        """
        Test camera connection.
        """

        capture = cv2.VideoCapture(url)

        success, _ = capture.read()

        capture.release()

        return success

    def camera_status(
        self,
        camera_name: str,
    ) -> CameraStatus | None:
        """
        Return camera status.
        """

        camera = self.cameras.get(camera_name)

        if camera is None:
            return None

        capture = cv2.VideoCapture(camera.camera_url)

        fps = capture.get(cv2.CAP_PROP_FPS)

        opened = capture.isOpened()

        capture.release()

        return CameraStatus(
            camera_name=camera.camera_name,
            status="ONLINE" if opened else "OFFLINE",
            fps=float(fps),
            is_recording=False,
        )


camera_service = CameraService()
