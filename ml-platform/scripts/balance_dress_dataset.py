import random
import shutil
from pathlib import Path


random.seed(42)


source = Path("ml-platform/datasets/processed/sentronix-dress-code-v2")

output = Path("ml-platform/datasets/processed/sentronix-dress-code-v4")


# Maximum traditional images in train
MAX_TRADITIONAL_IMAGES = 2500


# source folder -> output folder
splits = {"train": "train", "valid": "val", "test": "test"}


# Create output folders
for source_split, output_split in splits.items():

    (output / output_split / "images").mkdir(parents=True, exist_ok=True)

    (output / output_split / "labels").mkdir(parents=True, exist_ok=True)


# Process datasets
for source_split, output_split in splits.items():

    print("\nProcessing:", source_split)

    label_dir = source / source_split / "labels"
    image_dir = source / source_split / "images"

    if not label_dir.exists():
        print("Missing:", label_dir)
        continue

    labels = list(label_dir.glob("*.txt"))

    traditional = []
    others = []

    # Separate traditional and other classes
    for label in labels:

        classes = set()

        with open(label, "r") as f:

            for line in f:

                if line.strip():

                    classes.add(line.split()[0])

        if "3" in classes:

            traditional.append(label)

        else:

            others.append(label)

    # Reduce only training traditional images
    if source_split == "train":

        traditional = random.sample(
            traditional, min(MAX_TRADITIONAL_IMAGES, len(traditional))
        )

    selected = others + traditional

    # Copy images and labels
    copied = 0

    for label in selected:

        images = list(image_dir.glob(label.stem + ".*"))

        if not images:
            continue

        image = images[0]

        shutil.copy(image, output / output_split / "images" / image.name)

        shutil.copy(label, output / output_split / "labels" / label.name)

        copied += 1

    print(output_split, "images:", copied)


print("\nBALANCE COMPLETE")
