from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/dress-code")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-dress-v1")

CLASSES = [
    "Casual",
    "Formal",
    "Other",
    "Streetwear",
    "athletic wear",
]

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)

bbox_count = 0
polygon_count = 0
empty_count = 0
object_count = 0

for split in ["train", "valid", "test"]:
    source_images = SOURCE / split / "images"
    source_labels = SOURCE / split / "labels"

    output_split = "val" if split == "valid" else split

    output_images = OUTPUT / output_split / "images"
    output_labels = OUTPUT / output_split / "labels"

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    for image in source_images.iterdir():
        if image.is_file():
            shutil.copy2(image, output_images / image.name)

    for label in source_labels.glob("*.txt"):
        output_label = output_labels / label.name
        lines = label.read_text(errors="ignore").splitlines()

        valid_lines = []

        for line in lines:
            parts = line.split()

            if not parts:
                continue

            class_id = int(parts[0])
            values = [float(v) for v in parts[1:]]

            if len(values) == 4:
                x, y, w, h = values

                valid_lines.append(f"{class_id} {x:.10f} {y:.10f} {w:.10f} {h:.10f}")

                bbox_count += 1
                object_count += 1

            elif len(values) >= 6 and len(values) % 2 == 0:
                xs = values[0::2]
                ys = values[1::2]

                xmin = max(0.0, min(1.0, min(xs)))
                xmax = max(0.0, min(1.0, max(xs)))
                ymin = max(0.0, min(1.0, min(ys)))
                ymax = max(0.0, min(1.0, max(ys)))

                x_center = (xmin + xmax) / 2
                y_center = (ymin + ymax) / 2
                width = xmax - xmin
                height = ymax - ymin

                valid_lines.append(
                    f"{class_id} {x_center:.10f} {y_center:.10f} {width:.10f} {height:.10f}"
                )

                polygon_count += 1
                object_count += 1

        if not valid_lines:
            empty_count += 1

        output_label.write_text("\n".join(valid_lines) + ("\n" if valid_lines else ""))

yaml_text = """train: ../train/images
val: ../val/images
test: ../test/images

nc: 5
names:
  - Casual
  - Formal
  - Other
  - Streetwear
  - athletic wear
"""

(OUTPUT / "data.yaml").write_text(yaml_text)

print("=" * 70)
print("SENTRONIX DRESS CODE DATASET PREPARATION")
print("=" * 70)
print()
print("Bounding boxes converted/preserved :", bbox_count)
print("Polygons converted                :", polygon_count)
print("Total objects                     :", object_count)
print("Empty labels                      :", empty_count)
print("Output                            :", OUTPUT)
print()
print("RESULT: DRESS CODE DATASET PREPARATION COMPLETED")
print("=" * 70)
