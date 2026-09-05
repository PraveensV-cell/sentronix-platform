from pathlib import Path
import yaml


DATASET_PATH = Path("datasets/processed/sentronix-security-v1")


CONFIG_FILE = Path("configs/sentronix.yaml")


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


CLASS_COUNT = 8


def count_files(
    folder,
    extensions,
):

    count = 0

    if not folder.exists():
        return 0

    for file in folder.rglob("*"):
        if file.suffix.lower() in extensions:
            count += 1

    return count


def check_yaml():

    print("\nChecking YAML...")

    if not CONFIG_FILE.exists():
        print("❌ YAML missing")

        return False

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    if "names" not in data:
        print("❌ Classes missing")

        return False

    print("✅ YAML valid")

    return True


def check_split(split):

    image_dir = DATASET_PATH / "images" / split

    label_dir = DATASET_PATH / "labels" / split

    images = count_files(
        image_dir,
        IMAGE_EXTENSIONS,
    )

    labels = count_files(
        label_dir,
        {".txt"},
    )

    print(f"{split}:")

    print(f" Images: {images}")

    print(f" Labels: {labels}")

    return images == labels


def check_labels():

    print("\nChecking labels...")

    errors = 0

    label_dir = DATASET_PATH / "labels"

    for label in label_dir.rglob("*.txt"):
        with open(
            label,
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                values = line.split()

                if len(values) != 5:
                    errors += 1

                    continue

                class_id = int(values[0])

                if class_id < 0 or class_id >= CLASS_COUNT:
                    errors += 1

    print(f"Label errors: {errors}")

    return errors == 0


def main():

    print("Sentronix Training Readiness Check")

    yaml_ok = check_yaml()

    train_ok = check_split("train")

    val_ok = check_split("val")

    test_ok = check_split("test")

    labels_ok = check_labels()

    print("\nFinal Result")

    if yaml_ok and train_ok and val_ok and test_ok and labels_ok:
        print("✅ Dataset ready for training")

    else:
        print("❌ Dataset needs fixes")


if __name__ == "__main__":
    main()
