"""Source, input and environment receipts for locally measured experiments."""

import platform
from pathlib import Path

import numpy as np
import sklearn
import torch

from waferguard.data.acquire import sha256


def provenance(config: Path, split_report: Path) -> dict:
    source = Path(__file__).parents[1]
    code = {
        path.relative_to(source).as_posix(): sha256(path) for path in sorted(source.rglob("*.py"))
    }
    return {
        "config_sha256": sha256(config),
        "split_report_sha256": sha256(split_report),
        "dependency_lock_sha256": sha256(Path("uv.lock")),
        "source_sha256": code,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
        "torch": torch.__version__,
        "revision": "Uncommitted local source; code hashes supplied, no remote publication",
        "reproducibility_limit": "Replay is scoped to pinned software, hardware and threads",
    }
