from pathlib import Path
import json
from datetime import datetime
from collections import Counter


DATASET_DIR = Path("datasets/processed/sentronix-security-v1")


IMAGE_DIR = DATASET_DIR / "images"


LABEL_DIR = DATASET_DIR / "labels"


OUTPUT_FILE = DATASET_DIR / "metadata" / "dataset_info.json"


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


def create_output_directory():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def count_images():

    count = 0

    for image in IMAGE_DIR.rglob("*"):
        if image.suffix.lower() in (
            ".jpg",
            ".jpeg",
            ".png",
        ):
            count += 1

    return count


def analyze_labels():

    classes = Counter()

    total_labels = 0

    for label_file in LABEL_DIR.rglob("*.txt"):
        with open(
            label_file,
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()

        for line in lines:
            values = line.strip().split()

            if len(values) != 5:
                continue

            class_id = int(float(values[0]))

            classes[class_id] += 1

            total_labels += 1

    return (
        classes,
        total_labels,
    )


def create_metadata():

    classes, total_labels = analyze_labels()

    metadata = {
        "dataset_name": "Sentronix Security Dataset",
        "version": "v1.0",
        "created": datetime.now().isoformat(),
        "format": "YOLO",
        "images": count_images(),
        "labels": total_labels,
        "classes": {},
        "class_distribution": {},
    }

    for class_id, name in CLASS_NAMES.items():
        metadata["classes"][str(class_id)] = name

        metadata["class_distribution"][name] = classes.get(
            class_id,
            0,
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )


def main():

    print("Creating Sentronix dataset metadata...")

    create_output_directory()

    create_metadata()

    print("Metadata created:")

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
