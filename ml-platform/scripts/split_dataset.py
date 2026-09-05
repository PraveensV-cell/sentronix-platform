from pathlib import Path
import random
import shutil


SOURCE_IMAGES = Path("datasets/processed/sentronix-security-v1/final/images/train")


SOURCE_LABELS = Path("datasets/processed/sentronix-security-v1/final/labels/train")


OUTPUT_ROOT = Path("datasets/processed/sentronix-security-v1")


SPLITS = {
    "train": 0.7,
    "val": 0.2,
    "test": 0.1,
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


RANDOM_SEED = 42


def create_directories():

    for split in SPLITS:
        (OUTPUT_ROOT / "images" / split).mkdir(
            parents=True,
            exist_ok=True,
        )

        (OUTPUT_ROOT / "labels" / split).mkdir(
            parents=True,
            exist_ok=True,
        )


def get_images():

    images = []

    for file in SOURCE_IMAGES.iterdir():
        if file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file)

    return images


def copy_file(
    source,
    destination,
):

    shutil.copy2(
        source,
        destination,
    )


def split_dataset():

    images = get_images()

    print(f"Total images: {len(images)}")

    random.seed(RANDOM_SEED)

    random.shuffle(images)

    total = len(images)

    train_end = int(total * 0.7)

    val_end = int(total * 0.9)

    split_data = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:],
    }

    for split, files in split_data.items():
        print(f"{split}: {len(files)}")

        for image in files:
            label = SOURCE_LABELS / f"{image.stem}.txt"

            image_output = OUTPUT_ROOT / "images" / split / image.name

            label_output = OUTPUT_ROOT / "labels" / split / label.name

            copy_file(
                image,
                image_output,
            )

            if label.exists():
                copy_file(
                    label,
                    label_output,
                )


def main():

    print("Sentronix Dataset Split")

    create_directories()

    split_dataset()

    print("Dataset split completed")


if __name__ == "__main__":
    main()
