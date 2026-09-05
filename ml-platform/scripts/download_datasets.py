from pathlib import Path


DATASET_ROOT = Path("datasets/raw")


DATASETS = {
    "coco": DATASET_ROOT / "coco",
    "openimages": DATASET_ROOT / "openimages",
    "fire": DATASET_ROOT / "fire",
    "safety": DATASET_ROOT / "safety",
    "surveillance": DATASET_ROOT / "surveillance",
}


def create_dataset_folders():

    for name, path in DATASETS.items():
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"{name} folder ready")


def main():

    print("Initializing Sentronix Dataset Pipeline")

    create_dataset_folders()

    print("Dataset workspace ready")


if __name__ == "__main__":
    main()
