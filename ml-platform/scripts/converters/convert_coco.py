from pathlib import Path
import shutil

from pycocotools.coco import COCO


ANNOTATION_FILE = Path("datasets/raw/coco/annotations/instances_train2017.json")


IMAGE_DIR = Path("datasets/raw/coco/images/train")


OUTPUT_IMAGE_DIR = Path("datasets/processed/sentronix-security-v1/images/train")


OUTPUT_LABEL_DIR = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAP = {
    "person": 0,
    "car": 1,
    "truck": 1,
    "bus": 1,
    "motorcycle": 1,
    "bicycle": 1,
}


def create_directories():

    OUTPUT_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def convert_bbox(
    bbox,
    width,
    height,
):

    x, y, w, h = bbox

    x_center = (x + w / 2) / width

    y_center = (y + h / 2) / height

    box_width = w / width

    box_height = h / height

    return (
        x_center,
        y_center,
        box_width,
        box_height,
    )


def get_category_map(
    coco,
):

    categories = {}

    for category in coco.loadCats(coco.getCatIds()):
        name = category["name"]

        if name in CLASS_MAP:
            categories[category["id"]] = CLASS_MAP[name]

    return categories


def convert_dataset():

    coco = COCO(ANNOTATION_FILE)

    category_map = get_category_map(coco)

    image_ids = coco.getImgIds(catIds=list(category_map.keys()))

    print(f"Images found: {len(image_ids)}")

    converted = 0

    for image_id in image_ids:
        image_info = coco.loadImgs(image_id)[0]

        image_name = image_info["file_name"]

        source_image = IMAGE_DIR / image_name

        if not source_image.exists():
            continue

        shutil.copy2(
            source_image,
            OUTPUT_IMAGE_DIR / image_name,
        )

        annotations = coco.loadAnns(
            coco.getAnnIds(
                imgIds=image_id,
                catIds=list(category_map.keys()),
            )
        )

        labels = []

        for annotation in annotations:
            category_id = annotation["category_id"]

            class_id = category_map[category_id]

            bbox = convert_bbox(
                annotation["bbox"],
                image_info["width"],
                image_info["height"],
            )

            labels.append(
                [
                    class_id,
                    *bbox,
                ]
            )

        label_file = OUTPUT_LABEL_DIR / image_name.replace(
            ".jpg",
            ".txt",
        )

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


def main():

    print("COCO YOLO Conversion Started")

    create_directories()

    convert_dataset()

    print("COCO conversion completed")


if __name__ == "__main__":
    main()
