from pathlib import Path
from PIL import Image
from collections import Counter


IMAGE_DIR = Path("datasets/processed/sentronix-security-v1/images/train")


LABEL_DIR = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_NAMES = {
    0: "person",
    1: "vehicle",
}


def validate_images() -> int:
    """
    Check image integrity.
    """

    errors = 0

    print("\nChecking images...")

    for image in IMAGE_DIR.glob("*"):
        try:
            img = Image.open(image)

            img.verify()

        except Exception:
            print(f"Corrupted image: {image}")

            errors += 1

    return errors


def validate_labels() -> tuple[int, Counter]:
    """
    Validate YOLO labels.
    """

    errors = 0

    counter = Counter()

    print("\nChecking labels...")

    for label_file in LABEL_DIR.glob("*.txt"):
        with label_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()

        for line in lines:
            values = line.strip().split()

            if len(values) != 5:
                print(f"Invalid label: {label_file}")

                errors += 1

                continue

            cls, x, y, w, h = map(
                float,
                values,
            )

            if int(cls) not in CLASS_NAMES:
                print(f"Invalid class: {label_file}")

                errors += 1

            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                print(f"Invalid bbox: {label_file}")

                errors += 1

            counter[int(cls)] += 1

    return errors, counter


def report(
    counter: Counter,
) -> None:

    print("\nClass Distribution")

    for class_id, count in counter.items():
        print(f"{CLASS_NAMES[class_id]}: {count}")


def main():

    print("Sentronix COCO Dataset Validation")

    image_errors = validate_images()

    label_errors, stats = validate_labels()

    report(stats)

    total = image_errors + label_errors

    print("\nValidation Complete")

    if total == 0:
        print("Dataset Status: READY")

    else:
        print(f"Dataset Status: FAILED ({total})")


if __name__ == "__main__":
    main()
