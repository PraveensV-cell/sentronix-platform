import cv2
import re


RTSP_PATTERN = re.compile(
    r"^rtsp://.+",
    re.IGNORECASE,
)


def is_valid_rtsp_url(
    rtsp_url: str,
) -> bool:
    """
    Validate RTSP URL format.
    """

    return bool(RTSP_PATTERN.match(rtsp_url))


def check_camera_connection(
    rtsp_url: str,
    timeout: int = 5,
) -> bool:
    """
    Check whether an RTSP camera is reachable.
    """

    capture = cv2.VideoCapture(rtsp_url)

    capture.set(
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
        timeout * 1000,
    )

    if not capture.isOpened():
        capture.release()
        return False

    success, _ = capture.read()

    capture.release()

    return success
