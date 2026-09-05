from pathlib import Path
import cv2
from ultralytics import YOLO


MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


CAMERA_SOURCE = 0


CONFIDENCE = 0.5


# -------------------------------------------------
# RESTRICTED ZONE
# -------------------------------------------------

# Format:
# x1,y1,x2,y2

RESTRICTED_ZONE = (
    200,
    150,
    600,
    450,
)


# -------------------------------------------------
# CHECK ZONE
# -------------------------------------------------


def inside_zone(
    x,
    y,
):

    x1, y1, x2, y2 = RESTRICTED_ZONE

    if x1 <= x <= x2 and y1 <= y <= y2:
        return True

    return False


# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------


def load_model():

    if not MODEL_PATH.exists():
        print("Model missing")

        return None

    return YOLO(str(MODEL_PATH))


# -------------------------------------------------
# RUN INTRUSION SYSTEM
# -------------------------------------------------


def run_intrusion_detection():

    print("Sentronix Intrusion Detection")

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

        # Draw restricted zone

        cv2.rectangle(
            output,
            (
                RESTRICTED_ZONE[0],
                RESTRICTED_ZONE[1],
            ),
            (
                RESTRICTED_ZONE[2],
                RESTRICTED_ZONE[3],
            ),
            (
                0,
                0,
                255,
            ),
            3,
        )

        if results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().tolist()

            ids = results.boxes.id.cpu().tolist()

            for box, track_id in zip(
                boxes,
                ids,
            ):
                x1, y1, x2, y2 = box

                center_x = int((x1 + x2) / 2)

                center_y = int((y1 + y2) / 2)

                if inside_zone(
                    center_x,
                    center_y,
                ):
                    print(f"🚨 INTRUSION ALERT Object ID: {int(track_id)}")

                    cv2.putText(
                        output,
                        "INTRUSION",
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
            "Sentronix Intrusion Detection",
            output,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()


def main():

    run_intrusion_detection()


if __name__ == "__main__":
    main()
