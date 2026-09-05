from pathlib import Path
import shutil


SOURCE_IMAGES = Path("datasets/raw/tracking/images")


SOURCE_ANNOTATIONS = Path("datasets/raw/tracking/annotations")


OUTPUT_IMAGES = Path("datasets/processed/sentronix-security-v1/images/train")


OUTPUT_LABELS = Path("datasets/processed/sentronix-security-v1/labels/train")


CLASS_MAP = {
    1: 0,  # person
    2: 1,  # vehicle
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
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
    x,
    y,
    width,
    height,
    image_width,
    image_height,
):

    if image_width == 0 or image_height == 0:
        return None

    x_center = (x + width / 2) / image_width

    y_center = (y + height / 2) / image_height

    box_width = width / image_width

    box_height = height / image_height

    return (
        x_center,
        y_center,
        box_width,
        box_height,
    )


def find_image(frame_number):

    for ext in IMAGE_EXTENSIONS:
        image = SOURCE_IMAGES / f"{frame_number}{ext}"

        if image.exists():
            return image

    return None


def convert_dataset():

    gt_files = list(SOURCE_ANNOTATIONS.rglob("gt.txt"))

    print(f"Tracking files found: {len(gt_files)}")

    if not gt_files:
        print("No MOT annotations found.")

        return

    converted = 0

    for gt_file in gt_files:
        with open(
            gt_file,
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()

        frame_labels = {}

        for line in lines:
            values = line.strip().split(",")

            if len(values) < 7:
                continue

            frame_id = values[0]

            class_id = int(values[6])

            if class_id not in CLASS_MAP:
                continue

            x = float(values[2])

            y = float(values[3])

            w = float(values[4])

            h = float(values[5])

            # Image size should be updated
            # after checking dataset

            bbox = convert_bbox(
                x,
                y,
                w,
                h,
                1920,
                1080,
            )

            if bbox is None:
                continue

            frame_labels.setdefault(frame_id, []).append(
                [
                    CLASS_MAP[class_id],
                    *bbox,
                ]
            )

        for frame, labels in frame_labels.items():
            image_file = find_image(frame)

            if image_file is None:
                continue

            shutil.copy2(
                image_file,
                OUTPUT_IMAGES / image_file.name,
            )

            label_file = OUTPUT_LABELS / f"{image_file.stem}.txt"

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

    print(f"Converted frames: {converted}")


def main():

    print("Tracking YOLO Conversion Started")

    create_directories()

    convert_dataset()

    print("Tracking conversion completed")


if __name__ == "__main__":
    main()
