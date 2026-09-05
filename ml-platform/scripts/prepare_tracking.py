from pathlib import Path


TRACKING_DIR = Path("datasets/raw/tracking")


FOLDERS = [
    TRACKING_DIR / "images",
    TRACKING_DIR / "annotations",
    TRACKING_DIR / "tracking",
]


def create_structure():

    print("Preparing tracking dataset structure...")

    for folder in FOLDERS:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def main():

    print("Sentronix Tracking Dataset Preparation")

    create_structure()

    print(
        """
Place tracking dataset files here:

datasets/raw/tracking/

├── images/
├── annotations/
└── tracking/

Supported formats:
- MOT format
- COCO tracking JSON
- YOLO tracking format
"""
    )


if __name__ == "__main__":
    main()
