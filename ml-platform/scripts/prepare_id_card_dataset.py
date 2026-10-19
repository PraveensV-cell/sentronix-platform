from pathlib import Path
import shutil

SOURCE = Path("ml-platform/datasets/raw/id-card")
OUTPUT = Path("ml-platform/datasets/processed/sentronix-id-card-v1")

SPLITS = {
    "train": "train",
    "valid": "val",
    "test": "test",
}


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    total_images = 0
    total_labels = 0
    total_objects = 0
    empty_labels = 0

    for source_split, output_split in SPLITS.items():
        source_images = SOURCE / source_split / "images"
        source_labels = SOURCE / source_split / "labels"

        output_images = OUTPUT / output_split / "images"
        output_labels = OUTPUT / output_split / "labels"

        output_images.mkdir(parents=True, exist_ok=True)
        output_labels.mkdir(parents=True, exist_ok=True)

        for image in source_images.iterdir():
            if image.is_file():
                shutil.copy2(image, output_images / image.name)
                total_images += 1

        for label in source_labels.glob("*.txt"):
            target = output_labels / label.name
            text = label.read_text(errors="ignore").strip()

            if not text:
                target.write_text("")
                empty_labels += 1
                total_labels += 1
                continue

            lines = []

            for line in text.splitlines():
                if not line.strip():
                    continue

                parts = line.split()

                if len(parts) != 5:
                    continue

                lines.append(line)
                total_objects += 1

            target.write_text("\n".join(lines) + ("\n" if lines else ""))

            total_labels += 1

    (OUTPUT / "data.yaml").write_text(
        """train: ../train/images
val: ../val/images
test: ../test/images

nc: 1
names:
  - ID CARD
"""
    )

    print("=" * 70)
    print("SENTRONIX ID CARD DATASET PREPARATION")
    print("=" * 70)
    print()
    print(f"Images        : {total_images}")
    print(f"Labels        : {total_labels}")
    print(f"Objects       : {total_objects}")
    print(f"Empty labels  : {empty_labels}")
    print(f"Output        : {OUTPUT}")
    print()
    print("RESULT: ID CARD DATASET PREPARATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
