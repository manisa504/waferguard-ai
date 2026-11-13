#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --extra dev --frozen
(cd infrastructure/cdk && npm ci)
