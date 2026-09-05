from pathlib import Path


SOURCE_DIR = Path("datasets/raw/tracking")


OUTPUT_DIR = Path("datasets/processed/sentronix-security-v1/tracking")


TRACKING_CLASS_MAP = {
    "person": 0,
}


def create_output_structure() -> None:
    """
    Create tracking output folders.
    """

    folders = [
        OUTPUT_DIR / "images",
        OUTPUT_DIR / "labels",
        OUTPUT_DIR / "metadata",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def convert_mot_line(
    line: str,
) -> list[float] | None:
    """
    Convert MOT annotation line.

    Input:

    frame,id,x,y,w,h,...

    Output:

    frame,id,class,x_center,y_center,w,h
    """

    values = line.strip().split(",")

    if len(values) < 6:
        return None

    frame_id = int(values[0])

    object_id = int(values[1])

    x = float(values[2])

    y = float(values[3])

    width = float(values[4])

    height = float(values[5])

    return [
        frame_id,
        object_id,
        0,
        x,
        y,
        width,
        height,
    ]


def process_tracking_file(
    input_file: Path,
) -> list[list[float]]:
    """
    Process MOT annotation file.
    """

    converted = []

    with input_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            result = convert_mot_line(line)

            if result:
                converted.append(result)

    return converted


def main() -> None:

    print("Starting Tracking Dataset Conversion")

    create_output_structure()

    annotation_files = list(SOURCE_DIR.rglob("*.txt"))

    print(f"Tracking files found: {len(annotation_files)}")

    for file in annotation_files:
        data = process_tracking_file(file)

        print(f"{file.name}: {len(data)} objects")

    print("Tracking conversion completed")


if __name__ == "__main__":
    main()
