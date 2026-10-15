"""Split HAM10000 into stratified train/val/test folder trees (70/15/15).

Inputs:
  --metadata  HAM10000_metadata.csv (columns include image_id, dx)
  --images    directory containing <image_id>.jpg files
  --out       output directory for the train/ val/ test/ trees

Class folders are zero-padded (00_mel ... 06_nv) so ImageFolder's
alphabetical ordering equals the canonical class order in
ml/preprocessing.py.

Usage (from backend/):
  python ml/prepare_data.py --metadata HAM10000_metadata.csv \
      --images ../data/ham10000/images --out ../data/skin
"""
import argparse
import csv
import os
import random
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.preprocessing import DX_CODES

random.seed(42)


def folder_name(dx):
    return f"{DX_CODES.index(dx):02d}_{dx}"


def main():
    parser = argparse.ArgumentParser(description="Stratified HAM10000 splitter")
    parser.add_argument("--metadata", required=True, help="path to HAM10000_metadata.csv")
    parser.add_argument("--images", required=True, help="directory with <image_id>.jpg files")
    parser.add_argument("--out", required=True, help="output directory for train/val/test trees")
    args = parser.parse_args()

    with open(args.metadata, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    by_dx = defaultdict(list)
    missing = 0
    for row in rows:
        path = os.path.join(args.images, row["image_id"] + ".jpg")
        if not os.path.exists(path):
            missing += 1
            continue
        if row["dx"] in DX_CODES:
            by_dx[row["dx"]].append(path)
    if missing:
        print(f"Warning: {missing} metadata rows had no matching image file")

    for split in ("train", "val", "test"):
        os.makedirs(os.path.join(args.out, split), exist_ok=True)

    summary = {}
    for dx, paths in sorted(by_dx.items(), key=lambda kv: DX_CODES.index(kv[0])):
        random.shuffle(paths)
        n = len(paths)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        splits = {
            "train": paths[:n_train],
            "val": paths[n_train:n_train + n_val],
            "test": paths[n_train + n_val:],
        }
        for split, files in splits.items():
            dest = os.path.join(args.out, split, folder_name(dx))
            os.makedirs(dest, exist_ok=True)
            for src in files:
                shutil.copy2(src, dest)
        summary[dx] = {"total": n, "train": len(splits["train"]),
                       "val": len(splits["val"]), "test": len(splits["test"])}
        print(f"{dx:>6}: total={n} train={len(splits['train'])} "
              f"val={len(splits['val'])} test={len(splits['test'])}")

    absent = set(DX_CODES) - set(by_dx)
    if absent:
        print(f"Warning: no images found for dx codes: {', '.join(sorted(absent))}")
    total = sum(s["total"] for s in summary.values())
    print(f"Done. {total} images split into {args.out}")


if __name__ == "__main__":
    main()
