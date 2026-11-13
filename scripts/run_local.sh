#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo 'Gate 0–1: dataset tools only; application and trained model are not implemented.'
uv run --frozen waferguard-profile --help
