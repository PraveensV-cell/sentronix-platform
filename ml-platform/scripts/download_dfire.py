from pathlib import Path
import urllib.request
import zipfile


# Official D-Fire dataset release
DATASET_URL = "https://github.com/gaiasd/DFireDataset/archive/refs/heads/master.zip"


DOWNLOAD_DIR = Path("datasets/downloads")


OUTPUT_DIR = Path("datasets/raw/fire/dfire")


ZIP_FILE = DOWNLOAD_DIR / "dfire.zip"


def create_directories():

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def download_dataset():

    if ZIP_FILE.exists():
        print("D-Fire zip already exists.")

        return

    print("Downloading D-Fire dataset...")

    try:
        urllib.request.urlretrieve(
            DATASET_URL,
            ZIP_FILE,
        )

    except Exception as error:
        print("Download failed:")

        print(error)

        return

    print("Download completed.")


def extract_dataset():

    if not ZIP_FILE.exists():
        print("Zip file missing.")

        return

    extract_folder = DOWNLOAD_DIR / "dfire_extract"

    extract_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Extracting dataset...")

    with zipfile.ZipFile(
        ZIP_FILE,
        "r",
    ) as zip_file:
        zip_file.extractall(extract_folder)

    print("Extraction completed.")


def main():

    print("Sentronix D-Fire Download")

    create_directories()

    download_dataset()

    extract_dataset()

    print(
        """
Next:
Inspect extracted folders
and organize into:

datasets/raw/fire/dfire/

├── images
└── annotations
"""
    )


if __name__ == "__main__":
    main()
