from pathlib import Path


TRACKING_DIR = Path("datasets/raw/tracking")


DATASETS = {
    "crowdhuman": TRACKING_DIR / "crowdhuman",
    "mot17": TRACKING_DIR / "mot17",
    "mot20": TRACKING_DIR / "mot20",
}


def create_structure() -> None:
    """
    Create tracking dataset directories.
    """

    for name, path in DATASETS.items():
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"{name} dataset folder ready: {path}")


def main() -> None:

    print("Initializing Tracking Dataset Pipeline")

    create_structure()

    print("Tracking dataset workspace ready")


if __name__ == "__main__":
    main()
