from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "downloads"
    / "weapon_extract"
    / "OD-WeaponDetection-master"
    / "Weapons and similar handled objects"
    / "Sohas_weapon-Detection"
)

OUTPUT = (
    PROJECT_ROOT
    / "ml-platform"
    / "datasets"
    / "processed"
    / "sentronix-weapon-sohas-final-v1"
)

IMAGE_SOURCE = SOURCE
IMAGE_OUTPUT = OUTPUT / "images"
LABEL_OUTPUT = OUTPUT / "labels"

CLASS_MAPPING = {
    "pistol": 0,
    "knife": 1,
}


def build_image_map():
    image_files = []

    for path in SOURCE.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        image_files.append(path)

    image_map = {}

    for image in image_files:
        image_map[image.stem] = image

    return image_map


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source dataset not found: {SOURCE}")

    IMAGE_OUTPUT.mkdir(parents=True, exist_ok=True)

    LABEL_OUTPUT.mkdir(parents=True, exist_ok=True)

    image_map = build_image_map()

    xml_files = sorted(SOURCE.rglob("*.xml"))

    converted = 0
    skipped_no_image = 0
    skipped_invalid_xml = 0
    skipped_invalid_size = 0
    skipped_invalid_boxes = 0
    excluded_objects = 0

    pistol_objects = 0
    knife_objects = 0

    for xml_file in xml_files:

        image_file = image_map.get(xml_file.stem)

        if image_file is None:
            skipped_no_image += 1
            continue

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError:
            skipped_invalid_xml += 1
            continue

        size = root.find("size")

        if size is None:
            skipped_invalid_size += 1
            continue

        try:
            width = float(size.findtext("width", "0"))

            height = float(size.findtext("height", "0"))
        except ValueError:
            skipped_invalid_size += 1
            continue

        if width <= 0 or height <= 0:
            skipped_invalid_size += 1
            continue

        yolo_lines = []

        for obj in root.findall("object"):

            class_name = obj.findtext("name", "").strip().lower()

            if class_name not in CLASS_MAPPING:
                excluded_objects += 1
                continue

            box = obj.find("bndbox")

            if box is None:
                skipped_invalid_boxes += 1
                continue

            try:
                xmin = float(box.findtext("xmin", "0"))

                ymin = float(box.findtext("ymin", "0"))

                xmax = float(box.findtext("xmax", "0"))

                ymax = float(box.findtext("ymax", "0"))
            except ValueError:
                skipped_invalid_boxes += 1
                continue

            if (
                xmin < 0
                or ymin < 0
                or xmax > width
                or ymax > height
                or xmin >= xmax
                or ymin >= ymax
            ):
                skipped_invalid_boxes += 1
                continue

            class_id = CLASS_MAPPING[class_name]

            x_center = ((xmin + xmax) / 2) / width

            y_center = ((ymin + ymax) / 2) / height

            box_width = (xmax - xmin) / width

            box_height = (ymax - ymin) / height

            yolo_lines.append(
                f"{class_id} "
                f"{x_center:.6f} "
                f"{y_center:.6f} "
                f"{box_width:.6f} "
                f"{box_height:.6f}"
            )

            if class_id == 0:
                pistol_objects += 1
            else:
                knife_objects += 1

        output_image = IMAGE_OUTPUT / image_file.name

        output_label = LABEL_OUTPUT / f"{xml_file.stem}.txt"

        shutil.copy2(image_file, output_image)

        output_label.write_text("\n".join(yolo_lines), encoding="utf-8")

        converted += 1

    total_objects = pistol_objects + knife_objects

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
    print("================ SOHAS FINAL VOC TO YOLO ================")
    print(f"Source XML files       : {len(xml_files)}")
    print(f"Source images          : {len(image_map)}")
    print(f"Converted pairs        : {converted}")
    print(f"Skipped no image       : {skipped_no_image}")
    print(f"Skipped invalid XML    : {skipped_invalid_xml}")
    print(f"Skipped invalid size   : {skipped_invalid_size}")
    print(f"Skipped invalid boxes  : {skipped_invalid_boxes}")
    print(f"Excluded objects      : {excluded_objects}")
    print()
    print("CLASS MAPPING")
    print("0 = pistol")
    print("1 = knife")
    print()
    print(f"Pistol objects        : {pistol_objects}")
    print(f"Knife objects         : {knife_objects}")
    print(f"Total weapon objects  : {total_objects}")
    print()
    print(f"Output                : {OUTPUT}")
    print()
    print("RESULT: SOHAS FINAL CONVERSION COMPLETE")


if __name__ == "__main__":
    main()
