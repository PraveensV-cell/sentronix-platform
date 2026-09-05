from pathlib import Path


WEAPON_DIR = Path("datasets/raw/weapon")


FOLDERS = [
    WEAPON_DIR / "images",
    WEAPON_DIR / "annotations",
]


def create_structure():

    print("Preparing weapon dataset structure...")

    for folder in FOLDERS:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def main():

    print("Sentronix Weapon Dataset Preparation")

    create_structure()

    print(
        """
Place weapon dataset files here:

datasets/raw/weapon/

├── images/
└── annotations/

After download we will convert
the annotation format to YOLO.
"""
    )


if __name__ == "__main__":
    main()
