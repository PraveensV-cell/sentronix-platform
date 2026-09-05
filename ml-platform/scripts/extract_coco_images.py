from pathlib import Path
import json
import urllib.request

from pycocotools.coco import COCO


COCO_IMAGE_URL = "http://images.cocodataset.org/train2017/"


ANNOTATION_FILE = Path("datasets/downloads/annotations/instances_train2017.json")


OUTPUT_DIR = Path("datasets/raw/coco/images/train")


TARGET_CLASSES = [
    "person",
    "car",
    "truck",
    "bus",
    "motorcycle",
    "bicycle",
]


def create_output() -> None:
    """
    Create image output directory.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_required_images() -> list[dict]:
    """
    Get COCO images containing required classes.
    """

    if not ANNOTATION_FILE.exists():
        print(f"Missing annotation file: {ANNOTATION_FILE}")

        return []

    coco = COCO(ANNOTATION_FILE)

    category_ids = coco.getCatIds(catNms=TARGET_CLASSES)

    image_ids = coco.getImgIds(catIds=category_ids)

    images = coco.loadImgs(image_ids)

    return [dict(image) for image in images]


def download_images(
    images: list[dict],
) -> None:
    """
    Download selected COCO images.
    """

    total = len(images)

    print(f"Downloading {total} images...")

    for index, image in enumerate(images):
        filename = image.get("file_name")

        if filename is None:
            continue

        output_file = OUTPUT_DIR / filename

        if output_file.exists():
            continue

        url = COCO_IMAGE_URL + filename

        try:
            urllib.request.urlretrieve(
                url,
                output_file,
            )

        except Exception as error:
            print(f"Failed {filename}: {error}")

        if index % 100 == 0:
            print(f"{index}/{total} completed")


def save_metadata(
    images: list[dict],
) -> None:
    """
    Save dataset information.
    """

    metadata = {
        "dataset": "COCO2017",
        "classes": TARGET_CLASSES,
        "image_count": len(images),
    }

    metadata_file = OUTPUT_DIR.parent / "metadata.json"

    with open(
        metadata_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )


def main() -> None:

    print("Starting COCO image extraction")

    create_output()

    images = get_required_images()

    print(f"Images selected: {len(images)}")

    if not images:
        print("No images found.")

        return

    download_images(images)

    save_metadata(images)

    print("COCO extraction completed")


if __name__ == "__main__":
    main()
