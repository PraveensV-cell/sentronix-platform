import cv2


class VideoUtils:
    """
    Video utility functions.
    """

    @staticmethod
    def open(video_path: str):
        return cv2.VideoCapture(video_path)

    @staticmethod
    def fps(cap):
        return cap.get(cv2.CAP_PROP_FPS)

    @staticmethod
    def width(cap):
        return int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @staticmethod
    def height(cap):
        return int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @staticmethod
    def frame_count(cap):
        return int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
