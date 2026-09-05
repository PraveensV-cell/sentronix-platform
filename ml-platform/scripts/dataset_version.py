from pathlib import Path
from datetime import datetime


VERSION_FILE = Path("datasets/metadata/version.txt")


CURRENT_VERSION = "1.0.0"


def create_version_file() -> None:

    VERSION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    VERSION_FILE.write_text(
        f"""
Sentronix Dataset

Version:
{CURRENT_VERSION}

Created:
{datetime.now()}

""",
        encoding="utf-8",
    )

    print("Dataset version created")


def main():

    create_version_file()


if __name__ == "__main__":
    main()
