from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "downloads"
    / "weapon_extract"
    / "OD-WeaponDetection-master"
    / "Weapons and similar handled objects"
    / "Sohas_weapon-Detection-YOLOv5"
)

OUTPUT = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "processed"
    / "sentronix-weapon-sohas-v1"
)

SOURCE_IMAGES = SOURCE / "obj_train_data" / "images"
SOURCE_LABELS = SOURCE / "obj_train_data" / "labels"

OUTPUT_IMAGES = OUTPUT / "images"
OUTPUT_LABELS = OUTPUT / "labels"

CLASS_MAPPING = {
    "0": 0,
    "2": 1,
}

CLASS_NAMES = {
    0: "pistol",
    1: "knife",
}


def main():
    if not SOURCE_IMAGES.exists():
        raise FileNotFoundError(f"Source image directory not found: {SOURCE_IMAGES}")

    if not SOURCE_LABELS.exists():
        raise FileNotFoundError(f"Source label directory not found: {SOURCE_LABELS}")

    OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
    OUTPUT_LABELS.mkdir(parents=True, exist_ok=True)

    image_files = sorted(
        [
            path
            for path in SOURCE_IMAGES.rglob("*")
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
    )

    label_files = sorted(SOURCE_LABELS.rglob("*.txt"))

    image_map = {path.stem: path for path in image_files}

    converted_images = 0
    converted_labels = 0
    skipped_labels = 0
    skipped_objects = 0
    pistol_objects = 0
    knife_objects = 0

    for label_file in label_files:
        image_file = image_map.get(label_file.stem)

        if image_file is None:
            skipped_labels += 1
            continue

        output_image = OUTPUT_IMAGES / image_file.name
        output_label = OUTPUT_LABELS / f"{label_file.stem}.txt"

        shutil.copy2(image_file, output_image)

        output_lines = []

        lines = label_file.read_text(encoding="utf-8").splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 5:
                skipped_objects += 1
                continue

            source_class = parts[0]

            if source_class not in CLASS_MAPPING:
                skipped_objects += 1
                continue

            target_class = CLASS_MAPPING[source_class]

            output_lines.append(
                f"{target_class} {parts[1]} {parts[2]} {parts[3]} {parts[4]}"
            )

            if target_class == 0:
                pistol_objects += 1
            elif target_class == 1:
                knife_objects += 1

        output_label.write_text(
            "\n".join(output_lines),
            encoding="utf-8",
        )

        converted_images += 1
        converted_labels += 1

    data_yaml = OUTPUT / "data.yaml"

    data_yaml.write_text(
        "path: .\n"
        "train: images\n"
        "val: images\n"
        "test: images\n\n"
        "nc: 2\n"
        "names:\n"
        "  0: pistol\n"
        "  1: knife\n",
        encoding="utf-8",
    )

    print()
    print("================ SOHAS WEAPON YOLO CONVERSION ================")
    print(f"Source images       : {len(image_files)}")
    print(f"Source labels       : {len(label_files)}")
    print(f"Converted images    : {converted_images}")
    print(f"Converted labels    : {converted_labels}")
    print(f"Skipped labels      : {skipped_labels}")
    print(f"Skipped objects     : {skipped_objects}")
    print()
    print("CLASS MAPPING")
    print("Source 0 -> SENTRONIX 0 = pistol")
    print("Source 2 -> SENTRONIX 1 = knife")
    print()
    print(f"Pistol objects      : {pistol_objects}")
    print(f"Knife objects       : {knife_objects}")
    print(f"Total weapon objects: {pistol_objects + knife_objects}")
    print()
    print(f"Output              : {OUTPUT}")
    print()
    print("RESULT: CONVERSION COMPLETE")


if __name__ == "__main__":
    main()
