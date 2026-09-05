from pathlib import Path
from ultralytics import YOLO


MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


EXPORT_FORMAT = "onnx"


def export_model():

    if not MODEL_PATH.exists():
        print(f"Model not found: {MODEL_PATH}")

        return

    print("Loading trained model...")

    model = YOLO(MODEL_PATH)

    print("Exporting model...")

    model.export(
        format=EXPORT_FORMAT,
        imgsz=416,
        dynamic=True,
    )

    print("Model export completed.")


def main():

    print("Sentronix Model Export")

    export_model()


if __name__ == "__main__":
    main()
