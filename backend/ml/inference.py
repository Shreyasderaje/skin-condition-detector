"""Skin-lesion inference.

Model priority: PyTorch checkpoint (.pth) -> ONNX runtime (.onnx) ->
deterministic DemoModel. The demo model exists so the full product
workflow can be demonstrated before the ~100MB trained weights are
produced; every demo prediction is flagged with mode="demo" so it can
never be mistaken for a real model output.
"""
import json
import logging
import os
import threading

import numpy as np

from ml.preprocessing import CLASS_TO_RISK, CLASSES, DX_CODES, preprocess

logger = logging.getLogger(__name__)

RECOMMENDATIONS = {
    "LOW": "Continue routine care. Schedule a follow-up in 3 months.",
    "MEDIUM": "Monitor for changes. Refer to a dermatologist within 2 weeks.",
    "HIGH": "Refer to a dermatologist IMMEDIATELY.",
}

DISCLAIMER = (
    "This screening is a decision-support tool, NOT a diagnosis. "
    "All HIGH risk cases must be seen by a dermatologist. "
    "Consult a qualified physician for final diagnosis and treatment."
)

DEMO_NOTICE = (
    "Running in DEMO mode: trained model weights were not found, so this "
    "result comes from a deterministic placeholder heuristic. Train the "
    "model (see SETUP.md) and place ml/model.pth to enable real inference."
)

_lock = threading.Lock()
_model = None
_model_mode = None


def build_resnet50(num_classes=len(CLASSES)):
    """ResNet50 backbone + custom head (Dropout 0.5 -> 256 ReLU -> classes).

    Shared by training, ONNX export and inference so the architecture
    can never drift between them.
    """
    import torch
    import torchvision

    model = torchvision.models.resnet50(weights=None)
    model.fc = torch.nn.Sequential(
        torch.nn.Dropout(0.5),
        torch.nn.Linear(model.fc.in_features, 256),
        torch.nn.ReLU(),
        torch.nn.Linear(256, num_classes),
    )
    return model


class TorchModel:
    """ResNet50 fine-tuned on HAM10000 (7 classes). See ml/train.py."""

    def __init__(self, model_path):
        import torch

        self.torch = torch
        model = build_resnet50()
        state = torch.load(model_path, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state)
        model.eval()
        self.model = model
        self.perm = self._class_permutation(model_path)

    @staticmethod
    def _class_permutation(model_path):
        """Reorder raw outputs into canonical CLASSES order if training recorded
        a class list in metrics.json (guards against folder-order surprises)."""
        metrics_path = os.path.join(os.path.dirname(model_path), "metrics.json")
        if not os.path.exists(metrics_path):
            return None
        try:
            with open(metrics_path, "r", encoding="utf-8") as fh:
                names = json.load(fh).get("classes") or []
        except Exception:
            return None
        clean = []
        for name in names:
            code = name.split("_", 1)[1] if "_" in name else name
            clean.append(code if code in DX_CODES else None)
        if sorted(x for x in clean if x) != sorted(DX_CODES):
            return None
        return [clean.index(code) for code in DX_CODES]

    def predict_probs(self, img):
        torch = self.torch
        x = torch.from_numpy(preprocess(img)).unsqueeze(0)
        with torch.no_grad():
            probs = torch.softmax(self.model(x), dim=1)[0]
        probs = probs.numpy().astype(np.float64)
        if self.perm is not None:
            probs = probs[self.perm]
        return probs


class OnnxModel:
    """ONNX-exported checkpoint (see ml/export_onnx.py). Canonical class order."""

    def __init__(self, model_path):
        import onnxruntime as ort

        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def predict_probs(self, img):
        x = preprocess(img)[None].astype(np.float32)
        logits = self.session.run(None, {self.input_name: x})[0][0]
        e = np.exp(logits - logits.max())
        return (e / e.sum()).astype(np.float64)


class DemoModel:
    """Deterministic placeholder driven by simple image statistics
    (darkness, redness, saturation, texture). Never trained; output
    variance only makes the product flow demoable end to end."""

    WEIGHTS = np.array(
        [
            # darkness  redness  saturation  texture
            [2.0, 0.5, 0.6, 3.0],   # Melanoma
            [1.2, 0.3, 0.5, 2.2],   # Basal Cell Carcinoma
            [0.3, 1.6, 0.9, 0.8],   # Actinic Keratosis
            [0.2, 0.6, 0.4, 0.6],   # Benign Keratosis
            [0.2, 2.2, 1.2, 0.4],   # Vascular Lesion
            [0.1, 0.3, 0.6, 1.0],   # Dermatofibroma
            [-0.6, -0.2, 0.2, 0.4],  # Melanocytic Nevus
        ]
    )
    BIAS = np.array([-0.4, -0.3, -0.2, 0.6, -0.2, 0.2, 1.0])

    def predict_probs(self, img):
        arr = np.asarray(img.convert("RGB").resize((224, 224)), dtype=np.float32) / 255.0
        lum = arr.mean(axis=2)
        features = np.array(
            [
                1.0 - float(lum.mean()),
                float(np.clip(arr[:, :, 0] - (arr[:, :, 1] + arr[:, :, 2]) / 2, 0, 1).mean()),
                float((arr.max(axis=2) - arr.min(axis=2)).mean()),
                float(lum.std() * 2),
            ]
        )
        scores = self.WEIGHTS @ features + self.BIAS
        scaled = scores * 2.0
        e = np.exp(scaled - scaled.max())
        return (e / e.sum()).astype(np.float64)


def get_model():
    """Lazy singleton: best available model + a mode string."""
    global _model, _model_mode
    if _model is None:
        with _lock:
            if _model is None:
                from config import Config

                path = Config.MODEL_PATH
                if path.endswith(".onnx"):
                    try:
                        _model = OnnxModel(path)
                        _model_mode = "onnx"
                    except Exception as exc:
                        logger.warning("ONNX model unavailable (%s); falling back", exc)
                else:
                    try:
                        _model = TorchModel(path)
                        _model_mode = "torch"
                    except Exception as exc:
                        logger.warning(
                            "PyTorch model unavailable (%s); falling back to demo model", exc
                        )
                if _model is None:
                    _model = DemoModel()
                    _model_mode = "demo"
    return _model, _model_mode


def predict(img):
    """PIL image -> risk assessment dict consumed by the upload endpoint."""
    model, mode = get_model()
    probs = model.predict_probs(img)  # length-7, sums to 1

    condition = CLASSES[int(np.argmax(probs))]
    confidence = {"Low": 0.0, "Medium": 0.0, "High": 0.0}
    for cls, p in zip(CLASSES, probs):
        confidence[CLASS_TO_RISK[cls].capitalize()] += float(p)
    risk = max(confidence, key=confidence.get).upper()

    result = {
        "risk_level": risk,
        "confidence": {k: round(v, 4) for k, v in confidence.items()},
        "condition_type": condition,
        "mode": mode,
        "recommendation": RECOMMENDATIONS[risk],
        "medical_disclaimer": DISCLAIMER,
    }
    if mode == "demo":
        result["notice"] = DEMO_NOTICE
    return result
