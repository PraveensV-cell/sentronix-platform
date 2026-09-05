from pathlib import Path
import shutil


SOURCE_DIR = Path("datasets/raw/weapon")


OUTPUT_DIR = Path("datasets/processed/sentronix-security-v1")


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


WEAPON_CLASS_MAP = {
    "person": 0,
    "gun": 1,
    "handgun": 1,
    "knife": 2,
    "rifle": 3,
    "weapon": 4,
}


def create_output_structure() -> None:
    """
    Create Sentronix weapon dataset folders.
    """

    folders = [
        OUTPUT_DIR / "images/train",
        OUTPUT_DIR / "labels/train",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def find_images() -> list[Path]:
    """
    Find weapon dataset images.
    """

    images: list[Path] = []

    for image in SOURCE_DIR.rglob("*"):
        if image.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(image)

    return images


def copy_images(
    images: list[Path],
) -> None:
    """
    Copy images into Sentronix dataset.
    """

    destination = OUTPUT_DIR / "images/train"

    for image in images:
        shutil.copy2(
            image,
            destination / image.name,
        )

        print(f"Copied: {image.name}")


def main() -> None:

    print("Starting Weapon Dataset Conversion")

    create_output_structure()

    images = find_images()

    print(f"Weapon images found: {len(images)}")

    copy_images(images)

    print("Weapon conversion completed")


if __name__ == "__main__":
    main()
