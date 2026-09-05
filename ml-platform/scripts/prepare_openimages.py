from pathlib import Path


OPENIMAGES_DIR = Path("datasets/raw/openimages")


FOLDERS = [
    OPENIMAGES_DIR / "images",
    OPENIMAGES_DIR / "annotations",
    OPENIMAGES_DIR / "metadata",
]


def create_structure():

    print("Preparing OpenImages dataset structure...")

    for folder in FOLDERS:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def main():

    print("Sentronix OpenImages Preparation")

    create_structure()

    print(
        """
Required OpenImages classes:

- Person
- Car
- Truck
- Bus
- Motorcycle
- Helmet
- Weapon objects

Supported formats:
- CSV annotations
- COCO JSON
- YOLO labels
"""
    )


if __name__ == "__main__":
    main()
