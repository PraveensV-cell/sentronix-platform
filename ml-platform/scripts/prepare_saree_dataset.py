from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/saree")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-saree-v1")

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)

object_count = 0
empty_count = 0

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

                object_count += 1

        if not valid_lines:
            empty_count += 1

        output_label = output_labels / label.name

        output_label.write_text("\n".join(valid_lines) + ("\n" if valid_lines else ""))

yaml_text = """train: ../train/images
val: ../val/images
test: ../test/images

nc: 3
names:
  - clothes
  - dress
  - sarees
"""

(OUTPUT / "data.yaml").write_text(yaml_text)

print("=" * 70)
print("SENTRONIX SAREE DATASET PREPARATION")
print("=" * 70)
print()
print("Total objects :", object_count)
print("Empty labels  :", empty_count)
print("Output        :", OUTPUT)
print()
print("RESULT: SAREE DATASET PREPARATION COMPLETED")
print("=" * 70)
