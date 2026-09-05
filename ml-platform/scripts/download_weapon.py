from pathlib import Path
import urllib.request
import zipfile


DATASET_URL = (
    "https://github.com/ari-dasci/OD-WeaponDetection/archive/refs/heads/master.zip"
)


DOWNLOAD_DIR = Path("datasets/downloads")


OUTPUT_DIR = Path("datasets/raw/weapon")


ZIP_FILE = DOWNLOAD_DIR / "weapon_dataset.zip"


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
        print("Weapon dataset archive already exists.")

        return

    print("Downloading weapon dataset...")

    urllib.request.urlretrieve(
        DATASET_URL,
        ZIP_FILE,
    )

    print("Download completed.")


def extract_dataset():

    extract_dir = DOWNLOAD_DIR / "weapon_extract"

    if extract_dir.exists():
        print("Dataset already extracted.")

        return

    print("Extracting weapon dataset...")

    with zipfile.ZipFile(
        ZIP_FILE,
        "r",
    ) as zip_file:
        zip_file.extractall(extract_dir)

    print("Extraction completed.")


def main():

    print("Sentronix Weapon Dataset Download")

    create_directories()

    download_dataset()

    extract_dataset()

    print("\nWeapon dataset extracted.")

    print("Move images and annotations into:")

    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
