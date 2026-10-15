"""Export the trained .pth checkpoint to ONNX for cross-platform inference.

Usage (from backend/):
    python ml/export_onnx.py --model ml/model.pth --out ml/model.onnx
Then set MODEL_PATH=ml/model.onnx (and install requirements-ml.txt so
onnxruntime is available).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

from ml.inference import build_resnet50


def main():
    parser = argparse.ArgumentParser(description="Export model.pth to ONNX")
    parser.add_argument("--model", default="ml/model.pth")
    parser.add_argument("--out", default="ml/model.onnx")
    args = parser.parse_args()

    model = build_resnet50()
    model.load_state_dict(torch.load(args.model, map_location="cpu"))
    model.eval()

    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(
        model,
        dummy,
        args.out,
        input_names=["input"],
        output_names=["logits"],
        opset_version=14,
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    )
    size_mb = os.path.getsize(args.out) / (1024 * 1024)
    print(f"Exported {args.out} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
