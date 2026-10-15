"""Train the ResNet50 screening model on a HAM10000-style dataset.

Expected layout (created by `python ml/prepare_data.py`):
    data_dir/train/<00_mel ... 06_nv>/*.jpg
    data_dir/val/...   data_dir/test/...

Usage (from backend/):
    python -m ml.train --data-dir ../data/skin --epochs 30 --batch-size 32

Outputs:
    ml/model.pth      best checkpoint by validation loss (plain state_dict)
    ml/metrics.json   test accuracy, per-class precision/recall/F1, confusion matrix
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from ml.inference import build_resnet50
from ml.preprocessing import CLASSES


def build_transforms():
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    train_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            normalize,
        ]
    )
    eval_tf = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), normalize]
    )
    return train_tf, eval_tf


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total, correct, loss_sum = 0, 0, 0.0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        out = model(images)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        loss_sum += loss.item() * labels.size(0)
        correct += (out.argmax(1) == labels).sum().item()
        total += labels.size(0)
    return loss_sum / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total, correct, loss_sum = 0, 0, 0.0
    all_preds, all_labels = [], []
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        out = model(images)
        loss_sum += criterion(out, labels).item() * labels.size(0)
        preds = out.argmax(1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())
    return loss_sum / total, correct / total, np.array(all_preds), np.array(all_labels)


def per_class_metrics(y_true, y_pred, num_classes):
    precision, recall, f1 = [], [], []
    for c in range(num_classes):
        tp = int(((y_pred == c) & (y_true == c)).sum())
        fp = int(((y_pred == c) & (y_true != c)).sum())
        fn = int(((y_pred != c) & (y_true == c)).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        precision.append(round(p, 4))
        recall.append(round(r, 4))
        f1.append(round(f, 4))
    confusion = [
        [int(((y_pred == p) & (y_true == t)).sum()) for p in range(num_classes)]
        for t in range(num_classes)
    ]
    return precision, recall, f1, confusion


def main():
    parser = argparse.ArgumentParser(description="Train ResNet50 skin-lesion classifier")
    parser.add_argument("--data-dir", required=True, help="root with train/ val/ test/ folders")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=7, help="early stopping patience (epochs)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", default="ml/model.pth")
    parser.add_argument("--metrics-out", default="ml/metrics.json")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    train_tf, eval_tf = build_transforms()

    train_ds = datasets.ImageFolder(os.path.join(args.data_dir, "train"), transform=train_tf)
    val_ds = datasets.ImageFolder(os.path.join(args.data_dir, "val"), transform=eval_tf)
    test_ds = datasets.ImageFolder(os.path.join(args.data_dir, "test"), transform=eval_tf)
    print(f"Samples: train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")
    folder_codes = [c.split("_", 1)[-1] for c in train_ds.classes]
    if not set(folder_codes).issubset(set(["mel", "bcc", "akiec", "bkl", "vasc", "df", "nv"])):
        raise SystemExit(
            f"Unexpected class folders: {train_ds.classes}. "
            "Run ml/prepare_data.py to build the dataset tree."
        )

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.workers
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers
    )
    test_loader = DataLoader(
        test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers
    )

    model = build_resnet50(num_classes=len(CLASSES)).to(device)

    # Class-weighted loss mitigates the heavy LOW-class imbalance and
    # reduces the false negatives that matter most in screening.
    counts = np.bincount(np.array(train_ds.targets), minlength=len(CLASSES))
    weights = torch.tensor(
        len(train_ds) / (len(CLASSES) * np.maximum(counts, 1)), dtype=torch.float32
    ).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val_loss = float("inf")
    best_epoch, epochs_ran, start = 0, 0, time.time()
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, device)
        epochs_ran = epoch
        print(
            f"Epoch {epoch:02d}/{args.epochs}  "
            f"train_loss={train_loss:.4f} acc={train_acc:.4f}  "
            f"val_loss={val_loss:.4f} acc={val_acc:.4f}"
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            torch.save(model.state_dict(), args.out)
            print(f"  saved new best checkpoint -> {args.out}")
        elif epoch - best_epoch >= args.patience:
            print(f"Early stopping: no val_loss improvement in {args.patience} epochs")
            break

    model.load_state_dict(torch.load(args.out, map_location="cpu"))
    model.to(device)
    test_loss, test_acc, y_pred, y_true = evaluate(model, test_loader, criterion, device)
    precision, recall, f1, confusion = per_class_metrics(y_true, y_pred, len(CLASSES))

    metrics = {
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": str(device),
        "epochs_ran": epochs_ran,
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "test_loss": round(test_loss, 4),
        "test_accuracy": round(test_acc, 4),
        "classes": train_ds.classes,
        "per_class": {
            cls: {"precision": precision[i], "recall": recall[i], "f1": f1[i]}
            for i, cls in enumerate(CLASSES)
        },
        "confusion_matrix": confusion,  # rows = true class, cols = predicted
        "dataset": {
            "train": len(train_ds),
            "val": len(val_ds),
            "test": len(test_ds),
        },
    }
    with open(args.metrics_out, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"Test accuracy: {test_acc:.4f} (loss {test_loss:.4f})")
    print(f"Metrics written to {args.metrics_out}; best epoch {best_epoch}")


if __name__ == "__main__":
    main()
