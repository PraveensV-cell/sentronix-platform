from pathlib import Path
import torch
from ultralytics import YOLO


# -------------------------------------------------
# PATHS
# -------------------------------------------------

CONFIG_FILE = Path("configs/sentronix.yaml")


MODEL_NAME = "yolo11n.pt"


OUTPUT_DIR = Path("runs/detect/models/sentronix-detector-v1")


# -------------------------------------------------
# DEVICE SELECTOR
# -------------------------------------------------


def get_device():

    if torch.cuda.is_available():
        print("CUDA GPU detected")

        return 0

    else:
        print("CUDA not available")

        print("Using CPU training")

        return "cpu"


# -------------------------------------------------
# OUTPUT DIRECTORY
# -------------------------------------------------


def create_output():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# -------------------------------------------------
# CHECK FILES
# -------------------------------------------------


def check_files():

    if not CONFIG_FILE.exists():
        print("Dataset YAML missing:")

        print(CONFIG_FILE)

        return False

    return True


# -------------------------------------------------
# TRAIN MODEL
# -------------------------------------------------


def train_model():

    print("Loading YOLO model...")

    model = YOLO(MODEL_NAME)

    device = get_device()

    print("Starting Sentronix training...")

    model.train(
        data=str(CONFIG_FILE),
        epochs=100,
        imgsz=640,
        batch=2 if device == "cpu" else 8,
        workers=2,
        optimizer="AdamW",
        patience=20,
        project=str(OUTPUT_DIR),
        name="detector-v1",
        device=device,
        pretrained=True,
        verbose=True,
    )

    print("Training completed")


# -------------------------------------------------
# MAIN
# -------------------------------------------------


def main():

    print("Sentronix AI Training Pipeline")

    if not check_files():
        return

    create_output()

    train_model()


if __name__ == "__main__":
    main()
