from pathlib import Path


DATASET_ROOT = Path("datasets/raw")


DATASETS = {
    "coco": "Person and vehicle detection",
    "fire": "Fire and smoke detection",
    "weapon": "Weapon and restricted objects",
    "safety": "Helmet and safety vest detection",
    "surveillance": "Security camera scenes",
    "tracking": "Multi-object tracking datasets",
    "openimages": "Large object diversity dataset",
}


def create_dataset_structure():

    print("Creating dataset folders...")

    for name, description in DATASETS.items():
        folder = DATASET_ROOT / name

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")

        info_file = folder / "README.txt"

        with open(
            info_file,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(description)


def main():

    print("Sentronix Dataset Preparation")

    create_dataset_structure()

    print("\nDataset structure ready.")

    print("Now download datasets into datasets/raw/")


if __name__ == "__main__":
    main()
