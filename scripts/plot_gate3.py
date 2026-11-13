"""Export figures from stored measured validation results, never example/modelled values."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path("reports/metrics/gate3-v1")
output = Path("reports/figures/gate3-v1")
output.mkdir(parents=True, exist_ok=True)
names = ["majority", "forest", "cnn"]
results = {name: json.loads((root / f"{name}-validation.json").read_text()) for name in names}
classes = results["cnn"]["metrics"]["classes"]
colors = ["#718096", "#167d9a", "#d75e3f"]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1, 2]})
metrics = [results[name]["metrics"]["macro_f1"] for name in names]
axes[0].bar(names, metrics, color=colors)
axes[0].set_ylim(0, 1)
axes[0].set_ylabel("Macro-F1")
axes[0].set_title("Validation classification performance")
for i, value in enumerate(metrics):
    axes[0].text(i, value + 0.025, f"{value:.3f}", ha="center")
positions = np.arange(len(classes))
for index, name in enumerate(names):
    recall = [results[name]["metrics"]["per_class"][label]["recall"] for label in classes]
    axes[1].bar(positions + (index - 1) * 0.26, recall, 0.26, label=name, color=colors[index])
axes[1].set_xticks(positions, classes, rotation=35, ha="right")
axes[1].set_ylim(0, 1.12)
axes[1].set_ylabel("Recall")
axes[1].set_title("Minority classes remain visible")
axes[1].legend(frameon=False, ncol=3)
fig.suptitle("WaferGuard · Gate 3 · Validation only · Uncalibrated models", fontsize=12)
fig.tight_layout()
for extension in ["png", "svg"]:
    fig.savefig(output / f"model-comparison.{extension}", dpi=180, bbox_inches="tight")
plt.close(fig)

for name in ["forest", "cnn"]:
    matrix = np.array(results[name]["metrics"]["confusion_matrix"])
    normalized = matrix / np.maximum(matrix.sum(axis=1, keepdims=True), 1)
    fig, axis = plt.subplots(figsize=(8.8, 7.2))
    image = axis.imshow(normalized, vmin=0, vmax=1, cmap="Blues")
    axis.set_xticks(range(len(classes)), classes, rotation=40, ha="right")
    axis.set_yticks(range(len(classes)), classes)
    axis.set(
        xlabel="Predicted class",
        ylabel="True class",
        title=f"{name.capitalize()} · Validation confusion matrix",
    )
    for i in range(len(classes)):
        for j in range(len(classes)):
            axis.text(
                j,
                i,
                str(matrix[i, j]),
                ha="center",
                va="center",
                fontsize=8,
                color="white" if normalized[i, j] > 0.55 else "#172a3a",
            )
    fig.colorbar(image, ax=axis, label="Fraction within true class")
    fig.tight_layout()
    for extension in ["png", "svg"]:
        fig.savefig(output / f"{name}-confusion.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)

history = json.loads((root / "cnn-history.json").read_text())["epochs"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
epochs = [row["epoch"] for row in history]
axes[0].plot(epochs, [row["train_loss"] for row in history], marker="o", color=colors[2])
axes[0].set(xlabel="Epoch", ylabel="Training cross-entropy", title="CNN training loss")
axes[1].plot(
    epochs, [row["validation_metrics"]["macro_f1"] for row in history], marker="o", color=colors[1]
)
axes[1].set(
    xlabel="Epoch",
    ylabel="Validation macro-F1",
    ylim=(0, 1),
    title="Checkpoint selection uses validation only",
)
fig.tight_layout()
for extension in ["png", "svg"]:
    fig.savefig(output / f"cnn-training.{extension}", dpi=180, bbox_inches="tight")
plt.close(fig)
print("Exported measured validation comparison, confusion matrices and training history")
