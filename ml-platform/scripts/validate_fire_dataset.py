from pathlib import Path
from collections import Counter

from PIL import Image


IMAGE_DIR = Path("datasets/processed/sentronix-security-v1/images/train")

LABEL_DIR = Path("datasets/processed/sentronix-security-v1/labels/train")


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


SUPPORTED_IMAGES = {
    ".jpg",
    ".jpeg",
    ".png",
}


def validate_images() -> int:

    errors = 0

    print("\nChecking images...")

    if not IMAGE_DIR.exists():
        print("Image directory missing.")

        return 1

    for image in IMAGE_DIR.iterdir():
        if image.suffix.lower() not in SUPPORTED_IMAGES:
            continue

        try:
            img = Image.open(image)

            img.verify()

        except Exception:
            print(f"Corrupted image: {image}")

            errors += 1

    return errors


def validate_labels() -> tuple[int, Counter]:

    errors = 0

    classes = Counter()

    print("\nChecking labels...")

    if not LABEL_DIR.exists():
        print("Label directory missing.")

        return 1, classes

    for label in LABEL_DIR.glob("*.txt"):
        with open(
            label,
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()

        for line in lines:
            values = line.strip().split()

            if len(values) != 5:
                print(f"Invalid label format: {label}")

                errors += 1

                continue

            try:
                cls, x, y, w, h = map(
                    float,
                    values,
                )

            except ValueError:
                print(f"Invalid values: {label}")

                errors += 1

                continue

            class_id = int(cls)

            if class_id not in CLASS_NAMES:
                print(f"Invalid class {class_id}: {label}")

                errors += 1

            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                print(f"Invalid bounding box: {label}")

                errors += 1

            classes[class_id] += 1

    return errors, classes


def print_report(
    classes: Counter,
) -> None:

    print("\nClass Distribution")

    for class_id, count in sorted(classes.items()):
        name = CLASS_NAMES.get(
            class_id,
            "unknown",
        )

        print(f"{name}: {count}")


def main() -> None:

    print("Sentronix Dataset Validation")

    image_errors = validate_images()

    label_errors, classes = validate_labels()

    print_report(classes)

    total_errors = image_errors + label_errors

    print("\nValidation Completed")

    if total_errors == 0:
        print("Dataset Status: READY")

    else:
        print(f"Dataset Status: FAILED ({total_errors} errors)")


if __name__ == "__main__":
    main()
