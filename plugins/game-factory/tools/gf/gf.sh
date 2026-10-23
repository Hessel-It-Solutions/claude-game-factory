#!/bin/sh
# Runs the gf CLI. Uses the sprite-gen venv when it exists, else python3
# (which needs Pillow and numpy).
set -eu
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$SELF_DIR/../.." && pwd)
export PYTHONPATH="$SELF_DIR${PYTHONPATH:+:$PYTHONPATH}"
PY="$REPO/tools/sprite-gen/.venv/bin/python"
[ -x "$PY" ] || PY=python3
exec "$PY" -m gf "$@"
