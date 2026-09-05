from pathlib import Path
import json
import urllib.request
import zipfile


ANNOTATION_URL = (
    "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
)


BASE_DIR = Path("datasets/raw/coco")


ANNOTATION_DIR = BASE_DIR / "annotations"


DOWNLOAD_DIR = Path("datasets/downloads")


TARGET_CLASSES = {
    "person": 0,
    "car": 1,
    "truck": 1,
    "bus": 1,
    "motorcycle": 1,
    "bicycle": 1,
}


def create_directories() -> None:
    """
    Create required COCO folders.
    """

    folders = [
        BASE_DIR,
        ANNOTATION_DIR,
        DOWNLOAD_DIR,
        BASE_DIR / "images",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def download_annotations() -> Path:
    """
    Download COCO annotation zip.
    """

    output = DOWNLOAD_DIR / "annotations_trainval2017.zip"

    if output.exists():
        print("Annotation archive already exists.")

        return output

    print("Downloading COCO annotations...")

    try:
        urllib.request.urlretrieve(
            ANNOTATION_URL,
            output,
        )

    except Exception as error:
        print(f"Download failed: {error}")

        raise

    print("Annotation download complete.")

    return output


def extract_annotations(
    archive: Path,
) -> None:
    """
    Extract COCO annotations.
    """

    extracted_path = DOWNLOAD_DIR / "annotations"

    if extracted_path.exists():
        print("Annotations already extracted.")

        return

    print("Extracting annotations...")

    with zipfile.ZipFile(
        archive,
        "r",
    ) as zip_file:
        zip_file.extractall(DOWNLOAD_DIR)

    print("Extraction completed.")


def create_metadata() -> None:
    """
    Save Sentronix COCO metadata.
    """

    metadata = {
        "dataset": "COCO2017",
        "classes": TARGET_CLASSES,
        "source": "COCO",
    }

    with open(
        BASE_DIR / "metadata.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )


def verify_annotations() -> None:
    """
    Check annotation files.
    """

    train_file = DOWNLOAD_DIR / "annotations" / "instances_train2017.json"

    val_file = DOWNLOAD_DIR / "annotations" / "instances_val2017.json"

    if train_file.exists():
        print("Train annotations found.")

    else:
        print("Train annotations missing.")

    if val_file.exists():
        print("Validation annotations found.")

    else:
        print("Validation annotations missing.")


def main() -> None:

    print("Starting COCO Dataset Preparation")

    create_directories()

    archive = download_annotations()

    extract_annotations(archive)

    verify_annotations()

    create_metadata()

    print("COCO preparation completed.")


if __name__ == "__main__":
    main()
