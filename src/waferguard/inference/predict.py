"""Serve only an integrity-checked, calibrated release bundle."""

import json
from pathlib import Path

import numpy as np
import torch

from waferguard.data.acquire import sha256
from waferguard.data.preprocess import encode_wafer
from waferguard.data.validate import map_fingerprint
from waferguard.evaluation.calibration import probabilities
from waferguard.evaluation.ood import score
from waferguard.features.wafer_features import extract_features
from waferguard.training.advanced import make_model


class ModelBundle:
    def __init__(self, directory):
        self.path = Path(directory)
        self.manifest = json.loads((self.path / "manifest.json").read_text())
        if not self.manifest.get("qualification", {}).get("qualified_for_promotion", False):
            raise ValueError("Model release is unqualified; promotion is blocked")
        for name, digest in self.manifest["artifacts"].items():
            if Path(name).name != name or sha256(self.path / name) != digest:
                raise ValueError("Release bundle integrity check failed")
        self.calibration = json.loads((self.path / "calibration.json").read_text())
        self.policy = json.loads((self.path / "policy.json").read_text())
        self.guard = json.loads((self.path / "ood.json").read_text())
        self.samples = json.loads((self.path / "samples.json").read_text())
        self.classes = self.manifest["classes"]
        torch.set_num_threads(2)
        checkpoint = torch.load(self.path / "model.pt", map_location="cpu", weights_only=True)
        if checkpoint["classes"] != self.classes:
            raise ValueError("Checkpoint class order mismatch")
        self.model = make_model(checkpoint["architecture"], len(self.classes))
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()

    def versions(self):
        return {key: self.manifest[key + "_version"] for key in ["model", "calibration", "policy"]}

    def predict(self, wafer):
        states = np.asarray(wafer)
        if states.ndim != 2 or max(states.shape) > 256 or not np.isin(states, [0, 1, 2]).all():
            raise ValueError("Expected a categorical wafer grid with dimensions <=256")
        if np.count_nonzero(states) < 8:
            raise ValueError("Insufficient active die evidence")
        original_hash = map_fingerprint(states)
        image = encode_wafer(states, 64)
        encoded = image.argmax(0).astype(np.uint8)
        features = extract_features(encoded)
        distance = float(score(features, self.guard))
        with torch.inference_mode():
            logits = self.model(torch.from_numpy(image[None])).numpy()
        probability = probabilities(logits, self.calibration["temperature"])[0]
        predicted = int(probability.argmax())
        return {
            "predicted_class": self.classes[predicted],
            "confidence": float(probability[predicted]),
            "probabilities": dict(zip(self.classes, probability.tolist(), strict=True)),
            "ood": distance > self.guard["threshold"],
            "ood_score": distance,
            "input_hash": original_hash,
            "model_version": self.manifest["model_version"],
            "calibration_version": self.manifest["calibration_version"],
            "policy_version": self.manifest["policy_version"],
            "calibrated": True,
        }
