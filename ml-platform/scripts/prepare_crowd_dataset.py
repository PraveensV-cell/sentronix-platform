from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/crowd-detection")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-crowd-v1")

SPLITS = ["train", "valid", "test"]

print()
print("=" * 70)
print("SENTRONIX CROWD DATASET PREPARATION")
print("=" * 70)

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)

total_images = 0
total_labels = 0
total_objects = 0

for split in SPLITS:

    source_images = SOURCE / split / "images"
    source_labels = SOURCE / split / "labels"

    output_split = "val" if split == "valid" else split

    destination_images = OUTPUT / output_split / "images"
    destination_labels = OUTPUT / output_split / "labels"

    destination_images.mkdir(parents=True, exist_ok=True)
    destination_labels.mkdir(parents=True, exist_ok=True)

    images = [
        p
        for p in source_images.iterdir()
        if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]

    labels = list(source_labels.glob("*.txt"))

    split_objects = 0

    for image in images:
        shutil.copy2(image, destination_images / image.name)

    for label in labels:

        destination = destination_labels / label.name

        shutil.copy2(label, destination)

        content = label.read_text(encoding="utf-8").strip()

        if content:
            split_objects += len(content.splitlines())

    print()
    print(f"{split.upper()} images  : {len(images)}")
    print(f"{split.upper()} labels  : {len(labels)}")
    print(f"{split.upper()} objects : {split_objects}")

    total_images += len(images)
    total_labels += len(labels)
    total_objects += split_objects

data_yaml = OUTPUT / "data.yaml"

data_yaml.write_text(
    """train: ../train/images
val: ../val/images
test: ../test/images

nc: 1
names:
  - crowd
""",
    encoding="utf-8",
)

print()
print("---- TOTAL ----")
print(f"Total images  : {total_images}")
print(f"Total labels  : {total_labels}")
print(f"Total objects : {total_objects}")
print(f"Output        : {OUTPUT}")
print()
print("RESULT: CROWD DATASET PREPARATION COMPLETED")
print("=" * 70)
