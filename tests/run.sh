#!/usr/bin/env bash
# Launch Bashboard with the test scripts.json.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec .venv/bin/python main.py --config tests/scripts.json "$@"
