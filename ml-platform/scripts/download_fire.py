from pathlib import Path


FIRE_ROOT = Path("datasets/raw/fire")


DATASETS = {
    "dfire": FIRE_ROOT / "dfire",
    "firenet": FIRE_ROOT / "firenet",
    "cctv-fire": FIRE_ROOT / "cctv-fire",
}


def create_structure() -> None:
    """
    Create fire dataset folders.
    """

    for name, path in DATASETS.items():
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"Created: {name}")


def main():

    print("Initializing Fire Dataset Pipeline")

    create_structure()

    print("Fire dataset folders ready")


if __name__ == "__main__":
    main()
