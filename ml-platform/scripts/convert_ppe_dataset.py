from pathlib import Path
import shutil


SOURCE_DIR = Path("datasets/raw/safety")


OUTPUT_DIR = Path("datasets/processed/sentronix-security-v1")


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


PPE_CLASS_MAP = {
    "person": 0,
    "helmet": 1,
    "safety_vest": 2,
}


def create_output_structure() -> None:
    """
    Create Sentronix PPE output structure.
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
    Find PPE dataset images.
    """

    images = []

    for image in SOURCE_DIR.rglob("*"):
        if image.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(image)

    return images


def copy_images(
    images: list[Path],
) -> None:
    """
    Copy PPE images into Sentronix dataset.
    """

    destination = OUTPUT_DIR / "images/train"

    for image in images:
        shutil.copy2(
            image,
            destination / image.name,
        )

        print(f"Copied: {image.name}")


def main() -> None:

    print("Starting PPE Dataset Conversion")

    create_output_structure()

    images = find_images()

    print(f"PPE images found: {len(images)}")

    copy_images(images)

    print("PPE conversion completed")


if __name__ == "__main__":
    main()
