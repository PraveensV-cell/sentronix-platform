import shutil
from pathlib import Path

source = Path("ml-platform/datasets/processed/sentronix-dress-code-v4")

output = Path("ml-platform/datasets/processed/sentronix-dress-code-v5")


splits = {"train": "train", "valid": "valid", "test": "test"}


for split in splits:
    (output / split / "images").mkdir(parents=True, exist_ok=True)

    (output / split / "labels").mkdir(parents=True, exist_ok=True)

    img_dir = source / split / "images"
    lbl_dir = source / split / "labels"

    for label in lbl_dir.glob("*.txt"):
        new_lines = []

        for line in open(label):
            values = line.strip().split()

            if len(values) == 5:
                # already detection format
                new_lines.append(line.strip())

            elif len(values) > 5:
                # segmentation -> ignore
                continue

        if not new_lines:
            continue

        # copy image
        imgs = list(img_dir.glob(label.stem + ".*"))

        if imgs:
            shutil.copy(imgs[0], output / split / "images" / imgs[0].name)

        # write clean label
        with open(output / split / "labels" / label.name, "w") as f:
            f.write("\n".join(new_lines))

    print(split, "done")


print("CLEAN COMPLETE")
print("Output:", output)
