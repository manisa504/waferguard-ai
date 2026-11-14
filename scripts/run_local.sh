#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_public_site.py
printf 'WaferGuard local research app: http://127.0.0.1:%s/DOC/app/\n' "${PORT:-8768}"
python3 -m http.server "${PORT:-8768}" --bind 127.0.0.1 --directory .public-site
