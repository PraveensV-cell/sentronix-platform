from pathlib import Path
import shutil


SOURCE_DATASETS = [
    Path("datasets/processed/sentronix-security-v1/images/train"),
]


SOURCE_LABELS = [
    Path("datasets/processed/sentronix-security-v1/labels/train"),
]


FINAL_IMAGES = Path("datasets/processed/sentronix-security-v1/final/images/train")


FINAL_LABELS = Path("datasets/processed/sentronix-security-v1/final/labels/train")


def create_directories():

    FINAL_IMAGES.mkdir(
        parents=True,
        exist_ok=True,
    )

    FINAL_LABELS.mkdir(
        parents=True,
        exist_ok=True,
    )


def copy_files(
    source,
    destination,
):

    count = 0

    for file in source.iterdir():
        if file.is_file():
            shutil.copy2(
                file,
                destination / file.name,
            )

            count += 1

    return count


def merge_images():

    total = 0

    for dataset in SOURCE_DATASETS:
        if not dataset.exists():
            continue

        total += copy_files(
            dataset,
            FINAL_IMAGES,
        )

    return total


def merge_labels():

    total = 0

    for dataset in SOURCE_LABELS:
        if not dataset.exists():
            continue

        total += copy_files(
            dataset,
            FINAL_LABELS,
        )

    return total


def main():

    print("Sentronix Dataset Merge Started")

    create_directories()

    images = merge_images()

    labels = merge_labels()

    print(f"Images merged: {images}")

    print(f"Labels merged: {labels}")

    print("Dataset merge completed")


if __name__ == "__main__":
    main()
