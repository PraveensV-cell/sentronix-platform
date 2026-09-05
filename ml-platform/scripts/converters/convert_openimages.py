from pathlib import Path
import csv
import shutil


SOURCE_IMAGES = Path("datasets/raw/openimages/images")


SOURCE_ANNOTATIONS = Path(
    "datasets/raw/openimages/annotations/train-annotations-bbox.csv"
)


OUTPUT_IMAGES = Path("datasets/processed/sentronix-security-v1/images/train")


OUTPUT_LABELS = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAP = {
    "Person": 0,
    "Car": 1,
    "Truck": 1,
    "Bus": 1,
    "Motorcycle": 1,
    "Helmet": 5,
    "Gun": 4,
    "Weapon": 4,
}


def create_directories():

    OUTPUT_IMAGES.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_LABELS.mkdir(
        parents=True,
        exist_ok=True,
    )


def convert_bbox(
    xmin,
    xmax,
    ymin,
    ymax,
):

    x_center = (xmin + xmax) / 2

    y_center = (ymin + ymax) / 2

    width = xmax - xmin

    height = ymax - ymin

    return (
        x_center,
        y_center,
        width,
        height,
    )


def convert_dataset():

    if not SOURCE_ANNOTATIONS.exists():
        print("OpenImages annotation file missing.")

        return

    images = {}

    print("Reading OpenImages CSV...")

    with open(
        SOURCE_ANNOTATIONS,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            class_name = row["ClassName"]

            if class_name not in CLASS_MAP:
                continue

            image_id = row["ImageID"]

            xmin = float(row["XMin"])

            xmax = float(row["XMax"])

            ymin = float(row["YMin"])

            ymax = float(row["YMax"])

            bbox = convert_bbox(
                xmin,
                xmax,
                ymin,
                ymax,
            )

            images.setdefault(image_id, []).append(
                [
                    CLASS_MAP[class_name],
                    *bbox,
                ]
            )

    converted = 0

    for image_id, labels in images.items():
        image_file = None

        for ext in (
            ".jpg",
            ".jpeg",
            ".png",
        ):
            candidate = SOURCE_IMAGES / f"{image_id}{ext}"

            if candidate.exists():
                image_file = candidate

                break

        if image_file is None:
            continue

        shutil.copy2(
            image_file,
            OUTPUT_IMAGES / image_file.name,
        )

        label_file = OUTPUT_LABELS / f"{image_id}.txt"

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

    print("OpenImages YOLO Conversion Started")

    create_directories()

    convert_dataset()

    print("OpenImages conversion completed")


if __name__ == "__main__":
    main()
