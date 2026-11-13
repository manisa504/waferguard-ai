"""Fail CI if raw data, trained weights or credential files are tracked."""

import subprocess
from pathlib import PurePosixPath

tracked = (
    subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    .decode()
    .split("\0")
)
for name in filter(None, tracked):
    path = PurePosixPath(name)
    if (
        (name.startswith("data/raw/") and path.name != ".gitkeep")
        or name.startswith(("data/processed/", "artifacts/"))
        or path.suffix in {".pkl", ".pickle", ".zip", ".pt", ".pth", ".npy", ".npz", ".joblib"}
        or path.name in {".env", "kaggle.json", "credentials"}
        or (path.name.startswith(".env.") and path.name != ".env.example")
    ):
        raise SystemExit(f"Prohibited tracked file: {name}")
print("Tracked-file checks passed")
