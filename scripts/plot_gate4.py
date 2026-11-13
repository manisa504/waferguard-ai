"""Scientific figures drawn exclusively from stored Gate 4 measurements."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

reports = Path("reports/metrics/gate4-final")
out = Path("reports/figures/gate4-v1")
out.mkdir(parents=True, exist_ok=True)
validation = json.loads((reports / "validation.json").read_text())
test = json.loads((reports / "test.json").read_text())
refined = json.loads(Path("reports/metrics/gate4-balanced-v1/result.json").read_text())
base = json.loads(Path("reports/metrics/gate3-v1/cnn-validation.json").read_text())["metrics"]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.tight_layout()
    for extension in ["png", "svg"]:
        fig.savefig(out / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)


classes = validation["classification"]["classes"]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
x = np.arange(len(classes))
axes[0].bar(
    x - 0.18,
    [base["per_class"][k]["recall"] for k in classes],
    0.36,
    label="Gate 3 baseline",
    color="#758493",
)
axes[0].bar(
    x + 0.18,
    [validation["classification"]["per_class"][k]["recall"] for k in classes],
    0.36,
    label="Balanced candidate",
    color="#087f8c",
)
axes[0].set_xticks(x, classes, rotation=35, ha="right")
axes[0].set(
    ylabel="Validation recall", ylim=(0, 1.14), title="Minority sensitivity, including Scratch"
)
axes[0].legend(frameon=False, fontsize=8)
for key, label, color in [
    ("calibration_before", "Before scaling", "#d56240"),
    ("calibration_after", "After scaling", "#087f8c"),
]:
    bins = [row for row in validation[key]["reliability"] if row["count"]]
    axes[1].plot(
        [r["confidence"] for r in bins],
        [r["accuracy"] for r in bins],
        marker="o",
        label=f"{label}: ECE {validation[key]['ece']:.3f}",
        color=color,
    )
axes[1].plot([0, 1], [0, 1], linestyle="--", color="#899499")
axes[1].set(
    xlabel="Mean class confidence",
    ylabel="Observed accuracy",
    title="Validation reliability; fit on calibration only",
    xlim=(0, 1),
    ylim=(0, 1),
)
axes[1].legend(frameon=False, fontsize=8)
save(fig, "recall-calibration")

fig, axis = plt.subplots(figsize=(8, 4.8))
curve = [r for r in validation["selective"]["curve"] if r["accepted"]]
curve = sorted(curve, key=lambda row: row["coverage"])
axis.plot(
    [r["coverage"] for r in curve],
    [r["risk"] for r in curve],
    label="Validation observed risk",
    color="#087f8c",
)
axis.plot(
    [r["coverage"] for r in curve],
    [r["wilson_upper_95"] for r in curve],
    label="95% Wilson upper bound",
    linestyle="--",
    color="#d56240",
)
axis.axhline(0.01, color="#899499", linestyle=":", label="Target accepted error")
selected = validation["selective"]["selected"]
if selected:
    axis.scatter(
        [selected["coverage"]],
        [selected["risk"]],
        s=65,
        color="#172d3c",
        label="Frozen selected threshold",
        zorder=5,
    )
else:
    axis.text(
        0.03, 0.95, "No feasible threshold: acceptance disabled", transform=axis.transAxes, va="top"
    )
axis.set(
    xlabel="Coverage (accepted fraction)",
    ylabel="Classification error among accepted",
    title="Selective classification · validation policy selection",
)
axis.legend(frameon=False, fontsize=8)
save(fig, "risk-coverage")

matrix = np.array(test["classification"]["confusion_matrix"])
normalized = matrix / np.maximum(matrix.sum(1, keepdims=True), 1)
fig, axis = plt.subplots(figsize=(9, 7))
image = axis.imshow(normalized, vmin=0, vmax=1, cmap="Blues")
axis.set_xticks(range(len(classes)), classes, rotation=40, ha="right")
axis.set_yticks(range(len(classes)), classes)
for i in range(len(classes)):
    for j in range(len(classes)):
        axis.text(
            j,
            i,
            str(matrix[i, j]),
            ha="center",
            va="center",
            fontsize=8,
            color="white" if normalized[i, j] > 0.55 else "#152b3c",
        )
axis.set(
    xlabel="Predicted class",
    ylabel="True class",
    title="Frozen candidate · held-out test confusion matrix",
)
fig.colorbar(image, ax=axis, label="Fraction within true class")
save(fig, "test-confusion")
print("Exported measured recall, calibration, selective-risk and frozen test figures")
