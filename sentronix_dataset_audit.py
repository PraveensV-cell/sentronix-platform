from pathlib import Path
from collections import Counter
import math
import yaml

ROOT = Path(r"D:\majorproject\sentronix-platform")
CONFIG = ROOT / "ml-platform" / "training" / "configs" / "sentronix-security-v2.yaml"
EXPECTED = [
    "person",
    "fire",
    "smoke",
    "pistol",
    "knife",
    "helmet",
    "no-helmet",
    "vest",
    "no-vest",
    "boots",
    "no-boots",
    "gloves",
    "no-gloves",
    "goggles",
    "no-goggles",
    "autorickshaw",
    "bicycle",
    "bus",
    "car",
    "motorcycle",
    "truck",
    "backpack",
    "handbag",
    "laptop",
    "suitcase",
]
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main():
    with CONFIG.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    raw = cfg["names"]
    names = (
        {i: str(n) for i, n in enumerate(raw)}
        if isinstance(raw, list)
        else {int(k): str(v) for k, v in raw.items()}
    )
    root = Path(cfg["path"])
    if not root.is_absolute():
        root = (CONFIG.parent / root).resolve()
    print("\n=== SENTRONIX READ-ONLY DATASET AUDIT ===")
    print("Config:", CONFIG, "| exists:", CONFIG.is_file())
    print("Dataset root:", root, "| exists:", root.is_dir())
    print("nc:", cfg.get("nc"), "| class names:", len(names))
    print("IDs exactly 0..24:", sorted(names) == list(range(25)))
    print(
        "Expected class order matches:", [names.get(i) for i in range(25)] == EXPECTED
    )
    print("\n--- CLASS ID MAPPING ---")
    for i in range(25):
        print(f"{i:2}: {names.get(i,'<MISSING>')}")
    results, issues, examples = {}, Counter(), {}

    def issue(kind, p, detail):
        issues[kind] += 1
        examples.setdefault(kind, [])
        if len(examples[kind]) < 5:
            examples[kind].append(f"{p} — {detail}")

    for split in ("train", "val", "test"):
        if not cfg.get(split):
            continue
        imdir = root / cfg[split]
        lbdir = imdir.parent / "labels"
        if not imdir.is_dir():
            issue("missing image directory", imdir, "not found")
            continue
        if not lbdir.is_dir():
            issue("missing labels directory", lbdir, "not found")
            continue
        images = sorted(
            p for p in imdir.iterdir() if p.is_file() and p.suffix.lower() in EXTS
        )
        stems = {p.stem for p in images}
        labels = list(lbdir.glob("*.txt"))
        objects = Counter()
        class_images = Counter()
        empty = 0
        for im in images:
            lp = lbdir / f"{im.stem}.txt"
            if not lp.is_file():
                issue("missing label file", im, "no matching .txt")
                continue
            lines = [
                x
                for x in lp.read_text(
                    encoding="utf-8-sig", errors="replace"
                ).splitlines()
                if x.strip()
            ]
            if not lines:
                empty += 1
            present = set()
            for ln, line in enumerate(lines, 1):
                a = line.split()
                if len(a) != 5:
                    issue("malformed row", lp, f"line {ln}: expected 5 fields")
                    continue
                try:
                    cf = float(a[0])
                    v = [float(x) for x in a[1:]]
                except ValueError:
                    issue("non-numeric row", lp, f"line {ln}")
                    continue
                if not cf.is_integer():
                    issue("non-integer class ID", lp, f"line {ln}: {a[0]}")
                    continue
                c = int(cf)
                if c not in names:
                    issue("out-of-range class ID", lp, f"line {ln}: {c}")
                    continue
                if not all(math.isfinite(x) for x in v):
                    issue("non-finite coordinates", lp, f"line {ln}")
                    continue
                x, y, w, h = v
                if any(z < 0 or z > 1 for z in v):
                    issue("coordinates outside [0,1]", lp, f"line {ln}: {v}")
                if w <= 0 or h <= 0:
                    issue("non-positive box size", lp, f"line {ln}: {v}")
                if (
                    x - w / 2 < -1e-6
                    or x + w / 2 > 1 + 1e-6
                    or y - h / 2 < -1e-6
                    or y + h / 2 > 1 + 1e-6
                ):
                    issue("box extends outside image", lp, f"line {ln}: {v}")
                objects[c] += 1
                present.add(c)
            for c in present:
                class_images[c] += 1
        for lp in labels:
            if lp.stem not in stems:
                issue("orphan label file", lp, "no matching image")
        results[split] = {
            "images": len(images),
            "labels": len(labels),
            "empty": empty,
            "objects": objects,
            "class_images": class_images,
        }
        print(
            f"\n{split.upper()}: images={len(images)}, label_files={len(labels)}, empty_labels={empty}, objects={sum(objects.values())}"
        )
    print("\n--- CLASS FREQUENCIES ---")
    print(
        f"{'ID':>2} {'Class':16} {'Train obj':>10} {'Val obj':>8} {'Test obj':>9} {'Train imgs':>11} {'Val imgs':>8}"
    )
    for c in range(25):
        tr = results.get("train", {})
        va = results.get("val", {})
        te = results.get("test", {})
        print(
            f"{c:2} {names.get(c,'?'):16} {tr.get('objects',Counter())[c]:10} {va.get('objects',Counter())[c]:8} {te.get('objects',Counter())[c]:9} {tr.get('class_images',Counter())[c]:11} {va.get('class_images',Counter())[c]:8}"
        )
    print(
        "\n--- RARE / MISSING CLASSES (train objects=0, val objects=0, train images<20, or val images<5) ---"
    )
    for c in range(25):
        tr = results.get("train", {})
        va = results.get("val", {})
        ntr = tr.get("objects", Counter())[c]
        nva = va.get("objects", Counter())[c]
        itr = tr.get("class_images", Counter())[c]
        iva = va.get("class_images", Counter())[c]
        if ntr == 0 or nva == 0 or itr < 20 or iva < 5:
            print(
                f"{c:2} {names[c]:16} train_objects={ntr}, train_images={itr}, val_objects={nva}, val_images={iva}"
            )
    print("\n--- STRUCTURAL ISSUES ---")
    if not issues:
        print("No issues detected by these checks.")
    for kind, count in issues.most_common():
        print(f"{kind}: {count}")
        for ex in examples[kind]:
            print("  " + ex)
    print("\nRead-only audit complete. No training performed.")
    print("This checks label structure, not semantic correctness of every box.")


if __name__ == "__main__":
    main()
