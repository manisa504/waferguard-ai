"""Equal-class batch exposure with categorical D4 transforms; validation-only selection."""

import json
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.metrics import classification_metrics
from waferguard.models.cnn import WaferCNN
from waferguard.training.experiment import provenance
from waferguard.training.train import (
    atomic_torch_save,
    cnn_probabilities,
    image_batches,
    labels_for,
)


def main():
    config_path = Path("configs/balanced.yaml")
    config = yaml.safe_load(config_path.read_text())
    root = Path("artifacts/experiments/gate4-balanced-v1")
    reports = Path("reports/metrics/gate4-balanced-v1")
    root.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    identity = provenance(config_path, Path(config["split_report"]))
    identity["parent_sha256"] = sha256(Path(config["parent"]))
    if (root / "identity.json").exists():
        if json.loads((root / "identity.json").read_text()) != identity:
            raise ValueError("Refinement identity changed; use a new run directory")
    else:
        write_json(root / "identity.json", identity)
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(config["seed"])
    train, validation = [
        PreparedSplit(
            Path(config["processed"]), Path(config["splits"]), Path(config["split_report"]), name
        )
        for name in ["train", "validation"]
    ]
    truth, val_truth = labels_for(train), labels_for(validation)
    counts = np.bincount(truth, minlength=len(train.classes))
    weights = 1 / counts
    weights /= weights.mean()
    model = WaferCNN(len(train.classes))
    parent = torch.load(config["parent"], map_location="cpu", weights_only=True)
    model.load_state_dict(parent["state_dict"])
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"]
    )
    loss_fn = nn.CrossEntropyLoss(weight=None)
    start, best, best_epoch, history = 0, -1.0, 0, []
    if (root / "last.pt").exists():
        checkpoint = torch.load(root / "last.pt", map_location="cpu", weights_only=True)
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        torch.set_rng_state(checkpoint["rng"])
        start, best, best_epoch, history = (
            checkpoint[key] for key in ["epoch", "best", "best_epoch", "history"]
        )
    for epoch in range(start, config["epochs"]):
        began = time.monotonic()
        rng = np.random.default_rng(config["seed"] + epoch)
        probability = 1 / counts[truth]
        order = rng.choice(
            len(train), size=len(train), replace=True, p=probability / probability.sum()
        )
        model.train()
        loss_sum = 0.0
        for step, (positions, images) in enumerate(
            image_batches(train, config["batch_size"], order)
        ):
            images = torch.rot90(images, int(rng.integers(4)), dims=(2, 3))
            if rng.random() < 0.5:
                images = images.flip(3)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(images), torch.from_numpy(truth[positions]))
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite loss")
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * len(positions)
            if step and step % 200 == 0:
                print(f"Balanced epoch {epoch + 1}: batch {step}", flush=True)
        probability = cnn_probabilities(model, validation, config["batch_size"])
        metrics = classification_metrics(val_truth, probability, list(train.classes))
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": loss_sum / len(train),
                "validation": metrics,
                "seconds": time.monotonic() - began,
                "drawn_class_counts": np.bincount(
                    truth[order], minlength=len(train.classes)
                ).tolist(),
                "unique_source_rows": int(np.unique(order).size),
            }
        )
        recall = metrics["per_class"]["Scratch"]["recall"]
        if recall >= config["minimum_scratch_recall"] and metrics["macro_f1"] > best:
            best, best_epoch = metrics["macro_f1"], epoch + 1
            atomic_torch_save(
                {
                    "state_dict": model.state_dict(),
                    "classes": list(train.classes),
                    "architecture": "cnn",
                    "epoch": best_epoch,
                },
                root / "best.pt",
            )
        atomic_torch_save(
            {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "rng": torch.get_rng_state(),
                "epoch": epoch + 1,
                "best": best,
                "best_epoch": best_epoch,
                "history": history,
            },
            root / "last.pt",
        )
        write_json(reports / "history.json", {"epochs": history})
        print(
            f"Balanced epoch {epoch + 1}: macro-F1={metrics['macro_f1']:.4f}, "
            f"Scratch recall={recall:.4f}",
            flush=True,
        )
    if best_epoch == 0:
        raise ValueError("Refinement still fails the predeclared Scratch gate")
    checkpoint = torch.load(root / "best.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["state_dict"])
    probability = cnn_probabilities(model, validation, config["batch_size"])
    np.savez_compressed(root / "validation.npz", truth=val_truth, probabilities=probability)
    result = {
        "identity": identity,
        "classes": list(train.classes),
        "best_epoch": best_epoch,
        "validation": classification_metrics(val_truth, probability, list(train.classes)),
        "model_sha256": sha256(root / "best.pt"),
        "loss_weights": None,
        "sampling": "inverse_frequency_with_replacement",
        "augmentation": "D4 categorical rotations/reflections",
        "architecture": "cnn",
        "selection_split": "validation",
        "test_evaluated": False,
        "minimum_scratch_recall": config["minimum_scratch_recall"],
        "lineage": "Sampled parent; equal-class draws with D4 augmentation; optimizer reset",
    }
    write_json(root / "result.json", result)
    write_json(reports / "result.json", result)
    print(json.dumps({"best_epoch": best_epoch, "macro_f1": best, "test_evaluated": False}))


if __name__ == "__main__":
    main()
