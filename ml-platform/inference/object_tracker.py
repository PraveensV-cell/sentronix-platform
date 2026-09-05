from pathlib import Path
import cv2

from ultralytics import YOLO


MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


CAMERA_SOURCE = 0


CONFIDENCE = 0.5


def load_model():

    if not MODEL_PATH.exists():
        print("Model not found:")

        print(MODEL_PATH)

        return None

    model = YOLO(str(MODEL_PATH))

    return model


def run_tracking():

    print("Sentronix Object Tracking Started")

    model = load_model()

    if model is None:
        return

    camera = cv2.VideoCapture(CAMERA_SOURCE)

    if not camera.isOpened():
        print("Camera unavailable")

        return

    while True:
        success, frame = camera.read()

        if not success:
            break

        results = model.track(
            frame,
            conf=CONFIDENCE,
            persist=True,
            device="cpu",
            verbose=False,
        )

        output = results[0].plot()

        if results[0].boxes.id is not None:
            track_ids = results[0].boxes.id.cpu().tolist()

            classes = results[0].boxes.cls.cpu().tolist()

            for track_id, class_id in zip(
                track_ids,
                classes,
            ):
                name = model.names[int(class_id)]

                print(f"ID:{int(track_id)} Object:{name}")

        cv2.imshow(
            "Sentronix Object Tracking",
            output,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()


def main():

    run_tracking()


if __name__ == "__main__":
    main()
