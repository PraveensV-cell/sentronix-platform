from pathlib import Path
from ultralytics import YOLO


CONFIG_FILE = Path("configs/sentronix.yaml")


MODEL_NAME = "yolo11n.pt"


OUTPUT_DIR = Path("models/sentronix-detector-v1")


def create_output() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def train_model() -> None:

    print("Loading YOLO model...")

    model = YOLO(MODEL_NAME)

    print("Starting Sentronix training...")

    model.train(
        data=str(CONFIG_FILE),
        # CPU optimized settings
        epochs=50,
        imgsz=416,
        batch=2,
        workers=2,
        project=str(OUTPUT_DIR),
        name="detector-v1",
        patience=15,
        optimizer="AdamW",
        # No NVIDIA GPU
        device="cpu",
        # Save best model
        save=True,
        # Mixed precision disabled for CPU
        amp=False,
    )

    print("Training completed.")


def main() -> None:

    print("Sentronix AI Detector Training")

    create_output()

    train_model()


if __name__ == "__main__":
    main()
