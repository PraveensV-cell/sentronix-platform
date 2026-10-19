from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/traditional-dress")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-traditional-dress-v1")

CLASS_NAMES = ["female dress", "male dress"]
SPLITS = {
    "train": "train",
    "valid": "val",
    "test": "test",
}


def convert_polygon_to_bbox(parts):
    values = [float(v) for v in parts[1:]]

    if len(values) < 6 or len(values) % 2 != 0:
        return None

    xs = values[0::2]
    ys = values[1::2]

    xmin = max(0.0, min(1.0, min(xs)))
    xmax = max(0.0, min(1.0, max(xs)))
    ymin = max(0.0, min(1.0, min(ys)))
    ymax = max(0.0, min(1.0, max(ys)))

    if xmax <= xmin or ymax <= ymin:
        return None

    x_center = (xmin + xmax) / 2.0
    y_center = (ymin + ymax) / 2.0
    width = xmax - xmin
    height = ymax - ymin

    return (
        int(parts[0]),
        x_center,
        y_center,
        width,
        height,
    )


def format_bbox(class_id, x, y, w, h):
    return f"{class_id} {x:.10f} {y:.10f} {w:.10f} {h:.10f}"


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    total_objects = 0
    polygons_converted = 0
    empty_labels = 0
    invalid = 0
    class_counts = {0: 0, 1: 0}

    for source_split, output_split in SPLITS.items():
        source_images = SOURCE / source_split / "images"
        source_labels = SOURCE / source_split / "labels"

        output_images = OUTPUT / output_split / "images"
        output_labels = OUTPUT / output_split / "labels"

        output_images.mkdir(parents=True, exist_ok=True)
        output_labels.mkdir(parents=True, exist_ok=True)

        image_files = [p for p in source_images.iterdir() if p.is_file()]

        for image_path in image_files:
            shutil.copy2(image_path, output_images / image_path.name)

        for label_path in source_labels.glob("*.txt"):
            output_label = output_labels / label_path.name
            text = label_path.read_text(errors="ignore").strip()

            if not text:
                output_label.write_text("")
                empty_labels += 1
                continue

            converted = []

            for line in text.splitlines():
                parts = line.split()

                if not parts:
                    continue

                try:
                    class_id = int(parts[0])
                except ValueError:
                    invalid += 1
                    continue

                if class_id not in range(len(CLASS_NAMES)):
                    invalid += 1
                    continue

                bbox = convert_polygon_to_bbox(parts)

                if bbox is None:
                    invalid += 1
                    continue

                cid, x, y, w, h = bbox

                converted.append(format_bbox(cid, x, y, w, h))

                total_objects += 1
                polygons_converted += 1
                class_counts[cid] += 1

            output_label.write_text("\n".join(converted) + ("\n" if converted else ""))

    yaml_text = """train: ../train/images
val: ../val/images
test: ../test/images

nc: 2
names:
  - female dress
  - male dress
"""

    (OUTPUT / "data.yaml").write_text(yaml_text)

    print("=" * 70)
    print("SENTRONIX TRADITIONAL DRESS DATASET PREPARATION")
    print("=" * 70)
    print()
    print(f"Polygons converted : {polygons_converted}")
    print(f"Total objects      : {total_objects}")
    print(f"Empty labels       : {empty_labels}")
    print(f"Invalid            : {invalid}")
    print(f"Class counts       : {class_counts}")
    print(f"Output             : {OUTPUT}")
    print()
    print("RESULT: TRADITIONAL DRESS DATASET PREPARATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
