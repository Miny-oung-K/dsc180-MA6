#!/usr/bin/env bash
set -eu

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -x "$root/.venv/bin/python" ]; then
  python="$root/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  python=python
else
  python=python3
fi

exec "$python" -c '
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
event = json.load(sys.stdin)
if event.get("tool_name") not in {"Edit", "Write"}:
    sys.exit(0)

file_path = event.get("tool_input", {}).get("file_path")
if not file_path or not (root / file_path).resolve().is_relative_to(root / "src"):
    sys.exit(0)

tests = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--color=no"],
    cwd=root,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
if tests.returncode:
    sys.stderr.write(tests.stdout)
    sys.exit(2)
' "$root"
