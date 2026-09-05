from pathlib import Path
import cv2
from ultralytics import YOLO


# -------------------------------------------------
# PATHS
# -------------------------------------------------

MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


VIDEO_PATH = Path("test_video.mp4")


OUTPUT_DIR = Path("runs/inference/videos")


OUTPUT_VIDEO = OUTPUT_DIR / "sentronix_output.mp4"


CONFIDENCE = 0.5


# -------------------------------------------------
# MAIN VIDEO DETECTION
# -------------------------------------------------


def run_detection():

    print("Sentronix Video Detection")

    if not MODEL_PATH.exists():
        print("Model not found:")

        print(MODEL_PATH)

        return

    if not VIDEO_PATH.exists():
        print("Video not found:")

        print(VIDEO_PATH)

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading model...")

    model = YOLO(str(MODEL_PATH))

    capture = cv2.VideoCapture(str(VIDEO_PATH))

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))

    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fps = capture.get(cv2.CAP_PROP_FPS)

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (
            width,
            height,
        ),
    )

    print("Starting detection...")

    frame_count = 0

    while True:
        success, frame = capture.read()

        if not success:
            break

        results = model.predict(
            frame,
            conf=CONFIDENCE,
            device="cpu",
            verbose=False,
        )

        annotated_frame = results[0].plot()

        writer.write(annotated_frame)

        frame_count += 1

        cv2.imshow(
            "Sentronix Detection",
            annotated_frame,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()

    writer.release()

    cv2.destroyAllWindows()

    print(f"Frames processed: {frame_count}")

    print("Output saved:")

    print(OUTPUT_VIDEO)


def main():

    run_detection()


if __name__ == "__main__":
    main()
