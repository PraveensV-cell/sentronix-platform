from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is not installed.")
    print("Install it with: pip install pillow")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed.")
    print("Install it with: pip install pyyaml")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = (
    PROJECT_ROOT / "ml-platform" / "datasets" / "processed" / "sentronix-security-v2"
)

DATA_YAML = (
    PROJECT_ROOT / "ml-platform" / "training" / "configs" / "sentronix-security-v2.yaml"
)

REPORT_PATH = DATASET_ROOT / "metadata" / "pre_training_audit.json"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}

EXPECTED_CLASSES = {
    0: "person",
    1: "fire",
    2: "smoke",
    3: "pistol",
    4: "knife",
    5: "helmet",
    6: "no-helmet",
    7: "vest",
    8: "no-vest",
    9: "boots",
    10: "no-boots",
    11: "gloves",
    12: "no-gloves",
    13: "goggles",
    14: "no-goggles",
    15: "autorickshaw",
    16: "bicycle",
    17: "bus",
    18: "car",
    19: "motorcycle",
    20: "truck",
    21: "backpack",
    22: "handbag",
    23: "laptop",
    24: "suitcase",
}

SPLITS = ("train", "val", "test")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_yaml() -> dict:
    if not DATA_YAML.exists():
        return {}

    try:
        with DATA_YAML.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except Exception as exc:
        return {"_yaml_error": str(exc)}

    return data


def extract_yaml_names(data: dict) -> dict[int, str]:
    names = data.get("names", {})

    if isinstance(names, list):
        return {index: str(name) for index, name in enumerate(names)}

    if isinstance(names, dict):
        result = {}

        for key, value in names.items():
            try:
                result[int(key)] = str(value)
            except (TypeError, ValueError):
                pass

        return result

    return {}


def collect_files(directory: Path, extensions: set[str]) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    )


def collect_label_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(path for path in directory.rglob("*.txt") if path.is_file())


def validate_label_file(
    label_path: Path,
    expected_class_count: int,
) -> dict:
    result = {
        "objects": 0,
        "empty": False,
        "malformed": [],
        "invalid_class": [],
        "invalid_coordinates": [],
        "non_finite": [],
    }

    try:
        text = label_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        result["malformed"].append(
            {
                "line": 0,
                "reason": "label file is not valid UTF-8",
            }
        )
        return result
    except Exception as exc:
        result["malformed"].append(
            {
                "line": 0,
                "reason": f"cannot read label file: {exc}",
            }
        )
        return result

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        result["empty"] = True
        return result

    for line_number, line in enumerate(lines, start=1):
        parts = line.split()

        if len(parts) != 5:
            result["malformed"].append(
                {
                    "line": line_number,
                    "content": line,
                    "reason": "expected exactly 5 values",
                }
            )
            continue

        try:
            class_id = int(parts[0])
        except ValueError:
            result["malformed"].append(
                {
                    "line": line_number,
                    "content": line,
                    "reason": "class id is not an integer",
                }
            )
            continue

        if class_id < 0 or class_id >= expected_class_count:
            result["invalid_class"].append(
                {
                    "line": line_number,
                    "class_id": class_id,
                }
            )
            continue

        try:
            values = [float(value) for value in parts[1:]]
        except ValueError:
            result["malformed"].append(
                {
                    "line": line_number,
                    "content": line,
                    "reason": "coordinates are not numeric",
                }
            )
            continue

        if not all(
            value == value and value not in (float("inf"), float("-inf"))
            for value in values
        ):
            result["non_finite"].append(
                {
                    "line": line_number,
                    "values": values,
                }
            )
            continue

        x_center, y_center, width, height = values

        if not (
            0.0 <= x_center <= 1.0
            and 0.0 <= y_center <= 1.0
            and 0.0 < width <= 1.0
            and 0.0 < height <= 1.0
        ):
            result["invalid_coordinates"].append(
                {
                    "line": line_number,
                    "values": values,
                }
            )
            continue

        x_min = x_center - width / 2.0
        x_max = x_center + width / 2.0
        y_min = y_center - height / 2.0
        y_max = y_center + height / 2.0

        if x_min < 0.0 or x_max > 1.0 or y_min < 0.0 or y_max > 1.0:
            result["invalid_coordinates"].append(
                {
                    "line": line_number,
                    "values": values,
                    "reason": "bounding box extends outside image bounds",
                }
            )
            continue

        result["objects"] += 1

    return result


def verify_image(path: Path) -> tuple[bool, str | None]:
    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            image.load()

        return True, None

    except Exception as exc:
        return False, str(exc)


def audit_split(
    split: str,
    root: Path,
    expected_class_count: int,
) -> dict:
    images_dir = root / split / "images"
    labels_dir = root / split / "labels"

    images = collect_files(images_dir, IMAGE_EXTENSIONS)
    labels = collect_label_files(labels_dir)

    image_by_stem: dict[str, list[Path]] = {}
    label_by_stem: dict[str, list[Path]] = {}

    for image in images:
        image_by_stem.setdefault(image.stem, []).append(image)

    for label in labels:
        label_by_stem.setdefault(label.stem, []).append(label)

    duplicate_image_stems = {
        stem: [relative_path(path) for path in paths]
        for stem, paths in image_by_stem.items()
        if len(paths) > 1
    }

    duplicate_label_stems = {
        stem: [relative_path(path) for path in paths]
        for stem, paths in label_by_stem.items()
        if len(paths) > 1
    }

    missing_labels = []
    orphan_labels = []

    for stem, paths in image_by_stem.items():
        if stem not in label_by_stem:
            missing_labels.extend(relative_path(path) for path in paths)

    for stem, paths in label_by_stem.items():
        if stem not in image_by_stem:
            orphan_labels.extend(relative_path(path) for path in paths)

    class_counts = Counter()
    empty_labels = []
    malformed = []
    invalid_class = []
    invalid_coordinates = []
    non_finite = []
    invalid_images = []

    valid_pairs = 0

    for image in images:
        matching_labels = label_by_stem.get(image.stem, [])

        if len(matching_labels) != 1:
            continue

        label = matching_labels[0]
        valid_pairs += 1

        image_ok, image_error = verify_image(image)

        if not image_ok:
            invalid_images.append(
                {
                    "image": relative_path(image),
                    "error": image_error,
                }
            )

        validation = validate_label_file(
            label,
            expected_class_count,
        )

        if validation["empty"]:
            empty_labels.append(relative_path(label))

        for item in validation["malformed"]:
            malformed.append(
                {
                    "label": relative_path(label),
                    **item,
                }
            )

        for item in validation["invalid_class"]:
            invalid_class.append(
                {
                    "label": relative_path(label),
                    **item,
                }
            )

        for item in validation["invalid_coordinates"]:
            invalid_coordinates.append(
                {
                    "label": relative_path(label),
                    **item,
                }
            )

        for item in validation["non_finite"]:
            non_finite.append(
                {
                    "label": relative_path(label),
                    **item,
                }
            )

        try:
            text = label.read_text(encoding="utf-8")
        except Exception:
            continue

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 5:
                continue

            try:
                class_id = int(parts[0])
                values = [float(value) for value in parts[1:]]
            except ValueError:
                continue

            if class_id < 0 or class_id >= expected_class_count:
                continue

            if not all(
                value == value and value not in (float("inf"), float("-inf"))
                for value in values
            ):
                continue

            x_center, y_center, width, height = values

            if not (
                0.0 <= x_center <= 1.0
                and 0.0 <= y_center <= 1.0
                and 0.0 < width <= 1.0
                and 0.0 < height <= 1.0
            ):
                continue

            x_min = x_center - width / 2.0
            x_max = x_center + width / 2.0
            y_min = y_center - height / 2.0
            y_max = y_center + height / 2.0

            if x_min < 0.0 or x_max > 1.0 or y_min < 0.0 or y_max > 1.0:
                continue

            class_counts[class_id] += 1

    object_total = sum(class_counts.values())

    return {
        "images": len(images),
        "labels": len(labels),
        "paired_images": valid_pairs,
        "objects": object_total,
        "empty_labels": len(empty_labels),
        "empty_label_files": empty_labels,
        "missing_labels": missing_labels,
        "orphan_labels": orphan_labels,
        "duplicate_image_stems": duplicate_image_stems,
        "duplicate_label_stems": duplicate_label_stems,
        "malformed_labels": malformed,
        "invalid_class_entries": invalid_class,
        "invalid_coordinate_entries": invalid_coordinates,
        "non_finite_entries": non_finite,
        "invalid_images": invalid_images,
        "class_counts": {
            str(class_id): {
                "name": EXPECTED_CLASSES[class_id],
                "objects": class_counts.get(class_id, 0),
            }
            for class_id in range(expected_class_count)
        },
    }


def audit_duplicate_images(
    root: Path,
) -> dict:
    hashes: dict[str, list[str]] = {}

    for split in SPLITS:
        images_dir = root / split / "images"

        for image in collect_files(images_dir, IMAGE_EXTENSIONS):
            try:
                digest = sha256_file(image)
            except Exception:
                continue

            hashes.setdefault(digest, []).append(relative_path(image))

    duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}

    return {
        "unique_image_hashes": len(hashes),
        "duplicate_hash_groups": len(duplicates),
        "duplicate_images": duplicates,
    }


def check_split_stem_overlap(root: Path) -> dict:
    stems: dict[str, set[str]] = {}

    for split in SPLITS:
        stems[split] = {
            image.stem
            for image in collect_files(
                root / split / "images",
                IMAGE_EXTENSIONS,
            )
        }

    overlap = {}

    for index, split_a in enumerate(SPLITS):
        for split_b in SPLITS[index + 1 :]:
            common = stems[split_a] & stems[split_b]

            overlap[f"{split_a}_vs_{split_b}"] = {
                "count": len(common),
                "examples": sorted(common)[:20],
            }

    return overlap


def compare_yaml(yaml_data: dict) -> dict:
    errors = []
    warnings = []

    if "_yaml_error" in yaml_data:
        errors.append(f"YAML could not be parsed: {yaml_data['_yaml_error']}")
        return {
            "errors": errors,
            "warnings": warnings,
        }

    yaml_names = extract_yaml_names(yaml_data)

    if yaml_data.get("nc") != len(EXPECTED_CLASSES):
        errors.append(
            f"YAML nc={yaml_data.get('nc')} but expected {len(EXPECTED_CLASSES)}"
        )

    if yaml_names != EXPECTED_CLASSES:
        errors.append(
            "YAML class mapping does not exactly match expected 25-class mapping"
        )

    for split in ("train", "val", "test"):
        value = yaml_data.get(split)

        if split in ("train", "val") and not value:
            errors.append(f"YAML '{split}' path is missing or empty")

        if split == "test" and not value:
            warnings.append("YAML test path is missing or empty")

    return {
        "errors": errors,
        "warnings": warnings,
    }


def calculate_global_class_counts(
    split_results: dict,
) -> dict:
    totals = Counter()

    for split in SPLITS:
        counts = split_results[split]["class_counts"]

        for class_id, data in counts.items():
            totals[int(class_id)] += data["objects"]

    return {
        str(class_id): {
            "name": EXPECTED_CLASSES[class_id],
            "objects": totals[class_id],
        }
        for class_id in range(len(EXPECTED_CLASSES))
    }


def calculate_source_free_space() -> dict:
    try:
        usage = __import__("shutil").disk_usage(PROJECT_ROOT.anchor)

        return {
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
        }

    except Exception as exc:
        return {"error": str(exc)}


def run_audit() -> tuple[dict, bool]:
    errors = []
    warnings = []

    if not DATASET_ROOT.exists():
        errors.append(f"Dataset directory does not exist: {DATASET_ROOT}")

    if not DATA_YAML.exists():
        errors.append(f"Dataset YAML does not exist: {DATA_YAML}")

    for split in SPLITS:
        images_dir = DATASET_ROOT / split / "images"
        labels_dir = DATASET_ROOT / split / "labels"

        if not images_dir.exists():
            errors.append(f"Missing directory: {relative_path(images_dir)}")

        if not labels_dir.exists():
            errors.append(f"Missing directory: {relative_path(labels_dir)}")

    yaml_data = load_yaml()
    yaml_check = compare_yaml(yaml_data)

    errors.extend(yaml_check["errors"])
    warnings.extend(yaml_check["warnings"])

    split_results = {}

    for split in SPLITS:
        split_results[split] = audit_split(
            split,
            DATASET_ROOT,
            len(EXPECTED_CLASSES),
        )

        result = split_results[split]

        if result["missing_labels"]:
            errors.append(
                f"{split}: {len(result['missing_labels'])} images have no matching label"
            )

        if result["orphan_labels"]:
            errors.append(
                f"{split}: {len(result['orphan_labels'])} labels have no matching image"
            )

        if result["duplicate_image_stems"]:
            errors.append(f"{split}: duplicate image stems found")

        if result["duplicate_label_stems"]:
            errors.append(f"{split}: duplicate label stems found")

        if result["malformed_labels"]:
            errors.append(
                f"{split}: {len(result['malformed_labels'])} malformed label entries"
            )

        if result["invalid_class_entries"]:
            errors.append(
                f"{split}: {len(result['invalid_class_entries'])} invalid class entries"
            )

        if result["invalid_coordinate_entries"]:
            errors.append(
                f"{split}: {len(result['invalid_coordinate_entries'])} invalid coordinate entries"
            )

        if result["non_finite_entries"]:
            errors.append(
                f"{split}: {len(result['non_finite_entries'])} non-finite entries"
            )

        if result["invalid_images"]:
            errors.append(f"{split}: {len(result['invalid_images'])} unreadable images")

        if result["images"] != result["paired_images"]:
            errors.append(f"{split}: image/label pairing mismatch")

    duplicate_images = audit_duplicate_images(DATASET_ROOT)

    if duplicate_images["duplicate_hash_groups"]:
        warnings.append(
            f"{duplicate_images['duplicate_hash_groups']} duplicate image-content groups detected"
        )

    split_overlap = check_split_stem_overlap(DATASET_ROOT)

    for name, result in split_overlap.items():
        if result["count"] > 0:
            errors.append(
                f"Split leakage detected: {name} has {result['count']} overlapping image stems"
            )

    global_classes = calculate_global_class_counts(split_results)

    zero_object_classes = [
        class_id for class_id, data in global_classes.items() if data["objects"] == 0
    ]

    if zero_object_classes:
        warnings.append(
            "Classes with zero objects: "
            + ", ".join(
                f"{class_id} ({EXPECTED_CLASSES[int(class_id)]})"
                for class_id in zero_object_classes
            )
        )

    total_images = sum(split_results[split]["images"] for split in SPLITS)

    total_labels = sum(split_results[split]["labels"] for split in SPLITS)

    total_objects = sum(split_results[split]["objects"] for split in SPLITS)

    total_empty = sum(split_results[split]["empty_labels"] for split in SPLITS)

    report = {
        "audit": {
            "status": "PASS" if not errors else "FAIL",
            "timestamp_utc": utc_now(),
            "dataset": "sentronix-security-v2",
            "dataset_root": relative_path(DATASET_ROOT),
            "yaml": relative_path(DATA_YAML),
        },
        "expected": {
            "classes": len(EXPECTED_CLASSES),
            "class_mapping": {
                str(class_id): name for class_id, name in EXPECTED_CLASSES.items()
            },
            "splits": list(SPLITS),
        },
        "dataset_summary": {
            "total_images": total_images,
            "total_labels": total_labels,
            "total_objects": total_objects,
            "total_empty_labels": total_empty,
        },
        "splits": split_results,
        "global_class_counts": global_classes,
        "split_overlap": split_overlap,
        "duplicate_image_audit": duplicate_images,
        "yaml_audit": {
            "errors": yaml_check["errors"],
            "warnings": yaml_check["warnings"],
        },
        "storage": calculate_source_free_space(),
        "errors": errors,
        "warnings": warnings,
    }

    return report, not errors


def print_class_table(report: dict) -> None:
    print()
    print("=" * 72)
    print("GLOBAL CLASS DISTRIBUTION")
    print("=" * 72)

    print(
        f"{'ID':>3}  "
        f"{'CLASS':<18}  "
        f"{'TRAIN':>10}  "
        f"{'VAL':>10}  "
        f"{'TEST':>10}  "
        f"{'TOTAL':>10}"
    )

    print("-" * 72)

    for class_id in range(len(EXPECTED_CLASSES)):
        name = EXPECTED_CLASSES[class_id]

        train_count = report["splits"]["train"]["class_counts"][str(class_id)][
            "objects"
        ]

        val_count = report["splits"]["val"]["class_counts"][str(class_id)]["objects"]

        test_count = report["splits"]["test"]["class_counts"][str(class_id)]["objects"]

        total = train_count + val_count + test_count

        print(
            f"{class_id:>3}  "
            f"{name:<18}  "
            f"{train_count:>10,}  "
            f"{val_count:>10,}  "
            f"{test_count:>10,}  "
            f"{total:>10,}"
        )


def print_summary(report: dict, passed: bool) -> None:
    print()
    print("=" * 72)
    print("SENTRONIX SECURITY V2 — PRE-TRAINING AUDIT")
    print("=" * 72)

    summary = report["dataset_summary"]

    print(f"Dataset       : {report['audit']['dataset']}")
    print(f"Images        : {summary['total_images']:,}")
    print(f"Labels        : {summary['total_labels']:,}")
    print(f"Objects       : {summary['total_objects']:,}")
    print(f"Empty labels  : {summary['total_empty_labels']:,}")
    print(f"Classes       : {len(EXPECTED_CLASSES)}")

    print()
    print("SPLITS")
    print("-" * 72)

    for split in SPLITS:
        result = report["splits"][split]

        print(
            f"{split:<6} "
            f"images={result['images']:,} "
            f"labels={result['labels']:,} "
            f"objects={result['objects']:,} "
            f"empty={result['empty_labels']:,}"
        )

    print()
    print(
        f"Duplicate image groups : "
        f"{report['duplicate_image_audit']['duplicate_hash_groups']}"
    )

    print(
        "Split leakage          : "
        + (
            "DETECTED"
            if any(item["count"] > 0 for item in report["split_overlap"].values())
            else "NONE"
        )
    )

    print_class_table(report)

    print()
    print("=" * 72)

    if report["warnings"]:
        print("WARNINGS")
        print("=" * 72)

        for warning in report["warnings"]:
            print(f"[WARNING] {warning}")

        print()

    if report["errors"]:
        print("ERRORS")
        print("=" * 72)

        for error in report["errors"]:
            print(f"[ERROR] {error}")

        print()

    if passed:
        print("=" * 72)
        print("AUDIT RESULT: PASS")
        print("=" * 72)
        print("Security V2 dataset is structurally ready for training.")
    else:
        print("=" * 72)
        print("AUDIT RESULT: FAIL")
        print("=" * 72)
        print("Do NOT start training until the errors are fixed.")

    print()
    print(f"Report: {REPORT_PATH}")


def main() -> int:
    report, passed = run_audit()

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print_summary(report, passed)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
