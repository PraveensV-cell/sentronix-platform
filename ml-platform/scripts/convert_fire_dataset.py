from pathlib import Path
import shutil


SOURCE_DIR = Path("datasets/raw/fire")


OUTPUT_DIR = Path("datasets/processed/sentronix-security-v1")


FIRE_CLASS = {
    "fire": 2,
    "smoke": 3,
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def create_output():

    folders = [
        OUTPUT_DIR / "images/train",
        OUTPUT_DIR / "labels/train",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def find_images():

    images = []

    for image in SOURCE_DIR.rglob("*"):
        if image.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(image)

    return images


def copy_images(
    images: list[Path],
):

    destination = OUTPUT_DIR / "images/train"

    for image in images:
        shutil.copy2(
            image,
            destination / image.name,
        )

        print(f"Copied {image.name}")


def main():

    print("Starting Fire Dataset Conversion")

    create_output()

    images = find_images()

    print(f"Found fire images: {len(images)}")

    copy_images(images)

    print("Fire dataset conversion completed")


if __name__ == "__main__":
    main()
