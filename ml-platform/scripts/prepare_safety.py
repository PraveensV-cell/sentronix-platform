from pathlib import Path


SAFETY_DIR = Path("datasets/raw/safety")


FOLDERS = [
    SAFETY_DIR / "images",
    SAFETY_DIR / "annotations",
]


def create_structure():

    print("Preparing safety dataset structure...")

    for folder in FOLDERS:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def main():

    print("Sentronix Safety Dataset Preparation")

    create_structure()

    print(
        """
Place safety dataset files here:

datasets/raw/safety/

├── images/
└── annotations/

Supported formats:
- YOLO
- COCO JSON
- Pascal VOC XML
"""
    )


if __name__ == "__main__":
    main()
