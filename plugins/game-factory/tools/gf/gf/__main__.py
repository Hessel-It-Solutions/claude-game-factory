from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys

from .core import UsageError, find_root
from .schema import STATE_FIELDS
from .img import post, validate
from .cut import cut
from .board import board
from .codex import codex
from .assets import assets_add, assets_check
from .state import budget, state
from .check import check
from .context import context

CHROMA_CHOICES = ["magenta", "green", "none"]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gf", description="Game factory CLI")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("post", help="pixelize, lock to the palette, remove chroma, validate")
    x.add_argument("input"); x.add_argument("output"); x.add_argument("--width", type=int)
    x.add_argument("--pitch", default="auto"); x.add_argument("--chroma", choices=CHROMA_CHOICES, default="none")
    x.add_argument("--preview", type=int, default=0); x.add_argument("--rules"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=post)
    x = sub.add_parser("validate", help="palette, partial alpha, size and region rules (read only)")
    x.add_argument("paths", nargs="+"); x.add_argument("--rules"); x.add_argument("--size"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=validate)
    x = sub.add_parser("cut", help="cut a sheet or strip into cells")
    x.add_argument("sheet"); g = x.add_mutually_exclusive_group(required=True); g.add_argument("--grid"); g.add_argument("--auto", action="store_true")
    x.add_argument("--names"); x.add_argument("--cell"); x.add_argument("--margin", type=int, default=0); x.add_argument("--post", action="store_true")
    x.add_argument("--post-width", type=int); x.add_argument("--post-chroma", choices=CHROMA_CHOICES, default="none")
    x.add_argument("--json", action="store_true"); x.add_argument("outdir"); x.set_defaults(fn=cut)
    x = sub.add_parser("board", help="numbered contact sheet of NN.png frames")
    x.add_argument("folder"); x.add_argument("--out"); x.add_argument("--cols", type=int); x.add_argument("--scale", type=int, default=1)
    x.add_argument("--labels", action="store_true"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=board)
    x = sub.add_parser("codex", help="batch of Codex image generations through sprite-gen")
    x.add_argument("jobs"); x.add_argument("--parallel", type=int, default=1); x.add_argument("--dry-run", action="store_true"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=codex)
    assets = sub.add_parser("assets", help="asset registry").add_subparsers(dest="assets_command", required=True)
    x = assets.add_parser("add"); x.add_argument("jsonl"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=assets_add)
    x = assets.add_parser("check"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=assets_check)
    x = sub.add_parser("budget", help="append a row to production/BUDGET.md")
    x.add_argument("wave"); x.add_argument("before"); x.add_argument("after"); x.add_argument("--cap", required=True); x.add_argument("--notes", required=True)
    x.add_argument("--json", action="store_true"); x.set_defaults(fn=budget)
    x = sub.add_parser("state", help="update a field in production/STATE.md")
    x.add_argument("field", choices=list(STATE_FIELDS)); x.add_argument("value"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=state)
    x = sub.add_parser("check", help="mechanical continuity checks (read only)")
    x.add_argument("--scope"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=check)
    x = sub.add_parser("context", help="minimal context pack for a subagent prompt")
    x.add_argument("role"); x.add_argument("--seq"); x.add_argument("--chars"); x.add_argument("--locs"); x.add_argument("--out"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=context)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        root = find_root()
        if getattr(args, "json", False) and args.command not in {"validate", "check"}:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                code = args.fn(args, root)
            print(json.dumps({"code": code, "lines": captured.getvalue().splitlines()}, ensure_ascii=False))
            return code
        return args.fn(args, root)
    except UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
