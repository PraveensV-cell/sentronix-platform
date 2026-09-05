from pathlib import Path
import shutil


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def create_folder(path: Path):

    path.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_images(folder: Path):

    images = []

    for file in folder.rglob("*"):
        if file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file)

    return images


def copy_file(
    source: Path,
    destination: Path,
):

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )
