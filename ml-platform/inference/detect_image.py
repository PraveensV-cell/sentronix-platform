from pathlib import Path
from ultralytics import YOLO


MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


IMAGE_PATH = Path("test.jpg")


OUTPUT_DIR = Path("runs/inference/images")


CONFIDENCE = 0.5


def main():

    print("Sentronix Image Detection")

    if not MODEL_PATH.exists():
        print("Model not found:")

        print(MODEL_PATH)

        return

    if not IMAGE_PATH.exists():
        print("Image not found:")

        print(IMAGE_PATH)

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = YOLO(str(MODEL_PATH))

    print("Running detection...")

    results = model.predict(
        source=str(IMAGE_PATH),
        conf=CONFIDENCE,
        save=True,
        project=str(OUTPUT_DIR),
        name="result",
        device="cpu",
    )

    for result in results:
        boxes = result.boxes

        for box in boxes:
            class_id = int(box.cls[0])

            confidence = float(box.conf[0])

            name = model.names[class_id]

            print(f"{name}: {confidence:.2f}")

    print("Detection completed")


if __name__ == "__main__":
    main()
