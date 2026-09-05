from pathlib import Path
import zipfile


COCO_DIR = Path("datasets/raw/coco")


def extract_zip(file: Path):

    output = COCO_DIR / file.stem

    if output.exists():
        print(f"Already extracted {file}")

        return

    print(f"Extracting {file}")

    with zipfile.ZipFile(file, "r") as zip_ref:
        zip_ref.extractall(COCO_DIR)


def main():

    for file in COCO_DIR.glob("*.zip"):
        extract_zip(file)


if __name__ == "__main__":
    main()
