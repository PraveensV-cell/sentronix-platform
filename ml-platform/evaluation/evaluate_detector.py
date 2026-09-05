from pathlib import Path
from ultralytics import YOLO


MODEL_PATH = Path("models/sentronix-detector-v1/detector-v1/weights/best.pt")


DATA_CONFIG = Path("configs/sentronix.yaml")


OUTPUT_DIR = Path("evaluation/results")


def create_output() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def evaluate_model() -> None:

    if not MODEL_PATH.exists():
        print(f"Model not found: {MODEL_PATH}")

        print("Train the model first.")

        return

    if not DATA_CONFIG.exists():
        print(f"Dataset config missing: {DATA_CONFIG}")

        return

    print("Loading trained model...")

    model = YOLO(MODEL_PATH)

    print("Starting evaluation...")

    metrics = model.val(
        data=str(DATA_CONFIG),
        imgsz=416,
        batch=2,
        split="val",
        project=str(OUTPUT_DIR),
        name="detector-evaluation",
        device="cpu",
    )

    print("\nEvaluation Results")

    print(f"mAP50: {metrics.box.map50:.4f}")

    print(f"mAP50-95: {metrics.box.map:.4f}")

    print(f"Precision: {metrics.box.mp:.4f}")

    print(f"Recall: {metrics.box.mr:.4f}")


def main() -> None:

    print("Sentronix Detector Evaluation")

    create_output()

    evaluate_model()

    print("Evaluation completed.")


if __name__ == "__main__":
    main()
