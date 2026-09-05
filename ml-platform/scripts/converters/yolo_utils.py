from pathlib import Path


def create_yolo_dirs(output_dir: Path):

    images = output_dir / "images"

    labels = output_dir / "labels"

    images.mkdir(
        parents=True,
        exist_ok=True,
    )

    labels.mkdir(
        parents=True,
        exist_ok=True,
    )


def convert_bbox(
    xmin,
    ymin,
    xmax,
    ymax,
    width,
    height,
):

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


def save_yolo_label(
    file_path,
    labels,
):

    with open(
        file_path,
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
