from __future__ import annotations

import cv2
import numpy as np


class FrameProcessor:
    """
    Handles frame processing operations.
    """

    def resize(
        self,
        frame,
        width: int = 1280,
        height: int = 720,
    ):
        """
        Resize frame.
        """

        return cv2.resize(
            frame,
            (width, height),
        )

    def compress(
        self,
        frame,
        quality: int = 80,
    ):
        """
        Compress frame.
        """

        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                quality,
            ],
        )

        return cv2.imdecode(
            buffer,
            cv2.IMREAD_COLOR,
        )

    def rotate(
        self,
        frame,
        angle: int,
    ):
        """
        Rotate frame.
        """

        if angle == 90:
            return cv2.rotate(
                frame,
                cv2.ROTATE_90_CLOCKWISE,
            )

        if angle == 180:
            return cv2.rotate(
                frame,
                cv2.ROTATE_180,
            )

        if angle == 270:
            return cv2.rotate(
                frame,
                cv2.ROTATE_90_COUNTERCLOCKWISE,
            )

        return frame

    def grayscale(
        self,
        frame,
    ):
        """
        Convert frame to grayscale.
        """

        return cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

    def blur(
        self,
        frame,
        kernel: int = 5,
    ):
        """
        Apply Gaussian blur.
        """

        return cv2.GaussianBlur(
            frame,
            (kernel, kernel),
            0,
        )

    def sharpen(
        self,
        frame,
    ):
        """
        Sharpen frame.
        """

        sharpening_kernel = np.array(
            [
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0],
            ]
        )

        return cv2.filter2D(
            frame,
            -1,
            sharpening_kernel,
        )

    def enhance(
        self,
        frame,
    ):
        """
        Improve image contrast using CLAHE.
        """

        lab_image = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2LAB,
        )

        lightness_channel, green_red_channel, blue_yellow_channel = cv2.split(
            lab_image,
        )

        clahe = cv2.createCLAHE()

        enhanced_lightness = clahe.apply(
            lightness_channel,
        )

        enhanced_lab = cv2.merge(
            (
                enhanced_lightness,
                green_red_channel,
                blue_yellow_channel,
            ),
        )

        return cv2.cvtColor(
            enhanced_lab,
            cv2.COLOR_LAB2BGR,
        )


frame_processor = FrameProcessor()
