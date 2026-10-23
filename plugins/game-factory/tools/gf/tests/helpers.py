import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]


def make_project(root: Path, palette: str = "161412\nb08645\n", speakers: dict | None = None) -> Path:
    """Minimal game repo: production/STATE.md, docs/palette.hex, tools/gf/gf.json."""
    for folder in ["production", "docs/05-script", "docs/06-storyboard", "docs/03-characters", "tools/gf", "art"]:
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "production/STATE.md").write_text("# State\n\nCurrent wave: W1\nNext step: start\n")
    (root / "production/ASSETS.md").write_text("# Assets\n\n| asset_id | type | file | model | task_id | refs | credits | status | wave |\n|---|---|---|---|---|---|---|---|---|\n")
    (root / "production/BUDGET.md").write_text("# Budget\n\n| wave | before | cap | spent | after | notes |\n|---|---|---|---|---|---|\n")
    (root / "docs/palette.hex").write_text(palette)
    config = json.loads((TOOL / "gf.json").read_text())
    config["speakers"] = speakers or {}
    (root / "tools/gf/gf.json").write_text(json.dumps(config))
    return root


def run_gf(root: Path, *args):
    env = {**os.environ, "PYTHONPATH": str(TOOL)}
    return subprocess.run([sys.executable, "-m", "gf", *map(str, args)], cwd=root, env=env, text=True, capture_output=True)
