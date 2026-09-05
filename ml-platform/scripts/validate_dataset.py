from pathlib import Path


IMAGE_DIR = Path("datasets/processed/sentronix-security-v1/final/images/train")


LABEL_DIR = Path("datasets/processed/sentronix-security-v1/final/labels/train")


CLASS_COUNT = 8


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def check_images():

    images = []

    for file in IMAGE_DIR.iterdir():
        if file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file)

    return images


def validate_label(label_file):

    errors = []

    with open(
        label_file,
        "r",
        encoding="utf-8",
    ) as file:
        lines = file.readlines()

    if not lines:
        errors.append("Empty label")

        return errors

    for line_number, line in enumerate(lines, 1):
        values = line.strip().split()

        if len(values) != 5:
            errors.append(f"Line {line_number}: Invalid format")

            continue

        try:
            class_id = int(values[0])

            bbox = [float(value) for value in values[1:]]

        except ValueError:
            errors.append(f"Line {line_number}: Non numeric value")

            continue

        if class_id < 0 or class_id >= CLASS_COUNT:
            errors.append(f"Line {line_number}: Invalid class {class_id}")

        for value in bbox:
            if value < 0 or value > 1:
                errors.append(f"Line {line_number}: Invalid bbox")

    return errors


def validate_dataset():

    print("Sentronix Dataset Validation")

    images = check_images()

    print(f"Images found: {len(images)}")

    missing_labels = 0

    invalid_labels = 0

    empty_labels = 0

    for image in images:
        label_file = LABEL_DIR / f"{image.stem}.txt"

        if not label_file.exists():
            missing_labels += 1

            continue

        errors = validate_label(label_file)

        if errors:
            invalid_labels += 1

            if "Empty label" in errors:
                empty_labels += 1

    print(f"Missing labels: {missing_labels}")

    print(f"Invalid labels: {invalid_labels}")

    print(f"Empty labels: {empty_labels}")

    if missing_labels == 0 and invalid_labels == 0:
        print("Dataset validation PASSED")

    else:
        print("Dataset validation FAILED")


def main():

    validate_dataset()


if __name__ == "__main__":
    main()
