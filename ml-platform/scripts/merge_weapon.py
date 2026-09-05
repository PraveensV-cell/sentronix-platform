from pathlib import Path
import shutil

SOURCE = Path(
    "datasets/downloads/weapon_extract/"
    "OD-WeaponDetection-master/"
    "Weapons and similar handled objects/"
    "Sohas_weapon-Detection-YOLOv5/obj_train_data"
)

TARGET = Path("datasets/processed/sentronix-security-v1")

SOURCE_CLASSES = {
    0: "pistol",
    2: "knife",
}

TARGET_CLASS = 4


def process_split(split):
    source_images = SOURCE / "images" / split
    source_labels = SOURCE / "labels" / split

    target_images = TARGET / "images" / split
    target_labels = TARGET / "labels" / split

    target_images.mkdir(parents=True, exist_ok=True)
    target_labels.mkdir(parents=True, exist_ok=True)

    processed = 0

    for label_file in source_labels.glob("*.txt"):
        output_lines = []

        for line in label_file.read_text().splitlines():
            parts = line.split()

            if len(parts) != 5:
                continue

            class_id = int(parts[0])

            if class_id not in SOURCE_CLASSES:
                continue

            parts[0] = str(TARGET_CLASS)
            output_lines.append(" ".join(parts))

        if not output_lines:
            continue

        image_found = False

        for extension in (".jpg", ".jpeg", ".png"):
            image_file = source_images / f"{label_file.stem}{extension}"

            if image_file.exists():
                shutil.copy2(
                    image_file,
                    target_images / image_file.name,
                )
                image_found = True
                break

        if not image_found:
            continue

        (target_labels / label_file.name).write_text("\n".join(output_lines) + "\n")

        processed += 1

    print(f"{split}: {processed} files")


def main():
    print("Weapon merge")

    process_split("train")
    process_split("test")

    print("Done")


if __name__ == "__main__":
    main()
