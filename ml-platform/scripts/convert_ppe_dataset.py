from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/ppe")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-ppe-v1")

CLASS_NAMES = [
    "boots",
    "gloves",
    "goggles",
    "helmet",
    "no-boots",
    "no-gloves",
    "no-goggles",
    "no-helmet",
    "no-vest",
    "vest",
]


def polygon_to_bbox(parts):
    class_id = int(parts[0])
    coordinates = [float(value) for value in parts[1:]]

    xs = coordinates[0::2]
    ys = coordinates[1::2]

    xmin = min(xs)
    xmax = max(xs)
    ymin = min(ys)
    ymax = max(ys)

    center_x = (xmin + xmax) / 2.0
    center_y = (ymin + ymax) / 2.0
    width = xmax - xmin
    height = ymax - ymin

    return f"{class_id} {center_x:.8f} {center_y:.8f} {width:.8f} {height:.8f}"


def convert_label(source_label, output_label):
    output_lines = []

    for raw_line in source_label.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) == 5:
            output_lines.append(" ".join(parts))
            continue

        if len(parts) > 5:
            output_lines.append(polygon_to_bbox(parts))
            continue

        raise ValueError(f"Invalid annotation format in {source_label}: {line}")

    output_label.parent.mkdir(parents=True, exist_ok=True)
    output_label.write_text(
        "\n".join(output_lines) + "\n",
        encoding="utf-8",
    )


def process_split(split):
    source_images = SOURCE / split / "images"
    source_labels = SOURCE / split / "labels"

    output_images = OUTPUT / split / "images"
    output_labels = OUTPUT / split / "labels"

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    image_count = 0
    label_count = 0
    polygon_count = 0
    bbox_count = 0

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

        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) == 5:
                bbox_count += 1
            elif len(parts) > 5:
                polygon_count += 1

        convert_label(source_label, destination_label)
        label_count += 1

    return (
        image_count,
        label_count,
        bbox_count,
        polygon_count,
    )


def write_yaml():
    yaml_content = f"""path: {OUTPUT.as_posix()}
train: train/images
val: valid/images
test: test/images

nc: {len(CLASS_NAMES)}

names: {CLASS_NAMES}
"""

    (OUTPUT / "data.yaml").write_text(
        yaml_content,
        encoding="utf-8",
    )


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source dataset not found: {SOURCE}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    total_images = 0
    total_labels = 0
    total_boxes = 0
    total_polygons = 0

    print()
    print("=" * 70)
    print("SENTRONIX PPE DATASET CONVERSION")
    print("=" * 70)
    print()

    for split in ["train", "valid", "test"]:
        images, labels, boxes, polygons = process_split(split)

        total_images += images
        total_labels += labels
        total_boxes += boxes
        total_polygons += polygons

        print(f"{split:>8} images   : {images}")
        print(f"{split:>8} labels   : {labels}")
        print(f"{split:>8} bboxes   : {boxes}")
        print(f"{split:>8} polygons : {polygons}")
        print()

    write_yaml()

    print("-" * 70)
    print(f"Total images             : {total_images}")
    print(f"Total labels             : {total_labels}")
    print(f"Existing bbox annotations: {total_boxes}")
    print(f"Polygon annotations      : {total_polygons}")
    print(f"Output dataset           : {OUTPUT}")
    print()
    print("RESULT: PPE DATASET CONVERSION COMPLETED")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
