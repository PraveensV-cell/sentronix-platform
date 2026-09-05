from pathlib import Path
import cv2
import time
from ultralytics import YOLO


# -------------------------------------------------
# PATHS
# -------------------------------------------------

MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


# -------------------------------------------------
# CAMERA SETTINGS
# -------------------------------------------------

# 0 = Laptop webcam
# RTSP example:
# "rtsp://username:password@camera-ip:554/stream"

CAMERA_SOURCE = 0


CONFIDENCE = 0.5


# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------


def load_model():

    if not MODEL_PATH.exists():
        print("Model not found:")

        print(MODEL_PATH)

        return None

    model = YOLO(str(MODEL_PATH))

    return model


# -------------------------------------------------
# CAMERA DETECTION
# -------------------------------------------------


def run_camera():

    print("Sentronix Live Camera Detection")

    model = load_model()

    if model is None:
        return

    camera = cv2.VideoCapture(CAMERA_SOURCE)

    if not camera.isOpened():
        print("Camera could not open")

        return

    print("Camera started")

    previous_time = time.time()

    while True:
        success, frame = camera.read()

        if not success:
            print("Frame capture failed")

            break

        results = model.predict(
            frame,
            conf=CONFIDENCE,
            device="cpu",
            verbose=False,
        )

        output_frame = results[0].plot()

        current_time = time.time()

        fps = 1 / (current_time - previous_time)

        previous_time = current_time

        cv2.putText(
            output_frame,
            f"FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            "Sentronix Security AI",
            output_frame,
        )

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()


def main():

    run_camera()


if __name__ == "__main__":
    main()
