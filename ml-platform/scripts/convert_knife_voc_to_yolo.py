import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "downloads"
    / "weapon_extract"
    / "OD-WeaponDetection-master"
    / "Knife_detection"
)

OUTPUT = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "processed"
    / "sentronix-weapon-knife-v1"
)

IMAGE_SOURCE = SOURCE / "Images"
ANNOTATION_SOURCE = SOURCE / "annotations"

IMAGE_OUTPUT = OUTPUT / "images"
LABEL_OUTPUT = OUTPUT / "labels"

CLASS_NAME = "knife"
CLASS_ID = 0


def convert_box(xmin, ymin, xmax, ymax, width, height):
    x_center = ((xmin + xmax) / 2) / width
    y_center = ((ymin + ymax) / 2) / height
    box_width = (xmax - xmin) / width
    box_height = (ymax - ymin) / height

    return (
        CLASS_ID,
        x_center,
        y_center,
        box_width,
        box_height,
    )


def main():
    if not IMAGE_SOURCE.exists():
        raise FileNotFoundError(f"Image source not found: {IMAGE_SOURCE}")

    if not ANNOTATION_SOURCE.exists():
        raise FileNotFoundError(f"Annotation source not found: {ANNOTATION_SOURCE}")

    IMAGE_OUTPUT.mkdir(parents=True, exist_ok=True)
    LABEL_OUTPUT.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(ANNOTATION_SOURCE.glob("*.xml"))

    converted = 0
    skipped = 0
    total_objects = 0

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        size = root.find("size")

        if size is None:
            skipped += 1
            continue

        width = int(size.findtext("width", "0"))
        height = int(size.findtext("height", "0"))

        if width <= 0 or height <= 0:
            skipped += 1
            continue

        filename = root.findtext("filename")

        if not filename:
            skipped += 1
            continue

        source_image = IMAGE_SOURCE / filename

        if not source_image.exists():
            source_image = IMAGE_SOURCE / f"{xml_file.stem}.jpg"

        if not source_image.exists():
            skipped += 1
            continue

        yolo_lines = []

        for obj in root.findall("object"):
            name = obj.findtext("name", "").strip().lower()

            if name != CLASS_NAME:
                continue

            box = obj.find("bndbox")

            if box is None:
                continue

            xmin = float(box.findtext("xmin", "0"))
            ymin = float(box.findtext("ymin", "0"))
            xmax = float(box.findtext("xmax", "0"))
            ymax = float(box.findtext("ymax", "0"))

            if xmin < 0 or ymin < 0:
                continue

            if xmax > width or ymax > height:
                continue

            if xmin >= xmax or ymin >= ymax:
                continue

            class_id, x_center, y_center, box_width, box_height = convert_box(
                xmin,
                ymin,
                xmax,
                ymax,
                width,
                height,
            )

            yolo_lines.append(
                f"{class_id} "
                f"{x_center:.6f} "
                f"{y_center:.6f} "
                f"{box_width:.6f} "
                f"{box_height:.6f}"
            )

        destination_image = IMAGE_OUTPUT / source_image.name
        destination_label = LABEL_OUTPUT / f"{xml_file.stem}.txt"

        shutil.copy2(source_image, destination_image)

        destination_label.write_text(
            "\n".join(yolo_lines),
            encoding="utf-8",
        )

        converted += 1
        total_objects += len(yolo_lines)

    data_yaml = OUTPUT / "data.yaml"

    data_yaml.write_text(
        "path: .\n"
        "train: images\n"
        "val: images\n"
        "test: images\n\n"
        "nc: 1\n"
        "names:\n"
        "  0: knife\n",
        encoding="utf-8",
    )

    print()
    print("================ KNIFE VOC TO YOLO ================")
    print(f"Source XML files : {len(xml_files)}")
    print(f"Converted        : {converted}")
    print(f"Skipped          : {skipped}")
    print(f"YOLO objects     : {total_objects}")
    print(f"Output           : {OUTPUT}")
    print()
    print("CLASS MAPPING")
    print("0 = knife")
    print()
    print("RESULT: CONVERSION COMPLETE")


if __name__ == "__main__":
    main()
