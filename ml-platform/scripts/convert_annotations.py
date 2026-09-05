from typing import Iterable


CLASS_MAP = {
    "person": 0,
    "vehicle": 1,
    "fire": 2,
    "smoke": 3,
    "weapon": 4,
    "helmet": 5,
    "safety_vest": 6,
    "restricted_object": 7,
}


def convert_bbox(
    image_width: int,
    image_height: int,
    x: float,
    y: float,
    w: float,
    h: float,
) -> tuple[float, float, float, float]:
    """
    Convert bounding box from pixel format to YOLO format.

    Input:
        x, y:
            Top-left coordinates

        w, h:
            Bounding box width and height

    Output:

        (
            x_center,
            y_center,
            width,
            height
        )

    Values are normalized between 0 and 1.
    """

    x_center = (x + w / 2) / image_width

    y_center = (y + h / 2) / image_height

    width = w / image_width

    height = h / image_height

    return (
        x_center,
        y_center,
        width,
        height,
    )


def save_yolo_label(
    output_file: str,
    labels: Iterable[list[float]],
) -> None:
    """
    Save annotations in YOLO txt format.

    Format:

    class_id x_center y_center width height
    """

    with open(
        output_file,
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
