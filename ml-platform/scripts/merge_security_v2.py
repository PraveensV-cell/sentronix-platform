from pathlib import Path
import hashlib
import json
import os
import random
import shutil

ROOT = Path("ml-platform/datasets/processed")
OUTPUT = ROOT / "sentronix-security-v2"

SEED = 42
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

CLASS_NAMES = [
    "person",
    "fire",
    "smoke",
    "pistol",
    "knife",
    "helmet",
    "no-helmet",
    "vest",
    "no-vest",
    "boots",
    "no-boots",
    "gloves",
    "no-gloves",
    "goggles",
    "no-goggles",
    "autorickshaw",
    "bicycle",
    "bus",
    "car",
    "motorcycle",
    "truck",
    "backpack",
    "handbag",
    "laptop",
    "suitcase",
]

SOURCE_MAPS = {
    "dfire": {
        0: 2,
        1: 1,
    },
    "weapon": {
        0: 3,
        1: 4,
    },
    "ppe": {
        0: 9,
        1: 11,
        2: 13,
        3: 5,
        4: 10,
        5: 12,
        6: 14,
        7: 6,
        8: 8,
        9: 7,
    },
    "vehicle": {
        0: 15,
        1: 16,
        2: 17,
        3: 18,
        4: 19,
        5: 20,
    },
    "bag": {
        0: 21,
        1: 22,
        2: 23,
        3: 0,
        4: 24,
    },
    "coco": {
        0: 0,
    },
}


def image_hash(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def reset_output():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    for split in ["train", "val", "test"]:
        (OUTPUT / split / "images").mkdir(
            parents=True,
            exist_ok=True,
        )

        (OUTPUT / split / "labels").mkdir(
            parents=True,
            exist_ok=True,
        )

    (OUTPUT / "metadata").mkdir(
        parents=True,
        exist_ok=True,
    )


def find_images(directory):
    if not directory.exists():
        return []

    return sorted(
        [
            p
            for p in directory.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def find_label(labels_dir, image):
    if labels_dir is None or not labels_dir.exists():
        return None

    candidates = [
        labels_dir / f"{image.stem}.txt",
        labels_dir / f"{image.stem}.TXT",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def parse_yolo_label(label_path, mapping):
    output = []

    if label_path is None:
        return output

    with label_path.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        lines = f.readlines()

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        parts = line.strip().split()

        if not parts:
            continue

        if len(parts) != 5:
            raise ValueError(f"Invalid YOLO annotation: {label_path}:{line_number}")

        try:
            source_class = int(parts[0])
            values = [float(x) for x in parts[1:]]
        except ValueError as exc:
            raise ValueError(
                f"Invalid annotation values: {label_path}:{line_number}"
            ) from exc

        if source_class not in mapping:
            raise ValueError(
                f"Unmapped class {source_class} in {label_path}:{line_number}"
            )

        if not all(0.0 <= x <= 1.0 for x in values):
            raise ValueError(f"Invalid coordinates in {label_path}:{line_number}")

        if values[2] <= 0 or values[3] <= 0:
            raise ValueError(f"Invalid box dimensions in {label_path}:{line_number}")

        output.append([mapping[source_class]] + values)

    return output


def split_records(records):
    records = list(records)

    random.Random(SEED).shuffle(records)

    total = len(records)

    train_end = int(total * 0.80)
    val_end = train_end + int(total * 0.10)

    return (
        records[:train_end],
        records[train_end:val_end],
        records[val_end:],
    )


def register_record(
    records,
    image,
    label,
    source,
    split,
    mapping,
):
    records.append(
        {
            "image": image,
            "label": label,
            "source": source,
            "split": split,
            "mapping": mapping,
        }
    )


def collect_standard_dataset(
    dataset_name,
    source_name,
    split_names,
    records,
):
    dataset_root = ROOT / dataset_name

    for source_split in split_names:
        image_dir = dataset_root / source_split / "images"

        label_dir = dataset_root / source_split / "labels"

        for image in find_images(image_dir):
            label = find_label(
                label_dir,
                image,
            )

            output_split = "val" if source_split == "valid" else source_split

            register_record(
                records,
                image,
                label,
                source_name,
                output_split,
                SOURCE_MAPS[source_name],
            )


def collect_coco(records):
    dataset_root = ROOT / "sentronix-coco-person-v1"

    image_dir = dataset_root / "train" / "images"

    label_dir = dataset_root / "train" / "labels"

    source_records = []

    for image in find_images(image_dir):
        label = find_label(
            label_dir,
            image,
        )

        source_records.append(
            {
                "image": image,
                "label": label,
                "source": "coco",
                "mapping": SOURCE_MAPS["coco"],
            }
        )

    train, val, test = split_records(source_records)

    for record in train:
        record["split"] = "train"
        records.append(record)

    for record in val:
        record["split"] = "val"
        records.append(record)

    for record in test:
        record["split"] = "test"
        records.append(record)

    return {
        "total": len(source_records),
        "train": len(train),
        "val": len(val),
        "test": len(test),
    }


def collect_weapon(records):
    dataset_root = ROOT / "sentronix-weapon-v1"

    image_dir = dataset_root / "images"
    label_dir = dataset_root / "labels"

    source_records = []

    for image in find_images(image_dir):
        label = find_label(
            label_dir,
            image,
        )

        source_records.append(
            {
                "image": image,
                "label": label,
                "source": "weapon",
                "mapping": SOURCE_MAPS["weapon"],
            }
        )

    train, val, test = split_records(source_records)

    for record in train:
        record["split"] = "train"
        records.append(record)

    for record in val:
        record["split"] = "val"
        records.append(record)

    for record in test:
        record["split"] = "test"
        records.append(record)

    return {
        "total": len(source_records),
        "train": len(train),
        "val": len(val),
        "test": len(test),
    }


def write_record(
    record,
    used_hashes,
    counters,
):
    image = record["image"]
    label = record["label"]
    source = record["source"]
    split = record["split"]
    mapping = record["mapping"]

    digest = image_hash(image)

    if digest in used_hashes:
        counters["duplicates"] += 1
        return False

    used_hashes.add(digest)

    filename = f"{source}_{digest[:12]}{image.suffix.lower()}"

    destination_image = OUTPUT / split / "images" / filename

    destination_label = OUTPUT / split / "labels" / f"{Path(filename).stem}.txt"

    annotations = parse_yolo_label(
        label,
        mapping,
    )

    os.link(
        image,
        destination_image,
    )

    with destination_label.open(
        "w",
        encoding="utf-8",
    ) as f:
        for annotation in annotations:
            f.write(
                " ".join(
                    [
                        str(annotation[0]),
                        f"{annotation[1]:.6f}",
                        f"{annotation[2]:.6f}",
                        f"{annotation[3]:.6f}",
                        f"{annotation[4]:.6f}",
                    ]
                )
                + "\n"
            )

    counters["images"] += 1
    counters["labels"] += 1
    counters["objects"] += len(annotations)

    counters["sources"].setdefault(
        source,
        0,
    )

    counters["sources"][source] += 1

    counters["splits"].setdefault(
        split,
        0,
    )

    counters["splits"][split] += 1

    for annotation in annotations:
        class_id = annotation[0]

        counters["classes"][class_id] = (
            counters["classes"].get(
                class_id,
                0,
            )
            + 1
        )

    return True


def write_yaml():
    yaml_path = OUTPUT / "data.yaml"

    lines = [
        "path: .",
        "train: train/images",
        "val: val/images",
        "test: test/images",
        "",
        f"nc: {len(CLASS_NAMES)}",
        "names:",
    ]

    for index, name in enumerate(CLASS_NAMES):
        lines.append(f"  {index}: {name}")

    yaml_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def validate_output():
    results = {
        "images": 0,
        "labels": 0,
        "images_without_labels": 0,
        "labels_without_images": 0,
        "objects": 0,
        "empty_labels": 0,
        "invalid_entries": 0,
        "invalid_class_ids": 0,
        "invalid_coordinates": 0,
        "class_distribution": {},
        "split_distribution": {},
    }

    for split in [
        "train",
        "val",
        "test",
    ]:
        image_dir = OUTPUT / split / "images"

        label_dir = OUTPUT / split / "labels"

        images = find_images(image_dir)

        labels = list(label_dir.glob("*.txt"))

        results["split_distribution"][split] = {
            "images": len(images),
            "labels": len(labels),
        }

        results["images"] += len(images)

        results["labels"] += len(labels)

        image_stems = {p.stem for p in images}

        label_stems = {p.stem for p in labels}

        results["images_without_labels"] += len(image_stems - label_stems)

        results["labels_without_images"] += len(label_stems - image_stems)

        for label in labels:
            with label.open(
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as f:
                lines = f.readlines()

            valid_objects = 0

            for line in lines:
                parts = line.strip().split()

                if not parts:
                    continue

                if len(parts) != 5:
                    results["invalid_entries"] += 1
                    continue

                try:
                    class_id = int(parts[0])

                    values = [float(x) for x in parts[1:]]

                except ValueError:
                    results["invalid_entries"] += 1
                    continue

                if class_id < 0 or class_id >= len(CLASS_NAMES):
                    results["invalid_class_ids"] += 1
                    continue

                if not all(0.0 <= x <= 1.0 for x in values):
                    results["invalid_coordinates"] += 1
                    continue

                if values[2] <= 0 or values[3] <= 0:
                    results["invalid_coordinates"] += 1
                    continue

                valid_objects += 1

                results["objects"] += 1

                results["class_distribution"][class_id] = (
                    results["class_distribution"].get(
                        class_id,
                        0,
                    )
                    + 1
                )

            if valid_objects == 0:
                results["empty_labels"] += 1

    return results


def main():
    reset_output()

    records = []

    collect_standard_dataset(
        "sentronix-ppe-v1",
        "ppe",
        [
            "train",
            "valid",
            "test",
        ],
        records,
    )

    collect_standard_dataset(
        "sentronix-vehicle-v1",
        "vehicle",
        [
            "train",
            "valid",
            "test",
        ],
        records,
    )

    collect_standard_dataset(
        "sentronix-bag-v1",
        "bag",
        [
            "train",
            "valid",
            "test",
        ],
        records,
    )

    collect_standard_dataset(
        "dfire-sentronix-v1",
        "dfire",
        [
            "train",
            "val",
            "test",
        ],
        records,
    )

    coco_summary = collect_coco(records)

    weapon_summary = collect_weapon(records)

    used_hashes = set()

    counters = {
        "images": 0,
        "labels": 0,
        "objects": 0,
        "duplicates": 0,
        "sources": {},
        "splits": {},
        "classes": {},
    }

    source_order = {
        "dfire": 0,
        "weapon": 1,
        "ppe": 2,
        "vehicle": 3,
        "bag": 4,
        "coco": 5,
    }

    records.sort(
        key=lambda record: (
            record["split"],
            source_order[record["source"]],
            str(record["image"]),
        )
    )

    for record in records:
        write_record(
            record,
            used_hashes,
            counters,
        )

    write_yaml()

    validation = validate_output()

    metadata = {
        "dataset": ("sentronix-security-v2"),
        "version": "2.0.0",
        "seed": SEED,
        "storage_mode": ("hard_links"),
        "classes": {str(index): name for index, name in enumerate(CLASS_NAMES)},
        "source_splits": {
            "coco_person": (coco_summary),
            "weapon": (weapon_summary),
        },
        "merge": counters,
        "validation": validation,
    }

    metadata_path = OUTPUT / "metadata" / "dataset_info.json"

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("SENTRONIX SECURITY V2 MERGE")
    print("=" * 70)
    print()

    print(f"Images created       : {counters['images']}")

    print(f"Labels created       : {counters['labels']}")

    print(f"Objects created      : {counters['objects']}")

    print(f"Duplicates skipped   : {counters['duplicates']}")

    print()

    print("Source distribution:")

    for source, count in sorted(counters["sources"].items()):
        print(f"  {source:12} : {count}")

    print()

    print("Split distribution:")

    for split, count in sorted(counters["splits"].items()):
        print(f"  {split:12} : {count}")

    print()

    print("Validation:")

    print(f"  Images                  : {validation['images']}")

    print(f"  Labels                  : {validation['labels']}")

    print(f"  Images without labels   : {validation['images_without_labels']}")

    print(f"  Labels without images   : {validation['labels_without_images']}")

    print(f"  Total YOLO objects      : {validation['objects']}")

    print(f"  Empty labels            : {validation['empty_labels']}")

    print(f"  Invalid entries         : {validation['invalid_entries']}")

    print(f"  Invalid class IDs       : {validation['invalid_class_ids']}")

    print(f"  Invalid coordinates     : {validation['invalid_coordinates']}")

    print()

    print("Class distribution:")

    for class_id, class_name in enumerate(CLASS_NAMES):
        count = validation["class_distribution"].get(
            class_id,
            0,
        )

        print(f"  {class_id:2} {class_name:15} : {count}")

    print()

    print(f"Metadata: {metadata_path}")

    print(f"Dataset : {OUTPUT}")

    valid = (
        validation["images_without_labels"] == 0
        and validation["labels_without_images"] == 0
        and validation["invalid_entries"] == 0
        and validation["invalid_class_ids"] == 0
        and validation["invalid_coordinates"] == 0
        and validation["images"] == validation["labels"]
    )

    if valid:
        print()
        print("RESULT: SENTRONIX SECURITY V2 DATASET VERIFIED SUCCESSFULLY")
    else:
        print()
        print("RESULT: VALIDATION FAILED")


if __name__ == "__main__":
    main()
