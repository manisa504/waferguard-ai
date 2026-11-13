"""Controlled imbalance experiments selected on validation only."""

import argparse
import json
import random
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.metrics import classification_metrics
from waferguard.models.cnn import WaferCNN
from waferguard.models.lite import WaferLiteCNN
from waferguard.training.experiment import provenance
from waferguard.training.train import (
    atomic_torch_save,
    cnn_probabilities,
    image_batches,
    labels_for,
)


def make_model(architecture, classes):
    return WaferCNN(classes) if architecture == "cnn" else WaferLiteCNN(classes)


def run(config_path, root, reports):
    config = yaml.safe_load(config_path.read_text())
    identity = provenance(config_path, Path(config["split_report"]))
    root.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    receipt_path = root / "identity.json"
    if receipt_path.exists():
        if json.loads(receipt_path.read_text()) != identity:
            raise ValueError("Advanced experiment identity changed; use a new run")
    else:
        write_json(receipt_path, identity)
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    data = [
        PreparedSplit(
            Path(config["processed"]), Path(config["splits"]), Path(config["split_report"]), name
        )
        for name in ["train", "validation"]
    ]
    train, validation = data
    y_train, y_val = labels_for(train), labels_for(validation)
    counts = np.bincount(y_train, minlength=len(train.classes))
    raw_weights = 1 / np.sqrt(counts)
    weights = raw_weights / raw_weights.mean()
    outputs = {}
    for experiment in config["experiments"]:
        destination = root / experiment["name"]
        destination.mkdir(exist_ok=True)
        result_path = destination / "result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            if sha256(destination / "best.pt") != result["model_sha256"]:
                raise ValueError("Advanced checkpoint changed")
            outputs[experiment["name"]] = result
            continue
        seed = config["seed"]
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        model = make_model(experiment["architecture"], len(train.classes))
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"]
        )
        loss_fn = nn.CrossEntropyLoss(
            weight=(
                torch.tensor(weights, dtype=torch.float32)
                if experiment["weighting"] == "inverse_sqrt"
                else None
            )
        )
        best_score, best_epoch, history, start = -1.0, 0, [], 0
        if (destination / "last.pt").exists():
            saved = torch.load(destination / "last.pt", weights_only=True, map_location="cpu")
            model.load_state_dict(saved["model"])
            optimizer.load_state_dict(saved["optimizer"])
            torch.set_rng_state(saved["rng"])
            best_score, best_epoch = saved["best_score"], saved["best_epoch"]
            history, start = saved["history"], saved["epoch"]
        print(f"Training {experiment['name']} on {len(train):,} real records", flush=True)
        for epoch in range(start, config["epochs"]):
            started = time.monotonic()
            rng = np.random.default_rng(seed + epoch)
            if experiment["sampling"]:
                probability = raw_weights[y_train]
                order = rng.choice(
                    len(train), len(train), replace=True, p=probability / probability.sum()
                )
            else:
                order = rng.permutation(len(train))
            model.train()
            total, seen = 0.0, 0
            for step, (positions, images) in enumerate(
                image_batches(train, config["batch_size"], order)
            ):
                if experiment["augmentation"]:
                    # Categorical D4 transforms remain within the originating split.
                    images = torch.rot90(images, int(rng.integers(4)), dims=(2, 3))
                    if rng.random() < 0.5:
                        images = images.flip(3)
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(images), torch.from_numpy(y_train[positions]))
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite training loss")
                loss.backward()
                optimizer.step()
                total += float(loss.detach()) * len(positions)
                seen += len(positions)
                if step and step % 200 == 0:
                    print(f"{experiment['name']} epoch {epoch + 1}: {seen:,} samples", flush=True)
            probability = cnn_probabilities(model, validation, config["batch_size"])
            metrics = classification_metrics(y_val, probability, list(train.classes))
            history.append(
                {
                    "epoch": epoch + 1,
                    "loss": total / seen,
                    "validation": metrics,
                    "seconds": time.monotonic() - started,
                }
            )
            if metrics["macro_f1"] > best_score:
                best_score, best_epoch = metrics["macro_f1"], epoch + 1
                atomic_torch_save(
                    {
                        "state_dict": model.state_dict(),
                        "classes": list(train.classes),
                        "architecture": experiment["architecture"],
                        "epoch": best_epoch,
                    },
                    destination / "best.pt",
                )
            atomic_torch_save(
                {
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "rng": torch.get_rng_state(),
                    "epoch": epoch + 1,
                    "best_score": best_score,
                    "best_epoch": best_epoch,
                    "history": history,
                },
                destination / "last.pt",
            )
            write_json(destination / "history.json", {"epochs": history})
            print(
                f"{experiment['name']} epoch {epoch + 1}: macro-F1={metrics['macro_f1']:.4f}, "
                f"Scratch recall={metrics['per_class']['Scratch']['recall']:.4f}",
                flush=True,
            )
        checkpoint = torch.load(destination / "best.pt", weights_only=True, map_location="cpu")
        model.load_state_dict(checkpoint["state_dict"])
        probability = cnn_probabilities(model, validation, config["batch_size"])
        np.savez_compressed(destination / "validation.npz", probabilities=probability, truth=y_val)
        result = {
            "experiment": experiment,
            "classes": list(train.classes),
            "best_epoch": best_epoch,
            "validation": classification_metrics(y_val, probability, list(train.classes)),
            "model_sha256": sha256(destination / "best.pt"),
            "predictions_sha256": sha256(destination / "validation.npz"),
            "parameters": sum(p.numel() for p in model.parameters()),
            "train_counts": counts.tolist(),
            "loss_weights": weights.tolist(),
            "identity": identity,
            "created_at_utc": datetime.now(UTC).isoformat(),
        }
        write_json(result_path, result)
        write_json(reports / f"{experiment['name']}.json", result)
        write_json(reports / f"{experiment['name']}-history.json", {"epochs": history})
        outputs[experiment["name"]] = result
    eligible = {
        name: result
        for name, result in outputs.items()
        if result["validation"]["per_class"]["Scratch"]["recall"]
        >= config["minimum_scratch_recall"]
    }
    if not eligible:
        raise ValueError("No candidate meets the predeclared Scratch recall gate")
    selected = max(eligible, key=lambda name: eligible[name]["validation"]["macro_f1"])
    summary = {
        "selected": selected,
        "selection_split": "validation",
        "test_evaluated": False,
        "minimum_scratch_recall": config["minimum_scratch_recall"],
        "results": {
            name: {
                "macro_f1": item["validation"]["macro_f1"],
                "scratch_recall": item["validation"]["per_class"]["Scratch"]["recall"],
            }
            for name, item in outputs.items()
        },
    }
    write_json(reports / "selection.json", summary)
    write_json(root / "selection.json", summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/advanced.yaml"))
    parser.add_argument("--run", type=Path, default=Path("artifacts/experiments/gate4-v1"))
    parser.add_argument("--reports", type=Path, default=Path("reports/metrics/gate4-v1"))
    args = parser.parse_args()
    run(args.config, args.run, args.reports)


if __name__ == "__main__":
    main()
