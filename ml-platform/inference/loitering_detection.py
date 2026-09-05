from pathlib import Path
import cv2
import time

from ultralytics import YOLO


MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


CAMERA_SOURCE = 0


CONFIDENCE = 0.5


# Seconds before loitering alert

LOITER_TIME = 30


# Restricted monitoring zone

ZONE = (
    200,
    150,
    600,
    450,
)


# Store object entry times

person_times = {}


def inside_zone(
    x,
    y,
):

    x1, y1, x2, y2 = ZONE

    return x1 <= x <= x2 and y1 <= y <= y2


def load_model():

    if not MODEL_PATH.exists():
        print("Model not found")

        return None

    return YOLO(str(MODEL_PATH))


def check_loitering(
    track_id,
):

    current_time = time.time()

    if track_id not in person_times:
        person_times[track_id] = current_time

        return False

    duration = current_time - person_times[track_id]

    if duration > LOITER_TIME:
        return True

    return False


def run_loitering():

    print("Sentronix Loitering Detection")

    model = load_model()

    if model is None:
        return

    camera = cv2.VideoCapture(CAMERA_SOURCE)

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
        )[0]

        output = results.plot()

        cv2.rectangle(
            output,
            (
                ZONE[0],
                ZONE[1],
            ),
            (
                ZONE[2],
                ZONE[3],
            ),
            (
                255,
                0,
                0,
            ),
            3,
        )

        if results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().tolist()

            ids = results.boxes.id.cpu().tolist()

            classes = results.boxes.cls.cpu().tolist()

            for box, track_id, class_id in zip(
                boxes,
                ids,
                classes,
            ):
                # Only persons

                if int(class_id) != 0:
                    continue

                x1, y1, x2, y2 = box

                center_x = int((x1 + x2) / 2)

                center_y = int((y1 + y2) / 2)

                if inside_zone(
                    center_x,
                    center_y,
                ):
                    if check_loitering(int(track_id)):
                        print(f"🚨 LOITERING ALERT Person ID: {int(track_id)}")

                        cv2.putText(
                            output,
                            "LOITERING",
                            (
                                50,
                                50,
                            ),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.5,
                            (
                                0,
                                0,
                                255,
                            ),
                            3,
                        )

        cv2.imshow(
            "Sentronix Loitering Detection",
            output,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()


def main():

    run_loitering()


if __name__ == "__main__":
    main()
