from pathlib import Path


PPE_DIR = Path("datasets/raw/safety")


DATASETS = {
    "helmet": PPE_DIR / "helmet",
    "ppe": PPE_DIR / "ppe",
    "workers": PPE_DIR / "workers",
}


def create_structure() -> None:
    """
    Create PPE dataset directories.
    """

    for name, path in DATASETS.items():
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"{name} dataset folder ready: {path}")


def main() -> None:

    print("Initializing PPE Dataset Pipeline")

    create_structure()

    print("PPE dataset workspace ready")


if __name__ == "__main__":
    main()
