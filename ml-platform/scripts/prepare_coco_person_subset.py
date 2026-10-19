import json
import random
import shutil
from pathlib import Path

ROOT = Path("ml-platform/datasets/raw/coco")
TRAIN_IMAGES = ROOT / "train2017"
ANNOTATIONS = ROOT / "annotations" / "instances_train2017.json"

OUTPUT = Path("ml-platform/datasets/processed/sentronix-coco-person-v1")

TARGET_IMAGES = 13000
SEED = 42

print()
print("=" * 70)
print("SENTRONIX COCO PERSON SUBSET")
print("=" * 70)

print()
print("Loading COCO annotations...")

with ANNOTATIONS.open("r", encoding="utf-8") as f:
    data = json.load(f)

categories = {category["id"]: category["name"] for category in data["categories"]}

person_category_id = next(
    category_id for category_id, name in categories.items() if name == "person"
)

person_image_ids = {
    annotation["image_id"]
    for annotation in data["annotations"]
    if annotation["category_id"] == person_category_id
}

images_by_id = {image["id"]: image for image in data["images"]}

person_images = [
    images_by_id[image_id] for image_id in person_image_ids if image_id in images_by_id
]

print(f"COCO images available       : {len(data['images'])}")
print(f"Images containing person    : {len(person_images)}")
print(f"Requested subset            : {TARGET_IMAGES}")

random.seed(SEED)
random.shuffle(person_images)

selected_images = person_images[:TARGET_IMAGES]

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)

train_images_out = OUTPUT / "train" / "images"
train_labels_out = OUTPUT / "train" / "labels"

train_images_out.mkdir(parents=True, exist_ok=True)
train_labels_out.mkdir(parents=True, exist_ok=True)

annotations_by_image = {}

for annotation in data["annotations"]:
    if annotation["category_id"] != person_category_id:
        continue

    annotations_by_image.setdefault(annotation["image_id"], []).append(annotation)

copied = 0
missing = 0
objects = 0

for image in selected_images:

    image_id = image["id"]
    file_name = image["file_name"]

    source_image = TRAIN_IMAGES / file_name
    destination_image = train_images_out / file_name

    if not source_image.exists():
        missing += 1
        continue

    shutil.copy2(source_image, destination_image)

    label_file = train_labels_out / (Path(file_name).stem + ".txt")

    width = image["width"]
    height = image["height"]

    lines = []

    for annotation in annotations_by_image.get(image_id, []):

        x, y, w, h = annotation["bbox"]

        if w <= 0 or h <= 0:
            continue

        x_center = (x + w / 2) / width
        y_center = (y + h / 2) / height

        normalized_width = w / width
        normalized_height = h / height

        if not (
            0 <= x_center <= 1
            and 0 <= y_center <= 1
            and 0 < normalized_width <= 1
            and 0 < normalized_height <= 1
        ):
            continue

        lines.append(
            f"0 {x_center:.6f} {y_center:.6f} "
            f"{normalized_width:.6f} {normalized_height:.6f}"
        )

    if lines:
        label_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        objects += len(lines)

    copied += 1

data_yaml = OUTPUT / "data.yaml"

data_yaml.write_text(
    """train: ../train/images

nc: 1
names:
  - person
""",
    encoding="utf-8",
)

print()
print("---- RESULT ----")
print(f"Selected images             : {len(selected_images)}")
print(f"Copied images               : {copied}")
print(f"Missing source images       : {missing}")
print(f"Person bounding boxes       : {objects}")
print(f"Output                      : {OUTPUT}")
print()
print("RESULT: COCO PERSON SUBSET CREATED")
print("=" * 70)
