#!/usr/bin/env python3
"""Merge the changes of several batch clones into the main tree, file by file.

usage: merge_batches.py --base <baseline dir> --main <main tree> [--apply] <clone> [<clone> ...]

For every file that a clone changed relative to the baseline (same bytes check), do a
three-way merge with `git merge-file` into the main tree:
  - file untouched in main since the baseline: take the clone's version
  - file also changed in main (or by another clone merged earlier): git merge-file
  - conflicts: the file is written with conflict markers and listed at the end

Without --apply it only prints what would happen (dry run). Nothing is deleted: a file
removed in a clone is reported, not removed. Skips .git, .godot and .captures.
Baseline = a pristine clone or checkout taken when the batches were launched.
The dry run cannot predict conflicts between clones (each merge changes main), so review the
diff after --apply on a committed main tree.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKIP = {".git", ".godot", ".captures", "__pycache__", ".DS_Store"}


def walk(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not (set(path.relative_to(root).parts) & SKIP):
            yield path.relative_to(root)


def same(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--main", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("clones", nargs="+", type=Path)
    args = ap.parse_args()

    conflicts, merged, copied, removed = [], [], [], []
    for clone in args.clones:
        for rel in sorted(walk(clone)):
            c, b, m = clone / rel, args.base / rel, args.main / rel
            if same(c, b):
                continue  # the clone did not change this file
            if not m.exists() and not b.exists():
                copied.append((clone.name, rel))  # new file
                if args.apply:
                    m.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(c, m)
                continue
            if same(m, b) or not m.exists():
                copied.append((clone.name, rel))  # main did not touch it: take the clone's
                if args.apply:
                    m.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(c, m)
                continue
            if same(m, c):
                continue
            if not b.exists():
                conflicts.append((clone.name, rel))  # added on both sides with different content
                continue
            if args.apply:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                shutil.copy2(m, tmp_path)
                result = subprocess.run(["git", "merge-file", "-L", "main", "-L", "base", "-L", clone.name,
                                         str(tmp_path), str(b), str(c)], capture_output=True)
                if result.returncode < 0:
                    print(f"git merge-file failed on {rel}: {result.stderr.decode()}", file=sys.stderr)
                    return 2
                shutil.copy2(tmp_path, m)
                tmp_path.unlink()
                (conflicts if result.returncode > 0 else merged).append((clone.name, rel))
            else:
                merged.append((clone.name, rel))
        for rel in sorted(walk(args.base)):
            if not (clone / rel).exists():
                removed.append((clone.name, rel))

    verb = "" if args.apply else "would be "
    print(f"{len(copied)} file(s) {verb}taken as is, {len(merged)} {verb}three-way merged, "
          f"{len(conflicts)} conflict(s), {len(removed)} deleted in a clone (not removed)")
    for label, items in (("taken", copied), ("merged", merged), ("CONFLICT", conflicts), ("deleted in clone", removed)):
        for name, rel in items:
            print(f"{label}: {name}: {rel}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
