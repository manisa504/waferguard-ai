"""Gate 3: train-only fitting and validation-only measurement; test stays reserved."""

import argparse
import json
import os
import random
import time
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import torch
import yaml
from torch import nn

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.metrics import classification_metrics
from waferguard.features.wafer_features import FEATURE_NAMES, FEATURE_VERSION, extract_features
from waferguard.models.baseline import majority_class, make_forest
from waferguard.models.cnn import WaferCNN
from waferguard.training.experiment import provenance


def atomic_torch_save(value: dict, path: Path) -> None:
    temporary = path.with_suffix(".tmp")
    torch.save(value, temporary)
    os.replace(temporary, path)


def labels_for(dataset: PreparedSplit) -> np.ndarray:
    mapping = {name: index for index, name in enumerate(dataset.classes)}
    return np.array([mapping[row["label"]] for row in dataset.records], dtype=np.int64)


def image_batches(dataset: PreparedSplit, batch_size: int, order: np.ndarray):
    for start in range(0, len(order), batch_size):
        positions = order[start : start + batch_size]
        indices = [dataset.records[int(position)]["input_row"] for position in positions]
        grids = np.asarray(dataset.states[indices])
        states = torch.from_numpy(grids)
        image = (states.unsqueeze(1) == torch.arange(3).view(1, 3, 1, 1)).float()
        yield positions, image


def cnn_probabilities(model: WaferCNN, dataset: PreparedSplit, batch_size: int) -> np.ndarray:
    model.eval()
    result = []
    with torch.inference_mode():
        for _, images in image_batches(dataset, batch_size, np.arange(len(dataset))):
            result.append(model(images).softmax(dim=1).cpu().numpy())
    return np.concatenate(result)


def feature_matrix(dataset: PreparedSplit, destination: Path) -> np.ndarray:
    if destination.exists():
        raise ValueError("Unregistered feature cache exists")
    matrix = np.lib.format.open_memmap(
        destination, mode="w+", dtype=np.float32, shape=(len(dataset), len(FEATURE_NAMES))
    )
    for i, row in enumerate(dataset.records):
        matrix[i] = extract_features(dataset.states[row["input_row"]])
        if i and i % 25_000 == 0:
            print(f"{dataset.name}: extracted {i:,} feature vectors", flush=True)
    matrix.flush()
    return matrix


def save_result(
    root: Path,
    reports: Path,
    name: str,
    dataset: PreparedSplit,
    truth: np.ndarray,
    probabilities: np.ndarray,
    metadata: dict,
) -> dict:
    metrics = classification_metrics(truth, probabilities, list(dataset.classes))
    predictions = root / f"{name}-validation.npz"
    np.savez_compressed(
        predictions,
        truth=truth,
        probabilities=probabilities,
        row_ids=np.array([row["row_id"] for row in dataset.records]),
    )
    result = {
        "model": name,
        "split": "validation",
        "calibrated": False,
        "metrics": metrics,
        "metadata": metadata,
        "predictions_sha256": sha256(predictions),
    }
    write_json(reports / f"{name}-validation.json", result)
    write_json(root / f"{name}-result.json", result)
    print(
        f"{name}: validation macro-F1={metrics['macro_f1']:.4f}, "
        f"balanced accuracy={metrics['balanced_accuracy']:.4f}",
        flush=True,
    )
    return result


def run(config_path: Path, root: Path, reports: Path) -> dict:
    config = yaml.safe_load(config_path.read_text())
    if config["stage"] != "gate_3" or config["device"] != "cpu":
        raise ValueError("Gate 3 runner is configured for local CPU only")
    if config["validation_split"] != "validation":
        raise ValueError("Calibration/test cannot be used for Gate 3 model selection")
    if config["cnn"]["class_weights"] is not None or config["cnn"]["augmentation"]:
        raise ValueError("Class balancing and augmentation are separate later experiments")
    seed, threads = config["seed"], config["threads"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    identity = provenance(config_path, Path(config["split_report"]))
    identity["config"] = config
    receipt_path = root / "experiment.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["identity"] != identity:
            raise ValueError("Experiment code/config/environment changed; use a new run directory")
        if receipt["status"] == "completed":
            for name, digest in receipt["artifacts_sha256"].items():
                if sha256(root / name) != digest:
                    raise ValueError("Completed experiment artifact changed")
            return receipt
    else:
        root.mkdir(parents=True, exist_ok=False)
        receipt = {
            "identity": identity,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "status": "running",
            "selection_split": "validation",
            "calibration_used": False,
            "test_evaluated": False,
        }
        write_json(receipt_path, receipt)
    reports.mkdir(parents=True, exist_ok=True)
    print("Verifying audited train and validation artifacts", flush=True)
    processed, splits, audit = (
        Path(config[key]) for key in ["processed", "splits", "split_report"]
    )
    train = PreparedSplit(processed, splits, audit, "train")
    validation = PreparedSplit(processed, splits, audit, "validation")
    if train.classes != validation.classes:
        raise ValueError("Class ordering differs between splits")
    classes = len(train.classes)
    y_train, y_validation = labels_for(train), labels_for(validation)
    baseline_receipt = root / "baselines.json"
    results = {}
    if baseline_receipt.exists():
        saved = json.loads(baseline_receipt.read_text())
        for name, digest in saved["artifacts_sha256"].items():
            if sha256(root / name) != digest:
                raise ValueError("Baseline artifact changed")
        results.update(saved["results"])
    else:
        majority = majority_class(y_train, classes)
        probabilities = np.zeros((len(validation), classes), dtype=np.float32)
        probabilities[:, majority] = 1
        results["majority"] = save_result(
            root,
            reports,
            "majority",
            validation,
            y_validation,
            probabilities,
            {"training_majority": train.classes[majority]},
        )
        feature_files = []
        for split in [train, validation]:
            path = root / f"{split.name}-features.npy"
            # An incomplete previous extraction has no registered checksum; regenerate it.
            if path.exists():
                path.unlink()
            feature_matrix(split, path)
            feature_files.append(path)
        x_train, x_validation = [
            np.load(path, mmap_mode="r", allow_pickle=False) for path in feature_files
        ]
        forest = make_forest(config["forest"], seed, threads)
        print(f"Fitting unweighted forest on all {len(train):,} training records", flush=True)
        start = time.monotonic()
        forest.fit(x_train, y_train)
        fit_seconds = time.monotonic() - start
        if list(forest.classes_) != list(range(classes)):
            raise ValueError("Forest omitted a configured class")
        temporary = root / "forest.tmp"
        joblib.dump(forest, temporary, compress=3)
        os.replace(temporary, root / "forest.joblib")
        probabilities = forest.predict_proba(x_validation)
        results["forest"] = save_result(
            root,
            reports,
            "forest",
            validation,
            y_validation,
            probabilities,
            {
                "fit_seconds": fit_seconds,
                "feature_version": FEATURE_VERSION,
                "features": len(FEATURE_NAMES),
                "feature_importances": dict(
                    zip(FEATURE_NAMES, forest.feature_importances_.tolist(), strict=True)
                ),
            },
        )
        del forest, x_train, x_validation
        names = [
            "forest.joblib",
            "majority-validation.npz",
            "forest-validation.npz",
            "majority-result.json",
            "forest-result.json",
        ] + [p.name for p in feature_files]
        write_json(
            baseline_receipt,
            {"results": results, "artifacts_sha256": {name: sha256(root / name) for name in names}},
        )
    model = WaferCNN(classes)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["cnn"]["learning_rate"],
        weight_decay=config["cnn"]["weight_decay"],
    )
    loss_function = nn.CrossEntropyLoss()
    history, start_epoch, best_score, best_epoch = [], 0, -1.0, 0
    last = root / "cnn-last.pt"
    if last.exists():
        checkpoint = torch.load(last, map_location="cpu", weights_only=True)
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        torch.set_rng_state(checkpoint["torch_rng_state"])
        history, start_epoch = checkpoint["history"], checkpoint["epoch"]
        best_score, best_epoch = checkpoint["best_score"], checkpoint["best_epoch"]
        print(f"Resuming completed epoch {start_epoch}", flush=True)
    batch_size = config["cnn"]["batch_size"]
    for epoch in range(start_epoch, config["cnn"]["epochs"]):
        started = time.monotonic()
        model.train()
        order = np.random.default_rng(seed + epoch).permutation(len(train))
        total_loss, examples = 0.0, 0
        for step, (positions, images) in enumerate(image_batches(train, batch_size, order)):
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(images), torch.from_numpy(y_train[positions]))
            if not torch.isfinite(loss):
                raise ValueError("Training loss is nonfinite")
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(positions)
            examples += len(positions)
            if step and step % 100 == 0:
                print(f"CNN epoch {epoch + 1}: {examples:,}/{len(train):,} records", flush=True)
        probabilities = cnn_probabilities(model, validation, batch_size)
        metrics = classification_metrics(y_validation, probabilities, list(train.classes))
        item = {
            "epoch": epoch + 1,
            "train_loss": total_loss / examples,
            "validation_metrics": metrics,
            "duration_seconds": time.monotonic() - started,
        }
        history.append(item)
        if metrics["macro_f1"] > best_score:
            best_score, best_epoch = metrics["macro_f1"], epoch + 1
            atomic_torch_save(
                {
                    "state_dict": model.state_dict(),
                    "classes": list(train.classes),
                    "epoch": best_epoch,
                },
                root / "cnn-best.pt",
            )
        atomic_torch_save(
            {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "torch_rng_state": torch.get_rng_state(),
                "epoch": epoch + 1,
                "history": history,
                "best_score": best_score,
                "best_epoch": best_epoch,
            },
            last,
        )
        write_json(root / "cnn-history.json", {"epochs": history})
        write_json(reports / "cnn-history.json", {"epochs": history})
        print(
            f"CNN epoch {epoch + 1}: loss={item['train_loss']:.4f}; "
            f"validation macro-F1={metrics['macro_f1']:.4f}; "
            f"seconds={item['duration_seconds']:.1f}",
            flush=True,
        )
    best = torch.load(root / "cnn-best.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(best["state_dict"])
    probabilities = cnn_probabilities(model, validation, batch_size)
    results["cnn"] = save_result(
        root,
        reports,
        "cnn",
        validation,
        y_validation,
        probabilities,
        {
            "best_epoch": best_epoch,
            "selection": "validation macro-F1",
            "parameters": sum(p.numel() for p in model.parameters()),
            "train_records": len(train),
            "device": "cpu",
            "threads": threads,
            "epochs": config["cnn"]["epochs"],
        },
    )
    for name, digest in identity["source_sha256"].items():
        if sha256(Path(__file__).parents[1] / name) != digest:
            raise ValueError("Source changed during training; refuse completed experiment")
    if (
        sha256(config_path) != identity["config_sha256"]
        or sha256(Path("uv.lock")) != identity["dependency_lock_sha256"]
    ):
        raise ValueError("Configuration/dependencies changed during training")
    candidates = {name: result["metrics"]["macro_f1"] for name, result in results.items()}
    receipt.update(
        {
            "status": "completed",
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "classes": list(train.classes),
            "validation_results": results,
            "validation_selected_model": max(candidates, key=candidates.get),
            "artifacts_sha256": {
                path.name: sha256(path)
                for path in sorted(root.iterdir())
                if path.is_file() and path != receipt_path
            },
        }
    )
    write_json(receipt_path, receipt)
    write_json(reports / "experiment.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/train.yaml"))
    parser.add_argument("--run", type=Path, default=Path("artifacts/experiments/gate3-v1"))
    parser.add_argument("--reports", type=Path, default=Path("reports/metrics/gate3-v1"))
    args = parser.parse_args()
    result = run(args.config, args.run, args.reports)
    print(
        json.dumps(
            {
                "status": result["status"],
                "validation_selected_model": result["validation_selected_model"],
                "test_evaluated": result["test_evaluated"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
