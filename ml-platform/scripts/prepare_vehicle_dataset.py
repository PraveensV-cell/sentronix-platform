from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/vehicle-detection")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-vehicle-v1")

CLASS_NAMES = [
    "Autorickshaw",
    "Bicycle",
    "Bus",
    "Car",
    "Motorcycle",
    "Truck",
]


def process_split(split):
    source_images = SOURCE / split / "images"
    source_labels = SOURCE / split / "labels"

    output_images = OUTPUT / split / "images"
    output_labels = OUTPUT / split / "labels"

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    image_count = 0
    label_count = 0
    object_count = 0

    for image in sorted(source_images.iterdir()):
        if not image.is_file():
            continue

        destination_image = output_images / image.name
        shutil.copy2(image, destination_image)

        image_count += 1

        source_label = source_labels / f"{image.stem}.txt"
        destination_label = output_labels / f"{image.stem}.txt"

        if not source_label.exists():
            raise FileNotFoundError(f"Missing label for image: {image}")

        lines = source_label.read_text(encoding="utf-8").splitlines()

        valid_lines = []

        for line in lines:
            text = line.strip()

            if not text:
                continue

            parts = text.split()

            if len(parts) != 5:
                raise ValueError(f"Invalid YOLO annotation in {source_label}: {text}")

            class_id = int(parts[0])

            if class_id < 0 or class_id >= len(CLASS_NAMES):
                raise ValueError(f"Invalid class ID in {source_label}: {class_id}")

            values = [float(value) for value in parts[1:]]

            cx, cy, width, height = values

            if not (
                0 <= cx <= 1 and 0 <= cy <= 1 and 0 < width <= 1 and 0 < height <= 1
            ):
                raise ValueError(f"Invalid coordinates in {source_label}: {text}")

            valid_lines.append(f"{class_id} {cx:.8f} {cy:.8f} {width:.8f} {height:.8f}")

            object_count += 1

        destination_label.write_text(
            "\n".join(valid_lines) + "\n",
            encoding="utf-8",
        )

        label_count += 1

    return image_count, label_count, object_count


def write_yaml():
    content = f"""path: {OUTPUT.as_posix()}
train: train/images
val: valid/images
test: test/images

nc: {len(CLASS_NAMES)}

names: {CLASS_NAMES}
"""

    (OUTPUT / "data.yaml").write_text(
        content,
        encoding="utf-8",
    )


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source dataset not found: {SOURCE}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print("SENTRONIX VEHICLE DATASET PREPARATION")
    print("=" * 70)
    print()

    total_images = 0
    total_labels = 0
    total_objects = 0

    for split in ["train", "valid", "test"]:
        images, labels, objects = process_split(split)

        total_images += images
        total_labels += labels
        total_objects += objects

        print(f"{split:>8} images  : {images}")
        print(f"{split:>8} labels  : {labels}")
        print(f"{split:>8} objects : {objects}")
        print()

    write_yaml()

    print("-" * 70)
    print(f"Total images  : {total_images}")
    print(f"Total labels  : {total_labels}")
    print(f"Total objects : {total_objects}")
    print(f"Output        : {OUTPUT}")
    print()
    print("RESULT: VEHICLE DATASET PREPARATION COMPLETED")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
