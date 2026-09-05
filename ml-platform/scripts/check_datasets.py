from pathlib import Path


DATASET_ROOT = Path("datasets/raw")


DATASETS = [
    "coco",
    "fire",
    "weapon",
    "safety",
    "surveillance",
    "tracking",
    "openimages",
]


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


ANNOTATION_EXTENSIONS = {
    ".txt",
    ".xml",
    ".json",
    ".csv",
}


def count_files(
    folder,
    extensions,
):

    if not folder.exists():
        return 0

    count = 0

    for file in folder.rglob("*"):
        if file.suffix.lower() in extensions:
            count += 1

    return count


def check_dataset(
    name,
):

    dataset_path = DATASET_ROOT / name

    print(f"\n{name.upper()}")

    if not dataset_path.exists():
        print("❌ Folder missing")

        return

    images = count_files(
        dataset_path,
        IMAGE_EXTENSIONS,
    )

    annotations = count_files(
        dataset_path,
        ANNOTATION_EXTENSIONS,
    )

    print(f"Location: {dataset_path}")

    print(f"Images: {images}")

    print(f"Annotations: {annotations}")

    if images == 0:
        print("⚠ No images found")

    if annotations == 0:
        print("⚠ No annotations found")


def main():

    print("Sentronix Dataset Verification")

    for dataset in DATASETS:
        check_dataset(dataset)

    print("\nDataset verification completed.")


if __name__ == "__main__":
    main()
