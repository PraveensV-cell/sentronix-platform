from pathlib import Path
import hashlib


SOURCE_DIR = Path("datasets/downloads")


OUTPUT_DIR = Path("datasets/sentronix-security-v1")


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def create_output_structure() -> None:
    """
    Create Sentronix dataset directory structure.
    """

    folders = [
        OUTPUT_DIR / "images/train",
        OUTPUT_DIR / "images/val",
        OUTPUT_DIR / "images/test",
        OUTPUT_DIR / "labels/train",
        OUTPUT_DIR / "labels/val",
        OUTPUT_DIR / "labels/test",
        OUTPUT_DIR / "metadata",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {folder}")


def calculate_hash(
    file_path: Path,
) -> str:
    """
    Generate file hash for duplicate detection.
    """

    hash_object = hashlib.md5()

    with file_path.open(
        "rb",
    ) as file:
        for chunk in iter(
            lambda: file.read(4096),
            b"",
        ):
            hash_object.update(chunk)

    return hash_object.hexdigest()


def find_images() -> list[Path]:
    """
    Find all supported image files.
    """

    images: list[Path] = []

    if not SOURCE_DIR.exists():
        print("Source dataset directory not found.")

        return images

    for file in SOURCE_DIR.rglob("*"):
        if file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file)

    return images


def remove_duplicates(
    images: list[Path],
) -> list[Path]:
    """
    Remove duplicate images using file hash.
    """

    unique_hashes: set[str] = set()

    clean_images: list[Path] = []

    for image in images:
        file_hash = calculate_hash(image)

        if file_hash not in unique_hashes:
            unique_hashes.add(file_hash)

            clean_images.append(image)

    return clean_images


def main() -> None:
    """
    Dataset preparation pipeline entry point.
    """

    print("Starting Sentronix dataset preparation...")

    create_output_structure()

    images = find_images()

    print(f"Images found: {len(images)}")

    clean_images = remove_duplicates(images)

    print(f"Images after duplicate removal: {len(clean_images)}")

    print("Dataset preparation completed.")


if __name__ == "__main__":
    main()
