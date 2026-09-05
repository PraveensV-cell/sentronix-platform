from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


SOURCE_IMAGES = Path("datasets/raw/fire/dfire/images")

SOURCE_ANNOTATIONS = Path("datasets/raw/fire/dfire/annotations")


OUTPUT_IMAGES = Path("datasets/processed/sentronix-security-v1/images/train")


OUTPUT_LABELS = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAP = {
    "fire": 2,
    "smoke": 3,
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def create_directories() -> None:

    OUTPUT_IMAGES.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_LABELS.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_xml_text(
    element: ET.Element | None,
    tag: str,
) -> str | None:

    if element is None:
        return None

    child = element.find(tag)

    if child is None:
        return None

    return child.text


def find_image(
    name: str,
) -> Path | None:

    for extension in IMAGE_EXTENSIONS:
        image = SOURCE_IMAGES / f"{name}{extension}"

        if image.exists():
            return image

    return None


def convert_bbox(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    width: int,
    height: int,
):

    if width == 0 or height == 0:
        return None

    x_center = ((xmin + xmax) / 2) / width

    y_center = ((ymin + ymax) / 2) / height

    box_width = (xmax - xmin) / width

    box_height = (ymax - ymin) / height

    values = (
        x_center,
        y_center,
        box_width,
        box_height,
    )

    if not all(0 <= value <= 1 for value in values):
        return None

    return values


def parse_xml(
    xml_file: Path,
) -> list[list[float]]:

    try:
        tree = ET.parse(xml_file)

        root = tree.getroot()

    except ET.ParseError:
        print(f"Invalid XML: {xml_file}")

        return []

    size = root.find("size")

    width_text = get_xml_text(
        size,
        "width",
    )

    height_text = get_xml_text(
        size,
        "height",
    )

    if width_text is None or height_text is None:
        return []

    width = int(width_text)

    height = int(height_text)

    labels = []

    for obj in root.findall("object"):
        name_text = get_xml_text(
            obj,
            "name",
        )

        if name_text is None:
            continue

        name = name_text.lower()

        if name not in CLASS_MAP:
            continue

        bbox = obj.find("bndbox")

        xmin_text = get_xml_text(
            bbox,
            "xmin",
        )

        ymin_text = get_xml_text(
            bbox,
            "ymin",
        )

        xmax_text = get_xml_text(
            bbox,
            "xmax",
        )

        ymax_text = get_xml_text(
            bbox,
            "ymax",
        )

        if None in (
            xmin_text,
            ymin_text,
            xmax_text,
            ymax_text,
        ):
            continue

        bbox_values = convert_bbox(
            float(xmin_text),
            float(ymin_text),
            float(xmax_text),
            float(ymax_text),
            width,
            height,
        )

        if bbox_values is None:
            continue

        labels.append(
            [
                float(CLASS_MAP[name]),
                *bbox_values,
            ]
        )

    return labels


def convert_dataset() -> None:

    xml_files = list(SOURCE_ANNOTATIONS.glob("*.xml"))

    print(f"XML files found: {len(xml_files)}")

    converted = 0

    for xml_file in xml_files:
        image_file = find_image(xml_file.stem)

        if image_file is None:
            continue

        labels = parse_xml(xml_file)

        if not labels:
            continue

        destination_image = OUTPUT_IMAGES / image_file.name

        shutil.copy2(
            image_file,
            destination_image,
        )

        label_file = OUTPUT_LABELS / f"{xml_file.stem}.txt"

        with open(
            label_file,
            "w",
            encoding="utf-8",
        ) as file:
            for label in labels:
                file.write(
                    " ".join(
                        map(
                            str,
                            label,
                        )
                    )
                )

                file.write("\n")

        converted += 1

    print(f"Converted images: {converted}")


def main() -> None:

    print("D-Fire YOLO Conversion Started")

    create_directories()

    convert_dataset()

    print("D-Fire conversion completed")


if __name__ == "__main__":
    main()
