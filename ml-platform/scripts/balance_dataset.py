from pathlib import Path
from collections import Counter


LABEL_DIR = Path("datasets/processed/sentronix-security-v1/labels")


CLASS_NAMES = {
    0: "person",
    1: "vehicle",
    2: "fire",
    3: "smoke",
    4: "weapon",
    5: "helmet",
    6: "safety_vest",
}


def analyze_labels() -> Counter:
    """
    Analyze class distribution.
    """

    counter = Counter()

    for label_file in LABEL_DIR.rglob("*.txt"):
        with label_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                values = line.strip().split()

                if not values:
                    continue

                class_id = int(float(values[0]))

                counter[class_id] += 1

    return counter


def print_report(
    counter: Counter,
) -> None:
    """
    Print dataset balance report.
    """

    print("\nSentronix Dataset Balance Report")

    for class_id, count in sorted(counter.items()):
        name = CLASS_NAMES.get(
            class_id,
            "unknown",
        )

        print(f"{name}: {count}")


def main():

    print("Analyzing Sentronix Dataset...")

    stats = analyze_labels()

    print_report(stats)


if __name__ == "__main__":
    main()
