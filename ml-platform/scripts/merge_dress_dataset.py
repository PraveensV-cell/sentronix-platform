import shutil
from pathlib import Path

# Source datasets
datasets = [
    {
        "name": "clothing",
        "path": Path("ml-platform/datasets/raw/dress-code"),
        "mapping": {
            0: 0,  # Casual -> college_casual
            1: 1,  # Formal -> formal_wear
            4: 2,  # athletic wear -> sports_wear
        },
    },
    {
        "name": "saree",
        "path": Path("ml-platform/datasets/raw/saree"),
        "mapping": {2: 4},  # sarees -> saree
    },
    {
        "name": "traditional",
        "path": Path("ml-platform/datasets/raw/traditional-dress"),
        "mapping": {
            0: 3,  # female dress -> traditional
            1: 3,  # male dress -> traditional
        },
    },
]


output = Path("ml-platform/datasets/processed/sentronix-dress-code-v1")


splits = {"train": "train", "valid": "val", "test": "test"}


for split_src, split_dst in splits.items():
    (output / split_dst / "images").mkdir(parents=True, exist_ok=True)
    (output / split_dst / "labels").mkdir(parents=True, exist_ok=True)


counter = 0


for dataset in datasets:
    print("Processing:", dataset["name"])

    for split_src, split_dst in splits.items():
        img_dir = dataset["path"] / split_src / "images"
        label_dir = dataset["path"] / split_src / "labels"

        if not img_dir.exists():
            continue

        for img in img_dir.iterdir():
            if img.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            label = label_dir / (img.stem + ".txt")

            if not label.exists():
                continue

            new_name = f"{dataset['name']}_{counter}"

            # copy image
            shutil.copy(img, output / split_dst / "images" / f"{new_name}{img.suffix}")

            # convert labels
            new_labels = []

            with open(label, "r") as f:
                lines = f.readlines()

            for line in lines:
                values = line.strip().split()

                if len(values) < 5:
                    continue

                old_class = int(values[0])

                if old_class in dataset["mapping"]:
                    new_class = dataset["mapping"][old_class]

                    values[0] = str(new_class)

                    new_labels.append(" ".join(values))

            with open(output / split_dst / "labels" / f"{new_name}.txt", "w") as f:
                f.write("\n".join(new_labels))

            counter += 1


print("DONE")
print("Total images:", counter)
