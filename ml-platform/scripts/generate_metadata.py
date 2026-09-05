from pathlib import Path
import json
from collections import Counter


DATASET_DIR = Path("datasets/processed/sentronix-security-v1")


IMAGE_DIR = DATASET_DIR / "images"


LABEL_DIR = DATASET_DIR / "labels"


METADATA_DIR = DATASET_DIR / "metadata"


CLASS_NAMES = {
    0: "person",
    1: "vehicle",
    2: "fire",
    3: "smoke",
    4: "weapon",
    5: "helmet",
    6: "safety_vest",
    7: "restricted_object",
}


def create_directory():

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def count_images():

    count = 0

    for file in IMAGE_DIR.rglob("*"):
        if file.suffix.lower() in (
            ".jpg",
            ".jpeg",
            ".png",
        ):
            count += 1

    return count


def count_labels():

    count = 0

    for file in LABEL_DIR.rglob("*.txt"):
        count += 1

    return count


def calculate_class_distribution():

    counter = Counter()

    for label_file in LABEL_DIR.rglob("*.txt"):
        with open(
            label_file,
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                values = line.split()

                if len(values) != 5:
                    continue

                class_id = int(values[0])

                counter[CLASS_NAMES[class_id]] += 1

    return dict(counter)


def save_metadata():

    metadata = {
        "dataset": "sentronix-security-v1",
        "version": "1.0.0",
        "images": count_images(),
        "labels": count_labels(),
        "classes": CLASS_NAMES,
    }

    with open(
        METADATA_DIR / "dataset_info.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )


def save_distribution():

    distribution = calculate_class_distribution()

    with open(
        METADATA_DIR / "class_distribution.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            distribution,
            file,
            indent=4,
        )


def save_version():

    with open(
        METADATA_DIR / "version.txt",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("sentronix-security-v1\n")

        file.write("Version: 1.0.0")


def main():

    print("Generating dataset metadata...")

    create_directory()

    save_metadata()

    save_distribution()

    save_version()

    print("Metadata generation completed.")


if __name__ == "__main__":
    main()
