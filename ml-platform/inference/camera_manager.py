from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)

CAMERAS = {
    "camera_01": 0,
}

CONFIDENCE = 0.5


def load_model():
    if not MODEL_PATH.exists():
        print("Model not found:")
        print(MODEL_PATH)
        return None

    return YOLO(str(MODEL_PATH))


def process_camera(
    camera_id,
    source,
    model,
):
    print(f"Starting {camera_id}")

    camera = cv2.VideoCapture(source)

    if not camera.isOpened():
        print(f"{camera_id} unavailable")
        return

    while True:
        success, frame = camera.read()

        if not success:
            print(f"{camera_id} frame error")
            break

        results = model(
            frame,
            conf=CONFIDENCE,
            verbose=False,
        )[0]

        output = results.plot()

        cv2.putText(
            output,
            camera_id,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            camera_id,
            output,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()


def start_cameras():
    model = load_model()

    if model is None:
        return

    print("Sentronix Multi Camera System")

    for camera_id, source in CAMERAS.items():
        process_camera(
            camera_id,
            source,
            model,
        )

    cv2.destroyAllWindows()


def main():
    start_cameras()


if __name__ == "__main__":
    main()
