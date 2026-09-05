from pathlib import Path
from ultralytics import YOLO


# -------------------------------------------------
# PATHS
# -------------------------------------------------

MODEL_PATH = Path(
    "runs/detect/models/sentronix-detector-v1/detector-v1/weights/best.pt"
)


DATA_CONFIG = Path("configs/sentronix.yaml")


OUTPUT_DIR = Path("runs/evaluation")


# -------------------------------------------------
# CREATE OUTPUT
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

    if not MODEL_PATH.exists():
        print("\nERROR: Model file not found")

        print(f"Looking for:\n{MODEL_PATH}")

        print("\nFind your best.pt using:")

        print("dir runs\\detect /s /b | findstr best.pt")

        return False

    if not DATA_CONFIG.exists():
        print("\nERROR: Dataset config missing")

        print(f"Missing:\n{DATA_CONFIG}")

        return False

    return True


# -------------------------------------------------
# EVALUATION
# -------------------------------------------------


def evaluate_model():

    print("Loading trained Sentronix model...")

    model = YOLO(str(MODEL_PATH))

    print("Starting evaluation...")

    metrics = model.val(
        data=str(DATA_CONFIG),
        split="test",
        imgsz=640,
        batch=2,
        device="cpu",
        project=str(OUTPUT_DIR),
        name="detector-evaluation",
        save_json=True,
    )

    print("\n========== RESULTS ==========")

    print(f"mAP50: {metrics.box.map50:.4f}")

    print(f"mAP50-95: {metrics.box.map:.4f}")

    print(f"Precision: {metrics.box.mp:.4f}")

    print(f"Recall: {metrics.box.mr:.4f}")

    print("============================")


# -------------------------------------------------
# MAIN
# -------------------------------------------------


def main():

    print("Sentronix Model Evaluation")

    create_output()

    if not check_files():
        return

    evaluate_model()

    print("\nEvaluation completed")


if __name__ == "__main__":
    main()
