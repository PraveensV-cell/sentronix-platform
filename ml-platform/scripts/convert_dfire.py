from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


SOURCE_IMAGES = Path("datasets/raw/fire/dfire/images")

SOURCE_ANNOTATIONS = Path("datasets/raw/fire/dfire/annotations")


OUTPUT_IMAGES = Path("datasets/processed/sentronix-security-v1/images/train")

OUTPUT_LABELS = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAP: dict[str, int] = {
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


def find_image(
    name: str,
) -> Path | None:

    for ext in IMAGE_EXTENSIONS:
        image = SOURCE_IMAGES / f"{name}{ext}"

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
) -> tuple[float, float, float, float]:

    if width <= 0 or height <= 0:
        return (
            0.0,
            0.0,
            0.0,
            0.0,
        )

    x_center = ((xmin + xmax) / 2) / width

    y_center = ((ymin + ymax) / 2) / height

    box_width = (xmax - xmin) / width

    box_height = (ymax - ymin) / height

    return (
        x_center,
        y_center,
        box_width,
        box_height,
    )


def get_text(
    element: ET.Element | None,
) -> str | None:

    if element is None:
        return None

    return element.text


def parse_annotation(
    xml_file: Path,
) -> list[list[float]]:

    try:
        tree = ET.parse(xml_file)

        root = tree.getroot()

    except ET.ParseError as error:
        print(f"XML error {xml_file}: {error}")

        return []

    size = root.find("size")

    if size is None:
        return []

    width_text = get_text(size.find("width"))

    height_text = get_text(size.find("height"))

    if width_text is None or height_text is None:
        return []

    width = int(width_text)

    height = int(height_text)

    labels: list[list[float]] = []

    for obj in root.findall("object"):
        name_text = get_text(obj.find("name"))

        if name_text is None:
            continue

        name = name_text.lower()

        if name not in CLASS_MAP:
            continue

        bbox = obj.find("bndbox")

        if bbox is None:
            continue

        values: list[float] = []

        for tag in (
            "xmin",
            "ymin",
            "xmax",
            "ymax",
        ):
            value = get_text(bbox.find(tag))

            if value is None:
                break

            values.append(float(value))

        if len(values) != 4:
            continue

        yolo_box = convert_bbox(
            values[0],
            values[1],
            values[2],
            values[3],
            width,
            height,
        )

        if not all(0 <= value <= 1 for value in yolo_box):
            continue

        labels.append(
            [
                float(CLASS_MAP[name]),
                *yolo_box,
            ]
        )

    return labels


def process_dataset() -> None:

    xml_files = list(SOURCE_ANNOTATIONS.glob("*.xml"))

    print(f"Annotations found: {len(xml_files)}")

    converted = 0

    for xml_file in xml_files:
        image_file = find_image(xml_file.stem)

        if image_file is None:
            continue

        labels = parse_annotation(xml_file)

        if not labels:
            continue

        shutil.copy2(
            image_file,
            OUTPUT_IMAGES / image_file.name,
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

    print("Starting D-Fire conversion...")

    create_directories()

    process_dataset()

    print("D-Fire conversion completed.")


if __name__ == "__main__":
    main()
