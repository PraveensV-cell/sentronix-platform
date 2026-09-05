from pathlib import Path


SURVEILLANCE_DIR = Path("datasets/raw/surveillance")


FOLDERS = [
    SURVEILLANCE_DIR / "images",
    SURVEILLANCE_DIR / "annotations",
]


def create_structure():

    print("Preparing surveillance dataset structure...")

    for folder in FOLDERS:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def main():

    print("Sentronix Surveillance Dataset Preparation")

    create_structure()

    print(
        """
Place surveillance dataset files here:

datasets/raw/surveillance/

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
