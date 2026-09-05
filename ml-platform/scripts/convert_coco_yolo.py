from pathlib import Path
import shutil

from pycocotools.coco import COCO


ANNOTATION_FILE = Path("datasets/raw/coco/annotations/instances_train2017.json")


IMAGE_SOURCE = Path("datasets/raw/coco/images/train")


OUTPUT_IMAGE_DIR = Path("datasets/processed/sentronix-security-v1/images/train")


OUTPUT_LABEL_DIR = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAPPING: dict[str, int] = {
    "person": 0,
    "car": 1,
    "truck": 1,
    "bus": 1,
    "motorcycle": 1,
    "bicycle": 1,
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def create_directories() -> None:

    OUTPUT_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def convert_bbox(
    bbox: list[float],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:

    x, y, w, h = bbox

    if width <= 0 or height <= 0:
        return (
            0.0,
            0.0,
            0.0,
            0.0,
        )

    x_center = (x + w / 2) / width

    y_center = (y + h / 2) / height

    norm_width = w / width

    norm_height = h / height

    return (
        x_center,
        y_center,
        norm_width,
        norm_height,
    )


def get_categories(
    coco: COCO,
) -> dict[int, int]:

    categories: dict[int, int] = {}

    for category in coco.loadCats(coco.getCatIds()):
        name = category["name"]

        if name in CLASS_MAPPING:
            categories[category["id"]] = CLASS_MAPPING[name]

    return categories


def find_image(
    filename: str,
) -> Path | None:

    for ext in IMAGE_EXTENSIONS:
        image = IMAGE_SOURCE / filename

        if image.exists():
            return image

    return None


def process_images() -> None:

    if not ANNOTATION_FILE.exists():
        print("COCO annotation file missing.")

        return

    coco = COCO(ANNOTATION_FILE)

    category_map = get_categories(coco)

    image_ids = coco.getImgIds(catIds=list(category_map.keys()))

    print(f"Images: {len(image_ids)}")

    converted = 0

    for image_id in image_ids:
        image_info = coco.loadImgs(image_id)[0]

        filename = image_info.get("file_name")

        if filename is None:
            continue

        source_image = IMAGE_SOURCE / filename

        if not source_image.exists():
            continue

        annotations = coco.loadAnns(
            coco.getAnnIds(
                imgIds=image_id,
                catIds=list(category_map.keys()),
            )
        )

        labels = []

        for annotation in annotations:
            category_id = annotation["category_id"]

            if category_id not in category_map:
                continue

            class_id = category_map[category_id]

            bbox = convert_bbox(
                annotation["bbox"],
                image_info["width"],
                image_info["height"],
            )

            if not all(0 <= value <= 1 for value in bbox):
                continue

            labels.append(
                [
                    class_id,
                    *bbox,
                ]
            )

        if not labels:
            continue

        shutil.copy2(
            source_image,
            OUTPUT_IMAGE_DIR / filename,
        )

        label_file = OUTPUT_LABEL_DIR / Path(filename).with_suffix(".txt").name

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

    print("Starting COCO YOLO Conversion")

    create_directories()

    process_images()

    print("COCO conversion completed")


if __name__ == "__main__":
    main()
