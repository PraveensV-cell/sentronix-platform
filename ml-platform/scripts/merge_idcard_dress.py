import shutil
from pathlib import Path

sources = [
    {
        "name": "dress",
        "path": Path("ml-platform/datasets/processed/sentronix-dress-code-v1"),
        "mapping": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4},
    },
    {
        "name": "idcard",
        "path": Path("ml-platform/datasets/raw/id-card"),
        "mapping": {0: 5},
    },
]


output = Path("ml-platform/datasets/processed/sentronix-dress-code-v2")


splits = {"train": "train", "val": "valid", "test": "test"}


counter = 0


for src_split, dst_split in splits.items():
    img_out = output / dst_split / "images"
    lbl_out = output / dst_split / "labels"

    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    for dataset in sources:
        img_dir = dataset["path"] / src_split / "images"
        lbl_dir = dataset["path"] / src_split / "labels"

        if not img_dir.exists():
            continue

        for img in img_dir.iterdir():
            label = lbl_dir / f"{img.stem}.txt"

            if not label.exists():
                continue

            new_name = f"{dataset['name']}_{counter}"

            shutil.copy(img, img_out / f"{new_name}{img.suffix}")

            new_labels = []

            for line in open(label):
                parts = line.strip().split()

                if len(parts) >= 5:
                    old = int(parts[0])

                    if old in dataset["mapping"]:
                        parts[0] = str(dataset["mapping"][old])

                        new_labels.append(" ".join(parts))

            with open(lbl_out / f"{new_name}.txt", "w") as f:
                f.write("\n".join(new_labels))

            counter += 1


print("DONE")
print("Images:", counter)
